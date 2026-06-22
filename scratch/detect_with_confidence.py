import sys
import os
import re
import spacy

# Handle the import shadowing issue where local directory 'regex/' shadows PyPI's regex package
workspace_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path = [p for p in sys.path if p not in (workspace_dir, "", ".")]

from presidio_analyzer import AnalyzerEngine
from presidio_analyzer.nlp_engine import NlpEngineProvider

# Common clinical eponyms that shouldn't be flagged as PERSON names
EPONYMS = {
    "parkinson", "alzheimer", "crohn", "hodgkin", "huntington", 
    "down", "grave", "tourette", "asperger", "meniere", "wilson"
}

# Clinical metadata headers that frequently cause NER false positives (e.g. classified as ORG or PERSON)
HEADERS_TO_EXCLUDE = {
    "dob", "mrn", "ssn", "ip", "email", "aadhaar", "phone", 
    "address", "cell", "name", "contact", "portal", "residence",
    "backup", "mobile", "physician", "doctor", "patient", "license",
    "hospital", "clinic", "ward", "date", "status", "chief", "complaint",
    "history", "treatment", "discharged", "admitted", "review", "clinical", "note"
}

SPACY_TO_PRESIDIO_MAP = {
    "PERSON": "PERSON",
    "GPE": "LOCATION",
    "LOC": "LOCATION",
    "ORG": "ORGANIZATION",
    "DATE": "DATE_TIME"
}

def is_false_positive(word: str, entity_type: str) -> bool:
    """
    Checks if a detected word is a false positive based on clinical context and clean name rules.
    """
    word_clean = word.strip().lower()
    
    # Strip common non-alphanumeric punctuation from borders (e.g. "SSN:" -> "ssn")
    word_alphanumeric = re.sub(r'^[^a-z0-9]+|[^a-z0-9]+$', '', word_clean)
    
    # Rule 1: Exclude common clinical headers/meta-terms from PERSON, ORGANIZATION, and LOCATION
    if entity_type in ("PERSON", "ORGANIZATION", "LOCATION"):
        if word_alphanumeric in HEADERS_TO_EXCLUDE or word_clean in HEADERS_TO_EXCLUDE:
            return True
            
    # Rule 2: Specific validation for PERSON names
    if entity_type == "PERSON":
        # Person names should not contain numbers or clinical symbols
        if any(char.isdigit() or char in "+@/\\:#_[]=" for char in word):
            return True
        # Person names should not contain known disease eponyms (e.g. "Parkinson's disease")
        for ep in EPONYMS:
            if ep in word_clean:
                return True
        # Person names are usually longer than a single character
        if len(word_alphanumeric) <= 1:
            return True
            
    return False

