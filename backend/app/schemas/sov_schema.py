from typing import List, Dict, Any, Optional, Literal
from pydantic import BaseModel, Field
from datetime import datetime

# ============================================================
# TARGET 17 FIELDS SPECIFICATION (Strict Case-sensitive order)
# ============================================================
TARGET_FIELDS = [
    "Reference",
    "Address",
    "City",
    "State",
    "Zip",
    "County",
    "Country",
    "Building Value",
    "Contents",
    "BI",
    "Occupancy",
    "Construction",
    "Storeys",
    "Number of Buildings",
    "Year Built",
    "Fire Sprinklers (Y/N)",
    "Other",
]

TARGET_FIELD_TYPES = {
    "Reference": "String",
    "Address": "String",
    "City": "String",
    "State": "String",
    "Zip": "Integer",
    "County": "String",
    "Country": "String",
    "Building Value": "Float",
    "Contents": "Float",
    "BI": "Float",
    "Occupancy": "String",
    "Construction": "String",
    "Storeys": "Integer",
    "Number of Buildings": "Integer",
    "Year Built": "Integer",
    "Fire Sprinklers (Y/N)": "String",
    "Other": "Float",
}

TARGET_FIELD_DEFINITIONS = {
    "Reference": "Unique identifier for the property used in insurance documentation.",
    "Address": "Full street address of the insured property.",
    "City": "City where the insured property is located.",
    "State": "State or region (2-letter abbreviation preferred).",
    "Zip": "Postal / ZIP code for geographic risk identification.",
    "County": "County for regional risk analysis and policy assignment.",
    "Country": "Country; defines jurisdiction for policy coverage.",
    "Building Value": "Insured value of the building structure (replacement cost / market value).",
    "Contents": "Value of personal property or contents within the building.",
    "BI": "Business Income coverage; potential income loss during interruption.",
    "Occupancy": "Use or purpose of the building (residential, commercial, industrial).",
    "Construction": "Construction type or material (wood, steel, concrete, masonry).",
    "Storeys": "Number of floors in the building.",
    "Number of Buildings": "Total number of buildings at the location covered under the policy.",
    "Year Built": "Year the building was constructed.",
    "Fire Sprinklers (Y/N)": "Whether fire sprinkler systems are installed: Y, N, Y13, or Y(13R).",
    "Other": "Additional insured values not classified under Building Value or Contents.",
}


# ============================================================
# AGENT 1: SHEET INTELLIGENCE MODELS
# ============================================================
class SheetAnalysis(BaseModel):
    sheet_name: str
    classification: Literal["Primary", "Secondary", "Reject"]
    confidence: float
    header_row: int
    row_count: int
    column_count: int
    non_null_ratio: float
    header_density: float
    reasoning: List[str]
    preview_rows: List[List[Any]] = Field(default_factory=list)


class SheetDiscoveryResult(BaseModel):
    sheets: List[SheetAnalysis]
    selected_sheet: Optional[SheetAnalysis] = None
    total_sheets: int
    primary_sheet_name: Optional[str] = None
    primary_header_row: Optional[int] = None


# ============================================================
# AGENT 2: SCHEMA MAPPING MODELS
# ============================================================
MappingMethod = Literal["exact", "fuzzy", "semantic", "llm", "manual", "none"]


class ColumnMapping(BaseModel):
    source_column: str
    target_column: Optional[str] = None
    confidence: float
    method: MappingMethod
    reasoning: str
    flag_for_review: bool = False
    alternatives: List[Dict[str, Any]] = Field(default_factory=list)


class SchemaMappingResult(BaseModel):
    sheet_name: str
    header_row: int
    mappings: Dict[str, ColumnMapping]  # source_col -> ColumnMapping
    unresolved_count: int
    overall_confidence: float
    unmapped_target_fields: List[str] = Field(default_factory=list)


# ============================================================
# AGENT 3: DATA QUALITY & ANOMALY MODELS
# ============================================================
AnomalySeverity = Literal["critical", "high", "medium", "low"]
AnomalyType = Literal[
    "missing_value",
    "invalid_type",
    "negative_value",
    "future_year",
    "invalid_storeys",
    "invalid_zip",
    "invalid_sprinkler",
    "currency_symbol",
    "inconsistent_state",
    "duplicate_record",
    "logical_violation",
]


