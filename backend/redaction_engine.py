"""
redaction_engine.py
-------------------
Detects PHI/PII in clinical notes using:
  1. Regex rules  — dates, phones, MRNs, SSNs, emails, Aadhaar, addresses
  2. Name heuristic — title-prefixed names + capitalized bigrams

Each detected entity is replaced with a reversible pseudonym token
e.g. "Patient A", "DATE_1", "PHONE_1"
The token map is handed off to the Vault for storage.
"""

import re
import uuid

# ─────────────────────────────────────────────
# Regex rules
# ─────────────────────────────────────────────
REGEX_RULES = [
    ("DATE",    re.compile(r"\b(?:\d{1,2}[/-]\d{1,2}[/-]\d{2,4}|\d{4}-\d{2}-\d{2})\b")),
    ("PHONE",   re.compile(r"\b(?:\+?\d{1,3}[-.\s]?)?\(?\d{3,5}\)?[-.\s]?\d{3,4}[-.\s]?\d{3,4}\b")),
    ("EMAIL",   re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")),
    ("MRN",     re.compile(r"\bMRN[:\s#-]*\d{5,10}\b", re.IGNORECASE)),
    ("SSN",     re.compile(r"\b\d{3}-\d{2}-\d{4}\b")),
    ("AADHAAR", re.compile(r"\b\d{4}\s\d{4}\s\d{4}\b")),
    ("ADDRESS", re.compile(
        r"\b\d{1,5}\s[A-Za-z0-9.\s]{3,30}"
        r"(?:Street|St|Road|Rd|Avenue|Ave|Lane|Ln|Colony|Nagar)\b",
        re.IGNORECASE
    )),
]

NAME_PATTERN       = re.compile(r"\b(?:Mr|Mrs|Ms|Dr|Patient)\.?\s+([A-Z][a-z]+(?:\s[A-Z][a-z]+)?)\b")
PLAIN_NAME_PATTERN = re.compile(r"\b([A-Z][a-z]+\s[A-Z][a-z]+)\b")


# ─────────────────────────────────────────────
# Detection
# ─────────────────────────────────────────────
def _find_entities(text):
    entities = []

    for category, pattern in REGEX_RULES:
        for m in pattern.finditer(text):
            entities.append({
                "original": m.group(0),
                "category": category,
                "start": m.start(),
                "end": m.end()
            })

    for m in NAME_PATTERN.finditer(text):
        start = m.start() + m.group(0).index(m.group(1))
        entities.append({
            "original": m.group(1),
            "category": "NAME",
            "start": start,
            "end": start + len(m.group(1))
        })

    for m in PLAIN_NAME_PATTERN.finditer(text):
        start, end = m.start(1), m.end(1)
        overlaps = any(e["start"] <= start and end <= e["end"] for e in entities)
        if not overlaps:
            entities.append({
                "original": m.group(1),
                "category": "NAME",
                "start": start,
                "end": end
            })

    # Sort and de-duplicate
    entities.sort(key=lambda e: (e["start"], -(e["end"] - e["start"])))
    deduped, last_end = [], -1
    for e in entities:
        if e["start"] >= last_end:
            deduped.append(e)
            last_end = e["end"]

    return deduped


# ─────────────────────────────────────────────
# Redact
# ─────────────────────────────────────────────
def redact(text):
    """
    Replace PHI with pseudonym tokens.
    Returns:
        clean_text (str)   — safe to send to external AI
        token_map  (dict)  — pseudonym → original, for Vault
        entities   (list)  — detected entities with metadata
    """
    entities = _find_entities(text)
    token_map = {}
    counters  = {}

    clean_text = text
    for e in reversed(entities):
        counters[e["category"]] = counters.get(e["category"], 0) + 1
        if e["category"] == "NAME":
            idx = counters["NAME"] - 1
            label = chr(65 + idx) if idx < 26 else str(idx)
            pseudonym = f"Patient {label}"
        else:
            pseudonym = f"{e['category']}_{counters[e['category']]}"

        token_map[pseudonym] = e["original"]
        clean_text = clean_text[: e["start"]] + pseudonym + clean_text[e["end"]:]

    return clean_text, token_map, entities


# ─────────────────────────────────────────────
# Restore
# ─────────────────────────────────────────────
def restore(text, token_map):
    """Reverse pseudonym substitution using the stored token map."""
    restored = text
    for pseudonym, original in token_map.items():
        restored = restored.replace(pseudonym, original)
    return restored


def new_session_id():
    return str(uuid.uuid4())
