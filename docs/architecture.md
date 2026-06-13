# System Architecture

**Project:** HealthTech Automated PHI/PII Redaction Pipeline for LLMs  
**Organization:** Infotact Solutions  
**Document Version:** 1.0  
**Classification:** Internal — Compliance & Engineering Reference

---

## 1. System Overview

### 1.1 Purpose

The HealthTech PHI/PII Redaction Pipeline is a **privacy proxy** that sits between healthcare workers and external AI services (e.g., ChatGPT, Claude). Its sole purpose is to ensure that **no Protected Health Information (PHI) or Personally Identifiable Information (PII) ever leaves the organization's trust boundary** in identifiable form.

When a clinician submits a patient note for AI-assisted summarization, drafting, or analysis, the pipeline:

1. **Detects** all sensitive identifiers in the text.
2. **Pseudonymizes** real values with reversible tokens (e.g., `John Smith` → `PATIENT_001`).
3. **Forwards** only de-identified text to the external AI API.
4. **Receives** the AI response containing pseudonyms.
5. **Restores** original patient details via the token vault.
6. **Returns** a fully readable, clinically accurate report to the doctor.

### 1.2 Why This System Exists

| Regulatory Requirement | Business Need |
|------------------------|---------------|
| **HIPAA Privacy Rule** (45 CFR §164.502) prohibits disclosure of PHI to unauthorized third parties | Clinicians need AI tools for note drafting, differential diagnosis support, and patient education |
| **HIPAA Safe Harbor** (45 CFR §164.514(b)(2)) defines 18 identifier types that must be removed for de-identification | Manual redaction is slow, inconsistent, and error-prone at scale |
| **Breach Notification Rule** (45 CFR §164.400) imposes mandatory reporting and penalties for PHI leaks | Organizations need auditable, automated controls before adopting AI |

This system operationalizes Safe Harbor de-identification as an **automated, reversible, session-scoped proxy** — enabling AI adoption without sacrificing compliance.

### 1.3 Design Principles

- **Defense in depth:** Regex (deterministic) + NLP (contextual) scanners run in parallel.
- **Reversibility:** Pseudonymization preserves clinical coherence for the AI; restoration preserves readability for the clinician.
- **Minimal retention:** Token mappings expire with the session — PHI is not persisted beyond necessity.
- **Auditability:** Every request, detection, and external API call is logged (without logging PHI values).

---

## 2. Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        ORGANIZATION TRUST BOUNDARY                          │
│                                                                             │
│  ┌──────────┐    POST /redact-and-query                                     │
│  │          │    { "text": "Patient John Smith..." }                        │
│  │  Doctor  │──────────────────────────────────────────┐                    │
│  │ (Clinic) │                                          │                    │
│  └──────────┘                                          ▼                    │
│                                              ┌──────────────────┐           │
│                                              │  FastAPI Proxy   │           │
│                                              │  (api/main.py)   │           │
│                                              │                  │           │
│                                              │  • Auth / rate   │           │
│                                              │    limiting      │           │
│                                              │  • Session ID    │           │
│                                              │  • Audit logger  │           │
│                                              └────────┬─────────┘           │
│                                                       │                     │
│                         ┌─────────────────────────────┼─────────────────┐   │
│                         │         REDACTION ENGINE    │                 │   │
│                         │                             ▼                 │   │
│                         │              ┌──────────────────────────┐     │   │
│                         │              │   Parallel Detection     │     │   │
│                         │              └────────────┬─────────────┘     │   │
│                         │           ┌───────────────┴───────────────┐     │   │
│                         │           ▼                               ▼     │   │
│                         │  ┌─────────────────┐           ┌──────────────┐ │   │
│                         │  │  Regex Scanner  │           │ NLP Scanner  │ │   │
│                         │  │ (regex/)        │           │ (nlp/)       │ │   │
│                         │  │                 │           │              │ │   │
│                         │  │ • Phones        │           │ • Presidio   │ │   │
│                         │  │ • Emails        │           │ • spaCy NER  │ │   │
│                         │  │ • Dates, SSN    │           │ • Names      │ │   │
│                         │  │ • Aadhaar, MRN  │           │ • Locations  │ │   │
│                         │  │ • IPs, URLs     │           │ • Orgs       │ │   │
│                         │  └────────┬────────┘           └──────┬───────┘ │   │
│                         │           └───────────────┬───────────┘         │   │
│                         │                           ▼                     │   │
│                         │              ┌──────────────────────────┐       │   │
│                         │              │   Merged Entity List     │       │   │
│                         │              │   (deduplicated spans)   │       │   │
│                         │              └────────────┬─────────────┘       │   │
│                         │                           ▼                     │   │
│                         │              ┌──────────────────────────┐       │   │
│                         │              │     Token Vault          │       │   │
│                         │              │     (vault/ + Redis)     │       │   │
│                         │              │                          │       │   │
│                         │              │ John Smith → PATIENT_001 │       │   │
│                         │              │ 9876543210 → PHONE_001   │       │   │
│                         │              │ 12/03/1990 → DATE_001    │       │   │
│                         │              └────────────┬─────────────┘       │   │
│                         └───────────────────────────┼─────────────────────┘   │
│                                                     │                         │
│                                                     ▼                         │
│                              Clean (de-identified) text                       │
│                              "Patient PATIENT_001, DOB: DATE_001..."          │
│                                                     │                         │
└─────────────────────────────────────────────────────┼─────────────────────────┘
                                                      │
                                                      ▼
                                           ┌──────────────────┐
                                           │   External AI    │
                                           │  (ChatGPT API)   │
                                           └────────┬─────────┘
                                                    │
                              AI response with tokens
                              "PATIENT_001 should follow up..."
                                                    │
