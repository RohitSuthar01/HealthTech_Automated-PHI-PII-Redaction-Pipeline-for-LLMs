"""
NLP-based PHI/PII scanner and redactor using Microsoft Presidio and spaCy.

This module detects and redacts Protected Health Information (PHI)
and Personally Identifiable Information (PII) using natural language
processing (NLP) models, making it context-aware (especially for names,
organizations, and locations).
"""

from __future__ import annotations

import os
from typing import TypedDict
from presidio_analyzer import AnalyzerEngine
from presidio_anonymizer import AnonymizerEngine
from presidio_anonymizer.entities import OperatorConfig

# ---------------------------------------------------------------------------
# Shared types (matching the regex_redact.py structure for integration)
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
# NLP Redaction Engine Class
# ---------------------------------------------------------------------------

class PresidioScanner:
    def __init__(self):
        # Configure Presidio to use the small, fast en_core_web_sm model
        # instead of trying to download the large en_core_web_lg model.
        from presidio_analyzer.nlp_engine import NlpEngineProvider
        
        configuration = {
            "nlp_engine_name": "spacy",
            "models": [{"model_name": "en_core_web_sm", "lang_code": "en"}],
        }
        provider = NlpEngineProvider(nlp_configuration=configuration)
        nlp_engine = provider.create_engine()
        
        # Initialize the Analyzer and Anonymizer engines
        self.analyzer = AnalyzerEngine(nlp_engine=nlp_engine)
        self.anonymizer = AnonymizerEngine()
        
        # Mapping Presidio entities to our standard label formats
        self.redaction_labels = {
            "PERSON": "[PERSON_REDACTED]",
            "PHONE_NUMBER": "[PHONE_REDACTED]",
            "EMAIL_ADDRESS": "[EMAIL_REDACTED]",
            "DATE_TIME": "[DATE_REDACTED]",
            "IP_ADDRESS": "[IP_REDACTED]",
            "URL": "[URL_REDACTED]",
            "LOCATION": "[LOCATION_REDACTED]",
            "US_SSN": "[SSN_REDACTED]",
            "ORGANIZATION": "[ORGANIZATION_REDACTED]",
            "US_DRIVER_LICENSE": "[LICENSE_REDACTED]",
            "MEDICAL_LICENSE": "[LICENSE_REDACTED]",
        }

    def scan_and_redact(self, text: str) -> ScanResult:
        """
        Scan text for PII/PHI using Presidio (with spaCy NER) and redact it.
        """
        # 1. Analyze text to find PII entities
        raw_results = self.analyzer.analyze(text=text, language="en")
        
        # Filter analyzer results to only include those we explicitly support
        analyzer_results = [r for r in raw_results if r.entity_type in self.redaction_labels]
        
        # 2. Extract findings matching the standard structure
        findings: list[MatchFinding] = []
        summary: dict[str, int] = {}
        
        for result in analyzer_results:
            ent_type = result.entity_type
            # Keep only the entities we want to redact or have defined labels for
            if ent_type in self.redaction_labels:
                orig_val = text[result.start:result.end]
                findings.append({
                    "type": ent_type.lower(),
                    "original_value": orig_val,
                    "start": result.start,
                    "end": result.end
                })
                
                # Update count
                type_lower = ent_type.lower()
                summary[type_lower] = summary.get(type_lower, 0) + 1

        # 3. Anonymize the text using the AnonymizerEngine
        # Setup operator configurations for each entity type we support
        operators = {}
        for entity_name, label in self.redaction_labels.items():
            operators[entity_name] = OperatorConfig(
                "replace", 
                {"new_value": label}
            )

        anonymized_result = self.anonymizer.anonymize(
            text=text,
            analyzer_results=analyzer_results,
            operators=operators
        )
        
        return {
            "redacted_text": anonymized_result.text,
            "findings": sorted(findings, key=lambda f: f["start"]),
            "total_phi_found": len(findings),
            "redaction_summary": summary
        }


# ---------------------------------------------------------------------------
# Demo execution
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    scanner = PresidioScanner()
    
    # Path to sample notes
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    notes_path = os.path.join(base_dir, "nlp", "sample_notes.txt")
    
    if os.path.exists(notes_path):
        print(f"Reading sample notes from {notes_path}...")
        with open(notes_path, "r", encoding="utf-8") as f:
            content = f.read()
        
        # Split notes by blank lines / NOTE headers
        notes = [note.strip() for note in content.split("NOTE ") if note.strip()]
        
        for idx, note_body in enumerate(notes, 1):
            # Reconstruct the header since we split by it
            full_note = f"NOTE {note_body}"
            
            print("\n" + "="*80)
            print(f"PROCESSING NOTE {idx}:")
            print("-" * 40)
            print("ORIGINAL NOTE:")
            print(full_note)
            print("-" * 40)
            
            result = scanner.scan_and_redact(full_note)
            
            print("REDACTED NOTE:")
            print(result["redacted_text"])
            print("-" * 40)
            print(f"TOTAL PHI FOUND: {result['total_phi_found']}")
            
            breakdown_parts = [
                f"{category}: {count}"
                for category, count in sorted(result["redaction_summary"].items())
            ]
            print(f"FINDINGS BREAKDOWN: {', '.join(breakdown_parts)}")
            print("="*80)
    else:
        print(f"Error: Could not find sample notes file at: {notes_path}")
