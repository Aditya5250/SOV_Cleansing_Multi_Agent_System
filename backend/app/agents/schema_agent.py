import pandas as pd
from typing import Dict, List, Optional, Any, Tuple
from backend.app.services.matching_service import MatchingService
from backend.app.services.embedding_service import embedding_service
from backend.app.services.llm_service import llm_service
from backend.app.schemas.sov_schema import (
    ColumnMapping,
    SchemaMappingResult,
    TARGET_FIELDS,
    MappingMethod
)

class SchemaMappingAgent:
    """
    AGENT 2 — SCHEMA MAPPING AGENT
    Implements mandatory two-stage mapping:
    - Pass 1: Exact, normalized, and fuzzy matching (RapidFuzz >= 0.75)
    - Pass 2: Semantic embedding similarity + LLM reasoning for ambiguous headers
    Guarantees explainability, confidence scoring, and human review flags.
    """

    def __init__(self):
        pass

    def run(self, df: pd.DataFrame, sheet_name: str, header_row: int) -> SchemaMappingResult:
        source_columns = list(df.columns)
        mappings: Dict[str, ColumnMapping] = {}
        assigned_targets = set()
        unresolved_count = 0
        confidences = []

        # ============================================================
        # PASS 1: DETERMINISTIC & FUZZY MATCHING (RapidFuzz >= 0.75)
        # ============================================================
        pass1_unresolved = []

        for col in source_columns:
            target, conf, method, reasoning = MatchingService.match_column(col)

            if target and conf >= 0.75:
                mappings[col] = ColumnMapping(
                    source_column=col,
                    target_column=target,
                    confidence=conf,
                    method=method,  # "exact" or "fuzzy"
                    reasoning=reasoning,
                    flag_for_review=False
                )
                assigned_targets.add(target)
                confidences.append(conf)
            else:
                pass1_unresolved.append(col)

        # ============================================================
        # PASS 2: SEMANTIC EMBEDDINGS & LLM REASONING
        # ============================================================
        for col in pass1_unresolved:
            # Semantic embedding similarity
            sem_target, sem_conf, sem_method, sem_reason = embedding_service.match_column_semantic(col)

            sample_vals = [str(x) for x in df[col].dropna().head(5).tolist()]

            # If semantic embedding has good confidence and target not yet taken by high-conf match
            if sem_target and sem_conf >= 0.65 and sem_target not in assigned_targets:
                mappings[col] = ColumnMapping(
                    source_column=col,
                    target_column=sem_target,
                    confidence=sem_conf,
                    method="semantic",
                    reasoning=sem_reason,
                    flag_for_review=False
                )
                assigned_targets.add(sem_target)
                confidences.append(sem_conf)

            elif sem_conf >= 0.40:
                # LLM reasoning on ambiguous mapping
                candidates = [(sem_target, sem_conf)] if sem_target else []
                llm_res = llm_service.reason_about_mapping(col, sample_vals, candidates)
                llm_target = llm_res.get("target_column")
                llm_conf = float(llm_res.get("confidence", 0.50))
                llm_reasoning = llm_res.get("reasoning", "LLM reasoning evaluated domain taxonomy.")
                
                is_flagged = (llm_conf < 0.60 or llm_target is None)
                if is_flagged:
                    unresolved_count += 1

                mappings[col] = ColumnMapping(
                    source_column=col,
                    target_column=llm_target if llm_target in TARGET_FIELDS else None,
                    confidence=llm_conf,
                    method="llm",
                    reasoning=llm_reasoning,
                    flag_for_review=is_flagged
                )
                if llm_target:
                    assigned_targets.add(llm_target)
                confidences.append(llm_conf)

            else:
                # Unresolved / low confidence (< 0.50) -> flag for human review
                unresolved_count += 1
                mappings[col] = ColumnMapping(
                    source_column=col,
                    target_column=None,
                    confidence=round(float(sem_conf), 2),
                    method="none",
                    reasoning=f"No conclusive semantic match found for '{col}'. Required human review.",
                    flag_for_review=True
                )
                confidences.append(sem_conf)

        overall_conf = round(sum(confidences) / max(1, len(confidences)), 2)
        unmapped_targets = [t for t in TARGET_FIELDS if t not in assigned_targets]

        return SchemaMappingResult(
            sheet_name=sheet_name,
            header_row=header_row,
            mappings=mappings,
            unresolved_count=unresolved_count,
            overall_confidence=overall_conf,
            unmapped_target_fields=unmapped_targets
        )
