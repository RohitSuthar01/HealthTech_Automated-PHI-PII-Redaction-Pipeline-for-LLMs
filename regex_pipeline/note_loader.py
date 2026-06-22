"""
Utilities for loading numbered clinical notes from ``sample_notes.txt``.
"""

from __future__ import annotations

import re
from pathlib import Path

NOTE_HEADER_PATTERN = re.compile(r"^NOTE_(\d{3}):$", re.MULTILINE)


def load_sample_notes(path: str | Path | None = None) -> dict[str, str]:
    """
    Parse ``sample_notes.txt`` into a mapping of note ID to body text.

    Returns:
        ``{"NOTE_001": "Patient Rahul Sharma...", ...}``
    """
    if path is None:
        path = Path(__file__).resolve().parent / "sample_notes.txt"
    else:
        path = Path(path)

    content = path.read_text(encoding="utf-8").strip()
    if not content:
        return {}

    notes: dict[str, str] = {}
    parts = re.split(r"\n(?=NOTE_\d{3}:)", content)

    for part in parts:
        part = part.strip()
        if not part:
            continue
        lines = part.splitlines()
        header = lines[0].strip()
        if not header.endswith(":"):
            continue
        note_id = header.rstrip(":")
        body = "\n".join(lines[1:]).strip()
        notes[note_id] = body

    return notes


def iter_sample_notes(path: str | Path | None = None):
    """Yield ``(note_id, body)`` pairs in file order."""
    for note_id, body in load_sample_notes(path).items():
        yield note_id, body
