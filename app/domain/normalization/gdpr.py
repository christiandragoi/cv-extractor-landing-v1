import re
from typing import Tuple, List

GDPR_PATTERNS = {
    'street_address': r'\d{1,4}\s+[A-Za-zäöüÄÖÜß\s]+(?:straße|str\.|weg|platz|allee|gasse)\s+\d{1,3}[a-z]?\b',
    'postal_city': r'\b\d{5}\s+[A-Za-zäöüÄÖÜß\-]+\b',
    'phone': r'(?:\+49|0)[\d\s\-\/\(\)]{6,20}',
    'email': r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}',
}


def strip_gdpr_data(text: str) -> Tuple[str, List[str]]:
    removed = []
    cleaned = text
    for pattern_name, pattern in GDPR_PATTERNS.items():
        matches = list(re.finditer(pattern, cleaned, re.IGNORECASE))
        for match in reversed(matches):
            removed.append(f"{pattern_name}: {match.group()[:30]}...")
            cleaned = cleaned[:match.start()] + f"[{pattern_name.upper()}_REMOVED]" + cleaned[match.end():]
    return cleaned, removed
