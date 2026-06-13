# Pseudonymization & Token Mapping

**Project:** HealthTech Automated PHI/PII Redaction Pipeline for LLMs  
**Module:** `vault/` (Token Vault)  
**Document Version:** 1.0

---

## 1. What Is Pseudonymization?

### Redaction vs. Pseudonymization

When protecting patient data before sending it to an AI, there are two fundamentally different approaches:

| Approach | What Happens | AI Can Understand Context? | Reversible? |
|----------|-------------|---------------------------|-------------|
| **Redaction** | Sensitive values are removed or replaced with blanks/labels like `[REDACTED]` | ❌ No — AI loses all context | ❌ No |
| **Pseudonymization** | Sensitive values are replaced with consistent fake tokens like `PATIENT_001` | ✅ Yes — AI sees a coherent document | ✅ Yes — tokens map back to real values |

### Side-by-Side Example

**Original clinical note:**

```
Dr. Adams saw patient John Smith on 12/03/1990.
John Smith complained of chest pain.
Dr. Adams prescribed rest.
```

#### ❌ Redaction (Bad for AI)

```
Dr. [REDACTED] saw patient [REDACTED] on [REDACTED].
[REDACTED] complained of chest pain.
Dr. [REDACTED] prescribed rest.
```

**Problem:** The AI cannot tell who did what. It doesn't know if the same person is mentioned twice, who the doctor is, or when the visit occurred. The response will be generic and clinically useless.

#### ✅ Pseudonymization (Good for AI)

```
DOCTOR_001 saw patient PATIENT_001 on DATE_001.
PATIENT_001 complained of chest pain.
DOCTOR_001 prescribed rest.
```

**Benefit:** The AI understands that `PATIENT_001` is one person mentioned twice, that `DOCTOR_001` is the treating physician, and that the visit happened on `DATE_001`. It can generate a clinically coherent summary — and the pipeline swaps tokens back to real names before the doctor sees the result.

---

## 2. Token Naming Convention

Tokens follow a predictable, human-readable format:

```
{ENTITY_TYPE}_{SEQUENTIAL_NUMBER}
```

### Token Types

| Token Prefix | Entity Type | Example Original Value | Example Token |
|-------------|-------------|----------------------|---------------|
| `PATIENT_` | Patient / person name | `John Smith` | `PATIENT_001` |
| `DOCTOR_` | Physician / provider name | `Dr. Adams` | `DOCTOR_001` |
| `PHONE_` | Telephone number | `9876543210` | `PHONE_001` |
| `EMAIL_` | Email address | `john@gmail.com` | `EMAIL_001` |
| `DATE_` | Date of birth, visit date | `12/03/1990` | `DATE_001` |
| `SSN_` | Social Security number | `123-45-6789` | `SSN_001` |
| `MRN_` | Medical record number | `MRN-00234` | `MRN_001` |
| `AADHAAR_` | Aadhaar (Indian national ID) | `1234 5678 9012` | `AADHAAR_001` |
| `LOCATION_` | Address / city / PIN | `Mumbai 400001` | `LOCATION_001` |
| `ORG_` | Hospital / clinic name | `Sunrise Hospital` | `ORG_001` |
| `IP_` | IP address | `192.168.1.1` | `IP_001` |
| `URL_` | Website link | `www.hospital.com` | `URL_001` |
| `ZIP_` | US ZIP code | `90210` | `ZIP_001` |

### Numbering Rules

- Counters are **per entity type, per session** — `PATIENT_001` and `DOCTOR_001` can coexist.
- The **same original value always maps to the same token** within a session (consistency).
- **Different values always get different tokens** — `John Smith` → `PATIENT_001`, `Sarah Johnson` → `PATIENT_002`.
- Counters reset for each new session (new UUID).

---

## 3. Complete Worked Example

### Input Text

```
Dr. Adams saw patient John Smith on 12/03/1990.
John Smith complained of chest pain.
Dr. Adams prescribed rest.
```

**Session ID:** `sess-7f3a-9b2c-4d1e-8a6f-0c5b3e2d1a0f`

---

### Step 1 — Detection Results

Both the Regex and NLP scanners analyze the text:

| # | Detected Value | Entity Type | Detector | Start | End |
|---|---------------|-------------|----------|-------|-----|
| 1 | `Dr. Adams` | PERSON (provider) | NLP (Presidio) | 0 | 9 |
| 2 | `John Smith` | PERSON (patient) | NLP (Presidio) | 22 | 32 |
| 3 | `12/03/1990` | DATE | Regex | 36 | 46 |
| 4 | `John Smith` | PERSON (patient) | NLP (Presidio) | 48 | 58 |
| 5 | `Dr. Adams` | PERSON (provider) | NLP (Presidio) | 89 | 98 |

> Note: `John Smith` and `Dr. Adams` each appear twice — the vault deduplicates them.

---

### Step 2 — Token Assignment

The Token Vault checks: *"Have I seen this value before in this session?"*

