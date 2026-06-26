
# 🏥 HealthTech — Automated PHI/PII Redaction Pipeline for LLMs

<div align="center">

![Python](https://img.shields.io/badge/Python-3.13-blue?style=for-the-badge&logo=python)
![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)
![Status](https://img.shields.io/badge/Status-Active-brightgreen?style=for-the-badge)
![HIPAA](https://img.shields.io/badge/HIPAA-Safe%20Harbor-red?style=for-the-badge)
![Domain](https://img.shields.io/badge/Domain-Healthcare%20AI-blueviolet?style=for-the-badge)

> **A privacy-first proxy dashboard that lets healthcare professionals safely use external AI tools — without ever exposing patient data.**

</div>

---

## 🚨 The Problem

Healthcare workers want the power of AI assistants like ChatGPT to draft notes, summarize records, and answer clinical questions — but **sending a raw patient note to a third-party AI is a direct HIPAA violation.**

---

## ✅ The Solution — PHI Redaction Proxy

This frontend dashboard is the **visual interface** for the HealthTech PHI/PII Redaction Pipeline. It automatically:

- 🔍 Detects all protected patient information (PHI/PII)
- 🔄 Replaces real identities with reversible pseudonyms
- 🤖 Forwards only clean text to the external AI
- 🔓 Restores original patient details in the AI's response

---

## 🖥️ Dashboard Views

| View | Description |
|------|-------------|
| 📝 **New Note** | Submit a clinical note, run redaction, see token map, get AI response |
| 🔄 **Pipeline** | Visual 6-step flow diagram of the entire proxy pipeline |
| 🔒 **Vault Sessions** | Active token-map sessions stored in Redis (with TTL) |
| 📋 **Audit Log** | Every redaction and restoration event, for HIPAA compliance review |
| ⚙️ **Settings** | Configure PHI detection categories and vault behaviour |

---

## 🔄 How It Works — 6-Step Pipeline

```
┌─────────────────────────────────────────────────────────────────┐
│                    ORG CONTROL BOUNDARY                         │
│                                                                 │
│  1. Doctor submits note                                         │
│         ↓                                                       │
│  2. Redaction Engine  ──→  Regex rules + NLP entity detection   │
│         ↓                                                       │
│  3. Vault  ──→  stores  "Patient A" ↔ "Rahul Sharma"  (Redis)  │
│         ↓                                                       │
│  4. Clean text sent  ──────────────────────────────────────►   │  External AI
│                                                           ◄───  │  (GPT / Claude)
│  5. AI responds with pseudonyms only                            │
│         ↓                                                       │
│  6. Vault restores real identities  ──→  Doctor sees result     │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🕵️ PHI/PII Detection Categories

| Category | Example | Pattern Type |
|----------|---------|-------------|
| 👤 **Name** | `Rahul Sharma` → `Patient A` | NLP heuristic |
| 📅 **Date** | `14/03/1985` → `DATE_1` | Regex |
| 📞 **Phone** | `+91 98765 43210` → `PHONE_1` | Regex |
| 📧 **Email** | `rahul@gmail.com` → `EMAIL_1` | Regex |
| 🏥 **MRN** | `MRN: 4582193` → `MRN_1` | Regex |
| 🆔 **Aadhaar** | `1234 5678 9012` → `AADHAAR_1` | Regex |
| 🔢 **SSN** | `123-45-6789` → `SSN_1` | Regex |
| 🏠 **Address** | `22 MG Road, Jodhpur` → `ADDRESS_1` | Regex |

---

## 📁 File Structure

```
frontend/
├── 📄 index.html          # App shell — sidebar nav + 5 views
├── 📄 README.md           # This file
├── 📂 css/
│   └── 🎨 styles.css      # Full theme — clinical/technical design
└── 📂 js/
    ├── 🔍 redaction.js    # PHI detection rules + redact() / restore()
    └── ⚙️  app.js          # UI wiring, vault table, audit log, AI flow
```

---

## 🚀 Running Locally

### Option 1 — Just double-click (simplest)
Open `frontend/index.html` directly in Chrome or Edge. No server needed.

### Option 2 — VS Code Live Server
Right-click `index.html` in VS Code → **"Open with Live Server"**

### Option 3 — Python server
=======
# PHI Redaction Proxy — Frontend

A standalone HTML/CSS/JS dashboard demonstrating the HealthTech Automated PHI/PII Redaction Pipeline.

## Structure
```
frontend/
├── index.html        # App shell: sidebar nav + 5 views
├── css/
│   └── styles.css     # Theme + layout
└── js/
    ├── redaction.js   # Detection rules + redact()/restore() (mirrors backend redaction_engine.py)
    └── app.js          # UI wiring, vault table, audit log, simulated AI call
```

## Views
1. **New note** — paste a clinical note, run redaction, see the token map, simulate sending to an AI and getting a restored response.
2. **Pipeline** — visual walkthrough of the 6-step proxy flow.
3. **Vault sessions** — table of active token-map sessions (in-memory for this demo).
4. **Audit log** — running log of redaction/restore events.
5. **Settings** — detection categories and vault config (illustrative).

## Running locally
Just open `index.html` in a browser, or serve it:
>>>>>>> 3976790a400b747d59b109d17f2cb0b88ca48ecf
```bash
cd frontend
python -m http.server 8080
```
<<<<<<< HEAD
Then open → `http://localhost:8080`

---

## 🧪 Try It Out

Paste this sample note into the **New Note** view and click **Run Redaction**:

```
Patient Rahul Sharma, DOB 14/03/1985, MRN: 4582193, presented on
12/06/2026 with persistent cough and fever. Contact:
rahul.sharma@gmail.com, +91 98765 43210. Address: 22 MG Road, Jodhpur.
Dr. Anita Verma recommends a chest X-ray. Aadhaar 1234 5678 9012.
```

**Expected output:**
```
Patient A, DOB DATE_1, MRN: MRN_1, presented on DATE_2 with persistent
cough and fever. Contact: EMAIL_1, PHONE_1. Address: ADDRESS_1.
Patient B recommends a chest X-ray. Aadhaar AADHAAR_1.
```
=======
# 🏥 **HealthTech Automated PHI/PII Redaction Pipeline for LLMs**

![Python](https://img.shields.io/badge/Python-3.13-blue?logo=python&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green)
![Status](https://img.shields.io/badge/Status-Active-brightgreen)
![Domain](https://img.shields.io/badge/Domain-Healthcare%20AI-red)
![Compliance](https://img.shields.io/badge/HIPAA-Safe%20Harbor-purple)

> A privacy-first proxy pipeline that lets healthcare professionals safely use external AI tools — without ever exposing patient data.

---

## 📖 Overview

Healthcare workers want the power of AI assistants like ChatGPT to draft notes, summarize records, and answer clinical questions — but sending a raw patient note to a third-party AI is a direct HIPAA violation. **HealthTech Automated PHI/PII Redaction Pipeline for LLMs** solves this by acting as an intelligent privacy proxy. When a doctor submits a clinical note, the pipeline automatically detects and removes all protected patient information, replaces real identities with reversible pseudonyms, forwards only clean text to the external AI, and then restores the original patient details in the AI's response before returning it to the clinician. The doctor gets the full benefit of AI — with zero PHI ever leaving the organization's control boundary.

---

## 🎯 The Problem

| Challenge | Impact |
|-----------|--------|
| **HIPAA compliance** | Fines up to $1.5M per violation; criminal liability for willful neglect |
| **AI adoption blocked** | Clinicians avoid AI tools entirely out of fear of data leaks |
| **Manual redaction** | Doctors spend minutes scrubbing notes by hand — slow, error-prone, and unscalable |
| **Irreversible exposure** | Once PHI reaches an external LLM, it cannot be recalled or deleted |

This project bridges the gap between **healthcare compliance** and **AI productivity** — enabling safe, auditable, and reversible de-identification at the point of use.

---

## 🏗️ Architecture

```
┌──────────┐     ┌─────────────┐     ┌──────────────────────────────────┐
│          │     │             │     │       Redaction Engine           │
│  Doctor  │────▶│  API Proxy  │────▶│  ┌─────────┐    ┌─────────────┐  │
│          │     │  (FastAPI)  │     │  │  Regex  │ +  │ NLP/Presidio│  │
└──────────┘     └─────────────┘     │  └─────────┘    └─────────────┘  │
     ▲               │  Audit Log     │           │                      │
     │               │                │     ┌─────▼─────┐                │
     │               │                │     │   Vault   │ (Redis)      │
     │               │                │     │ Pseudonym │                │
     │               │                │     └─────┬─────┘                │
     │               ▼                └───────────┼──────────────────────┘
     │          Clean Text                        │
     │               │                            │
     │               ▼                            │
     │        ┌─────────────┐                       │
     │        │ External AI │  (ChatGPT / Claude)   │
     │        └─────────────┘                       │
     │               │                            │
     │          AI Response                       │
     │               │                            │
     └──────── Restore Names ◀───────────────────┘
              (de-pseudonymize via Vault)
```

**Flow in plain English:**

1. **Doctor** submits a patient note to the internal proxy API.
2. **Redaction Engine** runs regex rules + NLP entity detection in parallel to catch all PHI.
3. **Vault** stores a secure token map (`"Patient A"` ↔ `"Rahul Sharma"`) in Redis.
4. **Clean text** is sent to the external AI — no real names, dates, or identifiers.
5. **AI response** comes back referencing pseudonyms only.
6. **Vault restores** real patient names and the final result is returned to the doctor.
>>>>>>> 486e2b6ef1f085061da1a62be4d0086d126fd417

---

## 🛠️ Tech Stack

<<<<<<< HEAD
| Layer | Technology |
|-------|-----------|
| Structure | HTML5 |
| Styling | CSS3 (custom variables, no framework) |
| Logic | Vanilla JavaScript (ES6+) |
| Icons | Tabler Icons |
| Storage | In-memory (demo) / Redis (production) |
| AI Proxy | Simulated (swap `buildMockAIResponse()` for real API) |

---

## 👨‍💻 Author

**Rohit Suthar** — [@RohitSuthar01](https://github.com/RohitSuthar01)

Internship project — HealthTech Automated PHI/PII Redaction Pipeline for LLMs

---

<div align="center">
Made with ❤️ for HIPAA-compliant Healthcare AI
</div>
=======

## Notes
- `redaction.js` is a client-side mirror of `backend/redaction_engine.py`'s regex + name-detection rules, so the two stay structurally aligned if/when a real backend is wired in.
- The "Send to AI assistant" button currently simulates a response — swap `buildMockAIResponse()` in `app.js` for a real fetch to your proxy API.
>>>>>>> 3976790a400b747d59b109d17f2cb0b88ca48ecf
=======
| Layer | Technology | Purpose |
|-------|-----------|---------|
| 🐍 **Language** | Python 3.13 | Core pipeline logic |
| ⚡ **API** | FastAPI | High-performance async proxy service |
| 🧠 **NLP** | Microsoft Presidio + spaCy `en_core_web_lg` | Context-aware entity detection (names, locations, orgs) |
| 🔍 **Regex** | Python `re` (built-in) | Rule-based pattern matching (phones, SSN, Aadhaar, dates, IPs) |
| 🗄️ **Vault** | Redis | Secure, TTL-scoped pseudonym ↔ real-value token store |
| 🎭 **Data Gen** | Faker | Synthetic clinical notes for safe testing |
| ✅ **Testing** | pytest + fakeredis | Unit tests without a live Redis instance |

---

## 📁 Folder Structure

```
HealthTech_Automated-PHI-PII-Redaction-Pipeline-for-LLMs/
│
├── regex/                  # Rule-based regex PHI scanner          (Mantra)
│   ├── __init__.py         #   Package exports (scan_and_redact)
│   ├── regex_redact.py     #   Pattern detection + redaction engine
│   ├── note_loader.py      #   Load NOTE_001…NOTE_015 from sample_notes.txt
│   ├── batch_scan.py       #   Batch-scan all sample notes + report
│   ├── redirect.py         #   Optional Presidio comparison script
│   └── sample_notes.txt    #   15 synthetic clinical notes for testing
│
├── nlp/                    # NLP entity detection                  (Tirth)
│   └── presidio_scanner.py #   Presidio + spaCy NER pipeline
│
├── vault/                  # Pseudonymization + token store        (Jash)
│   └── redis_client.py     #   Redis connection + token vault
│
├── api/                    # FastAPI proxy service                 (Rohit)
│   └── main.py             #   Proxy endpoints + audit logging
│
├── docs/                   # Architecture & compliance docs
│   ├── architecture.md
│   └── hipaa_compliance.md
│
├── tests/                  # Unit tests for all modules
│   ├── test_regex.py
│   ├── test_nlp.py
│   ├── test_vault.py
│   └── test_api.py
│
├── sample_notes/           # Synthetic clinical notes (Faker-generated)
│
├── requirements.txt        # Python dependencies
└── README.md
```

---

## 🚀 Installation

### Prerequisites

- Python 3.13+
- Redis 7+ (local or Docker)
- Git

### 1. Clone the repository

```bash
git clone https://github.com/InfotactSolutions/HealthTech_Automated-PHI-PII-Redaction-Pipeline-for-LLMs.git
cd HealthTech_Automated-PHI-PII-Redaction-Pipeline-for-LLMs
```

### 2. Create and activate a virtual environment

```bash
python3.13 -m venv .venv
source .venv/bin/activate        # macOS / Linux
# .venv\Scripts\activate         # Windows
```

### 3. Install Python dependencies

```bash
pip install -r requirements.txt

# NLP stack (Presidio + spaCy)
pip install presidio-analyzer presidio-anonymizer spacy faker

# API layer
pip install fastapi uvicorn

# Download spaCy language model
python -m spacy download en_core_web_lg
```

### 4. Start Redis

**Option A — Docker (recommended):**

```bash
docker run -d --name phi-vault -p 6379:6379 redis:7-alpine
```

**Option B — macOS (Homebrew):**

```bash
brew install redis
brew services start redis
```

**Verify Redis is running:**

```bash
redis-cli ping
# Expected output: PONG
```

---

## ▶️ How to Run

### Run the regex redaction module (standalone)

The regex scanner works with zero external dependencies — great for a quick demo:

```bash
python regex/regex_redact.py
```

Batch-scan all 15 sample notes:

```bash
python regex/batch_scan.py
python regex/batch_scan.py --verbose
```

Expected output:

```
ORIGINAL TEXT: Patient Rahul Sharma, DOB: 14/02/1985, visited on 05/06/2026...
REDACTED TEXT: Patient Rahul Sharma, DOB: [DATE_REDACTED], visited on [DATE_REDACTED]...
TOTAL PHI FOUND: 11
FINDINGS BREAKDOWN: aadhaar: 1, date: 2, email: 1, ip: 1, mrn: 1, phone: 2, pin: 1, ssn: 1, url: 1
```

### Run the Presidio NLP prototype

```bash
python regex/redirect.py
```

### Start the full API proxy (when `api/` module is ready)

```bash
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
```

Then open **http://localhost:8000/docs** for the interactive Swagger UI.

**Example request:**

```bash
curl -X POST http://localhost:8000/redact \
  -H "Content-Type: application/json" \
  -d '{"text": "Patient John Smith, DOB: 14/02/1985. Phone: 9876543210."}'
```

---

## 🧪 Running Tests

```bash
# Run all tests
pytest tests/ -v

# Run with coverage report
pytest tests/ --cov=. --cov-report=term-missing

# Run a specific module's tests
pytest tests/test_regex.py -v
```

> Tests use `fakeredis` so no live Redis instance is required during CI.

---

## 👥 Team

| Name | Role | Module | Responsibility |
|------|------|--------|----------------|
| **Mantra** 👑 | Team Lead | `regex/` | Regex-based PHI pattern scanner & redactor |
| **Tirth** | Intern | `nlp/` | Presidio + spaCy NLP entity detection pipeline |
| **Jash** | Intern | `vault/` | Pseudonymization engine & Redis token vault |
| **Rohit** | Intern | `api/` | FastAPI proxy service & audit logging |

**Organization:** [Infotact Solutions](https://github.com/InfotactSolutions)  
**Duration:** 30-day internship · Cybersecurity + Healthcare AI

---

## 🔒 HIPAA Safe Harbor Compliance

Under the [HIPAA Privacy Rule](https://www.hhs.gov/hipaa/for-professionals/privacy/special-topics/de-identification/index.html), Safe Harbor de-identification requires removal of **18 identifier types**. This pipeline addresses them as follows:

| # | HIPAA Identifier | Handled By | Status |
|---|-----------------|-----------|--------|
| 1 | Names | NLP (Presidio + spaCy NER) | ✅ |
| 2 | Geographic data (below state level) | NLP + Regex (PIN/ZIP codes) | ✅ |
| 3 | Dates (except year) | Regex (multiple date formats) | ✅ |
| 4 | Telephone numbers | Regex (US + Indian formats) | ✅ |
| 5 | Fax numbers | Regex (phone pattern extension) | 🔜 |
| 6 | Email addresses | Regex | ✅ |
| 7 | Social Security numbers | Regex | ✅ |
| 8 | Medical record numbers | Regex (`MRN-XXXXX`) | ✅ |
| 9 | Health plan beneficiary numbers | Regex (planned pattern) | 🔜 |
| 10 | Account numbers | Regex (planned pattern) | 🔜 |
| 11 | Certificate / license numbers | NLP + Regex | 🔜 |
| 12 | Vehicle identifiers | — | ⬜ |
| 13 | Device identifiers | — | ⬜ |
| 14 | Web URLs | Regex | ✅ |
| 15 | IP addresses | Regex | ✅ |
| 16 | Biometric identifiers | — | ⬜ |
| 17 | Full-face photographs | — | ⬜ |
| 18 | Any other unique identifying number | Regex (Aadhaar, custom IDs) | ✅ |

> ✅ Implemented & tested · 🔜 Planned (Week 2–3) · ⬜ Out of scope (requires image/biometric modules)

---

## 🔮 Future Improvements

- [ ] **Multi-language support** — Hindi and regional language clinical notes (common in Indian healthcare)
- [ ] **Confidence scoring** — Flag low-confidence detections for human review before AI forwarding
- [ ] **Admin dashboard** — Real-time audit log viewer for compliance officers
- [ ] **FHIR integration** — Accept structured HL7 FHIR resources, not just free-text notes
- [ ] **On-premise LLM mode** — Route to a local model (Ollama / Llama) with zero external data transfer
- [ ] **Differential privacy layer** — Add statistical noise for research-use de-identification
- [ ] **PDF & image OCR** — Extend pipeline to scanned documents and handwritten notes
- [ ] **Role-based access control** — Per-clinician audit trails and permission tiers
- [ ] **Automated compliance reports** — Generate HIPAA audit PDFs on demand

---

## 📄 License

This project is licensed under the **MIT License** — free to use, modify, and distribute with attribution.

```
MIT License

Copyright (c) 2026 Infotact Solutions — HealthTech Intern Team
(Mantra, Tirth, Jash, Rohit)

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

---

<p align="center">
  Built with ❤️ by the Infotact Solutions HealthTech Intern Team<br>
  <em>Making AI safe for healthcare, one redaction at a time.</em>
</p>
>>>>>>> 486e2b6ef1f085061da1a62be4d0086d126fd417
