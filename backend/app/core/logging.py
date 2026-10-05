import logging
import json
import re
from typing import Any, Dict

# Keys containing sensitive data that should never be logged
SENSITIVE_KEY_PATTERNS = [
    re.compile(r"api[-_]?key", re.IGNORECASE),
    re.compile(r"password", re.IGNORECASE),
    re.compile(r"secret", re.IGNORECASE),
    re.compile(r"token", re.IGNORECASE),
    re.compile(r"auth", re.IGNORECASE),
    re.compile(r"credential", re.IGNORECASE),
    re.compile(r"bearer", re.IGNORECASE),
    re.compile(r"private[-_]?key", re.IGNORECASE),
    re.compile(r"session[-_]?id", re.IGNORECASE),
    re.compile(r"cookie", re.IGNORECASE),
    re.compile(r"jwt", re.IGNORECASE),
]

API_KEY_REGEX = re.compile(r"(AIza[0-9A-Za-z_-]{35})")

def mask_sensitive_data(data: Any) -> Any:
    """Recursively mask sensitive values (API keys, secrets, tokens)."""
    if isinstance(data, dict):
        masked = {}
        for k, v in data.items():
            k_str = str(k)
            if any(p.search(k_str) for p in SENSITIVE_KEY_PATTERNS):
                masked[k] = "***REDACTED***"
            elif isinstance(v, (dict, list)):
                masked[k] = mask_sensitive_data(v)
            elif isinstance(v, str):
                val_masked = API_KEY_REGEX.sub("***REDACTED_API_KEY***", v)
                if len(v) > 60 and any(kw in k_str.lower() for kw in ["key", "auth", "token"]):
                    masked[k] = "***REDACTED***"
                else:
                    masked[k] = val_masked
            else:
                masked[k] = v
        return masked
    elif isinstance(data, list):
        return [mask_sensitive_data(item) for item in data]
    elif isinstance(data, str):
        return API_KEY_REGEX.sub("***REDACTED_API_KEY***", data)
    return data

class StructuredLogFormatter(logging.Formatter):
    """Formats log records as clear, structured messages with masked sensitive data."""
    def format(self, record: logging.LogRecord) -> str:
        timestamp = self.formatTime(record, "%Y-%m-%d %H:%M:%S")
        log_level = record.levelname.ljust(8)
        logger_name = record.name

        msg = record.getMessage()
        msg = API_KEY_REGEX.sub("***REDACTED_API_KEY***", msg)
        if hasattr(record, "extra_data") and record.extra_data:
            safe_extra = mask_sensitive_data(record.extra_data)
            msg += f" | context: {json.dumps(safe_extra)}"

        return f"[{timestamp}] [{log_level}] [{logger_name}] {msg}"

# Configure root logger for InsightForge
def setup_structured_logging():
    logger = logging.getLogger("insightforge")
    logger.setLevel(logging.INFO)

    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(StructuredLogFormatter())
        logger.addHandler(handler)

    return logger

app_logger = setup_structured_logging()
