import os
import pandas as pd
import numpy as np

from typing import Dict, Any, List, Optional, Tuple
from backend.app.schemas.sov_schema import (
    PipelineState,
    SheetDiscoveryResult,
    SchemaMappingResult,
    DataQualityReport,
    RecommendationItem,
    CleanedSOVResult,
    AuditEntry
)
from backend.app.orchestration.state import state_manager
from backend.app.services.excel_service import ExcelService
from backend.app.services.validation_service import ValidationService
from backend.app.services.llm_service import llm_service
from backend.app.agents.sheet_agent import SheetIntelligenceAgent
from backend.app.agents.schema_agent import SchemaMappingAgent
from backend.app.agents.quality_agent import DataQualityAgent
from backend.app.agents.transformation_agent import ControlledTransformationAgent

class SOVOrchestrator:
    """
    Lightweight explicit state machine orchestrating the 4-agent pipeline.
    Manages stage transitions, data handoffs, human review gate, and re-reasoning.
    """

    def __init__(self):
        self.sheet_agent = SheetIntelligenceAgent()
        self.schema_agent = SchemaMappingAgent()
        self.quality_agent = DataQualityAgent()
        self.transformation_agent = ControlledTransformationAgent()

    def run_intake_pipeline(self, session_id: str) -> PipelineState:
        """
        Executes Agents 1, 2, and 3 sequentially:
        1. Agent 1: Sheet Intelligence & Discovery
        2. Agent 2: Schema Mapping
        3. Agent 3: Data Quality & Reasoning
        Halts before Agent 4 for Human-in-the-Loop Review.
        """
        state = state_manager.get_session(session_id)
        if not state or not state.raw_file_path:
            raise ValueError(f"Invalid session {session_id}")

        file_path = state.raw_file_path

        # -------------------------------------------------------------
        # STEP 1: AGENT 1 - SHEET INTELLIGENCE & DISCOVERY
        # -------------------------------------------------------------
        state_manager.log_agent_event(state, "Agent 1: Sheet Intelligence", "Scanning workbook structure and header candidates...")
        sheet_result = self.sheet_agent.run(file_path)
        
        if not sheet_result.selected_sheet:
            state.errors.append("Could not identify a primary data sheet in the uploaded file.")
            state_manager.log_agent_event(state, "Agent 1: Sheet Intelligence", "Failed to select primary sheet", "error")
            return state

        selected = sheet_result.selected_sheet
        state_manager.update_sheet_discovery(session_id, sheet_result.sheets, selected)

        # Extract authoritative DataFrame
        raw_df = ExcelService.extract_dataframe(file_path, selected.sheet_name, selected.header_row)

        # -------------------------------------------------------------
        # STEP 2: AGENT 2 - SCHEMA MAPPING
        # -------------------------------------------------------------
        state_manager.log_agent_event(state, "Agent 2: Schema Mapping", f"Executing two-pass mapping on sheet '{selected.sheet_name}'...")
        mapping_result = self.schema_agent.run(raw_df, selected.sheet_name, selected.header_row)
        state_manager.update_schema_mapping(session_id, mapping_result)

        # -------------------------------------------------------------
        # STEP 3: AGENT 3 - DATA QUALITY & REASONING
        # -------------------------------------------------------------
        state_manager.log_agent_event(state, "Agent 3: Data Quality", "Assessing dataset completeness, anomalies, and business rules...")
        quality_report, recommendations = self.quality_agent.run(raw_df, mapping_result.mappings)
        state_manager.update_data_quality(session_id, quality_report, recommendations)

        state_manager.log_agent_event(
            state,
            "Human-in-the-Loop Gateway",
            "Intake pipeline complete. Awaiting human approval before transformation.",
            "pending"
        )
        return state

    def handle_re_reasoning(self, session_id: str, rec_id: str, feedback: str) -> Optional[RecommendationItem]:
        """
        Bonus Feature: Agent re-reasons when human reviewer rejects recommendation with feedback.
        """
        state = state_manager.get_session(session_id)
        if not state:
            return None

        # Find target recommendation
        target_rec = next((r for r in state.recommendations if r.id == rec_id), None)
        if not target_rec:
            return None

        state_manager.log_agent_event(
            state,
            "Agent 3: Data Quality & Reasoning",
            f"Reviewer rejected recommendation {rec_id} with feedback: '{feedback}'. Re-evaluating..."
        )

        re_result = llm_service.re_reason_rejected_recommendation(target_rec.model_dump(), feedback)
        
        target_rec.proposed_after = re_result.get("revised_action", target_rec.proposed_after)
        target_rec.reasoning = re_result.get("revised_reasoning", target_rec.reasoning)
        target_rec.confidence = float(re_result.get("revised_confidence", target_rec.confidence))
        target_rec.rejection_feedback = feedback
        target_rec.status = "modified"

        state_manager.log_agent_event(
            state,
            "Agent 3: Data Quality & Reasoning",
            f"Re-reasoning completed for {rec_id}: {target_rec.reasoning}",
            "success"
        )
        return target_rec

    def execute_controlled_transformation(
        self,
        session_id: str,
        decisions: Dict[str, Dict[str, Any]],
        mapping_overrides: Optional[Dict[str, str]] = None,
        approved_by: str = "Human Reviewer"
    ) -> CleanedSOVResult:
        """
        Executes AGENT 4 only after human approval.
        Applies approved transformations, validates schema, and writes Cleaned_SOV.xlsx & Audit_Log.
        """
        state = state_manager.get_session(session_id)
        if not state or not state.selected_sheet or not state.schema_mapping:
            raise ValueError("Incomplete pipeline state. Run intake first.")

        state_manager.log_agent_event(
            state,
            "Agent 4: Controlled Transformation",
            f"Applying {len([d for d in decisions.values() if d.get('status') == 'accepted'])} approved human transformations..."
        )

        # Load raw dataframe
        raw_df = ExcelService.extract_dataframe(
            state.raw_file_path, state.selected_sheet.sheet_name, state.selected_sheet.header_row
        )

        # Combine confirmed mappings with user overrides
        confirmed_mappings = {}
        for src_col, col_map in state.schema_mapping.mappings.items():
            if col_map.target_column:
                confirmed_mappings[src_col] = col_map.target_column

        if mapping_overrides:
            for src_col, target_col in mapping_overrides.items():
                if target_col:
                    confirmed_mappings[src_col] = target_col
                elif src_col in confirmed_mappings:
                    del confirmed_mappings[src_col]

        # Execute transformation in Agent 4
        final_df, audit_log, errors = self.transformation_agent.execute_transformations(
            raw_df=raw_df,
            confirmed_mappings=confirmed_mappings,
            recommendations=state.recommendations,
            approved_decisions=decisions,
            approved_by=approved_by
        )

        # Validate conformance to strict 17-field schema (NFR-5)
        is_valid, validation_errors, metrics = ValidationService.validate_cleaned_dataframe(final_df)
        if not is_valid:
            state.errors.extend(validation_errors)
            state_manager.log_agent_event(
                state, "Schema Validation Gate", f"Schema validation warning: {'; '.join(validation_errors)}", "warning"
            )

        # Export Cleaned_SOV.xlsx and Audit_Log
        sov_path, audit_xlsx_path, audit_json_path = self.transformation_agent.export_cleaned_sov(
            final_df=final_df,
            audit_log=audit_log,
            session_id=session_id
        )

        # Update state
        state.audit_log = audit_log
        state.final_output_ready = True
        state.cleaned_file_path = sov_path
        state.audit_xlsx_path = audit_xlsx_path
        state.audit_json_path = audit_json_path

        state_manager.log_agent_event(
            state,
            "Agent 4: Controlled Transformation",
            f"Successfully generated Cleaned_SOV.xlsx with 17 strictly typed columns and recorded {len(audit_log)} audit entries.",
            "success"
        )

        # Generate sample preview
        preview_records = final_df.head(10).replace({np.nan: None}).to_dict(orient="records")

        return CleanedSOVResult(
            success=True,
            message="Cleaned SOV and Audit Log generated successfully.",
            row_count=len(final_df),
            column_count=len(final_df.columns),
            columns=list(final_df.columns),
            sample_preview=preview_records,
            total_transformations_applied=len(audit_log),
            audit_log_count=len(audit_log),
            download_sov_url=f"/api/export/{session_id}/Cleaned_SOV.xlsx",
            download_audit_xlsx_url=f"/api/export/{session_id}/Audit_Log.xlsx",
            download_audit_json_url=f"/api/export/{session_id}/Audit_Log.json"
        )

# Global orchestrator instance
orchestrator = SOVOrchestrator()