┌───────────────────────────────────────────────────┼─────────────────────────┐
│                        ORGANIZATION TRUST BOUNDARY│                         │
│                                                   ▼                         │
│                                        ┌──────────────────┐                 │
│                                        │  Token Vault     │                 │
│                                        │  Reverse Mapping │                 │
│                                        │  PATIENT_001     │                 │
│                                        │    → John Smith  │                 │
│                                        └────────┬─────────┘                 │
│                                                 │                           │
│                                                 ▼                           │
│                                        Restored clinical report             │
│                                        "John Smith should follow up..."     │
│                                                 │                           │
│  ┌──────────┐                                   │                           │
│  │  Doctor  │◀──────────────────────────────────┘                           │
│  └──────────┘                                                               │
│                                                                             │
│  Session ends → Vault TTL expires → All mappings destroyed                  │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Module Breakdown

### 3.1 Regex Module (`regex/`)

**Owner:** Mantra  
**Entry point:** `regex/regex_redact.py`

#### Role

The Regex Module provides **deterministic, rule-based PHI detection**. It catches structured identifiers that follow predictable formats — patterns that NLP models may miss or handle inconsistently.

#### Patterns Detected

| Category | Example Formats | Redaction Label |
|----------|----------------|-----------------|
| Indian phone numbers | `9876543210`, `+91-98765-43210` | `[PHONE_REDACTED]` / `PHONE_001` |
| US phone numbers | `(555) 123-4567`, `555-123-4567` | `[PHONE_REDACTED]` / `PHONE_001` |
| Email addresses | `user@domain.com` | `[EMAIL_REDACTED]` / `EMAIL_001` |
| Dates | `DD/MM/YYYY`, `MM-DD-YYYY`, `June 5 2026`, `YYYY-MM-DD` | `[DATE_REDACTED]` / `DATE_001` |
| SSN | `123-45-6789` | `[SSN_REDACTED]` |
| Aadhaar | `1234 5678 9012`, `123456789012` | `[AADHAAR_REDACTED]` |
| Medical Record Numbers | `MRN-00234` | `[MRN_REDACTED]` / `MRN_001` |
| IP addresses | `192.168.1.1` | `[IP_REDACTED]` |
| URLs | `www.hospital.com`, `https://...` | `[URL_REDACTED]` |
| Indian PIN codes | `400001` (6-digit) | `[PIN_REDACTED]` |
| US ZIP codes | `90210`, `90210-1234` | `[ZIP_REDACTED]` |

#### How It Works

```
Input text
    │
    ▼
For each compiled regex pattern:
    re.finditer() → collect (type, value, start, end)
    │
    ▼
Merge all findings → resolve overlapping spans
    (higher-priority / longer match wins)
    │
    ▼
Replace spans with redaction labels or pseudonym tokens
    │
    ▼
Return: { redacted_text, findings[], total_phi_found, summary }
```

**Key design decisions:**

- Uses only Python's built-in `re` module — zero external dependencies for this layer.
- Overlap resolution prevents double-redaction (e.g., a URL containing an IP address).
- Each pattern has a dedicated `detect_*()` and `redact_*()` function for testability.

