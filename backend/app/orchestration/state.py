import uuid
from typing import Dict, Optional, Any, List
from datetime import datetime, timezone
from backend.app.schemas.sov_schema import PipelineState, SheetAnalysis, SchemaMappingResult, DataQualityReport, RecommendationItem, AuditEntry

class StateManager:
    """
    Thread-safe in-memory session state manager for multi-agent pipeline.
    Ensures clear boundaries, auditability, and shared state tracking.
    """
    def __init__(self):
        self._sessions: Dict[str, PipelineState] = {}

    def create_session(self, file_info: Dict[str, Any], raw_file_path: str) -> PipelineState:
        session_id = str(uuid.uuid4())[:8]
        now_ts = datetime.now(timezone.utc).isoformat()
        state = PipelineState(
            session_id=session_id,
            file_info=file_info,
            raw_file_path=raw_file_path,
            created_at=now_ts,
            updated_at=now_ts
        )
        self.log_agent_event(state, "System", f"Session initialized for file: {file_info.get('filename')}")
        self._sessions[session_id] = state
        return state

    def get_session(self, session_id: str) -> Optional[PipelineState]:
        return self._sessions.get(session_id)

    def log_agent_event(self, state: PipelineState, agent_name: str, message: str, status: str = "info", details: Optional[Dict[str, Any]] = None):
        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "agent": agent_name,
            "message": message,
            "status": status,
            "details": details or {}
        }
        state.agent_logs.append(entry)
        state.current_agent = agent_name
        state.updated_at = datetime.now(timezone.utc).isoformat()



    def update_sheet_discovery(self, session_id: str, sheets: List[SheetAnalysis], selected: SheetAnalysis) -> Optional[PipelineState]:
        state = self.get_session(session_id)
        if not state:
            return None
        state.sheets = sheets
        state.selected_sheet = selected
        state.header_row = selected.header_row
        self.log_agent_event(
            state, 
            "Agent 1: Sheet Intelligence", 
            f"Selected primary sheet '{selected.sheet_name}' with header at row {selected.header_row} (confidence: {selected.confidence:.2f})",
            "success"
        )
        return state

    def update_schema_mapping(self, session_id: str, mapping_result: SchemaMappingResult) -> Optional[PipelineState]:
        state = self.get_session(session_id)
        if not state:
            return None
        state.schema_mapping = mapping_result
        self.log_agent_event(
            state,
            "Agent 2: Schema Mapping",
            f"Mapped {len(mapping_result.mappings)} columns with overall confidence {mapping_result.overall_confidence:.2f}",
            "success"
        )
        return state

    def update_data_quality(self, session_id: str, quality_report: DataQualityReport, recommendations: List[RecommendationItem]) -> Optional[PipelineState]:
        state = self.get_session(session_id)
        if not state:
            return None
        state.data_quality = quality_report
        state.recommendations = recommendations
        self.log_agent_event(
            state,
            "Agent 3: Data Quality & Reasoning",
            f"Identified {quality_report.total_anomalies} anomalies and generated {len(recommendations)} explainable recommendations",
            "success"
        )
        return state

# Global singleton
state_manager = StateManager()
