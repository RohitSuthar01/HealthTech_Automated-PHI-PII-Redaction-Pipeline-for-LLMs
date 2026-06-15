import pytest
from nlp.presidio_scanner import PresidioScanner

@pytest.fixture
def scanner():
    return PresidioScanner()

def test_scanner_structure(scanner):
    text = "Patient John Smith was admitted on 05/06/2026."
    result = scanner.scan_and_redact(text)
    
    # Assert result structure is correct
    assert "redacted_text" in result
    assert "findings" in result
    assert "total_phi_found" in result
    assert "redaction_summary" in result
    
    assert isinstance(result["findings"], list)
    assert isinstance(result["total_phi_found"], int)
    assert isinstance(result["redaction_summary"], dict)

def test_person_redaction(scanner):
    text = "Dr. Emily Carter treated the patient."
    result = scanner.scan_and_redact(text)
    
    # Verify Emily Carter is redacted
    assert "[PERSON_REDACTED]" in result["redacted_text"]
    assert "Emily Carter" not in result["redacted_text"]
    
    # Check that person type was found in the summary
    assert "person" in result["redaction_summary"]
    assert result["redaction_summary"]["person"] >= 1

def test_email_redaction(scanner):
    text = "Send reports to email: medical.records@hospital.com."
    result = scanner.scan_and_redact(text)
    
    # Verify email is redacted
    assert "[EMAIL_REDACTED]" in result["redacted_text"]
    assert "medical.records@hospital.com" not in result["redacted_text"]

def test_date_redaction(scanner):
    text = "Appointment scheduled for 10/24/2026."
    result = scanner.scan_and_redact(text)
    
    # Verify date is redacted
    assert "[DATE_REDACTED]" in result["redacted_text"]
    assert "10/24/2026" not in result["redacted_text"]
