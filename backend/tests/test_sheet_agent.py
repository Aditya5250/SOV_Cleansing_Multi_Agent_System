import os
import pytest
from backend.app.agents.sheet_agent import SheetIntelligenceAgent

SAMPLE_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "sample_data")

def test_sheet_detection_sample_1():
    agent = SheetIntelligenceAgent()
    file_path = os.path.join(SAMPLE_DIR, "Sample_SOV_1_Standard.xlsx")
    result = agent.run(file_path)

    assert result.total_sheets >= 1
    assert result.selected_sheet is not None
    assert result.selected_sheet.classification == "Primary"
    assert result.selected_sheet.header_row == 1
    assert result.selected_sheet.confidence >= 0.70

def test_multisheet_and_header_row_detection_sample_3():
    """
    Sample 3 has 3 sheets:
    - Instructions & Notes (must be Reject)
    - Location Schedule (must be Primary, header at Row 4)
    - Summary Rollup (must be Reject / Secondary)
    """
    agent = SheetIntelligenceAgent()
    file_path = os.path.join(SAMPLE_DIR, "Sample_SOV_3_MultiSheet_Messy.xlsx")
    result = agent.run(file_path)

    assert result.total_sheets == 3
    assert result.selected_sheet is not None
    assert result.selected_sheet.sheet_name == "Location Schedule"
    assert result.selected_sheet.classification == "Primary"
    assert result.selected_sheet.header_row == 4, f"Expected header row 4, got {result.selected_sheet.header_row}"

    # Verify rejection of instruction sheet
    sheet_classes = {s.sheet_name: s.classification for s in result.sheets}
    assert sheet_classes["Instructions & Notes"] == "Reject"
