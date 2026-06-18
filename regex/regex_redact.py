"""
Regex-based PHI/PII scanner and redactor for clinical text.

This module detects and redacts common Protected Health Information (PHI)
and Personally Identifiable Information (PII) patterns found in healthcare
notes. It follows HIPAA Safe Harbor de-identification guidelines by
replacing sensitive values with clear redaction labels.

Uses only Python's built-in ``re`` module — no external dependencies.
"""

from __future__ import annotations

import re
from typing import TypedDict


# ---------------------------------------------------------------------------
# Shared types
# ---------------------------------------------------------------------------

class MatchFinding(TypedDict):
    """A single PHI/PII match found in text."""

    type: str
    original_value: str
    start: int
    end: int


class ScanResult(TypedDict):
    """Full output returned by :func:`scan_and_redact`."""

    redacted_text: str
    findings: list[MatchFinding]
    total_phi_found: int
    redaction_summary: dict[str, int]


# ---------------------------------------------------------------------------
# Redaction labels (one per category)
# ---------------------------------------------------------------------------

REDACTION_LABELS: dict[str, str] = {
    "phone": "[PHONE_REDACTED]",
    "email": "[EMAIL_REDACTED]",
    "date": "[DATE_REDACTED]",
    "ssn": "[SSN_REDACTED]",
    "aadhaar": "[AADHAAR_REDACTED]",
    "mrn": "[MRN_REDACTED]",
    "ip": "[IP_REDACTED]",
    "url": "[URL_REDACTED]",
    "pin": "[PIN_REDACTED]",
    "zip": "[ZIP_REDACTED]",
}


# ---------------------------------------------------------------------------
# Indian phone numbers
# ---------------------------------------------------------------------------

# Matches Indian mobile numbers in these forms:
#   +91-98765-43210  → country code +91, then 5 digits, dash, 5 digits
#   +91 9876543210   → country code +91 with a space before 10 digits
#   9876543210       → plain 10-digit number starting with 6, 7, 8, or 9
INDIAN_PHONE_REGEX = (
    r"(?:"
    r"\+91[\s-]?\d{5}[\s-]?\d{5}"          # +91-XXXXX-XXXXX grouped format
    r"|"
    r"\+91[\s-]?[6-9]\d{9}"               # +91 followed by 10 mobile digits
    r"|"
    r"(?<!\d)[6-9]\d{9}(?!\d)"            # standalone 10-digit mobile number
    r")"
)

# ---------------------------------------------------------------------------
# US phone numbers
# ---------------------------------------------------------------------------

# Matches US phone numbers in these forms:
#   (555) 123-4567  → area code in parentheses, space, then XXX-XXXX
#   555-123-4567    → three groups of digits separated by dashes (3-3-4)
US_PHONE_REGEX = (
    r"(?:"
    r"\(\d{3}\)\s*\d{3}-\d{4}"            # (XXX) XXX-XXXX
    r"|"
    r"(?<!\d)\d{3}-\d{3}-\d{4}(?!\d)"     # XXX-XXX-XXXX
    r")"
)

# ---------------------------------------------------------------------------
# Email addresses
# ---------------------------------------------------------------------------

# Matches a typical email address:
#   username@domain.com  → letters/digits/symbols, @, domain, dot, TLD (2+ chars)
EMAIL_REGEX = r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"

# ---------------------------------------------------------------------------
# Dates (multiple formats)
# ---------------------------------------------------------------------------

# DD/MM/YYYY — day / month / four-digit year  (e.g. 14/02/1985)
DATE_DD_SLASH_MM_YYYY_REGEX = (
    r"\b(?:0?[1-9]|[12]\d|3[01])/(?:0?[1-9]|1[0-2])/\d{4}\b"
)

# MM/DD/YYYY — US-style month / day / year with slashes  (e.g. 07/21/1982)
DATE_MM_SLASH_DD_YYYY_REGEX = (
    r"\b(?:0?[1-9]|1[0-2])/(?:0?[1-9]|[12]\d|3[01])/\d{4}\b"
)

# MM-DD-YYYY — month-day-year with dashes  (e.g. 06-05-2026)
DATE_MM_DASH_DD_YYYY_REGEX = (
    r"\b(?:0?[1-9]|1[0-2])-(?:0?[1-9]|[12]\d|3[01])-\d{4}\b"
)

# DD-MM-YYYY — day-month-year with dashes  (e.g. 14-02-1985)
DATE_DD_DASH_MM_YYYY_REGEX = (
    r"\b(?:0?[1-9]|[12]\d|3[01])-(?:0?[1-9]|1[0-2])-\d{4}\b"
)

