import os
import shutil
from typing import Dict, Any, Optional
from fastapi import APIRouter, UploadFile, File, HTTPException, Body
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel

from backend.app.orchestration.state import state_manager
from backend.app.orchestration.orchestrator import orchestrator
from backend.app.schemas.sov_schema import (
    PipelineState,
    TransformationApprovalRequest,
    CleanedSOVResult,
    RecommendationItem
)

router = APIRouter(prefix="/api")

TEMP_UPLOAD_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "scratch", "uploads"))
os.makedirs(TEMP_UPLOAD_DIR, exist_ok=True)
SAMPLE_DATA_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "sample_data"))


class ReReasonRequest(BaseModel):
    rec_id: str
    feedback: str

class SheetSelectionRequest(BaseModel):
    sheet_name: str
    header_row: int

class MappingOverrideRequest(BaseModel):
    mappings: Dict[str, Optional[str]] # source_col -> target_col

@router.post("/upload", response_model=PipelineState)
async def upload_sov_file(file: UploadFile = File(...)):
    """
    Accepts .xlsx or .csv, initializes session, and executes intake pipeline (Agents 1, 2, 3).
    """
    filename = file.filename or "uploaded_sov.xlsx"
    ext = os.path.splitext(filename)[1].lower()

    if ext not in [".xlsx", ".xls", ".csv"]:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file format '{ext}'. Please upload an Excel (.xlsx) or CSV (.csv) Statement of Values."
        )

    # Save uploaded file
    file_path = os.path.join(TEMP_UPLOAD_DIR, filename)
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    file_size_kb = round(os.path.getsize(file_path) / 1024, 1)
    file_info = {
        "filename": filename,
        "extension": ext,
        "size_kb": file_size_kb
    }

    # Initialize shared pipeline state
    state = state_manager.create_session(file_info=file_info, raw_file_path=file_path)

    # Run intake pipeline through Agents 1, 2, and 3
    try:
        updated_state = orchestrator.run_intake_pipeline(state.session_id)
        return updated_state
    except Exception as e:
        state.errors.append(str(e))
        state_manager.log_agent_event(state, "Pipeline", f"Intake pipeline error: {str(e)}", "error")
        raise HTTPException(status_code=500, detail=f"Pipeline processing failed: {str(e)}")

@router.get("/session/{session_id}", response_model=PipelineState)
async def get_session_state(session_id: str):
    state = state_manager.get_session(session_id)
    if not state:
        raise HTTPException(status_code=404, detail="Session not found.")
    return state

@router.post("/session/{session_id}/select-sheet", response_model=PipelineState)
async def override_sheet_selection(session_id: str, req: SheetSelectionRequest):
    """
    Allows human reviewer to switch to a different sheet or adjust detected header row.
    Re-runs Schema Mapping (Agent 2) and Data Quality (Agent 3).
    """
    state = state_manager.get_session(session_id)
    if not state:
        raise HTTPException(status_code=404, detail="Session not found.")

    target_sheet = next((s for s in state.sheets if s.sheet_name == req.sheet_name), None)
    if not target_sheet:
        raise HTTPException(status_code=404, detail=f"Sheet '{req.sheet_name}' not found.")

    target_sheet.header_row = req.header_row
    state.selected_sheet = target_sheet
    state.header_row = req.header_row

    state_manager.log_agent_event(
        state, "Human Review", f"Reviewer changed active sheet to '{req.sheet_name}' at header row {req.header_row}."
    )

    # Re-run mapping and quality agents
    from backend.app.services.excel_service import ExcelService
    raw_df = ExcelService.extract_dataframe(state.raw_file_path, req.sheet_name, req.header_row)

    mapping_res = orchestrator.schema_agent.run(raw_df, req.sheet_name, req.header_row)
    state_manager.update_schema_mapping(session_id, mapping_res)

    quality_report, recs = orchestrator.quality_agent.run(raw_df, mapping_res.mappings)
    state_manager.update_data_quality(session_id, quality_report, recs)

    return state

@router.post("/session/{session_id}/mapping")
async def update_column_mappings(session_id: str, req: MappingOverrideRequest):
    """
    Allows human reviewer to adjust or confirm column mappings before transformation.
    """
    state = state_manager.get_session(session_id)
    if not state or not state.schema_mapping:
        raise HTTPException(status_code=404, detail="Session or mapping not found.")

    for src_col, target_col in req.mappings.items():
        if src_col in state.schema_mapping.mappings:
            mapping = state.schema_mapping.mappings[src_col]
            mapping.target_column = target_col
            mapping.method = "manual"
            mapping.confidence = 1.0
            mapping.reasoning = f"Manually verified and confirmed by Human Reviewer."
            mapping.flag_for_review = False

    state_manager.log_agent_event(
        state, "Human Review", f"Reviewer updated {len(req.mappings)} column mappings."
    )
    return {"status": "success", "schema_mapping": state.schema_mapping}

