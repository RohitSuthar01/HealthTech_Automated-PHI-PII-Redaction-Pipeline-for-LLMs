"""
Regex-based PHI/PII detection and redaction for clinical text.

Primary entry point: :func:`regex.regex_redact.scan_and_redact`
"""

from regex_pipeline.regex_redact import REDACTION_LABELS, ScanResult, scan_and_redact

__all__ = ["REDACTION_LABELS", "ScanResult", "scan_and_redact"]