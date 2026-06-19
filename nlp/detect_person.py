import os
import spacy
from typing import TypedDict

class PersonFinding(TypedDict):
    text: str
    start: int
    end: int

def detect_persons(text: str, model_name: str = "en_core_web_sm") -> list[PersonFinding]:
    """
    Load a spaCy model and detect all PERSON entities in the provided text.
    
    Args:
        text: The clinical text to analyze.
        model_name: The spaCy model to use (defaults to 'en_core_web_sm').
        
    Returns:
        A list of dictionaries containing the detected PERSON name and its offsets.
    """
    # Load model (spaCy caches loaded models, but loading once per run is standard)
    nlp = spacy.load(model_name)
    doc = nlp(text)
    
    findings: list[PersonFinding] = []
    for ent in doc.ents:
        if ent.label_ == "PERSON":
            findings.append({
                "text": ent.text,
                "start": ent.start_char,
                "end": ent.end_char
            })
            
    return findings

def main():
    # Path to sample clinical notes
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    notes_path = os.path.join(base_dir, "nlp", "sample_notes.txt")
    
    if os.path.exists(notes_path):
        print(f"Reading clinical notes from {notes_path}...\n")
        with open(notes_path, "r", encoding="utf-8") as f:
            content = f.read()
            
        # Split notes by NOTE header
        notes = [note.strip() for note in content.split("NOTE ") if note.strip()]
        
        for idx, note_body in enumerate(notes, 1):
            full_note = f"NOTE {note_body}"
            print("=" * 80)
            print(f"CLINICAL NOTE {idx}:")
            print("-" * 40)
            print(full_note)
            print("-" * 40)
            
            # Detect PERSON entities
            findings = detect_persons(full_note)
            
            print(f"DETECTED PERSON ENTITIES ({len(findings)} found):")
            if findings:
                for f in findings:
                    print(f"  * Name: '{f['text']}' | Span: [{f['start']}:{f['end']}]")
            else:
                print("  No PERSON entities detected.")
            print("=" * 80 + "\n")
    else:
        # Fallback clinical sample if file isn't found
        sample_text = (
            "Patient John Smith presented with chest pain. Attending Physician: Dr. Emily Carter. "
            "Referred by Dr. Anil Mehta."
        )
        print("Sample Notes file not found. Running on fallback sample text:")
        print(f"Text: {sample_text}\n")
        findings = detect_persons(sample_text)
        for f in findings:
            print(f"  * Name: '{f['text']}' | Span: [{f['start']}:{f['end']}]")

if __name__ == "__main__":
    main()