# Month DD YYYY — full month name, day, year  (e.g. June 5 2026 or June 5, 2026)
DATE_MONTH_NAME_REGEX = (
    r"\b(?:January|February|March|April|May|June|July|August|"
    r"September|October|November|December)\s+\d{1,2},?\s+\d{4}\b"
)

# YYYY-MM-DD — ISO-style year-month-day  (e.g. 2026-06-05)
DATE_YYYY_DASH_MM_DD_REGEX = (
    r"\b\d{4}-(?:0?[1-9]|1[0-2])-(?:0?[1-9]|[12]\d|3[01])\b"
)

# Combined date pattern (all formats above)
DATE_REGEX = (
    rf"(?:{DATE_DD_SLASH_MM_YYYY_REGEX}|{DATE_MM_SLASH_DD_YYYY_REGEX}|"
    rf"{DATE_MM_DASH_DD_YYYY_REGEX}|{DATE_DD_DASH_MM_YYYY_REGEX}|"
    rf"{DATE_MONTH_NAME_REGEX}|{DATE_YYYY_DASH_MM_DD_REGEX})"
)

# ---------------------------------------------------------------------------
# Social Security Number (SSN)
# ---------------------------------------------------------------------------

# Matches US SSN format: three digits, dash, two digits, dash, four digits
#   (e.g. 123-45-6789)
SSN_REGEX = r"\b\d{3}-\d{2}-\d{4}\b"

# ---------------------------------------------------------------------------
# Aadhaar (Indian 12-digit national ID)
# ---------------------------------------------------------------------------

# Matches Aadhaar numbers:
#   1234 5678 9012  → four groups of four digits separated by spaces
#   123456789012    → twelve consecutive digits
AADHAAR_REGEX = r"\b(?:\d{4}\s\d{4}\s\d{4}|\d{12})\b"

# ---------------------------------------------------------------------------
# Medical Record Number (MRN)
# ---------------------------------------------------------------------------

# Matches MRN labels like MRN-00234  → literal "MRN-" followed by one or more digits
MRN_REGEX = r"\bMRN-\d+\b"

# ---------------------------------------------------------------------------
# IP addresses
# ---------------------------------------------------------------------------

# Matches IPv4 addresses: four groups of 1-3 digit numbers separated by dots
#   (e.g. 192.168.1.1) — each octet must be 0-255
IP_ADDRESS_REGEX = (
    r"\b(?:"
    r"(?:25[0-5]|2[0-4]\d|[01]?\d{1,2})"
    r"(?:\.(?:25[0-5]|2[0-4]\d|[01]?\d{1,2})){3}"
    r")\b"
)

# ---------------------------------------------------------------------------
# URLs and website links
# ---------------------------------------------------------------------------

# Matches web links starting with http://, https://, or www.
#   followed by non-whitespace characters  (e.g. www.sunrisehospital.com)
URL_REGEX = r"(?:https?://|www\.)\S+"

# ---------------------------------------------------------------------------
# Indian PIN codes (postal codes)
# ---------------------------------------------------------------------------

# Matches 6-digit Indian PIN codes where the first digit is 1-9
#   (e.g. 400001) — avoids matching numbers that are part of longer sequences
INDIAN_PIN_REGEX = r"(?<!\d)[1-9]\d{5}(?!\d)"

# ---------------------------------------------------------------------------
# US ZIP codes
# ---------------------------------------------------------------------------

# Matches US ZIP codes:
#   90210       → standard 5-digit ZIP
#   90210-1234  → ZIP+4 format with a dash after the first five digits
US_ZIP_REGEX = r"\b\d{5}(?:-\d{4})?\b"


# ---------------------------------------------------------------------------
# Helper: build findings from a regex
# ---------------------------------------------------------------------------

def _find_matches(text: str, pattern: str, match_type: str) -> list[MatchFinding]:
    """Return all non-overlapping regex matches with their positions."""
    findings: list[MatchFinding] = []
    for match in re.finditer(pattern, text, flags=re.IGNORECASE):
        findings.append(
            {
                "type": match_type,
                "original_value": match.group(0),
                "start": match.start(),
                "end": match.end(),
            }
        )
    return findings


def _apply_redaction(text: str, label: str, pattern: str) -> tuple[str, list[MatchFinding]]:
    """Detect matches for *pattern* and replace each with *label*."""
    findings = _find_matches(text, pattern, _label_to_type(label))
    redacted = re.sub(pattern, label, text, flags=re.IGNORECASE)
    return redacted, findings


def _label_to_type(label: str) -> str:
    """Map a redaction label back to its summary category key."""
    for category, redaction_label in REDACTION_LABELS.items():
        if redaction_label == label:
            return category
    return "unknown"


# ---------------------------------------------------------------------------
# Detection functions (one per PHI/PII category)
# ---------------------------------------------------------------------------

