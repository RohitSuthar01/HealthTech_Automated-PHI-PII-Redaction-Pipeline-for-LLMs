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
```bash
cd frontend
python -m http.server 8080
```
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

---

## 🛠️ Tech Stack

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