@router.post("/session/{session_id}/re-reason", response_model=RecommendationItem)
async def re_reason_item(session_id: str, req: ReReasonRequest):
    """
    Bonus Feature: Agent re-reasons on rejected recommendation using human feedback note.
    """
    updated_rec = orchestrator.handle_re_reasoning(session_id, req.rec_id, req.feedback)
    if not updated_rec:
        raise HTTPException(status_code=404, detail="Recommendation not found.")
    return updated_rec

@router.post("/session/{session_id}/transform", response_model=CleanedSOVResult)
async def execute_transformation(session_id: str, req: TransformationApprovalRequest):
    """
    Executes AGENT 4 (Controlled Transformation Agent) after explicit human approval.
    """
    state = state_manager.get_session(session_id)
    if not state:
        raise HTTPException(status_code=404, detail="Session not found.")

    try:
        result = orchestrator.execute_controlled_transformation(
            session_id=session_id,
            decisions=req.recommendation_decisions,
            mapping_overrides=req.column_mapping_overrides,
            approved_by=req.approved_by
        )
        return result
    except Exception as e:
        state.errors.append(str(e))
        state_manager.log_agent_event(state, "Agent 4", f"Transformation error: {str(e)}", "error")
        raise HTTPException(status_code=500, detail=f"Transformation execution failed: {str(e)}")

@router.get("/export/{session_id}/{filename}")
async def download_file(session_id: str, filename: str):
    """
    Direct file download for Cleaned_SOV.xlsx, Audit_Log.xlsx, and Audit_Log.json.
    """
    scratch_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "scratch"))
    
    # Try session-specific or direct filename
    possible_paths = [
        os.path.join(scratch_dir, filename),
        os.path.join(scratch_dir, f"{os.path.splitext(filename)[0]}_{session_id}{os.path.splitext(filename)[1]}"),
        os.path.join(scratch_dir, f"Cleaned_SOV_{session_id}.xlsx"),
        os.path.join(scratch_dir, f"Audit_Log_{session_id}.xlsx"),
        os.path.join(scratch_dir, f"Audit_Log_{session_id}.json"),
    ]

    target_path = None
    for p in possible_paths:
        if os.path.exists(p):
            target_path = p
            break

    if not target_path:
        raise HTTPException(status_code=404, detail=f"Requested export file '{filename}' was not found.")

    media_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    if filename.endswith(".json"):
        media_type = "application/json"

    return FileResponse(
        target_path,
        media_type=media_type,
        filename=filename
    )

@router.get("/samples")
async def list_sample_sov_files():
    """
    List available official and synthetic test SOV files for 1-click evaluation.
    """
    samples = []
    if os.path.exists(SAMPLE_DATA_DIR):
        for f in os.listdir(SAMPLE_DATA_DIR):
            if f.endswith(".xlsx") or f.endswith(".csv"):
                p = os.path.join(SAMPLE_DATA_DIR, f)
                samples.append({
                    "filename": f,
                    "size_kb": round(os.path.getsize(p) / 1024, 1),
                    "description": _get_sample_description(f)
                })
    return {"samples": samples}

@router.post("/samples/load/{filename}", response_model=PipelineState)
async def load_sample_file(filename: str):
    """
    Load a pre-configured sample SOV directly into the multi-agent pipeline.
    """
    sample_path = os.path.join(SAMPLE_DATA_DIR, filename)
    if not os.path.exists(sample_path):
        raise HTTPException(status_code=404, detail=f"Sample file '{filename}' not found.")

    file_info = {
        "filename": filename,
        "extension": os.path.splitext(filename)[1].lower(),
        "size_kb": round(os.path.getsize(sample_path) / 1024, 1),
        "is_sample": True
    }

    state = state_manager.create_session(file_info=file_info, raw_file_path=sample_path)
    updated_state = orchestrator.run_intake_pipeline(state.session_id)
    return updated_state

def _get_sample_description(filename: str) -> str:
    if "Sample_SOV_1" in filename or "Standard" in filename:
        return "Baseline Test: Clean, well-structured headers (Row 1), single data sheet."
    elif "Sample_SOV_2" in filename or "Semantic" in filename:
        return "Semantic Test: Abbreviated & ambiguous headers ('Bldg Repl Cost', 'Fire Prot.', 'BI')."
    elif "Sample_SOV_3" in filename or "MultiSheet" in filename:
        return "Structural Diversity Test: Multi-sheet workbook, header at Row 4, merged title banner, nulls."
    return "Test Statement of Values workbook."
