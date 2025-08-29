import re

def norm(s: str) -> str:
    """Simple text normalizer: lowercase and strip extra spaces."""
    if not s:
        return ""
    s = s.lower()
    s = re.sub(r"\s+", " ", s)
    return s.strip()
