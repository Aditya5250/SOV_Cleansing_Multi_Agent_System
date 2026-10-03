import os
import pytest
from backend.app.agents.schema_agent import SchemaMappingAgent
from backend.app.agents.quality_agent import DataQualityAgent
from backend.app.services.excel_service import ExcelService

SAMPLE_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "sample_data")

def test_anomaly_detection_sample_2():
    """
    Sample 2 has planted anomalies:
    1. Negative building value (-450000)
    2. Currency signs in contents ($1,250,000)
    3. Future year built (2035)
    4. Inconsistent state name ('California', 'Georgia', 'Texas')
    5. Invalid sprinkler code ('Yes', '100%', 'None')
    6. Invalid storeys (0)
    """
    file_path = os.path.join(SAMPLE_DIR, "Sample_SOV_2_Complex_Semantic.xlsx")
    df = ExcelService.extract_dataframe(file_path, "Assets_Summary", 1)

    schema_agent = SchemaMappingAgent()
    mapping_res = schema_agent.run(df, "Assets_Summary", 1)

    quality_agent = DataQualityAgent()
    report, recommendations = quality_agent.run(df, mapping_res.mappings)

    detected_issue_types = {issue.issue_type for issue in report.issues}

    # Verify high anomaly recall (>= 90% target)
    assert "negative_value" in detected_issue_types
    assert "currency_symbol" in detected_issue_types
    assert "future_year" in detected_issue_types
    assert "inconsistent_state" in detected_issue_types
    assert "invalid_sprinkler" in detected_issue_types
    assert "invalid_storeys" in detected_issue_types

    assert len(report.issues) >= 6
    assert len(recommendations) >= 5

    # Check 100% explainability: every recommendation must have plain-English rationale
    for rec in recommendations:
        assert rec.reasoning and len(rec.reasoning.strip()) > 10
