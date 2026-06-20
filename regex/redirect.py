# Optional Presidio comparison script (requires presidio-analyzer + presidio-anonymizer).
# For the production regex scanner, use: python regex/regex_redact.py
# redact.py
# YOUR FIRST PHI REDACTION SCRIPT! 🎉
# What this does: Takes a patient note and hides all private info

from presidio_analyzer import AnalyzerEngine
from presidio_anonymizer import AnonymizerEngine

# ── Step 1: Start the engines ──────────────────────────────
analyzer  = AnalyzerEngine()   # This FINDS private info
anonymizer = AnonymizerEngine() # This REPLACES private info

# ── Step 2: A fake patient note to test on ─────────────────
sample_note = """
Patient John Smith, DOB: 14/02/1985, visited on 05/06/2026.
Phone: 9876543210. Email: john.smith@gmail.com.
Address: 42 MG Road, Mumbai, Maharashtra.
Complaints: Persistent cough and mild fever for 4 days.
Diagnosed with viral bronchitis. Prescribed azithromycin.
Referred to Dr. Emily Carter at Sunrise Hospital.
"""

# ── Step 3: Find all private info in the note ──────────────
print("=" * 60)
print("📄 ORIGINAL NOTE:")
print(sample_note)

results = analyzer.analyze(
    text=sample_note,
    language="en"
)

print("=" * 60)
print("🔍 WHAT PRESIDIO FOUND (private info detected):")
for result in results:
    detected_text = sample_note[result.start:result.end]
    print(f"  → [{result.entity_type}]  '{detected_text}'  (confidence: {result.score:.0%})")

# ── Step 4: Replace private info with fake labels ──────────
anonymized = anonymizer.anonymize(
    text=sample_note,
    analyzer_results=results
)

print("=" * 60)
print("✅ REDACTED NOTE (safe to send to AI):")
print(anonymized.text)
print("=" * 60)