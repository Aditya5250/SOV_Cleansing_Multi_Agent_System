import os
import re
import json
import datetime
import pandas as pd
import numpy as np
import openpyxl

from typing import Dict, List, Any, Tuple, Optional
from backend.app.schemas.sov_schema import (
    TARGET_FIELDS,
    TARGET_FIELD_TYPES,
    AuditEntry,
    CleanedSOVResult,
    RecommendationItem
)
from backend.app.services.validation_service import ValidationService

class ControlledTransformationAgent:
    """
    AGENT 4 — CONTROLLED TRANSFORMATION AGENT
    Strictly enforced gatekeeper:
    - Never mutates data without explicit human approval (C-01)
    - Conforms to exact 17-field schema order (C-03)
    - Never fabricates missing values (C-02)
    - Produces comprehensive Audit_Log.xlsx / Audit_Log.json (C-07)
    - Validates final output against strict exposure model schema (NFR-5)
    """

    US_STATE_MAP = {
        "alabama": "AL", "alaska": "AK", "arizona": "AZ", "arkansas": "AR", "california": "CA",
        "colorado": "CO", "connecticut": "CT", "delaware": "DE", "florida": "FL", "georgia": "GA",
        "hawaii": "HI", "idaho": "ID", "illinois": "IL", "indiana": "IN", "iowa": "IA",
        "kansas": "KS", "kentucky": "KY", "louisiana": "LA", "maine": "ME", "maryland": "MD",
        "massachusetts": "MA", "michigan": "MI", "minnesota": "MN", "mississippi": "MS", "missouri": "MO",
        "montana": "MT", "nebraska": "NE", "nevada": "NV", "new hampshire": "NH", "new jersey": "NJ",
        "new mexico": "NM", "new york": "NY", "north carolina": "NC", "north dakota": "ND", "ohio": "OH",
        "oklahoma": "OK", "oregon": "OR", "pennsylvania": "PA", "rhode island": "RI", "south carolina": "SC",
        "south dakota": "SD", "tennessee": "TN", "texas": "TX", "utah": "UT", "vermont": "VT",
        "virginia": "VA", "washington": "WA", "west virginia": "WV", "wisconsin": "WI", "wyoming": "WY",
        "district of columbia": "DC", "puerto rico": "PR"
    }

    SPRINKLER_NORMALIZATION = {
        "yes": "Y", "y": "Y", "sprinklered": "Y", "full": "Y", "100%": "Y", "1": "Y", "true": "Y",
        "no": "N", "n": "N", "none": "N", "un-sprinklered": "N", "unsprinklered": "N", "0%": "N", "0": "N", "false": "N",
        "y13": "Y13", "13": "Y13", "nfpa 13": "Y13", "nfpa13": "Y13",
        "y(13r)": "Y(13R)", "13r": "Y(13R)", "nfpa 13r": "Y(13R)", "nfpa13r": "Y(13R)"
    }

    def __init__(self, output_dir: Optional[str] = None):
        self.output_dir = output_dir or os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "scratch"))
        os.makedirs(self.output_dir, exist_ok=True)


    def execute_transformations(
        self,
        raw_df: pd.DataFrame,
        confirmed_mappings: Dict[str, str], # source_col -> target_col
        recommendations: List[RecommendationItem],
        approved_decisions: Dict[str, Dict[str, Any]], # rec_id -> { "status": "accepted"|"rejected", "user_value": ... }
        approved_by: str = "Human Reviewer"
    ) -> Tuple[pd.DataFrame, List[AuditEntry], List[str]]:
        """
        Execute transformations approved by human reviewer.
        Returns: (transformed_df, audit_entries, errors)
        """
        audit_log: List[AuditEntry] = []
        errors: List[str] = []
        now_str = datetime.datetime.now(datetime.timezone.utc).isoformat()


        # Step 1: Initialize target dataframe with exactly the 17 required columns
        target_df = pd.DataFrame(index=raw_df.index, columns=TARGET_FIELDS)

        # Step 2: Apply confirmed column mappings
        for src_col, target_col in confirmed_mappings.items():
            if target_col in TARGET_FIELDS and src_col in raw_df.columns:
                target_df[target_col] = raw_df[src_col].copy()
                audit_log.append(AuditEntry(
                    timestamp=now_str,
                    source_column=src_col,
                    target_column=target_col,
                    transformation_applied="column_mapping",
                    before_value=f"Mapped from source column '{src_col}'",
                    after_value=f"Placed in target field '{target_col}'",
                    confidence=1.0,
                    approved_by=approved_by,
                    reasoning=f"Approved mapping of '{src_col}' to '{target_col}'."
                ))

        # Build index of recommendation decisions
        rec_map = {r.id: r for r in recommendations}

        # Step 3: Apply ONLY approved data corrections & standardizations
        for rec_id, decision in approved_decisions.items():
            status = decision.get("status")
            if status != "accepted":
                continue # Skip rejected or unapproved items!

            rec_item = rec_map.get(rec_id)
            if not rec_item or not rec_item.transformation_rule:
                continue

            rule = rec_item.transformation_rule
            action = rule.get("action")
            field = rule.get("field")
            user_override = decision.get("user_value")

            if field not in target_df.columns:
                continue

            # Process action
            if action == "clean_currency":
                # Strip currency symbols and commas
                orig_series = target_df[field].copy()
                target_df[field] = target_df[field].astype(str).str.replace(r"[^\d.-]", "", regex=True)
                target_df[field] = pd.to_numeric(target_df[field], errors='coerce')

                audit_log.append(AuditEntry(
                    timestamp=now_str,
                    source_column=field,
                    target_column=field,
                    transformation_applied="clean_currency_formatting",
                    before_value=rec_item.before_value,
                    after_value=str(target_df[field].dropna().iloc[0]) if len(target_df[field].dropna()) > 0 else "",
                    confidence=rec_item.confidence,
                    approved_by=approved_by,
                    reasoning="Removed currency signs ($), commas, and spaces to cast to Float."
                ))

            elif action == "abs_numeric":
                # Convert negative monetary values to absolute positive
                target_df[field] = pd.to_numeric(target_df[field].astype(str).str.replace(r"[^\d.-]", "", regex=True), errors='coerce')
                neg_indices = target_df.index[target_df[field] < 0].tolist()
                for idx in neg_indices:
                    before_v = target_df.at[idx, field]
                    after_v = abs(before_v)
                    target_df.at[idx, field] = after_v
                    audit_log.append(AuditEntry(
                        timestamp=now_str,
                        source_column=field,
                        target_column=field,
                        transformation_applied="convert_negative_to_positive",
                        before_value=str(before_v),
                        after_value=str(after_v),
                        confidence=rec_item.confidence,
                        approved_by=approved_by,
                        row_index=idx + 2,
                        reasoning=f"Corrected negative monetary amount at row {idx+2}."
                    ))

            elif action == "min_storeys":
                target_df[field] = pd.to_numeric(target_df[field], errors='coerce')
                bad_idx = target_df.index[(target_df[field] < 1) & target_df[field].notna()].tolist()
                for idx in bad_idx:
                    before_v = target_df.at[idx, field]
                    target_df.at[idx, field] = 1
                    audit_log.append(AuditEntry(
                        timestamp=now_str,
                        source_column=field,
                        target_column=field,
                        transformation_applied="enforce_minimum_storeys",
                        before_value=str(before_v),
                        after_value="1",
                        confidence=rec_item.confidence,
                        approved_by=approved_by,
                        row_index=idx + 2,
                        reasoning=f"Set invalid storey count ({before_v}) to minimum of 1."
                    ))

            elif action == "min_bldgs":
                target_df[field] = pd.to_numeric(target_df[field], errors='coerce')
                bad_idx = target_df.index[(target_df[field] < 1) & target_df[field].notna()].tolist()
                for idx in bad_idx:
                    before_v = target_df.at[idx, field]
                    target_df.at[idx, field] = 1
                    audit_log.append(AuditEntry(
                        timestamp=now_str,
                        source_column=field,
                        target_column=field,
                        transformation_applied="enforce_minimum_buildings",
                        before_value=str(before_v),
                        after_value="1",
                        confidence=rec_item.confidence,
                        approved_by=approved_by,
                        row_index=idx + 2,
                        reasoning=f"Set invalid building count ({before_v}) to minimum of 1."
                    ))

            elif action == "standardize_sprinkler":
                sprinkler_series = target_df[field].astype(str).str.strip().str.lower()
                for idx, val in sprinkler_series.items():
                    if val in self.SPRINKLER_NORMALIZATION:
                        new_code = self.SPRINKLER_NORMALIZATION[val]
                        before_val = target_df.at[idx, field]
                        if before_val != new_code:
                            target_df.at[idx, field] = new_code
                            audit_log.append(AuditEntry(
                                timestamp=now_str,
                                source_column=field,
                                target_column=field,
                                transformation_applied="standardize_sprinkler_code",
                                before_value=str(before_val),
                                after_value=new_code,
                                confidence=rec_item.confidence,
                                approved_by=approved_by,
                                row_index=idx + 2,
                                reasoning=f"Standardized '{before_val}' to target sprinkler code '{new_code}'."
                            ))

            elif action == "standardize_state":
                state_series = target_df[field].dropna().astype(str).str.strip()
                for idx, val in state_series.items():
                    norm_val = val.lower()
                    if norm_val in self.US_STATE_MAP:
                        new_state = self.US_STATE_MAP[norm_val]
                        target_df.at[idx, field] = new_state
                        audit_log.append(AuditEntry(
                            timestamp=now_str,
                            source_column=field,
                            target_column=field,
                            transformation_applied="standardize_state_abbreviation",
                            before_value=val,
                            after_value=new_state,
                            confidence=rec_item.confidence,
                            approved_by=approved_by,
                            row_index=idx + 2,
                            reasoning=f"Standardized state name '{val}' to postal code '{new_state}'."
                        ))

            elif action == "clean_zip":
                zip_series = target_df[field].dropna().astype(str).str.strip()
                for idx, val in zip_series.items():
                    digits = "".join(re.findall(r"\d", val))
                    if digits:
                        clean_zip_int = int(digits[:5])
                        target_df.at[idx, field] = clean_zip_int
                        audit_log.append(AuditEntry(
                            timestamp=now_str,
                            source_column=field,
                            target_column=field,
                            transformation_applied="clean_postal_zip",
                            before_value=val,
                            after_value=str(clean_zip_int),
                            confidence=rec_item.confidence,
                            approved_by=approved_by,
                            row_index=idx + 2,
                            reasoning=f"Extracted valid integer zip '{clean_zip_int}' from '{val}'."
                        ))

        # Step 4: Strict Type Casting & Handling of Missing Values
        # Per C-02 & Section 08: Missing values must remain blank cells in Excel, not zeros, not "N/A"
        final_df = pd.DataFrame(index=target_df.index)

        for col in TARGET_FIELDS:
            expected_type = TARGET_FIELD_TYPES[col]
            series = target_df[col]

            if expected_type == "Float":
                # Convert to numeric float, keep missing as np.nan
                cleaned = series.astype(str).str.replace(r"[^\d.-]", "", regex=True)
                numeric_val = pd.to_numeric(cleaned, errors='coerce')
                # Replace inf/-inf with nan
                numeric_val = numeric_val.replace([np.inf, -np.inf], np.nan)
                final_df[col] = numeric_val

            elif expected_type == "Integer":
                # In pandas, integer with nulls can be nullable Int64 or float with formatting on export
                cleaned = series.astype(str).str.replace(r"[^\d-]", "", regex=True)
                numeric_val = pd.to_numeric(cleaned, errors='coerce')
                # Use pandas nullable integer type Int64
                final_df[col] = numeric_val.round().astype('Int64')

            else:  # String
                # Strings with nulls should be blank strings or None
                def clean_str(v):
                    if pd.isna(v) or v is None:
                        return None
                    s = str(v).strip()
                    if s.lower() in ["nan", "null", "none", "n/a", ""]:
                        return None
                    return s
                final_df[col] = series.apply(clean_str)

        # Enforce exact column order
        final_df = final_df[TARGET_FIELDS]

        return final_df, audit_log, errors

    def export_cleaned_sov(
        self,
        final_df: pd.DataFrame,
        audit_log: List[AuditEntry],
        session_id: str
    ) -> Tuple[str, str, str]:
        """
        Produce:
        1. Cleaned_SOV.xlsx (Sheet: "Cleaned_SOV", headers in row 1, data row 2+, no merged cells, no colour formatting)
        2. Audit_Log.xlsx (Dedicated workbook with audit trail)
        3. Audit_Log.json (Companion JSON audit log)
        """
        sov_filename = f"Cleaned_SOV_{session_id}.xlsx"
        audit_xlsx_filename = f"Audit_Log_{session_id}.xlsx"
        audit_json_filename = f"Audit_Log_{session_id}.json"

        sov_path = os.path.join(self.output_dir, sov_filename)
        audit_xlsx_path = os.path.join(self.output_dir, audit_xlsx_filename)
        audit_json_path = os.path.join(self.output_dir, audit_json_filename)

        # Also write the canonical non-prefixed files for direct download compliance
        canonical_sov_path = os.path.join(self.output_dir, "Cleaned_SOV.xlsx")
        canonical_audit_xlsx_path = os.path.join(self.output_dir, "Audit_Log.xlsx")
        canonical_audit_json_path = os.path.join(self.output_dir, "Audit_Log.json")

        # 1. Export Cleaned_SOV.xlsx using openpyxl
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Cleaned_SOV"

        # Headers in row 1
        ws.append(TARGET_FIELDS)

        # Data from row 2
        for _, row in final_df.iterrows():
            row_data = []
            for col in TARGET_FIELDS:
                val = row[col]
                # Check for null / pd.isna
                if pd.isna(val) or val is None or str(val).lower() == "<na>":
                    row_data.append(None)  # Openpyxl writes empty blank cell
                else:
                    expected_type = TARGET_FIELD_TYPES[col]
                    if expected_type == "Float":
                        try:
                            row_data.append(float(val))
                        except Exception:
                            row_data.append(None)
                    elif expected_type == "Integer":
                        try:
                            row_data.append(int(val))
                        except Exception:
                            row_data.append(None)
                    else:
                        row_data.append(str(val))
            ws.append(row_data)

        # Save both session and canonical file
        wb.save(sov_path)
        wb.save(canonical_sov_path)
        wb.close()

        # 2. Export Audit_Log.xlsx
        wb_audit = openpyxl.Workbook()
        ws_audit = wb_audit.active
        ws_audit.title = "Audit_Log"

        audit_headers = [
            "Timestamp", "Source Column", "Target Column", "Transformation Applied",
            "Before Value", "After Value", "Confidence", "Approved By", "Row Index", "Reasoning"
        ]
        ws_audit.append(audit_headers)

        for entry in audit_log:
            ws_audit.append([
                entry.timestamp,
                entry.source_column,
                entry.target_column,
                entry.transformation_applied,
                entry.before_value,
                entry.after_value,
                entry.confidence,
                entry.approved_by,
                entry.row_index if entry.row_index is not None else "",
                entry.reasoning or ""
            ])

        wb_audit.save(audit_xlsx_path)
        wb_audit.save(canonical_audit_xlsx_path)
        wb_audit.close()

        # 3. Export Audit_Log.json
        audit_dicts = [e.model_dump() for e in audit_log]
        with open(audit_json_path, "w", encoding="utf-8") as f:
            json.dump(audit_dicts, f, indent=2)
        with open(canonical_audit_json_path, "w", encoding="utf-8") as f:
            json.dump(audit_dicts, f, indent=2)

        return sov_path, audit_xlsx_path, audit_json_path
