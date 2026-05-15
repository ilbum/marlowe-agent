import hashlib
import re


def stable_key(title: str, url: str) -> str:
    normalized = _normalize(title) + "|" + _normalize(url)
    return hashlib.sha256(normalized.encode()).hexdigest()[:32]


def _normalize(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r"\s+", " ", text)
    return text
