import os
import openpyxl
import pandas as pd
import pytest
from backend.app.agents.transformation_agent import ControlledTransformationAgent
from backend.app.services.validation_service import ValidationService
from backend.app.schemas.sov_schema import TARGET_FIELDS, RecommendationItem

def test_controlled_transformation_enforcement():
    agent = ControlledTransformationAgent()

    # Raw test data
    raw_df = pd.DataFrame({
        "Property_ID": ["LOC-1", "LOC-2"],
        "Address_Line": ["10 Main St", "20 Market St"],
        "Replacement_Val": ["$1,000,000", "-500000"],
        "Floors": [3, 0],
        "Sprinkler_Sys": ["Yes", "NFPA 13"]
    })

    confirmed_mappings = {
        "Property_ID": "Reference",
        "Address_Line": "Address",
        "Replacement_Val": "Building Value",
        "Floors": "Storeys",
        "Sprinkler_Sys": "Fire Sprinklers (Y/N)"
    }

    recommendations = [
        RecommendationItem(
            id="rec_curr",
            action_type="standardisation",
            field="Building Value",
            severity="medium",
            before_value="$1,000,000",
            proposed_after="1000000.0",
            confidence=0.98,
            reasoning="Clean currency formatting",
            transformation_rule={"action": "clean_currency", "field": "Building Value"}
        ),
        RecommendationItem(
            id="rec_neg",
            action_type="data_correction",
            field="Building Value",
            severity="critical",
            before_value="-500000",
            proposed_after="500000.0",
            confidence=0.95,
            reasoning="Absolute value for negative sum insured",
            transformation_rule={"action": "abs_numeric", "field": "Building Value"}
        ),
        RecommendationItem(
            id="rec_storeys",
            action_type="data_correction",
            field="Storeys",
            severity="high",
            before_value="0",
            proposed_after="1",
            confidence=0.92,
            reasoning="Set min storey to 1",
            transformation_rule={"action": "min_storeys", "field": "Storeys"}
        ),
        RecommendationItem(
            id="rec_sprinkler",
            action_type="standardisation",
            field="Fire Sprinklers (Y/N)",
            severity="high",
            before_value="Yes",
            proposed_after="Y",
            confidence=0.96,
            reasoning="Standardize to code Y",
            transformation_rule={"action": "standardize_sprinkler", "field": "Fire Sprinklers (Y/N)"}
        )
    ]

    # Explicit human approval for all 4
    approved_decisions = {
        "rec_curr": {"status": "accepted"},
        "rec_neg": {"status": "accepted"},
        "rec_storeys": {"status": "accepted"},
        "rec_sprinkler": {"status": "accepted"},
    }

    final_df, audit_log, errors = agent.execute_transformations(
        raw_df=raw_df,
        confirmed_mappings=confirmed_mappings,
        recommendations=recommendations,
        approved_decisions=approved_decisions,
        approved_by="Lead Underwriter"
    )

    # 1. Conformance check: exactly 17 columns
    assert list(final_df.columns) == TARGET_FIELDS
    assert len(final_df.columns) == 17

    # 2. Check corrections were applied
    assert final_df["Building Value"].iloc[0] == 1000000.0
    assert final_df["Building Value"].iloc[1] == 500000.0  # Converted from -500000
    assert final_df["Storeys"].iloc[1] == 1  # Corrected from 0
    assert final_df["Fire Sprinklers (Y/N)"].iloc[0] == "Y"  # Standardized from 'Yes'

    # 3. Missing fields remain null/empty (Rule C-02)
    assert pd.isna(final_df["BI"].iloc[0])
    assert pd.isna(final_df["Contents"].iloc[0])

    # 4. Audit completeness (NFR-3)
    assert len(audit_log) >= 5
    for entry in audit_log:
        assert entry.approved_by == "Lead Underwriter"
        assert entry.timestamp is not None
        assert entry.confidence > 0

    # 5. Schema validation service passes
    is_valid, val_errors, metrics = ValidationService.validate_cleaned_dataframe(final_df)
    assert is_valid, f"Validation failed with errors: {val_errors}"
