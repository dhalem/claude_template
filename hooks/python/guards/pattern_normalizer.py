"""Pattern name normalization utilities for MetaCognitiveGuard."""

from typing import Dict, List


def normalize_pattern_name(pattern: str) -> str:
    """Normalize a pattern name to standard format."""
    if not isinstance(pattern, str):
        return str(pattern)

    pattern_lower = pattern.lower().replace("-", " ").replace("_", " ")

    if "infrastructure" in pattern_lower and "blame" in pattern_lower:
        return "Infrastructure Blame"
    elif "theory" in pattern_lower and ("lock" in pattern_lower or "lockin" in pattern_lower):
        return "Theory Lock-in"
    elif "rabbit" in pattern_lower and "hole" in pattern_lower:
        return "Rabbit Holes"
    elif "excuse" in pattern_lower and ("making" in pattern_lower or "make" in pattern_lower):
        return "Excuse Making"
    else:
        # Keep original if not recognized
        return pattern


def normalize_patterns(patterns: List[str]) -> List[str]:
    """Normalize a list of pattern names."""
    return [normalize_pattern_name(p) for p in patterns if p]


def normalize_confidence_scores(scores: Dict[str, float]) -> Dict[str, float]:
    """Normalize confidence score keys to standard pattern names."""
    normalized = {}
    for key, value in scores.items():
        normalized_key = normalize_pattern_name(key)
        normalized[normalized_key] = value
    return normalized
