import json
import logging
import time
from typing import Any, Dict
from ..security.redaction import SecretRedactor

class JsonFormatter(logging.Formatter):
    """
    Structured JSON log formatter with automatic secret redaction.
    """
    def format(self, record: logging.LogRecord) -> str:
        msg = record.getMessage()
        redacted_msg = SecretRedactor.redact_text(msg)
        
        log_obj = {
            "timestamp": time.time(),
            "level": record.levelname,
            "logger": record.name,
            "message": redacted_msg
        }
        if hasattr(record, "task_id"):
            log_obj["task_id"] = getattr(record, "task_id")
        if hasattr(record, "user_id"):
            log_obj["user_id"] = getattr(record, "user_id")
        if hasattr(record, "channel_id"):
            log_obj["channel_id"] = getattr(record, "channel_id")
        if hasattr(record, "model"):
            log_obj["model"] = getattr(record, "model")
        if hasattr(record, "latency_ms"):
            log_obj["latency_ms"] = getattr(record, "latency_ms")

        return json.dumps(log_obj)

def get_logger(name: str = "coding_agent") -> logging.Logger:
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(JsonFormatter())
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    return logger
