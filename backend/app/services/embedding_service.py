import os
import json
import numpy as np
from typing import Dict, Tuple, Optional, List
from backend.app.schemas.sov_schema import TARGET_FIELDS, TARGET_FIELD_DEFINITIONS

class EmbeddingService:
    """
    Pass 2 Semantic Embedding Service using sentence-transformers.
    Includes target field semantic descriptions and vector memory for cross-submission learning.
    """

    _instance = None
    _model = None

    # Enriched semantic representations for the 17 target fields
    TARGET_SEMANTIC_PROFILES = {
        "Reference": "unique identifier property schedule location number item id code tag",
        "Address": "street address physical location property premise door number road avenue boulevard",
        "City": "city municipality town locality township urban center",
        "State": "state province territory region 2-letter postal abbreviation",
        "Zip": "postal code zip zipcode pin code geographic postal area number",
        "County": "county parish borough administrative division regional district",
        "Country": "country nation sovereign state territory jurisdiction USA Canada UK",
        "Building Value": "building value structure replacement cost new rcn real property physical asset limit",
        "Contents": "contents value personal property business personal property bpp stock equipment machinery inventory ff&e",
        "BI": "business income business interruption time element loss of rent extra expense ale gross earnings profits",
        "Occupancy": "occupancy type building use tenant classification commercial residential industrial office retail",
        "Construction": "construction type material framing masonry steel concrete wood frame iso class exterior wall",
        "Storeys": "number of storeys stories floors levels building height elevation vertical tiers",
        "Number of Buildings": "number of buildings structures units count total structures complex count",
        "Year Built": "year built constructed construction date age vintage completion year",
        "Fire Sprinklers (Y/N)": "fire sprinklers fire protection sprinklered system suppression hydrant extinguisher nfpa 13 y n",
        "Other": "other value miscellaneous limit extra additional insured coverage auxiliary outdoor structures appurtenant"
    }

    def __init__(self, memory_file_path: Optional[str] = None):
        self.memory_file_path = memory_file_path or os.path.join(
            os.path.dirname(__file__), "..", "..", "sample_data", "vector_memory.json"
        )
        self.vector_memory: Dict[str, str] = self._load_vector_memory()
        self._target_embeddings: Optional[Dict[str, np.ndarray]] = None
        self._init_model()

    def _init_model(self):
        """Lazy load sentence transformer or fallback to semantic token TF-IDF."""
        try:
            from sentence_transformers import SentenceTransformer
            model_name = os.getenv("EMBEDDING_MODEL_NAME", "all-MiniLM-L6-v2")
            self._model = SentenceTransformer(model_name)
            self._precompute_target_embeddings()
        except Exception as e:
            print(f"Warning: SentenceTransformer init warning ({e}). Falling back to fast n-gram semantic vectorizer.")
            self._model = None

    def _load_vector_memory(self) -> Dict[str, str]:
        """Load persistent vector memory of confirmed mappings for cross-submission learning."""
        try:
            if os.path.exists(self.memory_file_path):
                with open(self.memory_file_path, "r", encoding="utf-8") as f:
                    return json.load(f)
        except Exception:
            pass
        return {}

    def save_mapping_to_memory(self, source_column: str, target_column: str):
        """Store approved mapping in vector memory for cross-submission learning."""
        try:
            norm_key = source_column.strip().lower()
            self.vector_memory[norm_key] = target_column
            os.makedirs(os.path.dirname(self.memory_file_path), exist_ok=True)
            with open(self.memory_file_path, "w", encoding="utf-8") as f:
                json.dump(self.vector_memory, f, indent=2)
        except Exception as e:
            print(f"Failed to persist vector memory: {e}")

    def _precompute_target_embeddings(self):
        """Precompute normalized embeddings for the 17 target fields."""
        if not self._model:
            return
        self._target_embeddings = {}
        for target, profile in self.TARGET_SEMANTIC_PROFILES.items():
            emb = self._model.encode(f"{target}: {profile}", normalize_embeddings=True)
            self._target_embeddings[target] = emb

    def _cosine_similarity(self, a: np.ndarray, b: np.ndarray) -> float:
        norm_a = np.linalg.norm(a)
        norm_b = np.linalg.norm(b)
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return float(np.dot(a, b) / (norm_a * norm_b))

    def _fallback_token_vector(self, text: str) -> Dict[str, float]:
        tokens = text.lower().replace("_", " ").replace("/", " ").replace("-", " ").split()
        vec = {}
        for t in tokens:
            vec[t] = vec.get(t, 0.0) + 1.0
        total = sum(v*v for v in vec.values()) ** 0.5 or 1.0
        return {k: v / total for k, v in vec.items()}

    def _fallback_similarity(self, text1: str, text2: str) -> float:
        v1 = self._fallback_token_vector(text1)
        v2 = self._fallback_token_vector(text2)
        dot = sum(v1[k] * v2.get(k, 0.0) for k in v1)
        return float(dot)

    def match_column_semantic(self, source_header: str) -> Tuple[Optional[str], float, str, str]:
        """
        Execute Pass 2 Semantic Matching:
        1. Check Cross-Submission Vector Memory
        2. Encode source header and compute cosine similarity against 17 target field profiles
        
        Returns: (target_field, confidence, method, reasoning)
        """
        norm_source = source_header.strip().lower()

        # Check Vector Memory
        if norm_source in self.vector_memory:
            target = self.vector_memory[norm_source]
            return (
                target,
                0.98,
                "semantic",
                f"Resolved via Cross-Submission Vector Memory (learned from prior verified SOV submission)."
            )

        best_target = None
        best_score = 0.0

        if self._model and self._target_embeddings:
            source_emb = self._model.encode(source_header, normalize_embeddings=True)
            for target, target_emb in self._target_embeddings.items():
                sim = self._cosine_similarity(source_emb, target_emb)
                if sim > best_score:
                    best_score = sim
                    best_target = target
        else:
            # High-performance token/sub-word fallback
            for target, profile in self.TARGET_SEMANTIC_PROFILES.items():
                sim = self._fallback_similarity(source_header, f"{target} {profile}")
                if sim > best_score:
                    best_score = sim
                    best_target = target

        # Calibrate confidence score
        confidence = min(0.96, max(0.0, round(float(best_score), 2)))

        if confidence >= 0.50 and best_target:
            reasoning = (
                f"Semantic embedding similarity identified strong conceptual alignment between "
                f"'{source_header}' and target property field '{best_target}' (score: {confidence:.2f})."
            )
            return best_target, confidence, "semantic", reasoning

        return (
            best_target,
            confidence,
            "none",
            f"Low semantic confidence ({confidence:.2f}) for '{source_header}'. Flagged for human review."
        )

# Global singleton
embedding_service = EmbeddingService()