def detect_indian_phones(text: str) -> list[MatchFinding]:
    """Find all Indian phone number matches and their positions."""
    return _find_matches(text, INDIAN_PHONE_REGEX, "phone")


def detect_us_phones(text: str) -> list[MatchFinding]:
    """Find all US phone number matches and their positions."""
    return _find_matches(text, US_PHONE_REGEX, "phone")


def detect_emails(text: str) -> list[MatchFinding]:
    """Find all email address matches and their positions."""
    return _find_matches(text, EMAIL_REGEX, "email")


def detect_dates(text: str) -> list[MatchFinding]:
    """Find all date matches (every supported format) and their positions."""
    return _find_matches(text, DATE_REGEX, "date")


def detect_ssns(text: str) -> list[MatchFinding]:
    """Find all SSN matches and their positions."""
    return _find_matches(text, SSN_REGEX, "ssn")


def detect_aadhaar(text: str) -> list[MatchFinding]:
    """Find all Aadhaar number matches and their positions."""
    return _find_matches(text, AADHAAR_REGEX, "aadhaar")


def detect_mrns(text: str) -> list[MatchFinding]:
    """Find all Medical Record Number matches and their positions."""
    return _find_matches(text, MRN_REGEX, "mrn")


def detect_ip_addresses(text: str) -> list[MatchFinding]:
    """Find all IPv4 address matches and their positions."""
    return _find_matches(text, IP_ADDRESS_REGEX, "ip")


def detect_urls(text: str) -> list[MatchFinding]:
    """Find all URL / website link matches and their positions."""
    return _find_matches(text, URL_REGEX, "url")


def detect_indian_pins(text: str) -> list[MatchFinding]:
    """Find all Indian PIN code matches and their positions."""
    return _find_matches(text, INDIAN_PIN_REGEX, "pin")


def detect_us_zips(text: str) -> list[MatchFinding]:
    """Find all US ZIP code matches and their positions."""
    return _find_matches(text, US_ZIP_REGEX, "zip")


# ---------------------------------------------------------------------------
# Redaction functions (one per PHI/PII category)
# ---------------------------------------------------------------------------

def redact_indian_phones(text: str) -> tuple[str, list[MatchFinding]]:
    """Replace Indian phone numbers with [PHONE_REDACTED]."""
    return _apply_redaction(text, REDACTION_LABELS["phone"], INDIAN_PHONE_REGEX)


def redact_us_phones(text: str) -> tuple[str, list[MatchFinding]]:
    """Replace US phone numbers with [PHONE_REDACTED]."""
    return _apply_redaction(text, REDACTION_LABELS["phone"], US_PHONE_REGEX)


def redact_emails(text: str) -> tuple[str, list[MatchFinding]]:
    """Replace email addresses with [EMAIL_REDACTED]."""
    return _apply_redaction(text, REDACTION_LABELS["email"], EMAIL_REGEX)


def redact_dates(text: str) -> tuple[str, list[MatchFinding]]:
    """Replace dates with [DATE_REDACTED]."""
    return _apply_redaction(text, REDACTION_LABELS["date"], DATE_REGEX)


def redact_ssns(text: str) -> tuple[str, list[MatchFinding]]:
    """Replace SSNs with [SSN_REDACTED]."""
    return _apply_redaction(text, REDACTION_LABELS["ssn"], SSN_REGEX)


def redact_aadhaar(text: str) -> tuple[str, list[MatchFinding]]:
    """Replace Aadhaar numbers with [AADHAAR_REDACTED]."""
    return _apply_redaction(text, REDACTION_LABELS["aadhaar"], AADHAAR_REGEX)


def redact_mrns(text: str) -> tuple[str, list[MatchFinding]]:
    """Replace MRNs with [MRN_REDACTED]."""
    return _apply_redaction(text, REDACTION_LABELS["mrn"], MRN_REGEX)


def redact_ip_addresses(text: str) -> tuple[str, list[MatchFinding]]:
    """Replace IP addresses with [IP_REDACTED]."""
    return _apply_redaction(text, REDACTION_LABELS["ip"], IP_ADDRESS_REGEX)


def redact_urls(text: str) -> tuple[str, list[MatchFinding]]:
    """Replace URLs with [URL_REDACTED]."""
    return _apply_redaction(text, REDACTION_LABELS["url"], URL_REGEX)


def redact_indian_pins(text: str) -> tuple[str, list[MatchFinding]]:
    """Replace Indian PIN codes with [PIN_REDACTED]."""
    return _apply_redaction(text, REDACTION_LABELS["pin"], INDIAN_PIN_REGEX)


