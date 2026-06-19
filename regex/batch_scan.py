#!/usr/bin/env python3
"""
Batch-scan all notes in ``sample_notes.txt`` and print a redaction report.

Usage:
    python regex/batch_scan.py
    python regex/batch_scan.py --notes path/to/notes.txt
    python regex/batch_scan.py --verbose
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# Allow running as ``python regex/batch_scan.py`` from project root.
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from regex.note_loader import load_sample_notes
from regex.regex_redact import scan_and_redact

MEDICAL_TERMS = (
    "Parkinson's disease",
    "Alzheimer's disease",
)


def _check_medical_terms_preserved(original: str, redacted: str) -> list[str]:
    """Return disease names that were incorrectly removed from the text."""
    violations: list[str] = []
    for term in MEDICAL_TERMS:
        if term in original and term not in redacted:
            violations.append(term)
    return violations


def run_batch(notes_path: Path, verbose: bool = False, as_json: bool = False) -> int:
    """Scan every note and print a summary. Returns count of notes with issues."""
    notes = load_sample_notes(notes_path)
    if not notes:
        print(f"No notes found in {notes_path}", file=sys.stderr)
        return 1

    issues = 0
    report: dict[str, object] = {"notes": {}, "total_notes": len(notes)}

    for note_id, body in notes.items():
        result = scan_and_redact(body)
        preserved_violations = _check_medical_terms_preserved(body, result["redacted_text"])
        if preserved_violations:
            issues += 1

        entry = {
            "total_phi_found": result["total_phi_found"],
            "redaction_summary": result["redaction_summary"],
            "medical_term_violations": preserved_violations,
        }
        report["notes"][note_id] = entry

        if not as_json:
            summary = ", ".join(
                f"{k}: {v}" for k, v in sorted(result["redaction_summary"].items())
            )
            print(f"{note_id}: {result['total_phi_found']} PHI items ({summary})")
            if preserved_violations:
                print(f"  WARNING: medical terms altered: {', '.join(preserved_violations)}")
            if verbose:
                print(f"  ORIGINAL:  {body[:120]}{'...' if len(body) > 120 else ''}")
                print(f"  REDACTED:  {result['redacted_text'][:120]}{'...' if len(result['redacted_text']) > 120 else ''}")
                print()

    if as_json:
        print(json.dumps(report, indent=2))
    else:
        print("-" * 60)
        print(f"Scanned {len(notes)} notes. Issues: {issues}")

    return issues


def main() -> None:
    parser = argparse.ArgumentParser(description="Batch-scan clinical notes for PHI/PII.")
    parser.add_argument(
        "--notes",
        type=Path,
        default=Path(__file__).resolve().parent / "sample_notes.txt",
        help="Path to numbered sample notes file",
    )
    parser.add_argument("--verbose", action="store_true", help="Print original/redacted snippets")
    parser.add_argument("--json", action="store_true", help="Output machine-readable JSON")
    args = parser.parse_args()

    exit_code = 1 if run_batch(args.notes, verbose=args.verbose, as_json=args.json) else 0
    raise SystemExit(exit_code)


if __name__ == "__main__":
    main()
