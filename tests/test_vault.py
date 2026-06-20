import pytest
import fakeredis
from vault.token_store import TokenStore
from vault.token_generator import TokenGenerator

@pytest.fixture
def fake_redis_client():
    """Provides a fake Redis client for testing without a real Redis server."""
    return fakeredis.FakeStrictRedis(decode_responses=True)

@pytest.fixture
def token_store(fake_redis_client):
    """Provides a TokenStore instance using the fake Redis client."""
    return TokenStore(fake_redis_client)

def test_generate_token_sequence(fake_redis_client):
    generator = TokenGenerator(fake_redis_client)
    token1 = generator.generate_token("PATIENT")
    token2 = generator.generate_token("PATIENT")
    token3 = generator.generate_token("DOCTOR")
    
    assert token1 == "PATIENT_001"
    assert token2 == "PATIENT_002"
    assert token3 == "DOCTOR_001"

def test_get_or_create_token_new(token_store):
    token = token_store.get_or_create_token("PATIENT", "John Smith")
    assert token == "PATIENT_001"
    
def test_get_or_create_token_existing(token_store):
    token1 = token_store.get_or_create_token("PATIENT", "Jane Doe")
    token2 = token_store.get_or_create_token("PATIENT", "Jane Doe")
    assert token1 == token2 == "PATIENT_001"

def test_get_name_from_token(token_store):
    token = token_store.get_or_create_token("DOCTOR", "Dr. Adams")
    name = token_store.get_name_from_token(token)
    assert name == "Dr. Adams"

def test_get_name_from_invalid_token(token_store):
    name = token_store.get_name_from_token("INVALID_TOKEN")
    assert name is None