def redact_us_zips(text: str) -> tuple[str, list[MatchFinding]]:
    """Replace US ZIP codes with [ZIP_REDACTED]."""
    return _apply_redaction(text, REDACTION_LABELS["zip"], US_ZIP_REGEX)


# ---------------------------------------------------------------------------
# Overlap resolution
# ---------------------------------------------------------------------------

# Higher number = higher priority when two patterns match the same span.
# More specific patterns (URLs, emails, IPs) win over generic digit patterns.
_PATTERN_PRIORITY: dict[str, int] = {
    "url": 100,
    "email": 90,
    "ip": 85,
    "aadhaar": 80,
    "ssn": 75,
    "mrn": 70,
    "phone": 65,
    "date": 60,
    "zip": 50,
    "pin": 40,
}


def _resolve_overlaps(findings: list[MatchFinding]) -> list[MatchFinding]:
    """
    Remove overlapping matches, keeping the highest-priority (longest) span.

    When two detectors claim the same characters, the more specific pattern
    wins so we never double-redact or leave partial PHI behind.
    """
    if not findings:
        return []

    # Sort by start position, then by span length (longest first), then priority.
    ranked = sorted(
        findings,
        key=lambda f: (
            f["start"],
            -(f["end"] - f["start"]),
            -_PATTERN_PRIORITY.get(f["type"], 0),
        ),
    )

    accepted: list[MatchFinding] = []
    for candidate in ranked:
        overlaps = any(
            not (candidate["end"] <= kept["start"] or candidate["start"] >= kept["end"])
            for kept in accepted
        )
        if not overlaps:
            accepted.append(candidate)

    return sorted(accepted, key=lambda f: f["start"])


def _redact_from_findings(text: str, findings: list[MatchFinding]) -> str:
    """Apply redaction labels to *text* using resolved *findings* (end → start)."""
    redacted = text
    for finding in sorted(findings, key=lambda f: f["start"], reverse=True):
        label = REDACTION_LABELS[finding["type"]]
        redacted = (
            redacted[: finding["start"]]
            + label
            + redacted[finding["end"] :]
        )
    return redacted


def _build_summary(findings: list[MatchFinding]) -> dict[str, int]:
    """Count redactions grouped by category."""
    summary: dict[str, int] = {}
    for finding in findings:
        category = finding["type"]
        summary[category] = summary.get(category, 0) + 1
    return summary


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def scan_and_redact(text: str) -> ScanResult:
    """
    Scan *text* for all supported PHI/PII patterns and redact them.

    Returns a dictionary containing:
      - redacted_text: text with sensitive values replaced by labels
      - findings: list of detected items (type, original value, position)
      - total_phi_found: total number of items redacted
      - redaction_summary: count per category (phone, email, date, …)
    """
    all_findings: list[MatchFinding] = []

    all_findings.extend(detect_urls(text))
    all_findings.extend(detect_emails(text))
    all_findings.extend(detect_ip_addresses(text))
    all_findings.extend(detect_aadhaar(text))
    all_findings.extend(detect_ssns(text))
    all_findings.extend(detect_mrns(text))
    all_findings.extend(detect_indian_phones(text))
    all_findings.extend(detect_us_phones(text))
    all_findings.extend(detect_dates(text))
    all_findings.extend(detect_us_zips(text))
    all_findings.extend(detect_indian_pins(text))

    resolved = _resolve_overlaps(all_findings)
    redacted_text = _redact_from_findings(text, resolved)
    summary = _build_summary(resolved)

    return {
        "redacted_text": redacted_text,
        "findings": resolved,
        "total_phi_found": len(resolved),
        "redaction_summary": summary,
    }


# ---------------------------------------------------------------------------
# Demo / self-test
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    SAMPLE_NOTE = (
        "Patient Rahul Sharma, DOB: 14/02/1985, visited on "
        "05/06/2026. Phone: 9876543210, also reachable at "
        "+91-98765-43210. Email: rahul.sharma@gmail.com. "
        "SSN: 123-45-6789. Aadhaar: 1234 5678 9012. "
        "MRN: MRN-00234. Address: 42 MG Road, Mumbai 400001. "
        "IP: 192.168.1.1. Referred by Dr. Emily from "
        "www.sunrisehospital.com"
    )

    result = scan_and_redact(SAMPLE_NOTE)

    print(f"ORIGINAL TEXT: {SAMPLE_NOTE}")
    print(f"REDACTED TEXT: {result['redacted_text']}")
    print(f"TOTAL PHI FOUND: {result['total_phi_found']}")

    breakdown_parts = [
        f"{category}: {count}"
        for category, count in sorted(result["redaction_summary"].items())
    ]
    print(f"FINDINGS BREAKDOWN: {', '.join(breakdown_parts)}")