---

### 3.2 NLP Module (`nlp/`)

**Owner:** Tirth  
**Entry point:** `nlp/presidio_scanner.py` (planned)

#### Role

The NLP Module handles **context-dependent entities** that regex cannot reliably detect — primarily **person names, geographic locations, and organization names** embedded in free-form clinical prose.

#### Technology Stack

| Component | Purpose |
|-----------|---------|
| **Microsoft Presidio Analyzer** | Orchestrates entity detection; provides confidence scores and entity typing |
| **spaCy `en_core_web_lg`** | Large English language model for Named Entity Recognition (NER) |
| **Presidio Anonymizer** | Applies replacement operators to detected spans |

#### Entities Detected

| Presidio Entity Type | Clinical Example | Token Assigned |
|---------------------|------------------|----------------|
| `PERSON` | "John Smith", "Dr. Emily Carter" | `PATIENT_001`, `DOCTOR_001` |
| `LOCATION` | "Mumbai", "42 MG Road" | `LOCATION_001` |
| `ORGANIZATION` | "Sunrise Hospital" | `ORG_001` |
| `DATE_TIME` | "last Tuesday", "three days ago" | `DATE_001` |
| `PHONE_NUMBER` | (fallback for regex misses) | `PHONE_001` |
| `EMAIL_ADDRESS` | (fallback for regex misses) | `EMAIL_001` |
| `NRP` (Nationality/Religion/Political) | Rare in clinical notes | Context-dependent |

#### How spaCy and Presidio Work Together

```
Clinical text: "Dr. Adams referred patient John Smith to Sunrise Hospital."
                              │
                              ▼
              ┌───────────────────────────────┐
              │   spaCy en_core_web_lg        │
              │   Tokenization + NER tagging  │
              │                               │
              │   "Dr. Adams"    → PERSON     │
              │   "John Smith"   → PERSON     │
              │   "Sunrise Hospital" → ORG    │
              └───────────────┬───────────────┘
                              │
                              ▼
              ┌───────────────────────────────┐
              │   Presidio AnalyzerEngine     │
              │                               │
              │   • Validates spaCy spans     │
              │   • Adds regex-based recog.   │
              │   • Assigns confidence scores │
              │   • Filters false positives   │
              │     (e.g. "Parkinson" ≠ PERSON)│
              └───────────────┬───────────────┘
                              │
                              ▼
              Entity list with (type, start, end, score)
                              │
                              ▼
              Forward to Token Vault for pseudonym assignment
```

**False-positive mitigation:** Clinical condition names (e.g., "Parkinson's disease") are excluded via a deny-list and context rules — they are medical terms, not person names.

---

### 3.3 Token Vault (`vault/`)

**Owner:** Jash  
**Entry point:** `vault/redis_client.py`, `vault/token_vault.py` (planned)

#### Role

The Token Vault is the **pseudonymization engine**. It replaces detected PHI with consistent, reversible tokens and stores the bidirectional mapping in Redis for the duration of the session.

#### Pseudonymization Flow

```
Detection:  "John Smith" (PERSON, offset 8–18)
                │
                ▼
Lookup:     Has "John Smith" been seen in this session?
                │
        ┌───────┴───────┐
        │ Yes           │ No
        ▼               ▼
   Return existing   Assign PATIENT_001
   token PATIENT_001 Store mapping in Redis
                │
                ▼
Replace in text: "Patient PATIENT_001, DOB: ..."
```

#### Redis Storage Model

| Key | Value | TTL |
|-----|-------|-----|
| `{session_id}:PERSON:PATIENT_001` | `John Smith` | Session duration (default: 30 min) |
| `{session_id}:PHONE:PHONE_001` | `9876543210` | Session duration |
| `{session_id}:DATE:DATE_001` | `12/03/1990` | Session duration |

#### Reverse Mapping

After the AI responds, the vault performs a **token → original value** substitution:

```python
# Pseudonymized AI response
"PATIENT_001 should schedule a follow-up on DATE_001."

# After reverse mapping
"John Smith should schedule a follow-up on 12/03/1990."
```

Reverse mapping iterates tokens **longest-first** to prevent partial replacements (e.g., `PATIENT_001` before `PATIENT_01`).

#### Session Lifecycle

```
Session created (UUID) → TTL set on all keys → AI query completes
    → Reverse mapping applied → Response returned → Session TTL expires
    → All Redis keys for session_id deleted automatically
```

