import os
import openpyxl
import pandas as pd
import numpy as np
from typing import List, Dict, Tuple, Any, Optional

class ExcelService:
    """
    Robust Excel & CSV ingestion service.
    Analyzes sheet structure, detects merged cells, and identifies header rows.
    """

    INSURANCE_HEADER_KEYWORDS = {
        "loc", "location", "ref", "reference", "id", "property", "site",
        "address", "street", "addr", "premise",
        "city", "town", "municipality",
        "state", "st", "province", "region",
        "zip", "postal", "postcode", "zipcode",
        "county", "parish", "jurisdiction",
        "country", "nation", "territory",
        "bldg", "building", "structure", "cost", "value", "val", "rcn", "replacement",
        "content", "contents", "stock", "equipment", "machinery", "ff&e", "personal property",
        "bi", "business income", "interruption", "ale", "extra expense", "loss of rent",
        "occupancy", "occ", "use", "usage", "tenant", "operation",
        "construction", "const", "frame", "masonry", "iso", "class",
        "storeys", "stories", "floors", "levels", "height",
        "no of bldgs", "number of buildings", "bldg count", "units",
        "year built", "yr built", "built", "construction year", "age",
        "fire", "sprinkler", "sprinklers", "protection", "prot", "hydrant",
        "other", "misc", "auto", "land", "improvement"
    }

    @staticmethod
    def load_workbook_sheets(file_path: str) -> List[str]:
        """Return list of sheet names from Excel or ['Sheet1'] for CSV."""
        if file_path.lower().endswith(".csv"):
            return ["CSV_Data"]
        
        wb = openpyxl.load_workbook(file_path, read_only=True, data_only=True)
        sheets = wb.sheetnames
        wb.close()
        return sheets

    @staticmethod
    def analyze_sheet_structure(file_path: str, sheet_name: str) -> Dict[str, Any]:
        """
        Deep structural analysis of a worksheet.
        Evaluates row continuity, null distribution, merged cells, header candidates.
        """
        if file_path.lower().endswith(".csv"):
            return ExcelService._analyze_csv(file_path)

        # Use openpyxl data_only to evaluate values rather than formulas
        wb = openpyxl.load_workbook(file_path, data_only=True)
        ws = wb[sheet_name]

        merged_cell_count = len(ws.merged_cells.ranges) if hasattr(ws, 'merged_cells') else 0
        total_rows = ws.max_row or 0
        total_cols = ws.max_column or 0

        # Read top 50 rows for structural profiling
        rows_sample = []
        for r_idx, row in enumerate(ws.iter_rows(values_only=True), start=1):
            if r_idx > 60:
                break
            rows_sample.append(list(row))
        wb.close()

        if not rows_sample:
            return {
                "sheet_name": sheet_name,
                "row_count": 0,
                "column_count": 0,
                "merged_cells": 0,
                "non_null_ratio": 0.0,
                "header_row": 1,
                "header_density": 0.0,
                "preview": []
            }

        # Find best candidate header row
        best_header_row, best_density = ExcelService._detect_header_row(rows_sample)

        # Calculate non-null ratio across sample
        all_cells = [cell for r in rows_sample for cell in r]
        non_null_count = sum(1 for c in all_cells if c is not None and str(c).strip() != "")
        total_cells = max(1, len(all_cells))
        non_null_ratio = non_null_count / total_cells

        # Preview rows (up to 8 rows starting from header)
        start_idx = max(0, best_header_row - 1)
        preview = [[str(c) if c is not None else "" for c in r] for r in rows_sample[start_idx:start_idx + 8]]

        return {
            "sheet_name": sheet_name,
            "row_count": total_rows,
            "column_count": total_cols,
            "merged_cells": merged_cell_count,
            "non_null_ratio": round(non_null_ratio, 3),
            "header_row": best_header_row,
            "header_density": round(best_density, 3),
            "preview": preview
        }

    @staticmethod
    def _analyze_csv(file_path: str) -> Dict[str, Any]:
        """Analyze CSV structure."""
        df_sample = pd.read_csv(file_path, nrows=50, header=None)
        rows_sample = df_sample.values.tolist()
        best_header_row, best_density = ExcelService._detect_header_row(rows_sample)
        
        # Count total rows
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            total_rows = sum(1 for _ in f)
        
        all_cells = [cell for r in rows_sample for cell in r]
        non_null_count = sum(1 for c in all_cells if pd.notna(c) and str(c).strip() != "")
        non_null_ratio = non_null_count / max(1, len(all_cells))

        start_idx = max(0, best_header_row - 1)
        preview = [[str(c) if pd.notna(c) else "" for c in r] for r in rows_sample[start_idx:start_idx + 8]]

        return {
            "sheet_name": "CSV_Data",
            "row_count": total_rows,
            "column_count": df_sample.shape[1],
            "merged_cells": 0,
            "non_null_ratio": round(non_null_ratio, 3),
            "header_row": best_header_row,
            "header_density": round(best_density, 3),
            "preview": preview
        }

    @staticmethod
    def _detect_header_row(rows_sample: List[List[Any]]) -> Tuple[int, float]:
        """
        Evaluate candidate header rows (1 to min(20, len(rows_sample))).
        Scores based on:
        1. Non-empty string ratio
        2. Unique token ratio (headers shouldn't repeat)
        3. Match with insurance domain vocabulary
        4. Data continuity in subsequent rows
        """
        best_row = 1
        best_score = -1.0

        for r_idx, row in enumerate(rows_sample[:25], start=1):
            if not row:
                continue

            cleaned_cells = [str(c).strip() for c in row if c is not None and str(c).strip() != ""]
            if len(cleaned_cells) < 2:
                continue

            # Check string nature
            string_cells = sum(1 for c in cleaned_cells if not c.replace(".", "", 1).replace("-", "", 1).isdigit())
            string_ratio = string_cells / len(cleaned_cells)

            # Check uniqueness
            unique_ratio = len(set(cleaned_cells)) / len(cleaned_cells)

            # Check insurance keyword matches
            kw_matches = 0
            for c in cleaned_cells:
                tokens = set(c.lower().replace("_", " ").replace("-", " ").replace("/", " ").split())
                if tokens.intersection(ExcelService.INSURANCE_HEADER_KEYWORDS):
                    kw_matches += 1
            kw_ratio = kw_matches / len(cleaned_cells)

            # Check if next row has data
            next_row_has_data = 0.5
            if r_idx < len(rows_sample):
                next_row = [c for c in rows_sample[r_idx] if c is not None and str(c).strip() != ""]
                if len(next_row) >= len(cleaned_cells) * 0.5:
                    next_row_has_data = 1.0

            # Composite scoring formula
            score = (string_ratio * 0.3) + (unique_ratio * 0.2) + (kw_ratio * 0.35) + (next_row_has_data * 0.15)

            if score > best_score:
                best_score = score
                best_row = r_idx

        return best_row, max(0.0, best_score)

    @staticmethod
    def extract_dataframe(file_path: str, sheet_name: str, header_row: int) -> pd.DataFrame:
        """
        Extract clean pandas DataFrame from designated sheet and header row.
        Handles row skipping, unnamed columns, and merged header gaps.
        """
        skip = max(0, header_row - 1)
        if file_path.lower().endswith(".csv"):
            df = pd.read_csv(file_path, skiprows=skip)
        else:
            df = pd.read_excel(file_path, sheet_name=sheet_name, skiprows=skip, engine="openpyxl")

        # Clean column names
        cleaned_cols = []
        seen_cols = set()
        for idx, col in enumerate(df.columns):
            col_str = str(col).strip() if pd.notna(col) else f"Unnamed_{idx+1}"
            if "Unnamed:" in col_str or col_str == "" or col_str.lower() == "nan":
                col_str = f"Column_{idx+1}"
            
            # Ensure unique column names in raw df
            orig_col = col_str
            counter = 1
            while col_str in seen_cols:
                col_str = f"{orig_col}_{counter}"
                counter += 1
            seen_cols.add(col_str)
            cleaned_cols.append(col_str)

        df.columns = cleaned_cols

        # Drop entirely empty rows
        df = df.dropna(how="all").reset_index(drop=True)
        return df
