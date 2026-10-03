import re
from typing import Dict, Tuple, Optional, List
from rapidfuzz import fuzz
from backend.app.schemas.sov_schema import TARGET_FIELDS

class MatchingService:
    """
    Pass 1 deterministic & fuzzy column matcher.
    Implements exact matching, normalization, domain synonyms, and RapidFuzz scoring.
    """

    # Comprehensive Insurance Domain Knowledgebase for SOV
    DOMAIN_SYNONYMS: Dict[str, str] = {
        # Reference / ID
        "loc": "Reference",
        "loc #": "Reference",
        "loc no": "Reference",
        "location #": "Reference",
        "location no": "Reference",
        "location id": "Reference",
        "loc id": "Reference",
        "prop id": "Reference",
        "property id": "Reference",
        "property #": "Reference",
        "site #": "Reference",
        "site id": "Reference",
        "ref #": "Reference",
        "item": "Reference",
        "item #": "Reference",
        "unit #": "Reference",
        "record id": "Reference",
        "schedule #": "Reference",

        # Address
        "street": "Address",
        "street address": "Address",
        "property address": "Address",
        "site address": "Address",
        "location address": "Address",
        "physical address": "Address",
        "address line 1": "Address",
        "addr": "Address",
        "premise address": "Address",

        # City
        "city name": "City",
        "municipality": "City",
        "town": "City",

        # State
        "st": "State",
        "province": "State",
        "region": "State",
        "state prov": "State",
        "state/prov": "State",
        "state code": "State",


        # Zip
        "zipcode": "Zip",
        "postal": "Zip",
        "postal code": "Zip",
        "post code": "Zip",
        "pin code": "Zip",
        "zip code": "Zip",

        # County
        "parish": "County",
        "county name": "County",
        "borough": "County",

        # Country
        "nation": "Country",
        "cntry": "Country",
        "jurisdiction": "Country",

        # Building Value
        "bldg value": "Building Value",
        "building val": "Building Value",
        "bldg val": "Building Value",
        "bldg cost": "Building Value",
        "bldg repl cost": "Building Value",
        "bldg repl cost new": "Building Value",
        "building replacement cost": "Building Value",
        "building rcn": "Building Value",
        "rcn building": "Building Value",
        "structure value": "Building Value",
        "property value": "Building Value",
        "real property": "Building Value",
        "building limit": "Building Value",
        "bldg tiv": "Building Value",

        # Contents
        "content": "Contents",
        "bpp": "Contents",
        "business personal property": "Contents",
        "personal property": "Contents",
        "stock": "Contents",
        "equipment": "Contents",
        "machinery": "Contents",
        "ff&e": "Contents",
        "contents value": "Contents",
        "content value": "Contents",
        "contents limit": "Contents",

        # BI (Business Interruption)
        "business interruption": "BI",
        "business income": "BI",
        "bi value": "BI",
        "bi limit": "BI",
        "loss of rents": "BI",
        "loss of rent": "BI",
        "ale": "BI",
        "extra expense": "BI",
        "time element": "BI",

        # Occupancy
        "occupancy type": "Occupancy",
        "occupancy description": "Occupancy",
        "occupancy code": "Occupancy",
        "use": "Occupancy",
        "usage": "Occupancy",
        "building use": "Occupancy",
        "tenant type": "Occupancy",
        "operation": "Occupancy",
        "business type": "Occupancy",

        # Construction
        "construction type": "Construction",
        "const type": "Construction",
        "const": "Construction",
        "bldg construction": "Construction",
        "iso construction": "Construction",
        "wall construction": "Construction",
        "frame / masonry": "Construction",
        "construction class": "Construction",

        # Storeys
        "stories": "Storeys",
        "no of stories": "Storeys",
        "number of stories": "Storeys",
        "no of storeys": "Storeys",
        "number of storeys": "Storeys",
        "floors": "Storeys",
        "number of floors": "Storeys",
        "levels": "Storeys",
        "bldg height (stories)": "Storeys",

        # Number of Buildings
        "no of buildings": "Number of Buildings",
        "no of bldgs": "Number of Buildings",
        "building count": "Number of Buildings",
        "total buildings": "Number of Buildings",
        "number of structures": "Number of Buildings",
        "num bldgs": "Number of Buildings",

        # Year Built
        "yr built": "Year Built",
        "built year": "Year Built",
        "year of construction": "Year Built",
        "construction year": "Year Built",
        "yr": "Year Built",
        "age": "Year Built",

        # Fire Sprinklers (Y/N)
        "fire sprinklers": "Fire Sprinklers (Y/N)",
        "sprinklers": "Fire Sprinklers (Y/N)",
        "fire prot": "Fire Sprinklers (Y/N)",
        "fire protection": "Fire Sprinklers (Y/N)",
        "sprinklered": "Fire Sprinklers (Y/N)",
        "sprinklered (y/n)": "Fire Sprinklers (Y/N)",
        "sprinkler %": "Fire Sprinklers (Y/N)",
        "fire suppression": "Fire Sprinklers (Y/N)",
        "fire prot.": "Fire Sprinklers (Y/N)",

        # Other
        "other value": "Other",
        "misc value": "Other",
        "other limit": "Other",
        "miscellaneous": "Other",
        "other structures": "Other",
        "appurtenant structures": "Other",
        "yard items": "Other"
    }

    @staticmethod
    def normalize_header(header: str) -> str:
        """Strip non-alphanumeric, lower case, standardize spacing."""
        cleaned = re.sub(r"[^\w\s]", " ", header.lower())
        return " ".join(cleaned.split())

    @classmethod
    def match_column(cls, source_header: str) -> Tuple[Optional[str], float, str, str]:
        """
        Execute Pass 1 Matching:
        1. Exact match with target fields (confidence 1.0)
        2. Exact match with domain synonyms (confidence 0.96 - 0.99)
        3. Normalized fuzzy matching with RapidFuzz (threshold >= 0.75)
        
        Returns: (target_field, confidence, method, reasoning)
        """
        raw_clean = source_header.strip()
        norm_source = cls.normalize_header(raw_clean)

        # 1. Exact string match against target fields (case-insensitive)
        for target in TARGET_FIELDS:
            if raw_clean.lower() == target.lower():
                return target, 1.0, "exact", f"Exact string match with standard target field '{target}'."
            if norm_source == cls.normalize_header(target):
                return target, 0.99, "exact", f"Exact normalized match with standard target field '{target}'."

        # 2. Known domain synonym match
        for syn, target in cls.DOMAIN_SYNONYMS.items():
            if norm_source == cls.normalize_header(syn):
                return target, 0.98, "fuzzy", f"Matched known insurance industry synonym '{syn}' -> '{target}'."


        # 3. Fuzzy matching against domain synonyms
        best_target = None
        best_ratio = 0.0
        best_reason = ""

        # Test against domain synonyms table
        for syn, target in cls.DOMAIN_SYNONYMS.items():
            ratio = fuzz.token_sort_ratio(norm_source, syn) / 100.0
            if ratio > best_ratio:
                best_ratio = ratio
                best_target = target
                best_reason = f"Fuzzy matched synonym '{syn}' -> '{target}' with {ratio*100:.1f}% similarity."

        # Also test directly against standard target fields
        for target in TARGET_FIELDS:
            norm_target = cls.normalize_header(target)
            ratio = fuzz.token_sort_ratio(norm_source, norm_target) / 100.0
            if ratio > best_ratio:
                best_ratio = ratio
                best_target = target
                best_reason = f"Fuzzy matched target field '{target}' with {ratio*100:.1f}% similarity."

        if best_ratio >= 0.75:
            # Scale confidence smoothly
            conf = min(0.95, round(best_ratio, 2))
            return best_target, conf, "fuzzy", best_reason

        # Unresolved in Pass 1
        return None, round(best_ratio, 2), "none", "No high-confidence exact or fuzzy match found in Pass 1."
