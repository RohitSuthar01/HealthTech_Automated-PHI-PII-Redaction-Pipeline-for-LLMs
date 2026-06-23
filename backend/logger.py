import json
import logging
from datetime import datetime

class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        
        # Include extra attributes if they are present in the log record
        if hasattr(record, "session_id"):
            log_data["session_id"] = record.session_id
        if hasattr(record, "event_type"):
            log_data["event_type"] = record.event_type
        if hasattr(record, "latency_ms"):
            log_data["latency_ms"] = record.latency_ms
            
        # Include details on exceptions if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
            
        return json.dumps(log_data)

def setup_logging():
    # Setup root logger to output structured JSON to stdout
    root = logging.getLogger()
    
    # Remove existing handlers to avoid duplicate output formatting
    for handler in root.handlers[:]:
        root.removeHandler(handler)
        
    handler = logging.StreamHandler()
    handler.setFormatter(JsonFormatter())
    root.addHandler(handler)
    root.setLevel(logging.INFO)
    
    # Silence noisy dependencies while keeping core events
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("spacy").setLevel(logging.WARNING)
