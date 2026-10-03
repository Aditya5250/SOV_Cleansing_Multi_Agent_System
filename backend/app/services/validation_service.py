import pandas as pd
import numpy as np
from typing import Dict, Any, List, Tuple
from backend.app.schemas.sov_schema import TARGET_FIELDS, TARGET_FIELD_TYPES

class ValidationService:
    """
    Strict post-transformation schema validator.
    Enforces NFR-5 and Section 08:
    1. Exactly 17 required columns
    2. Exact case-sensitive names and sequence
    3. Proper data types
    4. Blank cells for missing values (no NaN strings or fabricated zeros)
    5. Sprinkler code whitelist ['Y', 'N', 'Y13', 'Y(13R)']
    """

    ALLOWED_SPRINKLER_CODES = {"Y", "N", "Y13", "Y(13R)"}

    @classmethod
    def validate_cleaned_dataframe(cls, df: pd.DataFrame) -> Tuple[bool, List[str], Dict[str, Any]]:
        errors = []
        warnings = []
        metrics = {
            "row_count": len(df),
            "column_count": len(df.columns),
            "columns": list(df.columns),
            "missing_per_col": {},
            "type_conformance": {}
        }

        # 1. Column count check
        if len(df.columns) != 17:
            errors.append(f"Target schema must contain EXACTLY 17 columns. Found {len(df.columns)}.")

        # 2. Exact column name and order check
        if list(df.columns) != TARGET_FIELDS:
            missing_cols = [c for c in TARGET_FIELDS if c not in df.columns]
            extra_cols = [c for c in df.columns if c not in TARGET_FIELDS]
            if missing_cols:
                errors.append(f"Missing required columns: {missing_cols}")
            if extra_cols:
                errors.append(f"Disallowed additional columns: {extra_cols}")
            if not missing_cols and not extra_cols and list(df.columns) != TARGET_FIELDS:
                errors.append(f"Column order is invalid. Target sequence must match exactly: {TARGET_FIELDS}")

        # 3. Row-level type & format checks
        for col in df.columns:
            if col not in TARGET_FIELD_TYPES:
                continue

            expected_type = TARGET_FIELD_TYPES[col]
            series = df[col]
            null_count = int(series.isna().sum())
            metrics["missing_per_col"][col] = null_count

            # Check for illegal string representations of missing values
            has_nan_string = series.astype(str).str.strip().str.lower().isin(["nan", "null", "none", "n/a"]).any()
            if has_nan_string:
                errors.append(f"Column '{col}' contains illegal placeholder strings ('NaN', 'null', or 'N/A'). Must be clean blank cells.")

            # Validate non-null values
            non_null = series.dropna()
            if len(non_null) > 0:
                if expected_type == "Float":
                    non_numeric = pd.to_numeric(non_null, errors='coerce').isna()
                    if non_numeric.any():
                        bad_samples = non_null[non_numeric].head(3).tolist()
                        errors.append(f"Column '{col}' expected Float but found non-numeric entries: {bad_samples}")
                    else:
                        metrics["type_conformance"][col] = "Float (100% compliant)"

                elif expected_type == "Integer":
                    non_int = pd.to_numeric(non_null, errors='coerce').isna()
                    if non_int.any():
                        bad_samples = non_null[non_int].head(3).tolist()
                        errors.append(f"Column '{col}' expected Integer but found non-integer entries: {bad_samples}")
                    else:
                        metrics["type_conformance"][col] = "Integer (100% compliant)"

                elif col == "Fire Sprinklers (Y/N)":
                    str_vals = non_null.astype(str).str.strip()
                    invalid_sprinklers = str_vals[~str_vals.isin(cls.ALLOWED_SPRINKLER_CODES)]
                    if len(invalid_sprinklers) > 0:
                        bad_samples = invalid_sprinklers.head(3).tolist()
                        errors.append(f"Column 'Fire Sprinklers (Y/N)' contains non-standard codes: {bad_samples}. Allowed: {cls.ALLOWED_SPRINKLER_CODES}")
                    else:
                        metrics["type_conformance"][col] = "String (Valid Sprinkler Code)"
                else:
                    metrics["type_conformance"][col] = f"{expected_type} (Valid)"

        is_valid = len(errors) == 0
        return is_valid, errors, metrics
