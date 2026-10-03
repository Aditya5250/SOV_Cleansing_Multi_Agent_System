import os
from typing import List, Dict, Any, Tuple
from backend.app.services.excel_service import ExcelService
from backend.app.schemas.sov_schema import SheetAnalysis, SheetDiscoveryResult

class SheetIntelligenceAgent:
    """
    AGENT 1 — SHEET INTELLIGENCE & DISCOVERY AGENT
    Scans workbook sheets, evaluates structural characteristics, detects header row,
    classifies sheets (Primary / Secondary / Reject), and scores confidence.
    """

    REJECT_NAME_KEYWORDS = {"readme", "notes", "instruction", "cover", "summary", "legend", "metadata", "glossary", "terms"}
    SECONDARY_NAME_KEYWORDS = {"contacts", "lookup", "rates", "tier", "endorsement", "exclusions", "agents", "broker"}
    PRIMARY_NAME_KEYWORDS = {"sov", "statement of values", "schedule", "location", "locations", "property", "properties", "assets", "site"}

    def __init__(self):
        pass

    def run(self, file_path: str) -> SheetDiscoveryResult:
        sheet_names = ExcelService.load_workbook_sheets(file_path)
        analyzed_sheets: List[SheetAnalysis] = []

        for name in sheet_names:
            analysis_dict = ExcelService.analyze_sheet_structure(file_path, name)
            classification, confidence, reasons = self._classify_sheet(name, analysis_dict)

            analysis = SheetAnalysis(
                sheet_name=name,
                classification=classification,
                confidence=confidence,
                header_row=analysis_dict["header_row"],
                row_count=analysis_dict["row_count"],
                column_count=analysis_dict["column_count"],
                non_null_ratio=analysis_dict["non_null_ratio"],
                header_density=analysis_dict["header_density"],
                reasoning=reasons,
                preview_rows=analysis_dict.get("preview", [])
            )
            analyzed_sheets.append(analysis)

        # Rank sheets: Primary > Secondary > Reject, then by confidence descending, then row_count
        sort_order = {"Primary": 0, "Secondary": 1, "Reject": 2}
        analyzed_sheets.sort(key=lambda s: (sort_order[s.classification], -s.confidence, -s.row_count))

        # Select primary candidate
        primary_candidate = None
        for s in analyzed_sheets:
            if s.classification == "Primary":
                primary_candidate = s
                break
        
        # Fallback if no sheet qualified as Primary
        if not primary_candidate and analyzed_sheets:
            primary_candidate = analyzed_sheets[0]
            primary_candidate.classification = "Primary"
            primary_candidate.reasoning.append("Fallback candidate selected based on maximum data density.")

        return SheetDiscoveryResult(
            sheets=analyzed_sheets,
            selected_sheet=primary_candidate,
            total_sheets=len(analyzed_sheets),
            primary_sheet_name=primary_candidate.sheet_name if primary_candidate else None,
            primary_header_row=primary_candidate.header_row if primary_candidate else 1
        )

    def _classify_sheet(self, name: str, stats: Dict[str, Any]) -> Tuple[str, float, List[str]]:
        reasons = []
        name_lower = name.lower()
        rows = stats["row_count"]
        cols = stats["column_count"]
        density = stats["header_density"]
        non_null = stats["non_null_ratio"]
        merged = stats["merged_cells"]

        # Base score from tabular metrics
        score = 0.50

        # Check for immediate rejection clues
        if any(kw in name_lower for kw in self.REJECT_NAME_KEYWORDS):
            reasons.append(f"Sheet name '{name}' indicates explanatory notes, summary, or metadata.")
            return "Reject", 0.90, reasons

        if rows < 3 or cols < 3:
            reasons.append(f"Dimensions ({rows} rows x {cols} cols) too small for an asset Statement of Values.")
            return "Reject", 0.92, reasons

        # Positive Indicators
        if any(kw in name_lower for kw in self.PRIMARY_NAME_KEYWORDS):
            score += 0.25
            reasons.append(f"Sheet name '{name}' strongly matches standard property schedule terminology.")

        if density >= 0.50:
            score += 0.20
            reasons.append(f"High header keyword density ({density*100:.1f}%) matches insurance asset vocabulary.")
        elif density >= 0.25:
            score += 0.10
            reasons.append(f"Moderate header keyword density ({density*100:.1f}%).")
        else:
            score -= 0.15
            reasons.append(f"Low header keyword density ({density*100:.1f}%).")

        if non_null >= 0.40:
            score += 0.15
            reasons.append(f"Robust data fill ratio ({non_null*100:.1f}% non-null).")
        else:
            score -= 0.10
            reasons.append(f"Sparse data fill ratio ({non_null*100:.1f}% non-null).")

        if rows >= 5 and cols >= 6:
            score += 0.15
            reasons.append(f"Tabular volume ({rows} rows, {cols} columns) indicates full location schedule.")

        if merged > 10:
            score -= 0.05
            reasons.append(f"Contains {merged} merged cells; handled via offset discovery.")

        # Determine classification
        confidence = min(0.98, max(0.20, round(score, 2)))

        if any(kw in name_lower for kw in self.SECONDARY_NAME_KEYWORDS):
            return "Secondary", confidence, reasons

        if confidence >= 0.65 and cols >= 5:
            classification = "Primary"
        elif confidence >= 0.45:
            classification = "Secondary"
        else:
            classification = "Reject"

        return classification, confidence, reasons
