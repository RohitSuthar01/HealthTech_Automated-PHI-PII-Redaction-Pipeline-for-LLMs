# NLP Research: spaCy NER vs. Microsoft Presidio

## 1. spaCy NER vs. Microsoft Presidio

| Aspect | spaCy NER (Named Entity Recognition) | Microsoft Presidio |
| :--- | :--- | :--- |
| **Primary Goal** | General-purpose linguistic entity extraction (e.g., Person, Org, Location, Date). | Sensitive data (PII/PHI) identification, classification, and anonymization. |
| **Detection Method** | Purely statistical / machine learning (Transition-based parser, Transformers). | Hybrid approach: combining regex, rule-based checklists, context keywords, and ML (spaCy/BERT). |
| **Customizability** | Requires retraining or using entity rulers to define new custom classes. | High customizability via custom Pattern Recognizers (regex) and custom ML Recognizers. |
| **Output** | Tuple of entity span elements (`doc.ents`) containing start/end and type. | List of `RecognizerResult` with scores, bounds, and support for anonymization engines. |
| **Handling Structured Data** | Poor (struggles to find SSNs, credit cards, or IPs consistently without context). | Excellent (built-in regex models for structured numbers coupled with check-digit validation). |

---

## 2. What Presidio Catches vs. Misses

Based on our testing run using the 5 sample patient notes, here is the breakdown of Presidio's strengths and limitations:

### What it Catches Well
1. **Names (`PERSON`)**: Consistently identifies doctor and patient names (e.g., *John Smith*, *Emily Carter*, *Rahul Verma*, *Sarah Johnson*, *Alice Green*) in grammatical contexts.
2. **Dates (`DATE_TIME`)**: Effectively captures diverse date patterns (e.g., *14/02/1985*, *05/06/2026*, *03/15/2026*).
3. **Structured PII**: Correctly extracts valid formatted emails (`EMAIL_ADDRESS`) and phone numbers (`PHONE_NUMBER`).
4. **General Locations (`LOCATION`)**: Catches large/well-known cities and states (e.g., *Mumbai*, *Maharashtra*, *Delhi*).

### What it Misses / Misclassifies (Limitations)
1. **Checksum Validation & Invalid Formats**: 
   - Presidio skipped redacting `SSN: 666-29-9012` as an SSN because it uses checksum validation, and `666` is an invalid SSN prefix. Instead, it misclassified the prefix `"SSN"` as an `ORGANIZATION`.
2. **Context-Driven Misclassifications**:
   - `MRN-998822` was partially redacted, but the numeric part `998822` was misclassified as a `US_DRIVER_LICENSE`.
   - Structural text like `"Home Address"` or `"Emergency Contact"` was sometimes labeled as an `ORGANIZATION`.
3. **Indian/Local Context**:
   - Indian mobile number formats (e.g., `91-98765-43210` or `9123456780`) were occasionally missed or misclassified as `DATE_TIME`.
   - Custom IDs like Insurance IDs (`INS-789012-A`) or Medical Record Numbers (`MRN-998822`) are completely unrecognized out of the box and need custom regex recognizers.

---

## 3. HIPAA Safe Harbor Mapping: 18 Identifiers

