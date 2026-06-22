import sys
import os
import re

# Filter out project root to avoid shadowing issues
workspace_dir = r"c:\Users\Tirth Patel\OneDrive\Onedrive-Desktop\Infotact\HealthTech_Automated-PHI-PII-Redaction-Pipeline-for-LLMs"
sys.path = [p for p in sys.path if p not in (workspace_dir, "", ".")]

from presidio_analyzer import AnalyzerEngine
from presidio_analyzer.nlp_engine import NlpEngineProvider

configuration = {
    "nlp_engine_name": "spacy",
    "models": [{"model_name": "en_core_web_sm", "lang_code": "en"}],
}
provider = NlpEngineProvider(nlp_configuration=configuration)
nlp_engine = provider.create_engine()
analyzer = AnalyzerEngine(nlp_engine=nlp_engine)

def classify_person(text: str, start: int, end: int, name: str) -> str:
    if re.match(r'^(dr|dr\.|doctor|md|m\.d\.)\b', name, re.IGNORECASE):
        return "DOCTOR"
        
    window_start = max(0, start - 30)
    preceding_window = text[window_start:start]
    
    doctor_pattern = re.compile(
        r'\b(dr|dr\.|doctor|physician|md|m\.d\.|provider|attending|referred|specialist)\b', 
        re.IGNORECASE
    )
    
    if doctor_pattern.search(preceding_window):
        return "DOCTOR"
        
    return "PATIENT"

notes_path = os.path.join(workspace_dir, "nlp", "sample_notes.txt")
with open(notes_path, "r", encoding="utf-8") as f:
    content = f.read()

notes = [note.strip() for note in content.split("NOTE ") if note.strip()]

for idx, note_body in enumerate(notes, 1):
    full_note = f"NOTE {note_body}"
    print(f"\n--- Note {idx} ---")
    results = analyzer.analyze(text=full_note, language="en")
    for r in results:
        if r.entity_type == "PERSON":
            name = full_note[r.start:r.end]
            category = classify_person(full_note, r.start, r.end, name)
            preceding = full_note[max(0, r.start-30):r.start].replace('\n', ' ')
            print(f"Name: {name:<20} | Classified as: {category:<8} | Preceding context: '...{preceding}'")