def detect_phi_combined(text: str) -> list[dict]:
    """
    Detects PHI/PII by combining spaCy NER and Microsoft Presidio.
    Applies verification rules, filters false positives, resolves overlaps,
    and boosts confidence for entities confirmed by both engines.
    """
    # 1. Initialize spaCy model
    nlp = spacy.load("en_core_web_sm")
    doc = nlp(text)
    
    # 2. Initialize Presidio Analyzer Engine
    configuration = {
        "nlp_engine_name": "spacy",
        "models": [{"model_name": "en_core_web_sm", "lang_code": "en"}],
    }
    provider = NlpEngineProvider(nlp_configuration=configuration)
    nlp_engine = provider.create_engine()
    analyzer = AnalyzerEngine(nlp_engine=nlp_engine)
    
    # 3. Gather spaCy findings
    spacy_findings = []
    for ent in doc.ents:
        mapped_type = SPACY_TO_PRESIDIO_MAP.get(ent.label_)
        if mapped_type:
            # Filter false positives
            if is_false_positive(ent.text, mapped_type):
                continue
                
            spacy_findings.append({
                "word": ent.text,
                "type": mapped_type,
                "start": ent.start_char,
                "end": ent.end_char,
                "confidence": 0.80,  # Default spaCy NER confidence
                "source": "spaCy"
            })
            
    # 4. Gather Presidio findings
    presidio_results = analyzer.analyze(text=text, language="en")
    presidio_findings = []
    for r in presidio_results:
        word = text[r.start:r.end]
        
        # Filter false positives
        if is_false_positive(word, r.entity_type):
            continue
            
        presidio_findings.append({
            "word": word,
            "type": r.entity_type,
            "start": r.start,
            "end": r.end,
            "confidence": r.score,
            "source": "Presidio"
        })
        
    # 5. Merge findings and resolve overlaps
    # Combine both list of findings
    raw_combined = spacy_findings + presidio_findings
    
    # Sort:
    # 1. Start position ascending
    # 2. Length descending (longer span first)
    # 3. Confidence score descending
    raw_combined.sort(key=lambda x: (x["start"], -(x["end"] - x["start"]), -x["confidence"]))
    
    merged: list[dict] = []
    for candidate in raw_combined:
        # Check if candidate overlaps with any already accepted finding
        overlap_found = False
        for kept in merged:
            # Overlap condition: start and end bounds intersect
            if not (candidate["end"] <= kept["start"] or candidate["start"] >= kept["end"]):
                overlap_found = True
                
                # Check for exact span match
                if candidate["start"] == kept["start"] and candidate["end"] == kept["end"]:
                    # Same span: if types are compatible, boost confidence and combine sources
                    if candidate["type"] == kept["type"]:
                        if candidate["source"] != kept["source"] and "Confirmed" not in kept["source"]:
                            kept["source"] = f"{kept['source']}+{candidate['source']} (Confirmed)"
                            # Boost confidence score for double agreement
                            kept["confidence"] = min(1.0, kept["confidence"] + 0.15)
                    else:
                        # Different types: Prefer Presidio's specific type mappings if confidence is higher
                        if candidate["source"] == "Presidio" and candidate["confidence"] > kept["confidence"]:
                            kept["type"] = candidate["type"]
                            kept["confidence"] = candidate["confidence"]
                            kept["source"] = "Presidio"
                break
                
        if not overlap_found:
            merged.append(candidate)
            
    # Final sort by start offset
    merged.sort(key=lambda x: x["start"])
    return merged

def run_on_sample_notes():
    # Path to sample clinical notes
    notes_path = os.path.join(workspace_dir, "regex", "sample_notes.txt")
    
    if not os.path.exists(notes_path):
        print(f"Error: Sample notes file not found at: {notes_path}")
        return
        
    print(f"Reading sample notes from {notes_path}...\n")
    with open(notes_path, "r", encoding="utf-8") as f:
        content = f.read()
        
    # Split notes by NOTE_### header
    raw_notes = content.split("NOTE_")
    notes = []
    for rn in raw_notes:
        if not rn.strip():
            continue
        lines = rn.split("\n")
        header = f"NOTE_{lines[0].split(':')[0]}"
        body = "\n".join(lines[1:]).strip()
        notes.append((header, body))
        
    # Test on first 10 notes
    test_count = min(10, len(notes))
    print(f"Testing combined spaCy + Presidio engine on the first {test_count} notes:\n")
    
    for i in range(test_count):
        header, body = notes[i]
        print("=" * 100)
        print(f"NOTE: {header}")
        print("-" * 100)
        print("Original Text:")
        print(body)
        print("-" * 100)
        
        detections = detect_phi_combined(body)
        
        print(f"{'Detected Word':<25} | {'Entity Type':<18} | {'Confidence':<10} | {'Detection Source':<30}")
        print("-" * 100)
        if detections:
            for d in detections:
                print(f"{d['word']:<25} | {d['type']:<18} | {d['confidence']:.0%} | {d['source']:<30}")
        else:
            print("No entities detected.")
        print("=" * 100 + "\n")

if __name__ == "__main__":
    run_on_sample_notes()
