import os
import pytest
from backend.app.agents.schema_agent import SchemaMappingAgent
from backend.app.services.excel_service import ExcelService
from backend.app.services.matching_service import MatchingService

SAMPLE_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "sample_data")

def test_exact_and_fuzzy_mapping():
    # Test MatchingService directly
    target, conf, method, reasoning = MatchingService.match_column("Reference")
    assert target == "Reference"
    assert conf == 1.0
    assert method == "exact"

    target, conf, method, reasoning = MatchingService.match_column("Loc #")
    assert target == "Reference"
    assert conf >= 0.90

    target, conf, method, reasoning = MatchingService.match_column("Street Address")
    assert target == "Address"
    assert conf >= 0.90

def test_semantic_mapping_sample_2():
    """
    Test semantic mappings on Sample 2:
    - 'Bldg Repl Cost' -> 'Building Value'
    - 'Fire Prot.' -> 'Fire Sprinklers (Y/N)'
    - 'Business Interruption' -> 'BI'
    - 'Stories' -> 'Storeys'
    """
    file_path = os.path.join(SAMPLE_DIR, "Sample_SOV_2_Complex_Semantic.xlsx")
    df = ExcelService.extract_dataframe(file_path, "Assets_Summary", 1)

    agent = SchemaMappingAgent()
    result = agent.run(df, "Assets_Summary", 1)

    mapped_dict = {col: m.target_column for col, m in result.mappings.items()}

    assert mapped_dict.get("Bldg Repl Cost") == "Building Value", f"Got {mapped_dict.get('Bldg Repl Cost')}"
    assert mapped_dict.get("Fire Prot.") == "Fire Sprinklers (Y/N)", f"Got {mapped_dict.get('Fire Prot.')}"
    assert mapped_dict.get("Business Interruption") == "BI", f"Got {mapped_dict.get('Business Interruption')}"
    assert mapped_dict.get("Stories") == "Storeys", f"Got {mapped_dict.get('Stories')}"
    assert result.overall_confidence >= 0.74, f"Target accuracy >= 74%, got {result.overall_confidence}"