class DataQualityIssue(BaseModel):
    id: str
    issue_type: AnomalyType
    field: str
    severity: AnomalySeverity
    affected_rows: List[int]
    affected_count: int
    current_value: Optional[str] = None
    sample_values: List[str] = Field(default_factory=list)
    reasoning: str
    recommended_action: str


class FieldCompleteness(BaseModel):
    field: str
    total_rows: int
    non_null_count: int
    completeness_pct: float
    anomaly_count: int


class DataQualityReport(BaseModel):
    total_rows: int
    total_columns: int
    overall_quality_score: float
    completeness_by_field: Dict[str, FieldCompleteness]
    issues: List[DataQualityIssue]
    total_anomalies: int
    critical_anomalies: int
    high_anomalies: int
    medium_anomalies: int
    low_anomalies: int


# ============================================================
# RECOMMENDATION & HUMAN REVIEW MODELS
# ============================================================
ActionType = Literal[
    "column_mapping",
    "data_correction",
    "standardisation",
    "flag_for_review",
]
RecommendationStatus = Literal["pending", "accepted", "rejected", "modified"]


class RecommendationItem(BaseModel):
    id: str
    action_type: ActionType
    field: str
    severity: AnomalySeverity
    affected_rows: List[int] = Field(default_factory=list)
    before_value: Optional[str] = None
    proposed_after: Optional[str] = None
    confidence: float
    reasoning: str
    uncertainty: Optional[str] = None
    status: RecommendationStatus = "pending"
    user_override_value: Optional[str] = None
    rejection_feedback: Optional[str] = None
    transformation_rule: Optional[Dict[str, Any]] = None


# ============================================================
# AGENT 4: CONTROLLED TRANSFORMATION & AUDIT MODELS
# ============================================================
class AuditEntry(BaseModel):
    timestamp: str
    source_column: str
    target_column: str
    transformation_applied: str
    before_value: Optional[str] = None
    after_value: Optional[str] = None
    confidence: float
    approved_by: str
    row_index: Optional[int] = None
    reasoning: Optional[str] = None


class TransformationApprovalRequest(BaseModel):
    recommendation_decisions: Dict[str, Dict[str, Any]]  # rec_id -> { "status": "accepted"|"rejected", "user_value": ..., "feedback": ... }
    column_mapping_overrides: Optional[Dict[str, str]] = None  # source_col -> target_col
    approved_by: str = "Human Reviewer (Underwriting Ops)"


class CleanedSOVResult(BaseModel):
    success: bool
    message: str
    row_count: int
    column_count: int
    columns: List[str]
    sample_preview: List[Dict[str, Any]]
    total_transformations_applied: int
    audit_log_count: int
    download_sov_url: str
    download_audit_xlsx_url: str
    download_audit_json_url: str


# ============================================================
# SHARED PIPELINE STATE (Multi-Agent State Container)
# ============================================================
class PipelineState(BaseModel):
    session_id: str
    file_info: Dict[str, Any] = Field(default_factory=dict)
    raw_file_path: Optional[str] = None
    sheets: List[SheetAnalysis] = Field(default_factory=list)
    selected_sheet: Optional[SheetAnalysis] = None
    header_row: Optional[int] = None
    schema_mapping: Optional[SchemaMappingResult] = None
    data_quality: Optional[DataQualityReport] = None
    recommendations: List[RecommendationItem] = Field(default_factory=list)
    human_decisions: Dict[str, Any] = Field(default_factory=dict)
    approved_transformations: List[Dict[str, Any]] = Field(default_factory=list)
    audit_log: List[AuditEntry] = Field(default_factory=list)
    final_output_ready: bool = False
    cleaned_file_path: Optional[str] = None
    audit_xlsx_path: Optional[str] = None
    audit_json_path: Optional[str] = None
    current_agent: str = "Idle"
    agent_logs: List[Dict[str, Any]] = Field(default_factory=list)
    errors: List[str] = Field(default_factory=list)
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