---

### 3.4 FastAPI Proxy (`api/`)

**Owner:** Rohit  
**Entry point:** `api/main.py` (planned)

#### Role

The FastAPI Proxy is the **single entry point** for all clinician-to-AI interactions. It orchestrates the full pipeline and ensures no request bypasses de-identification.

#### Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/redact` | Detect and pseudonymize text; return clean text + session ID |
| `POST` | `/redact-and-query` | Full pipeline: redact → query AI → restore → return |
| `POST` | `/restore` | Reverse-map tokens in an AI response using session ID |
| `GET` | `/health` | Service health check (API + Redis connectivity) |
| `DELETE` | `/session/{session_id}` | Manually purge a session's vault data |

#### Request Interception Flow

```python
@app.post("/redact-and-query")
async def redact_and_query(request: RedactQueryRequest):
    session_id = str(uuid4())

    # 1. Parallel detection
    regex_findings = scan_and_redact(request.text)
    nlp_findings   = presidio_scan(request.text)

    # 2. Merge + pseudonymize via vault
    clean_text = vault.pseudonymize(
        text=request.text,
        findings=merge(regex_findings, nlp_findings),
        session_id=session_id,
    )

    # 3. Forward clean text to external AI
    ai_response = await external_ai_client.query(clean_text)

    # 4. Restore original values
    restored = vault.restore(ai_response, session_id=session_id)

    # 5. Audit log (no PHI values logged)
    audit.log(event="query_complete", session_id=session_id,
              phi_count=regex_findings.total + nlp_findings.total)

    return {"response": restored, "session_id": session_id}
```

#### Audit Logging

Every request generates a structured audit record:

```json
{
  "timestamp": "2026-06-13T10:30:00Z",
  "event": "query_complete",
  "session_id": "a1b2c3d4-...",
  "user_id": "dr.smith@hospital.org",
  "phi_entities_detected": 5,
  "phi_types": ["PERSON", "PHONE", "DATE"],
  "external_ai_provider": "openai",
  "latency_ms": 1240,
  "status": "success"
}
```

**Critical rule:** Audit logs record **counts and types only** — never original PHI values or token mappings.

---

## 4. Data Flow Example

### Input

```
Patient John Smith, DOB: 12/03/1990, Phone: 9876543210
```

### Stage-by-Stage Transformation

#### Stage 1 — FastAPI Proxy receives request

```
Session ID:  f47ac10b-58cc-4372-a567-0e02b2c3d479
Raw input:   "Patient John Smith, DOB: 12/03/1990, Phone: 9876543210"
```

#### Stage 2 — Regex Scanner

| Type | Value | Start | End |
|------|-------|-------|-----|
| `date` | `12/03/1990` | 28 | 38 |
| `phone` | `9876543210` | 47 | 57 |

#### Stage 3 — NLP Scanner (Presidio + spaCy)

| Type | Value | Start | End | Confidence |
|------|-------|-------|-----|------------|
| `PERSON` | `John Smith` | 8 | 18 | 0.95 |

#### Stage 4 — Token Vault assigns pseudonyms

| Original Value | Entity Type | Token Assigned |
|---------------|-------------|----------------|
| `John Smith` | PERSON | `PATIENT_001` |
| `12/03/1990` | DATE | `DATE_001` |
| `9876543210` | PHONE | `PHONE_001` |

**Redis entries created:**

```
SET f47ac10b:PERSON:PATIENT_001  "John Smith"   EX 1800
SET f47ac10b:DATE:DATE_001       "12/03/1990"   EX 1800
SET f47ac10b:PHONE:PHONE_001      "9876543210"   EX 1800
```

#### Stage 5 — Clean text sent to External AI

```
Patient PATIENT_001, DOB: DATE_001, Phone: PHONE_001
```

> **No PHI leaves the organization.** The external AI sees only pseudonyms.

#### Stage 6 — AI Response

```
PATIENT_001 is a 36-year-old patient. Recommend follow-up call at PHONE_001.
```

#### Stage 7 — Token Vault reverse mapping

```
PATIENT_001  →  John Smith
DATE_001     →  12/03/1990
PHONE_001    →  9876543210
```

#### Stage 8 — Final output returned to doctor

```
John Smith is a 36-year-old patient. Recommend follow-up call at 9876543210.
```

---

## 5. Security Design

### 5.1 Zero PHI Leakage Guarantees

