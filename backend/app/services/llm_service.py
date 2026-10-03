import os
import json
import re
from typing import Dict, Any, Optional, List, Tuple
from backend.app.schemas.sov_schema import TARGET_FIELDS, TARGET_FIELD_DEFINITIONS

class LLMService:
    """
    LLM reasoning service supporting OpenAI, Google Gemini, and deterministic fallback.
    Enforces structured JSON outputs, strict explainability, and re-reasoning on reviewer rejection.
    """

    def __init__(self):
        self.provider = os.getenv("LLM_PROVIDER", "deterministic").lower()
        self.model = os.getenv("LLM_MODEL", "gpt-4o")
        self.openai_key = os.getenv("LLM_API_KEY") or os.getenv("OPENAI_API_KEY")
        self.gemini_key = os.getenv("GEMINI_API_KEY")

        # Auto-detect available keys if provider not explicitly configured
        if self.provider == "deterministic":
            if self.openai_key:
                self.provider = "openai"
            elif self.gemini_key:
                self.provider = "gemini"

    def reason_about_mapping(
        self, source_col: str, sample_values: List[str], candidate_targets: List[Tuple[str, float]]
    ) -> Dict[str, Any]:
        """
        Reason about ambiguous column mapping using LLM or deterministic insurance logic.
        """
        candidates_str = ", ".join([f"'{c[0]}' ({c[1]:.2f})" for c in candidate_targets[:4]])
        samples_str = ", ".join([str(s) for s in sample_values[:5] if s])

        prompt = (
            f"You are an insurance statement of values (SOV) data engineering specialist.\n"
            f"Analyze this raw column: '{source_col}'\n"
            f"Sample data values: [{samples_str}]\n"
            f"Candidate target fields: [{candidates_str}]\n"
            f"Allowed 17 target fields: {json.dumps(TARGET_FIELDS)}\n\n"
            f"Respond ONLY in valid JSON format:\n"
            f"{{\n"
            f'  "target_column": "<one of 17 fields or null>",\n'
            f'  "confidence": <float 0.0 to 1.0>,\n'
            f'  "reasoning": "<concise domain justification>",\n'
            f'  "uncertainty": "<note if uncertain, else null>"\n'
            f"}}"
        )

        llm_response = self._call_llm_json(prompt)
        if llm_response and "target_column" in llm_response:
            target = llm_response.get("target_column")
            if target in TARGET_FIELDS or target is None:
                return {
                    "target_column": target,
                    "confidence": float(llm_response.get("confidence", 0.85)),
                    "reasoning": str(llm_response.get("reasoning", "LLM reasoning based on field nomenclature and sample values.")),
                    "uncertainty": llm_response.get("uncertainty")
                }

        # Deterministic domain rule fallback
        return self._deterministic_mapping_reasoning(source_col, sample_values, candidate_targets)

    def explain_quality_issue(
        self, issue_type: str, field: str, sample_values: List[str], row_count: int
    ) -> Dict[str, Any]:
        """
        Generate plain-English explainable rationale and recommended remediation action.
        """
        prompt = (
            f"You are an exposure management data quality analyst in P&C insurance.\n"
            f"A data quality issue was detected in field '{field}'.\n"
            f"Issue type: '{issue_type}', Affected row count: {row_count}.\n"
            f"Sample offending values: {sample_values[:5]}\n\n"
            f"Provide an explainable diagnosis and recommended action in JSON:\n"
            f"{{\n"
            f'  "action_type": "<column_mapping | data_correction | standardisation | flag_for_review>",\n'
            f'  "reasoning": "<clear business impact and technical explanation>",\n'
            f'  "proposed_action": "<what should be done>",\n'
            f'  "confidence": <float 0.0 to 1.0>\n'
            f"}}"
        )

        llm_response = self._call_llm_json(prompt)
        if llm_response and "reasoning" in llm_response:
            return llm_response

        # Deterministic explainability fallback
        return self._deterministic_quality_reasoning(issue_type, field, sample_values, row_count)

    def re_reason_rejected_recommendation(
        self, original_item: Dict[str, Any], user_feedback: str
    ) -> Dict[str, Any]:
        """
        Iterative re-reasoning when a human reviewer rejects a recommendation with feedback (Bonus requirement).
        """
        prompt = (
            f"A human reviewer rejected an automated data cleansing recommendation.\n"
            f"Field: '{original_item.get('field')}'\n"
            f"Original proposed action: '{original_item.get('proposed_after')}'\n"
            f"Original rationale: '{original_item.get('reasoning')}'\n"
            f"Reviewer Feedback: '{user_feedback}'\n\n"
            f"Re-evaluate the issue taking the human feedback into account.\n"
            f"Respond in JSON:\n"
            f"{{\n"
            f'  "revised_action": "<revised value or flag_for_review>",\n'
            f'  "revised_reasoning": "<why this was revised based on feedback>",\n'
            f'  "revised_confidence": <float 0.0 to 1.0>,\n'
            f'  "status": "<accepted | modified | escalated>"\n'
            f"}}"
        )

        llm_response = self._call_llm_json(prompt)
        if llm_response and "revised_reasoning" in llm_response:
            return llm_response

        # Deterministic re-reasoning
        return {
            "revised_action": user_feedback.strip() if user_feedback else "flag_for_review",
            "revised_reasoning": f"Re-evaluated in response to reviewer note: '{user_feedback}'. Adjusted remediation to comply with human reviewer specification.",
            "revised_confidence": 0.95,
            "status": "modified"
        }

    def _call_llm_json(self, prompt: str) -> Optional[Dict[str, Any]]:
        """Call LLM provider and parse structured JSON safely."""
        try:
            if self.provider == "openai" and self.openai_key:
                from openai import OpenAI
                client = OpenAI(api_key=self.openai_key)
                response = client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": "You are a professional P&C insurance data quality and SOV AI agent. Output valid JSON only."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.1,
                    response_format={"type": "json_object"}
                )
                content = response.choices[0].message.content
                return json.loads(content)

            elif self.provider == "gemini" and self.gemini_key:
                from google import genai
                client = genai.Client(api_key=self.gemini_key)
                response = client.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=f"{prompt}\nReturn strictly JSON."
                )
                text = response.text.strip()
                # Extract json code block if present
                match = re.search(r"```(?:json)?(.*?)```", text, re.DOTALL)
                raw_json = match.group(1).strip() if match else text
                return json.loads(raw_json)

        except Exception as e:
            print(f"LLM API call notice ({self.provider}): {e}. Using deterministic reasoning engine.")

        return None

    def _deterministic_mapping_reasoning(
        self, source_col: str, sample_values: List[str], candidate_targets: List[Tuple[str, float]]
    ) -> Dict[str, Any]:
        """High-precision domain heuristic for ambiguous mapping."""
        norm = source_col.lower().strip()

        if candidate_targets and candidate_targets[0][1] >= 0.50:
            top_target = candidate_targets[0][0]
            top_score = candidate_targets[0][1]
            return {
                "target_column": top_target,
                "confidence": min(0.92, top_score + 0.1),
                "reasoning": f"Nomenclature analysis correlates '{source_col}' with standard target '{top_target}' in Property & Casualty exposure models.",
                "uncertainty": None
            }

        return {
            "target_column": None,
            "confidence": 0.35,
            "reasoning": f"Column '{source_col}' lacks strong deterministic evidence for target schema fields.",
            "uncertainty": "Uncertain whether this column represents an unclassified insured value or auxiliary property attribute."
        }

    def _deterministic_quality_reasoning(
        self, issue_type: str, field: str, sample_values: List[str], count: int
    ) -> Dict[str, Any]:
        """Deterministic business impact explanations for data anomalies."""
        sample_str = ", ".join([f"'{s}'" for s in sample_values[:3]])

        if issue_type == "negative_value":
            return {
                "action_type": "data_correction",
                "reasoning": f"Building, Contents, or BI values cannot be negative ({sample_str}). Downstream catastrophe models (e.g. RMS, AIR) reject negative sums insured.",
                "proposed_action": "Convert absolute value or flag negative entries for underwriting audit.",
                "confidence": 0.98
            }
        elif issue_type == "future_year":
            return {
                "action_type": "data_correction",
                "reasoning": f"Year Built ({sample_str}) exceeds current calendar year. This typically indicates a data-entry typo (e.g. transposition error).",
                "proposed_action": "Flag for reviewer confirmation or cap at current year.",
                "confidence": 0.95
            }
        elif issue_type == "invalid_storeys":
            return {
                "action_type": "data_correction",
                "reasoning": f"Storeys value ({sample_str}) is below 1. Physical insured structures must have at least 1 storey.",
                "proposed_action": "Default to 1 storey for ground-level single structures or request clarification.",
                "confidence": 0.92
            }
        elif issue_type == "currency_symbol":
            return {
                "action_type": "standardisation",
                "reasoning": f"Numeric financial field contains currency symbols or punctuation ({sample_str}). Exposure models require clean IEEE floating-point numbers.",
                "proposed_action": "Strip currency symbols, commas, and white-space, then cast to Float.",
                "confidence": 0.99
            }
        elif issue_type == "invalid_sprinkler":
            return {
                "action_type": "standardisation",
                "reasoning": f"Fire Sprinklers contains non-standard values ({sample_str}). Required target codes are strictly Y, N, Y13, or Y(13R).",
                "proposed_action": "Standardise 'Yes'/'100%'/'Full' -> 'Y', 'No'/'0%'/'None' -> 'N', '13' -> 'Y13'.",
                "confidence": 0.96
            }
        elif issue_type == "inconsistent_state":
            return {
                "action_type": "standardisation",
                "reasoning": f"State values ({sample_str}) are not standard 2-letter uppercase postal abbreviations.",
                "proposed_action": "Map full state names and lowercase codes to standard 2-letter postal abbreviations (e.g. 'California' -> 'CA').",
                "confidence": 0.99
            }
        elif issue_type == "invalid_zip":
            return {
                "action_type": "data_correction",
                "reasoning": f"Postal / ZIP values ({sample_str}) must be valid 5-digit US integer postal codes for geocoding accuracy.",
                "proposed_action": "Clean hyphens/extensions and cast to standard 5-digit integer ZIP.",
                "confidence": 0.94
            }
        elif issue_type == "missing_value":
            return {
                "action_type": "flag_for_review",
                "reasoning": f"Field '{field}' has {count} missing records. Per constraint C-02, missing values must remain blank in export and never be hallucinated.",
                "proposed_action": "Preserve as blank in export; notify underwriting of coverage gap.",
                "confidence": 1.0
            }

        return {
            "action_type": "flag_for_review",
            "reasoning": f"Data anomaly detected in '{field}' requiring underwriting assessment.",
            "proposed_action": "Flag for human review before transformation.",
            "confidence": 0.85
        }

# Global singleton
llm_service = LLMService()
