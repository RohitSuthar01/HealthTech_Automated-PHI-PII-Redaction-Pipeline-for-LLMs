import sys
import os

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

text = "Patient John Smith presented with chest pain."
results = analyzer.analyze(text=text, language="en")
for r in results:
    print("Before:", r.entity_type)
    r.entity_type = "PATIENT"
    print("After:", r.entity_type)
