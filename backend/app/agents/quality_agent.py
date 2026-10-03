import re
import datetime
import pandas as pd
import numpy as np
from typing import Dict, List, Any, Tuple, Optional
from backend.app.schemas.sov_schema import (
    DataQualityIssue,
    FieldCompleteness,
    DataQualityReport,
    RecommendationItem,
    AnomalySeverity,
    AnomalyType,
    TARGET_FIELDS,
    TARGET_FIELD_TYPES
)
from backend.app.services.llm_service import llm_service

class DataQualityAgent:
    """
    AGENT 3 — DATA QUALITY & REASONING AGENT
    Profiles dataset completeness, executes deterministic validation checks,
    identifies anomalies across 11+ categories, and generates human-review recommendations.
    """

    CURRENT_YEAR = datetime.datetime.now().year

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

    def __init__(self):
        pass

    def run(self, df: pd.DataFrame, mappings: Dict[str, Any]) -> Tuple[DataQualityReport, List[RecommendationItem]]:
        """
        Execute profiling and anomaly detection on the mapped DataFrame.
        """
        # Map source columns to target names for temporary analysis
        col_rename = {}
        for src_col, mapping in mappings.items():
            target = mapping.target_column if hasattr(mapping, "target_column") else mapping.get("target_column")
            if target and target in TARGET_FIELDS:
                col_rename[src_col] = target

        mapped_df = df.rename(columns=col_rename)

        issues: List[DataQualityIssue] = []
        recommendations: List[RecommendationItem] = []
        completeness: Dict[str, FieldCompleteness] = {}

        total_rows = len(mapped_df)
        total_cols = len(mapped_df.columns)

        # Profile completeness for target fields
        for target_col in TARGET_FIELDS:
            if target_col in mapped_df.columns:
                series = mapped_df[target_col]
                # Non-null values
                non_null_mask = series.notna() & (series.astype(str).str.strip() != "") & (~series.astype(str).str.lower().isin(["nan", "null", "none"]))
                non_null_count = int(non_null_mask.sum())
                pct = round((non_null_count / max(1, total_rows)) * 100, 1)
                completeness[target_col] = FieldCompleteness(
                    field=target_col,
                    total_rows=total_rows,
                    non_null_count=non_null_count,
                    completeness_pct=pct,
                    anomaly_count=0
                )
            else:
                completeness[target_col] = FieldCompleteness(
                    field=target_col,
                    total_rows=total_rows,
                    non_null_count=0,
                    completeness_pct=0.0,
                    anomaly_count=0
                )

        # ============================================================
        # 1. CURRENCY SYMBOLS & FORMAT INCONSISTENCIES IN NUMERIC FIELDS
        # ============================================================
        monetary_fields = ["Building Value", "Contents", "BI", "Other"]
        for field in monetary_fields:
            if field in mapped_df.columns:
                raw_series = mapped_df[field].dropna().astype(str)
                currency_mask = raw_series.str.contains(r"[\$,€,£,¥]|usd", case=False, regex=True)
                if currency_mask.any():
                    affected_rows = (mapped_df[field].dropna()[currency_mask].index + 2).tolist()
                    sample_vals = raw_series[currency_mask].head(3).tolist()
                    sample_clean = re.sub(r"[^\d.-]", "", sample_vals[0]) if sample_vals else "0.0"

                    issue_id = f"issue_curr_{field.replace(' ', '_')}"
                    diag = llm_service.explain_quality_issue("currency_symbol", field, sample_vals, len(affected_rows))

                    issues.append(DataQualityIssue(
                        id=issue_id,
                        issue_type="currency_symbol",
                        field=field,
                        severity="medium",
                        affected_rows=affected_rows,
                        affected_count=len(affected_rows),
                        current_value=sample_vals[0] if sample_vals else "",
                        sample_values=sample_vals,
                        reasoning=diag.get("reasoning", f"Field '{field}' contains raw currency formatting symbols."),
                        recommended_action=diag.get("proposed_action", "Strip currency symbols and commas, casting to Float.")
                    ))

                    recommendations.append(RecommendationItem(
                        id=f"rec_{issue_id}",
                        action_type="standardisation",
                        field=field,
                        severity="medium",
                        affected_rows=affected_rows,
                        before_value=sample_vals[0] if sample_vals else "",
                        proposed_after=sample_clean,
                        confidence=0.98,
                        reasoning=diag.get("reasoning", f"Format cleanup: Remove currency indicators and cast to Float."),
                        transformation_rule={"action": "clean_currency", "field": field}
                    ))

        # ============================================================
        # 2. NEGATIVE MONETARY VALUES
        # ============================================================
        for field in monetary_fields:
            if field in mapped_df.columns:
                # Convert to numeric safely
                cleaned_numeric = mapped_df[field].astype(str).str.replace(r"[^\d.-]", "", regex=True)
                numeric_series = pd.to_numeric(cleaned_numeric, errors='coerce')
                neg_mask = numeric_series < 0
                if neg_mask.any():
                    affected_rows = (mapped_df.index[neg_mask] + 2).tolist()
                    sample_vals = mapped_df.loc[neg_mask, field].head(3).astype(str).tolist()
                    abs_val = str(abs(float(sample_vals[0].replace("$", "").replace(",", "")))) if sample_vals else "0.0"

                    issue_id = f"issue_neg_{field.replace(' ', '_')}"
                    diag = llm_service.explain_quality_issue("negative_value", field, sample_vals, len(affected_rows))

                    issues.append(DataQualityIssue(
                        id=issue_id,
                        issue_type="negative_value",
                        field=field,
                        severity="critical",
                        affected_rows=affected_rows,
                        affected_count=len(affected_rows),
                        current_value=sample_vals[0] if sample_vals else "",
                        sample_values=sample_vals,
                        reasoning=diag.get("reasoning", f"Negative monetary value in '{field}'. Sums insured must be non-negative."),
                        recommended_action=diag.get("proposed_action", "Convert to absolute positive value or flag for underwriter review.")
                    ))

                    recommendations.append(RecommendationItem(
                        id=f"rec_{issue_id}",
                        action_type="data_correction",
                        field=field,
                        severity="critical",
                        affected_rows=affected_rows,
                        before_value=sample_vals[0] if sample_vals else "",
                        proposed_after=abs_val,
                        confidence=0.95,
                        reasoning=f"Convert negative sum insured to positive absolute value ({sample_vals[0]} -> {abs_val}).",
                        transformation_rule={"action": "abs_numeric", "field": field}
                    ))

        # ============================================================
        # 3. YEAR BUILT GREATER THAN CURRENT YEAR OR UNREALISTIC
        # ============================================================
        if "Year Built" in mapped_df.columns:
            cleaned_yr = pd.to_numeric(mapped_df["Year Built"].astype(str).str.extract(r'(\d{4})')[0], errors='coerce')
            future_mask = (cleaned_yr > self.CURRENT_YEAR) | (cleaned_yr < 1700)
            if future_mask.any():
                affected_rows = (mapped_df.index[future_mask] + 2).tolist()
                sample_vals = mapped_df.loc[future_mask, "Year Built"].head(3).astype(str).tolist()

                issue_id = "issue_future_year"
                diag = llm_service.explain_quality_issue("future_year", "Year Built", sample_vals, len(affected_rows))

                issues.append(DataQualityIssue(
                    id=issue_id,
                    issue_type="future_year",
                    field="Year Built",
                    severity="high",
                    affected_rows=affected_rows,
                    affected_count=len(affected_rows),
                    current_value=sample_vals[0] if sample_vals else "",
                    sample_values=sample_vals,
                    reasoning=diag.get("reasoning", f"Year Built ({sample_vals[0]}) exceeds current year {self.CURRENT_YEAR}."),
                    recommended_action=diag.get("proposed_action", "Flag invalid construction year for underwriting verification.")
                ))

                recommendations.append(RecommendationItem(
                    id=f"rec_{issue_id}",
                    action_type="flag_for_review",
                    field="Year Built",
                    severity="high",
                    affected_rows=affected_rows,
                    before_value=sample_vals[0] if sample_vals else "",
                    proposed_after=str(self.CURRENT_YEAR),
                    confidence=0.75,
                    reasoning=f"Future construction year detected ({sample_vals[0]}). Requires human underwriter confirmation.",
                    uncertainty="Potential typo: could be 19XX or intended future completion date.",
                    transformation_rule={"action": "flag_year", "field": "Year Built"}
                ))

        # ============================================================
        # 4. STOREYS BELOW 1
        # ============================================================
        if "Storeys" in mapped_df.columns:
            cleaned_storeys = pd.to_numeric(mapped_df["Storeys"], errors='coerce')
            invalid_storeys = (cleaned_storeys < 1) & cleaned_storeys.notna()
            if invalid_storeys.any():
                affected_rows = (mapped_df.index[invalid_storeys] + 2).tolist()
                sample_vals = mapped_df.loc[invalid_storeys, "Storeys"].head(3).astype(str).tolist()

                issue_id = "issue_storeys_min"
                diag = llm_service.explain_quality_issue("invalid_storeys", "Storeys", sample_vals, len(affected_rows))

                issues.append(DataQualityIssue(
                    id=issue_id,
                    issue_type="invalid_storeys",
                    field="Storeys",
                    severity="high",
                    affected_rows=affected_rows,
                    affected_count=len(affected_rows),
                    current_value=sample_vals[0] if sample_vals else "",
                    sample_values=sample_vals,
                    reasoning=diag.get("reasoning", f"Storeys cannot be less than 1 (found {sample_vals[0]})."),
                    recommended_action="Set minimum storey count to 1 for ground-level structures."
                ))

                recommendations.append(RecommendationItem(
                    id=f"rec_{issue_id}",
                    action_type="data_correction",
                    field="Storeys",
                    severity="high",
                    affected_rows=affected_rows,
                    before_value=sample_vals[0] if sample_vals else "",
                    proposed_after="1",
                    confidence=0.92,
                    reasoning="Default invalid floor count (< 1) to minimum valid building storey of 1.",
                    transformation_rule={"action": "min_storeys", "field": "Storeys", "val": 1}
                ))

        # ============================================================
        # 5. NUMBER OF BUILDINGS BELOW 1
        # ============================================================
        if "Number of Buildings" in mapped_df.columns:
            cleaned_bldgs = pd.to_numeric(mapped_df["Number of Buildings"], errors='coerce')
            invalid_bldgs = (cleaned_bldgs < 1) & cleaned_bldgs.notna()
            if invalid_bldgs.any():
                affected_rows = (mapped_df.index[invalid_bldgs] + 2).tolist()
                sample_vals = mapped_df.loc[invalid_bldgs, "Number of Buildings"].head(3).astype(str).tolist()

                issues.append(DataQualityIssue(
                    id="issue_num_bldgs_min",
                    issue_type="logical_violation",
                    field="Number of Buildings",
                    severity="medium",
                    affected_rows=affected_rows,
                    affected_count=len(affected_rows),
                    current_value=sample_vals[0] if sample_vals else "",
                    sample_values=sample_vals,
                    reasoning="Number of Buildings must be at least 1 at an insured location.",
                    recommended_action="Set minimum building count to 1."
                ))

                recommendations.append(RecommendationItem(
                    id="rec_issue_num_bldgs_min",
                    action_type="data_correction",
                    field="Number of Buildings",
                    severity="medium",
                    affected_rows=affected_rows,
                    before_value=sample_vals[0] if sample_vals else "",
                    proposed_after="1",
                    confidence=0.93,
                    reasoning="Reset building count below 1 to default minimum of 1.",
                    transformation_rule={"action": "min_bldgs", "field": "Number of Buildings", "val": 1}
                ))

        # ============================================================
        # 6. INVALID SPRINKLER CODES
        # ============================================================
        if "Fire Sprinklers (Y/N)" in mapped_df.columns:
            sprinkler_series = mapped_df["Fire Sprinklers (Y/N)"].dropna().astype(str).str.strip()
            # Allowed are Y, N, Y13, Y(13R)
            invalid_sprinkler_mask = ~sprinkler_series.isin(["Y", "N", "Y13", "Y(13R)"])
            if invalid_sprinkler_mask.any():
                affected_rows = (sprinkler_series[invalid_sprinkler_mask].index + 2).tolist()
                sample_vals = sprinkler_series[invalid_sprinkler_mask].head(3).tolist()
                
                # Resolve proposed normalization
                first_norm = self.SPRINKLER_NORMALIZATION.get(sample_vals[0].lower(), "Y")

                issue_id = "issue_sprinkler_codes"
                diag = llm_service.explain_quality_issue("invalid_sprinkler", "Fire Sprinklers (Y/N)", sample_vals, len(affected_rows))

                issues.append(DataQualityIssue(
                    id=issue_id,
                    issue_type="invalid_sprinkler",
                    field="Fire Sprinklers (Y/N)",
                    severity="high",
                    affected_rows=affected_rows,
                    affected_count=len(affected_rows),
                    current_value=sample_vals[0],
                    sample_values=sample_vals,
                    reasoning=diag.get("reasoning", f"Non-standard fire sprinkler designation ('{sample_vals[0]}')."),
                    recommended_action="Standardize to approved codes [Y, N, Y13, Y(13R)]."
                ))

                recommendations.append(RecommendationItem(
                    id=f"rec_{issue_id}",
                    action_type="standardisation",
                    field="Fire Sprinklers (Y/N)",
                    severity="high",
                    affected_rows=affected_rows,
                    before_value=sample_vals[0],
                    proposed_after=first_norm,
                    confidence=0.96,
                    reasoning=f"Standardize verbose or percentage sprinkler values to strict schema code ('{sample_vals[0]}' -> '{first_norm}').",
                    transformation_rule={"action": "standardize_sprinkler", "field": "Fire Sprinklers (Y/N)"}
                ))

        # ============================================================
        # 7. INCONSISTENT STATE ABBREVIATIONS
        # ============================================================
        if "State" in mapped_df.columns:
            state_series = mapped_df["State"].dropna().astype(str).str.strip()
            non_std_states = state_series[~state_series.str.match(r'^[A-Z]{2}$')]
            if len(non_std_states) > 0:
                affected_rows = (non_std_states.index + 2).tolist()
                sample_vals = non_std_states.head(3).tolist()
                proposed_code = self.US_STATE_MAP.get(sample_vals[0].lower(), sample_vals[0].upper()[:2])

                issue_id = "issue_state_abbrev"
                diag = llm_service.explain_quality_issue("inconsistent_state", "State", sample_vals, len(affected_rows))

                issues.append(DataQualityIssue(
                    id=issue_id,
                    issue_type="inconsistent_state",
                    field="State",
                    severity="medium",
                    affected_rows=affected_rows,
                    affected_count=len(affected_rows),
                    current_value=sample_vals[0],
                    sample_values=sample_vals,
                    reasoning=diag.get("reasoning", f"State field contains non-standard entries ('{sample_vals[0]}')."),
                    recommended_action="Convert to 2-letter uppercase postal state code."
                ))

                recommendations.append(RecommendationItem(
                    id=f"rec_{issue_id}",
                    action_type="standardisation",
                    field="State",
                    severity="medium",
                    affected_rows=affected_rows,
                    before_value=sample_vals[0],
                    proposed_after=proposed_code,
                    confidence=0.99,
                    reasoning=f"Convert full or lowercase state names to 2-letter postal code ('{sample_vals[0]}' -> '{proposed_code}').",
                    transformation_rule={"action": "standardize_state", "field": "State"}
                ))

        # ============================================================
        # 8. INVALID ZIP VALUES
        # ============================================================
        if "Zip" in mapped_df.columns:
            zip_series = mapped_df["Zip"].dropna().astype(str).str.strip()
            # Non-digits or weird lengths
            clean_digits = zip_series.str.extract(r'(\d{5})')[0]
            invalid_zips = zip_series[clean_digits.isna()]
            if len(invalid_zips) > 0:
                affected_rows = (invalid_zips.index + 2).tolist()
                sample_vals = invalid_zips.head(3).tolist()

                issue_id = "issue_invalid_zip"
                issues.append(DataQualityIssue(
                    id=issue_id,
                    issue_type="invalid_zip",
                    field="Zip",
                    severity="medium",
                    affected_rows=affected_rows,
                    affected_count=len(affected_rows),
                    current_value=sample_vals[0],
                    sample_values=sample_vals,
                    reasoning=f"Postal / ZIP values contains malformed format ('{sample_vals[0]}'). Must be integer 5-digit postal code.",
                    recommended_action="Clean non-numeric characters and cast to integer."
                ))

                recommendations.append(RecommendationItem(
                    id=f"rec_{issue_id}",
                    action_type="data_correction",
                    field="Zip",
                    severity="medium",
                    affected_rows=affected_rows,
                    before_value=sample_vals[0],
                    proposed_after=re.sub(r'\D', '', sample_vals[0])[:5] or "00000",
                    confidence=0.88,
                    reasoning="Extract 5-digit integer ZIP code from malformed postal string.",
                    transformation_rule={"action": "clean_zip", "field": "Zip"}
                ))

        # ============================================================
        # 9. DUPLICATE RECORDS DETECTION
        # ============================================================
        check_cols = [c for c in ["Reference", "Address"] if c in mapped_df.columns]
        if check_cols:
            dup_mask = mapped_df.duplicated(subset=check_cols, keep=False)
            if dup_mask.any():
                affected_rows = (mapped_df.index[dup_mask] + 2).tolist()
                sample_val = str(mapped_df.loc[dup_mask, check_cols[0]].iloc[0])

                issues.append(DataQualityIssue(
                    id="issue_duplicate_rows",
                    issue_type="duplicate_record",
                    field=check_cols[0],
                    severity="high",
                    affected_rows=affected_rows,
                    affected_count=len(affected_rows),
                    current_value=sample_val,
                    sample_values=[sample_val],
                    reasoning=f"Duplicate asset records detected across key fields {check_cols}.",
                    recommended_action="Flag duplicate locations for underwriter review before risk model exposure ingestion."
                ))

                recommendations.append(RecommendationItem(
                    id="rec_duplicate_rows",
                    action_type="flag_for_review",
                    field=check_cols[0],
                    severity="high",
                    affected_rows=affected_rows,
                    before_value=sample_val,
                    proposed_after="Flagged for deduplication review",
                    confidence=0.85,
                    reasoning="Duplicate locations inflate aggregate exposure in catastrophe modeling.",
                    uncertainty="Potential multi-building schedule or distinct policies at same address.",
                    transformation_rule={"action": "flag_duplicates", "field": check_cols[0]}
                ))

        # ============================================================
        # 10. MISSING VALUES NOTIFICATION
        # ============================================================
        for target_col, comp in completeness.items():
            missing_count = comp.total_rows - comp.non_null_count
            if missing_count > 0 and comp.completeness_pct < 100.0:
                # Add informational issue
                severity = "critical" if target_col in ["Building Value", "Address"] else ("medium" if comp.completeness_pct < 50 else "low")
                issues.append(DataQualityIssue(
                    id=f"issue_missing_{target_col.replace(' ', '_')}",
                    issue_type="missing_value",
                    field=target_col,
                    severity=severity,
                    affected_rows=[],
                    affected_count=missing_count,
                    current_value="[BLANK]",
                    sample_values=["[EMPTY CELL]"],
                    reasoning=f"Field '{target_col}' has {missing_count} blank entries ({100-comp.completeness_pct:.1f}% missing). Per Rule C-02, missing values must remain empty cells.",
                    recommended_action="Preserve missing values as blank cells. Do NOT hallucinate or fill with zeros."
                ))

        # Compute counts by severity
        crit_count = sum(1 for i in issues if i.severity == "critical")
        high_count = sum(1 for i in issues if i.severity == "high")
        med_count = sum(1 for i in issues if i.severity == "medium")
        low_count = sum(1 for i in issues if i.severity == "low")

        # Overall Intake Quality Score (0 to 100)
        penalty = (crit_count * 15) + (high_count * 8) + (med_count * 3) + (low_count * 1)
        base_score = 100.0 - min(80.0, penalty)
        overall_score = round(max(10.0, base_score), 1)

        report = DataQualityReport(
            total_rows=total_rows,
            total_columns=total_cols,
            overall_quality_score=overall_score,
            completeness_by_field=completeness,
            issues=issues,
            total_anomalies=len(issues),
            critical_anomalies=crit_count,
            high_anomalies=high_count,
            medium_anomalies=med_count,
            low_anomalies=low_count
        )

        return report, recommendations