| Control | Implementation |
|---------|---------------|
| **Network isolation** | External AI API calls originate only from the proxy server; clinicians never call AI APIs directly |
| **Pre-flight validation** | No text is forwarded until both scanners complete and vault assignment succeeds |
| **Token vault encryption** | Redis configured with `requirepass`; TLS enabled for Redis connections in production (`rediss://`) |
| **No PHI in logs** | Audit logger records entity *types* and *counts* only — never original values or token mappings |
| **Session-scoped storage** | Mappings keyed by UUID session ID; inaccessible across sessions |
| **Automatic expiry (TTL)** | All vault keys expire after session timeout (default 30 minutes); no manual cleanup required |
| **Deny-list for medical terms** | NLP module excludes disease names (Parkinson, Alzheimer, etc.) from PERSON detection |

### 5.2 Token Vault Security

```
Production Redis configuration:
  requirepass         → Strong random password via env var REDIS_PASSWORD
  bind 127.0.0.1      → Localhost only (proxy connects via private network)
  maxmemory-policy    → allkeys-lru (bounded memory)
  tls-port 6380       → Encrypted transport
```

### 5.3 Audit Logging

- Logs written to append-only storage (file or SIEM integration).
- Fields: timestamp, user ID, session ID, event type, PHI count by type, latency, status.
- **Never logged:** patient names, phone numbers, dates, token mappings, AI request/response bodies containing PHI.

### 5.4 Session-Based Vault Clearing

```
Session start  →  UUID generated, TTL = 1800s applied to all new keys
Session active →  Keys accessible for reverse mapping only within same session
Session end    →  TTL expires → Redis automatically deletes all session keys
Manual purge   →  DELETE /session/{id} → immediate key deletion
```

This ensures PHI mappings exist **only for the minimum time necessary** to complete a single AI interaction.

---

## 6. HIPAA Safe Harbor Alignment

The HIPAA Privacy Rule defines 18 identifier types that must be removed for Safe Harbor de-identification (45 CFR §164.514(b)(2)). The table below maps each identifier to the responsible module.

| # | HIPAA Identifier | Regex Module | NLP Module | Vault | Status |
|---|-----------------|:------------:|:----------:|:-----:|--------|
| 1 | Names | — | ✅ Presidio `PERSON` | ✅ | Implemented |
| 2 | Geographic subdivisions (smaller than state) | ✅ PIN/ZIP codes | ✅ `LOCATION` | ✅ | Implemented |
| 3 | Dates (except year) | ✅ Multiple formats | ✅ `DATE_TIME` | ✅ | Implemented |
| 4 | Telephone numbers | ✅ US + Indian | ✅ Fallback | ✅ | Implemented |
| 5 | Fax numbers | ✅ Phone pattern | — | ✅ | Planned |
| 6 | Email addresses | ✅ | ✅ Fallback | ✅ | Implemented |
| 7 | Social Security numbers | ✅ | — | ✅ | Implemented |
| 8 | Medical record numbers | ✅ `MRN-XXXXX` | — | ✅ | Implemented |
| 9 | Health plan beneficiary numbers | 🔜 Pattern TBD | — | ✅ | Planned |
| 10 | Account numbers | 🔜 Pattern TBD | — | ✅ | Planned |
| 11 | Certificate / license numbers | 🔜 | ✅ Context NER | ✅ | Planned |
| 12 | Vehicle identifiers | — | — | — | Out of scope |
| 13 | Device identifiers | — | — | — | Out of scope |
| 14 | Web URLs | ✅ | — | ✅ | Implemented |
| 15 | IP addresses | ✅ | — | ✅ | Implemented |
| 16 | Biometric identifiers | — | — | — | Out of scope |
| 17 | Full-face photographs | — | — | — | Out of scope |
| 18 | Any other unique identifying number | ✅ Aadhaar, custom | ✅ Context NER | ✅ | Implemented |

**Legend:** ✅ Implemented · 🔜 Planned (Week 2–3) · — Not applicable

---

## 7. Related Documentation

| Document | Description |
|----------|-------------|
| [redis_notes.md](./redis_notes.md) | Redis token vault implementation details |
| [token_mapping.md](./token_mapping.md) | Pseudonymization system and reverse mapping |
| [../README.md](../README.md) | Project overview, installation, and team |

---

<p align="center"><em>Document maintained by the Infotact Solutions HealthTech Intern Team — Mantra, Tirth, Jash, Rohit</em></p>