| Original Value | Entity Type | Already Seen? | Token Assigned |
|---------------|-------------|:-------------:|----------------|
| `Dr. Adams` | DOCTOR | No | `DOCTOR_001` |
| `John Smith` | PATIENT | No | `PATIENT_001` |
| `12/03/1990` | DATE | No | `DATE_001` |
| `John Smith` | PATIENT | **Yes** → reuse | `PATIENT_001` |
| `Dr. Adams` | DOCTOR | **Yes** → reuse | `DOCTOR_001` |

**Unique tokens assigned: 3** (not 5 — deduplication saves tokens and keeps the AI context clean).

---

### Step 3 — Pseudonymized Text (Sent to AI)

```
DOCTOR_001 saw patient PATIENT_001 on DATE_001.
PATIENT_001 complained of chest pain.
DOCTOR_001 prescribed rest.
```

This text contains **zero PHI** and is safe to send to an external AI API.

---

### Step 4 — AI Response (With Tokens)

```
Based on the clinical note, PATIENT_001 presented with chest pain
on DATE_001. DOCTOR_001 prescribed rest. Recommend follow-up
if symptoms persist beyond 48 hours.
```

---

### Step 5 — Restored Text (Returned to Doctor)

The vault performs reverse mapping (longest token first):

| Token in AI Response | Lookup | Restored Value |
|---------------------|--------|----------------|
| `PATIENT_001` | Redis GET | `John Smith` |
| `DATE_001` | Redis GET | `12/03/1990` |
| `DOCTOR_001` | Redis GET | `Dr. Adams` |

**Final output:**

```
Based on the clinical note, John Smith presented with chest pain
on 12/03/1990. Dr. Adams prescribed rest. Recommend follow-up
if symptoms persist beyond 48 hours.
```

The doctor sees a fully readable, clinically accurate report — with no indication that pseudonymization ever occurred.

---

## 4. Mapping Table Example

For session `sess-7f3a-9b2c-4d1e-8a6f-0c5b3e2d1a0f`, the vault maintains:

| Token | Type | Original Value | Session ID |
|-------|------|---------------|------------|
| `PATIENT_001` | PATIENT | John Smith | `sess-7f3a-...` |
| `DOCTOR_001` | DOCTOR | Dr. Adams | `sess-7f3a-...` |
| `DATE_001` | DATE | 12/03/1990 | `sess-7f3a-...` |

In Redis, this corresponds to:

```
sess-7f3a-9b2c-4d1e-8a6f-0c5b3e2d1a0f:PERSON:PATIENT_001  = "John Smith"
sess-7f3a-9b2c-4d1e-8a6f-0c5b3e2d1a0f:PERSON:DOCTOR_001   = "Dr. Adams"
sess-7f3a-9b2c-4d1e-8a6f-0c5b3e2d1a0f:DATE:DATE_001       = "12/03/1990"
```

All keys expire after the session TTL (default: 30 minutes).

---

## 5. How Reverse Mapping Works

### Algorithm

```
1. Load all token → original_value pairs for the session from Redis
2. Sort tokens by length (longest first) to prevent partial matches
3. For each token in the AI response text:
     text = text.replace(token, original_value)
4. Return restored text
5. (Optional) Clear session or let TTL expire
```

### Python Implementation

```python
import re
from vault.redis_client import RedisClient


def get_session_mappings(
    redis_client,
    session_id: str,
) -> dict[str, str]:
    """Load all token → original value pairs for a session."""
    pattern = f"{session_id}:*"
    mappings = {}
    for key in redis_client.keys(pattern):
        # Key format: session_id:ENTITY_TYPE:TOKEN
        token = key.split(":")[-1]
        original = redis_client.get(key)
        if original:
            mappings[token] = original
    return mappings


def restore_text(
    pseudonymized_text: str,
    session_id: str,
    redis_client=None,
) -> str:
    """Replace all pseudonym tokens with original PHI values."""
    if redis_client is None:
        redis_client = RedisClient().get_client()

    mappings = get_session_mappings(redis_client, session_id)

    # Sort longest token first to avoid partial replacements
    for token in sorted(mappings.keys(), key=len, reverse=True):
        pseudonymized_text = pseudonymized_text.replace(
            token, mappings[token]
        )

    return pseudonymized_text


# Usage
ai_response = (
    "PATIENT_001 presented with chest pain on DATE_001. "
    "DOCTOR_001 prescribed rest."
)
restored = restore_text(ai_response, session_id="sess-7f3a-9b2c-4d1e-8a6f-0c5b3e2d1a0f")
print(restored)
# "John Smith presented with chest pain on 12/03/1990. Dr. Adams prescribed rest."
```

### Flow Diagram

```
AI Response (with tokens)
        │
        ▼
┌─────────────────────────┐
│  Load session mappings  │
│  from Redis             │
└───────────┬─────────────┘
            │
            ▼
┌─────────────────────────┐
│  Sort tokens longest    │
│  first                  │
└───────────┬─────────────┘
            │
            ▼
┌─────────────────────────┐
│  Replace each token     │
│  with original value    │
│                         │
│  PATIENT_001 → John Smith
│  DOCTOR_001  → Dr. Adams
│  DATE_001    → 12/03/1990
└───────────┬─────────────┘
            │
            ▼
Restored text returned to doctor
```

