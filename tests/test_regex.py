"""
Unit tests for the regex-based PHI/PII scanner (``regex/regex_redact.py``).
"""

from __future__ import annotations

from pathlib import Path

import pytest

from regex.note_loader import load_sample_notes
from regex.regex_redact import (
    REDACTION_LABELS,
    detect_dates,
    detect_emails,
    detect_indian_phones,
    detect_mrns,
    detect_ssns,
    detect_us_phones,
    scan_and_redact,
)

SAMPLE_NOTES_PATH = Path(__file__).resolve().parent.parent / "regex" / "sample_notes.txt"


@pytest.fixture
def sample_notes() -> dict[str, str]:
    return load_sample_notes(SAMPLE_NOTES_PATH)


def test_scan_result_structure():
    result = scan_and_redact("Email: test@example.com")
    assert set(result.keys()) == {
        "redacted_text",
        "findings",
        "total_phi_found",
        "redaction_summary",
    }
    assert isinstance(result["findings"], list)
    assert isinstance(result["redaction_summary"], dict)


@pytest.mark.parametrize(
    "text,label",
    [
        ("Call 9876543210", "[PHONE_REDACTED]"),
        ("Call +91-98765-43210", "[PHONE_REDACTED]"),
        ("Email: a@b.co", "[EMAIL_REDACTED]"),
        ("DOB 14/02/1985", "[DATE_REDACTED]"),
        ("DOB 07/21/1982", "[DATE_REDACTED]"),
        ("Seen 06/20/2026", "[DATE_REDACTED]"),
        ("SSN 123-45-6789", "[SSN_REDACTED]"),
        ("Aadhaar 1234 5678 9012", "[AADHAAR_REDACTED]"),
        ("MRN: MRN-00234", "[MRN_REDACTED]"),
        ("IP 192.168.1.1", "[IP_REDACTED]"),
        ("Site www.hospital.com", "[URL_REDACTED]"),
        ("Mumbai 400001", "[PIN_REDACTED]"),
        ("ZIP 90210-1234", "[ZIP_REDACTED]"),
    ],
)
def test_individual_redaction_labels(text: str, label: str):
    result = scan_and_redact(text)
    assert label in result["redacted_text"]
    assert result["total_phi_found"] >= 1


def test_us_phone_formats():
    text = "Home (312) 555-7812, work 312-555-9910"
    result = scan_and_redact(text)
    assert result["redaction_summary"].get("phone", 0) == 2
    assert "(312)" not in result["redacted_text"]


def test_indian_phone_dedup_overlap():
    """Plain 10-digit number should not double-count when +91 variant overlaps."""
    text = "Phone: 9876543210, backup +91-98765-43210"
    result = scan_and_redact(text)
    assert result["redaction_summary"].get("phone", 0) == 2


def test_us_mm_dd_yyyy_slash_dates():
    assert detect_dates("DOB 07/21/1982")
    assert detect_dates("Follow-up 06/20/2026")
    assert detect_dates("Visit 03/19/2026")


def test_multiple_date_formats_in_one_note():
    text = "DOB 1989-11-23, visit 06-14-2026, tele-visit 06/20/2026"
    result = scan_and_redact(text)
    assert result["redaction_summary"].get("date", 0) == 3


def test_medical_disease_names_not_redacted_by_regex():
    """Regex module does not target names; disease phrases must remain intact."""
    text = (
        "Patient has Parkinson's disease. Family history of Alzheimer's disease. "
        "Email: test@clinic.com"
    )
    result = scan_and_redact(text)
    assert "Parkinson's disease" in result["redacted_text"]
    assert "Alzheimer's disease" in result["redacted_text"]
    assert "[EMAIL_REDACTED]" in result["redacted_text"]


def test_findings_include_positions():
    text = "Email: patient@hospital.com"
    result = scan_and_redact(text)
    assert len(result["findings"]) == 1
    finding = result["findings"][0]
    assert finding["type"] == "email"
    assert finding["original_value"] == "patient@hospital.com"
    assert text[finding["start"] : finding["end"]] == "patient@hospital.com"


def test_redaction_labels_cover_all_types():
    expected = {
        "phone",
        "email",
        "date",
        "ssn",
        "aadhaar",
        "mrn",
        "ip",
        "url",
        "pin",
        "zip",
    }
    assert set(REDACTION_LABELS.keys()) == expected


def test_sample_notes_file_loads_fifteen_notes(sample_notes: dict[str, str]):
    assert len(sample_notes) == 15
    assert "NOTE_001" in sample_notes
    assert "NOTE_015" in sample_notes
    assert "Rahul Sharma" in sample_notes["NOTE_001"]


@pytest.mark.parametrize("note_id", [f"NOTE_{i:03d}" for i in range(1, 16)])
def test_each_sample_note_finds_phi(sample_notes: dict[str, str], note_id: str):
    result = scan_and_redact(sample_notes[note_id])
    assert result["total_phi_found"] >= 5


@pytest.mark.parametrize("note_id", ["NOTE_003", "NOTE_004", "NOTE_009", "NOTE_014"])
def test_parkinson_alzheimer_preserved_in_sample_notes(
    sample_notes: dict[str, str], note_id: str
):
    body = sample_notes[note_id]
    result = scan_and_redact(body)
    if "Parkinson's disease" in body:
        assert "Parkinson's disease" in result["redacted_text"]
    if "Alzheimer's disease" in body:
        assert "Alzheimer's disease" in result["redacted_text"]


def test_canonical_demo_note():
    """Matches the ``if __name__ == '__main__'`` demo in regex_redact.py."""
    note = (
        "Patient Rahul Sharma, DOB: 14/02/1985, visited on "
        "05/06/2026. Phone: 9876543210, also reachable at "
        "+91-98765-43210. Email: rahul.sharma@gmail.com. "
        "SSN: 123-45-6789. Aadhaar: 1234 5678 9012. "
        "MRN: MRN-00234. Address: 42 MG Road, Mumbai 400001. "
        "IP: 192.168.1.1. Referred by Dr. Emily from "
        "www.sunrisehospital.com"
    )
    result = scan_and_redact(note)
    assert result["total_phi_found"] == 11
    assert "rahul.sharma@gmail.com" not in result["redacted_text"]
    assert "9876543210" not in result["redacted_text"]


def test_detect_helpers_return_typed_findings():
    assert detect_emails("a@b.com")[0]["type"] == "email"
    assert detect_ssns("123-45-6789")[0]["type"] == "ssn"
    assert detect_mrns("MRN-99")[0]["type"] == "mrn"
    assert detect_indian_phones("9876543210")[0]["type"] == "phone"
    assert detect_us_phones("(555) 123-4567")[0]["type"] == "phone"