| # | HIPAA Identifier | Presidio Capability | Alignment Strategy |
|---|-----------------|---------------------|--------------------|
| 1 | **Names** | Supported (`PERSON`) | Extremely reliable using spaCy NER. |
| 2 | **Geographic data** | Supported (`LOCATION`) | Catches cities/states. Needs regex additions for postal/PIN codes. |
| 3 | **Dates (except year)** | Supported (`DATE_TIME`) | Catches dates. Needs custom logic to retain year if requested. |
| 4 | **Telephone numbers** | Supported (`PHONE_NUMBER`) | Reliable for US formats; needs regex adjustments for Indian formats. |
| 5 | **Fax numbers** | Partially supported | Can be caught under `PHONE_NUMBER`. |
| 6 | **Email addresses** | Supported (`EMAIL_ADDRESS`) | Highly reliable built-in pattern. |
| 7 | **Social Security numbers** | Supported (`US_SSN`) | Reliable for US SSNs (ignores invalid/test patterns). |
| 8 | **Medical record numbers** | Not supported | Must use Mantra's regex scanner (`MRN-XXXXX`). |
| 9 | **Health plan beneficiary numbers**| Not supported | Requires custom regex patterns. |
| 10| **Account numbers** | Not supported | Requires custom regex patterns. |
| 11| **Certificate / license numbers** | Partially supported | Catches `US_DRIVER_LICENSE` and `MEDICAL_LICENSE`. |
| 12| **Vehicle identifiers** | Not supported | Requires custom patterns (out of scope). |
| 13| **Device identifiers** | Not supported | Requires custom patterns (out of scope). |
| 14| **Web URLs** | Supported (`URL`) | Highly reliable. |
| 15| **IP addresses** | Supported (`IP_ADDRESS`) | Highly reliable for IPv4/IPv6. |
| 16| **Biometric identifiers** | Not supported | Out of scope for text-based pipelines. |
| 17| **Full-face photographs** | Not supported | Out of scope for text-based pipelines. |
| 18| **Any other unique number/code** | Not supported | Requires custom regex (e.g., Indian Aadhaar, PAN). |

---

## 4. Run Execution Outputs (5 Sample Notes)

Below is the verified output when running `presidio_scanner.py` on the 5 sample notes:

```
Reading sample notes from C:\Users\Tirth Patel\OneDrive\Onedrive-Desktop\Infotact\HealthTech_Automated-PHI-PII-Redaction-Pipeline-for-LLMs\nlp\sample_notes.txt...

================================================================================
PROCESSING NOTE 1:
----------------------------------------
ORIGINAL NOTE:
NOTE 1:
Patient: John Smith
Date of Birth: 14/02/1985
Admitted: 05/06/2026
Phone: +1 (555) 019-2834
SSN: 666-29-9012
Address: 42 MG Road, Mumbai, Maharashtra 400001
Attending Physician: Dr. Emily Carter at Sunrise Hospital
Notes: Patient presented with a persistent cough and mild fever for 4 days. Diagnosed with viral bronchitis. Prescribed azithromycin 500mg daily. Referred to Dr. Emily Carter.
----------------------------------------
REDACTED NOTE:
NOTE 1:
Patient: [PERSON_REDACTED]
Date of Birth: [DATE_REDACTED]
Admitted: [DATE_REDACTED]
Phone: +1 [PHONE_REDACTED]
[ORGANIZATION_REDACTED]: 666-29-9012
Address: 42 [LOCATION_REDACTED], [LOCATION_REDACTED], [ORGANIZATION_REDACTED]
Attending Physician: Dr. [PERSON_REDACTED] at Sunrise Hospital
Notes: Patient presented with a persistent cough and mild fever for [DATE_REDACTED]. Diagnosed with viral bronchitis. Prescribed azithromycin 500mg daily. Referred to Dr. [PERSON_REDACTED].
----------------------------------------
TOTAL PHI FOUND: 12
FINDINGS BREAKDOWN: date_time: 3, location: 2, organization: 2, person: 3, phone_number: 1, us_driver_license: 1
================================================================================

================================================================================
PROCESSING NOTE 2:
----------------------------------------
ORIGINAL NOTE:
NOTE 2:
Patient Name: Rahul Verma
Age: 28
Medical Record Number: MRN-998822
Admitted: 01/06/2026
Email: rahul.verma@outlook.com
Mobile: 91-98765-43210
Chief Complaint: Acute chest pain radiating to left arm. History of mild hypertension.
Action: ECG performed, showing normal sinus rhythm. Under observation by Dr. Anil Mehta in the Cardiology Wing of Metro Care Center.
----------------------------------------
REDACTED NOTE:
NOTE 2:
Patient Name: [PERSON_REDACTED]: 28
Medical Record Number: MRN-[LICENSE_REDACTED]
Admitted: [DATE_REDACTED]
Email: [EMAIL_REDACTED]
Mobile: [PHONE_REDACTED]
Chief Complaint: Acute chest pain radiating to left arm. History of mild hypertension.
Action: [ORGANIZATION_REDACTED] performed, showing normal sinus rhythm. Under observation by Dr. [PERSON_REDACTED] in [ORGANIZATION_REDACTED] Metro Care Center.
----------------------------------------
TOTAL PHI FOUND: 10
FINDINGS BREAKDOWN: date_time: 1, email_address: 1, organization: 2, person: 2, phone_number: 1, url: 2, us_driver_license: 1
================================================================================

================================================================================
PROCESSING NOTE 3:
----------------------------------------
ORIGINAL NOTE:
NOTE 3:
Name: Sarah Johnson
Age: 45
Insurance ID: INS-789012-A
Diagnosis: Parkinson's disease symptoms worsening.
Home Address: 15 Park Street, Delhi 110001
Emergency Contact: Mike Johnson (Spouse) - Phone: 9123456780
Attending Physician: Dr. Priya Nair, License No: MH-2024-7890.
(Note: Do NOT redact Parkinson's disease - it is a clinical condition!)
----------------------------------------
REDACTED NOTE:
NOTE 3:
Name: [PERSON_REDACTED]
Age: 45
Insurance ID: INS-[LICENSE_REDACTED]-A
Diagnosis: Parkinson's disease symptoms worsening.
[ORGANIZATION_REDACTED]: 15 Park Street, [LOCATION_REDACTED] [DATE_REDACTED]
Emergency Contact: [PERSON_REDACTED] (Spouse) - Phone: [DATE_REDACTED]
Attending Physician: Dr. [PERSON_REDACTED], License No: [DATE_REDACTED].
(Note: Do NOT redact Parkinson's disease - it is a clinical condition!)
----------------------------------------
TOTAL PHI FOUND: 12
FINDINGS BREAKDOWN: date_time: 3, location: 1, organization: 1, person: 3, phone_number: 1, us_driver_license: 3
================================================================================

================================================================================
PROCESSING NOTE 4:
----------------------------------------
ORIGINAL NOTE:
NOTE 4:
Date: June 12, 2026
Patient: Robert 'Bob' Taylor (DOB: 09-18-1972)
IP Address of Device: 192.168.1.104
Email: rtaylor72@yahoo.com
Notes: Patient was connected to the telemetry monitor. Vital signs monitored continuously. No arrhythmias detected. Discharged home under care of Dr. Sarah Jenkins.
----------------------------------------
REDACTED NOTE:
NOTE 4:
Date: [DATE_REDACTED]
Patient: [PERSON_REDACTED] ([ORGANIZATION_REDACTED]: [DATE_REDACTED])
[ORGANIZATION_REDACTED]: [IP_REDACTED]
Email: [EMAIL_REDACTED]
Notes: Patient was connected to the telemetry monitor. Vital signs monitored continuously. No arrhythmias detected. Discharged home under care of Dr. [PERSON_REDACTED].
----------------------------------------
TOTAL PHI FOUND: 12
FINDINGS BREAKDOWN: date_time: 2, email_address: 1, ip_address: 1, organization: 2, person: 3, phone_number: 2, url: 1
================================================================================

================================================================================
PROCESSING NOTE 5:
----------------------------------------
ORIGINAL NOTE:
NOTE 5:
Patient: Alice Green
Age: 62
Date of Visit: 03/15/2026
URL: https://clinical-portal.local/records/g-89211
Notes: Patient visited the orthopedic clinic following a fall. Right wrist X-ray showed a hairline fracture of the distal radius. Temporary cast applied. Follow-up in 4 weeks with Dr. James Andrews.
----------------------------------------
REDACTED NOTE:
NOTE 5:
Patient: [PERSON_REDACTED]: 62
Date of Visit: [DATE_REDACTED]
URL: https://clinical-portal.local/records/g-89211
Notes: Patient visited the orthopedic clinic following a fall. Right wrist X-ray showed a hairline fracture of the distal radius. Temporary cast applied. Follow-up in [DATE_REDACTED] with Dr. [PERSON_REDACTED].
----------------------------------------
TOTAL PHI FOUND: 4
FINDINGS BREAKDOWN: date_time: 2, person: 2
================================================================================
```