---

## 6. Edge Cases Handled

### 6.1 Same Person Mentioned Multiple Times → Same Token

```
Input:  "John Smith arrived. John Smith was examined. John Smith left."
Output: "PATIENT_001 arrived. PATIENT_001 was examined. PATIENT_001 left."
```

The vault maintains a **value → token cache** within each session. The first occurrence of `"John Smith"` assigns `PATIENT_001`; all subsequent occurrences reuse it. This ensures the AI treats them as one person.

### 6.2 Two Different Patients → Different Tokens

```
Input:  "John Smith and Sarah Johnson were seen today."
Output: "PATIENT_001 and PATIENT_002 were seen today."
```

Each unique value gets its own incrementing counter within the entity type.

### 6.3 Doctor Name vs. Disease Name (e.g., "Parkinson")

Clinical notes frequently mention disease names that resemble person names:

```
Input:  "Patient diagnosed with Parkinson's disease."
```

**Problem:** Naive NER might tag `Parkinson` as a `PERSON` entity.

**Solution (multi-layered):**

| Layer | Mechanism |
|-------|-----------|
| **Deny-list** | Known medical terms (`Parkinson`, `Alzheimer`, `Crohn`, `Hodgkin`, etc.) are excluded from PERSON detection |
| **Context rules** | Presidio context enhancer checks surrounding words — `"Parkinson's disease"` triggers a medical context, not a person context |
| **Confidence threshold** | Entities below 0.7 confidence are flagged for review, not auto-pseudonymized |
| **Possessive pattern** | `"Parkinson's disease"` matches a `{TERM}'s disease` pattern → classified as medical, not PERSON |

```
Correct output: "Patient diagnosed with Parkinson's disease."
                 (no pseudonymization — disease name preserved)
```

### 6.4 Overlapping Detections (Regex + NLP)

When both scanners detect the same span (e.g., a phone number found by regex and Presidio):

- Spans are merged; the **longer, higher-priority match** wins.
- Only **one token** is assigned — no double-replacement.

### 6.5 Token Collision Prevention

Token strings like `PATIENT_001` are designed to be **unlikely to appear in natural clinical text**. The `{TYPE}_{NUMBER}` format with uppercase prefixes avoids accidental matches during reverse mapping.

---

## 7. Privacy Guarantees

### Why This Approach Is HIPAA Compliant

| HIPAA Requirement | How Pseudonymization Satisfies It |
|-------------------|----------------------------------|
| **Minimum necessary** (§164.502(b)) | Only the de-identified text leaves the organization; real values stay in the vault |
| **Safe Harbor de-identification** (§164.514(b)(2)) | All 18 identifier types are detected and replaced before external transmission |
| **Limited retention** | Token mappings expire with session TTL — no long-term PHI storage |
| **Audit controls** (§164.312(b)) | Every pseudonymization event is logged (type + count, never values) |
| **Access controls** (§164.312(a)(1)) | Vault accessible only via authenticated API proxy; session-scoped isolation |

### Re-Identification Risk

**Re-identification** is the process of linking de-identified data back to a specific individual. Our risk mitigations:

| Risk Factor | Mitigation |
|-------------|-----------|
| Token mappings stored in Redis | Session-scoped, TTL-expired, password-protected |
| External AI provider stores pseudonymized text | Tokens carry no intrinsic meaning (`PATIENT_001` reveals nothing) |
| Combinations of quasi-identifiers (age + ZIP + gender) | Multiple identifier types removed simultaneously |
| AI provider logging | Only pseudonymized text is transmitted; provider cannot re-identify |
| Insider threat (Redis access) | Redis password, network isolation, no PHI in application logs |

**Residual risk:** If an attacker gains simultaneous access to both the pseudonymized AI transcript *and* the Redis vault within the TTL window, re-identification is theoretically possible. This is mitigated by network segmentation, TTL expiry, and access controls — reducing the attack window to near zero.

### Compliance Summary

```
┌─────────────────────────────────────────────────────────┐
│                  PRIVACY GUARANTEE                       │
│                                                         │
│  1. PHI never transmitted to external AI in raw form   │
│  2. Tokens are meaningless without vault access         │
│  3. Vault data auto-expires (no long-term PHI storage)  │
│  4. Audit trail exists without logging PHI values       │
│  5. Same person = same token (clinical coherence)     │
│  6. Different persons = different tokens (no confusion) │
│  7. Medical terms preserved (not falsely pseudonymized) │
└─────────────────────────────────────────────────────────┘
```

---

## Related Documentation

| Document | Description |
|----------|-------------|
| [architecture.md](./architecture.md) | Full system architecture and module breakdown |
| [redis_notes.md](./redis_notes.md) | Redis storage design and setup |
| [../README.md](../README.md) | Project overview and installation |

---

<p align="center"><em>Document maintained by the Infotact Solutions HealthTech Intern Team — Mantra, Tirth, Jash, Rohit</em></p>
