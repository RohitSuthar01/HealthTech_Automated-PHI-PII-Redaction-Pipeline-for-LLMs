import pytest
import fakeredis
from vault.vault import Vault
from vault.token_store import TokenStore
from vault.token_generator import TokenGenerator
from vault.nlp_adapter import NLPAdapter
from vault.text_engine import TextEngine
from vault.risk_analyzer import RiskAnalyzer

@pytest.fixture
def fake_redis_client():
    return fakeredis.FakeStrictRedis(decode_responses=True)

@pytest.fixture
def vault(fake_redis_client):
    return Vault(fake_redis_client, ttl_seconds=60)

def test_vault_redact_and_restore(vault):
    session_id = "session_123"
    original_note = "Patient John Smith visited Dr. Adams at General Hospital."
    
    nlp_entities = [
        {"text": "John Smith", "type": "PATIENT", "confidence": 0.99},
        {"text": "Dr. Adams", "type": "DOCTOR", "confidence": 0.95},
        {"text": "General Hospital", "type": "HOSPITAL", "confidence": 0.8}
    ]
    
    redacted_note, processed_entities = vault.redact_note(session_id, original_note, nlp_entities)
    
    assert "John Smith" not in redacted_note
    assert "PATIENT_001" in redacted_note
    assert "DOCTOR_001" in redacted_note
    assert "HOSPITAL_001" in redacted_note
    
    restored_note = vault.restore_note(session_id, redacted_note)
    assert restored_note == original_note

def test_duplicate_entity_handling(vault):
    session_id = "session_456"
    note = "John Smith told John Smith's wife that he is John Smith."
    nlp = [{"text": "John Smith", "type": "PATIENT", "confidence": 0.9}]
    
    redacted, _ = vault.redact_note(session_id, note, nlp)
    
    # Should replace all 3 instances
    assert "John Smith" not in redacted
    assert redacted.count("PATIENT_001") == 3
    
    restored = vault.restore_note(session_id, redacted)
    assert restored == note

def test_collision_prevention(vault):
    session_id = "session_789"
    note = "Patient John Smith saw Doctor John Smith."
    nlp = [
        {"text": "John Smith", "type": "PATIENT"},
        {"text": "John Smith", "type": "DOCTOR"}
    ]
    
    redacted, entities = vault.redact_note(session_id, note, nlp)
    tokens = {e["type"]: e["token"] for e in entities}
    
    # Even though text is the same, types are different, so tokens must be different
    assert tokens["PATIENT"] != tokens["DOCTOR"]
    assert "PATIENT_001" in redacted
    assert "DOCTOR_001" in redacted

def test_risk_analyzer():
    unsafe_text = "My SSN is 123-45-6789 and my email is test@example.com."
    safe_text = "My SSN is SSN_001 and my email is EMAIL_001."
    
    unsafe_result = RiskAnalyzer.calculate_risk(unsafe_text, unsafe_text)
    assert not unsafe_result["is_safe"]
    assert len(unsafe_result["leakages"]) == 2
    
    safe_result = RiskAnalyzer.calculate_risk(safe_text, safe_text)
    assert safe_result["is_safe"]

def test_clear_session(vault):
    session_id = "session_clear"
    nlp = [{"text": "Jane Doe", "type": "PATIENT"}]
    
    redacted, _ = vault.redact_note(session_id, "Jane Doe", nlp)
    
    # Keys should exist
    assert vault.redis.keys(f"{session_id}:*")
    
    # Clear.
    removed = vault.clear_session(session_id)
    assert removed > 0
    assert not vault.redis.keys(f"{session_id}:*")
