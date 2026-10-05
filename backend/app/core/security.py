import os
import re
import time
import asyncio
from typing import Optional, Dict, List
from collections import defaultdict
from app.core.errors import FileSecurityException, RateLimitException, RequestTimeoutException
from app.core.logging import app_logger

MAX_FILE_SIZE_BYTES = 25 * 1024 * 1024  # 25 MB
ALLOWED_EXTENSIONS = {".csv", ".xlsx", ".xls"}

ALLOWED_MIME_TYPES = {
    ".csv": {
        "text/csv",
        "text/plain",
        "application/csv",
        "application/vnd.ms-excel",
        "text/x-csv",
        "application/octet-stream"
    },
    ".xlsx": {
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "application/octet-stream",
        "application/zip",
        "application/x-zip-compressed"
    },
    ".xls": {
        "application/vnd.ms-excel",
        "application/octet-stream",
        "application/x-msexcel"
    }
}

# Dangerous binary signatures to strictly block
DISALLOWED_MAGIC_SIGNATURES = [
    (b"MZ", "Windows Executable (PE/EXE/DLL)"),
    (b"\x7fELF", "Linux Executable (ELF)"),
    (b"\xca\xfe\xba\xbe", "Java Class / Mach-O Binary"),
    (b"\xfe\xed\xfa\xce", "Mach-O Binary"),
    (b"\xfe\xed\xfa\xcf", "Mach-O Binary"),
    (b"#!/", "Shell Script"),
    (b"<?php", "PHP Script"),
    (b"<script", "HTML / JS Script")
]

def is_safe_path(base_dir: str, path: str) -> bool:
    """Validate that path is strictly within base_dir to prevent path traversal."""
    try:
        base = os.path.abspath(base_dir)
        target = os.path.abspath(path)
        return os.path.commonpath([base, target]) == base
    except Exception:
        return False

def validate_dataset_id(dataset_id: Optional[str]) -> bool:
    """Validate dataset ID conforms to UUID or safe alphanumeric string."""
    if not dataset_id or not isinstance(dataset_id, str):
        return False
    return bool(re.match(r"^[a-zA-Z0-9_-]{1,100}$", dataset_id))

def sanitize_filename(filename: Optional[str]) -> str:
    """
    Sanitize filename to prevent directory traversal and filesystem attacks.
    - Strips all directory components
    - Removes null bytes
    - Normalizes character set to [a-zA-Z0-9_.-]
    - Caps maximum length to 100 chars
    """
    if not filename:
        return "dataset.csv"

    # Remove path traversal characters
    base = os.path.basename(filename.replace("\\", "/"))
    # Remove null bytes
    base = base.replace("\x00", "")
    
    # Strip dangerous characters
    safe_name = re.sub(r"[^a-zA-Z0-9_.-]", "_", base)
    
    # Strip leading dots to prevent hidden files
    safe_name = safe_name.lstrip(".")
    if not safe_name:
        safe_name = "dataset.csv"

    # Preserve extension so validator can inspect it
    root, ext = os.path.splitext(safe_name)
    if not ext:
        ext = ".csv"

    return f"{root[:80]}{ext.lower()}"

def validate_uploaded_file(raw_bytes: bytes, filename: str, content_type: Optional[str] = None):
    """
    Validate uploaded dataset security:
    1. Size limit (<= 25 MB)
    2. Non-empty (>= 1 byte)
    3. Allowed extension (.csv, .xlsx, .xls)
    4. Permitted MIME types
    5. Absence of malicious executable magic bytes
    6. Expected file structure
    """
    # 1. Non-empty check
    if not raw_bytes or len(raw_bytes) == 0:
        raise FileSecurityException(
            message="The uploaded dataset file is empty (0 bytes). Please upload a valid CSV or Excel file.",
            code="EMPTY_FILE",
            status_code=400
        )

    # 2. Maximum file size check
    if len(raw_bytes) > MAX_FILE_SIZE_BYTES:
        raise FileSecurityException(
            message=f"File size ({len(raw_bytes) / (1024 * 1024):.1f} MB) exceeds the maximum allowed limit of 25 MB.",
            code="PAYLOAD_TOO_LARGE",
            status_code=413
        )

    # 3. Extension check
    _, ext = os.path.splitext(filename.lower())
    if ext not in ALLOWED_EXTENSIONS:
        raise FileSecurityException(
            message=f"Unsupported format '{ext}'. InsightForge supports only CSV, XLSX, and XLS datasets.",
            code="UNSUPPORTED_FORMAT",
            status_code=400
        )

    # 4. MIME type check if supplied
    if content_type:
        clean_content_type = content_type.split(";")[0].strip().lower()
        allowed_mimes = ALLOWED_MIME_TYPES.get(ext, set())
        if allowed_mimes and clean_content_type not in allowed_mimes:
            app_logger.warning(f"File MIME type rejected: got '{clean_content_type}' for extension '{ext}'")
            raise FileSecurityException(
                message=f"MIME type '{clean_content_type}' is invalid for dataset format '{ext}'.",
                code="INVALID_MIME_TYPE",
                status_code=400
            )

    # 5. Magic signature inspection (reject executables / scripts masquerading as CSV)
    head_bytes = raw_bytes[:16]
    for sig, desc in DISALLOWED_MAGIC_SIGNATURES:
        if raw_bytes.startswith(sig) or head_bytes.startswith(sig):
            app_logger.error(f"Malicious file signature detected: {desc}")
            raise FileSecurityException(
                message=f"Upload rejected: Disallowed file signature ({desc}) detected.",
                code="DISALLOWED_FILE_SIGNATURE",
                status_code=400
            )

    # 6. Specific format header validation
    if ext == ".xlsx":
        # XLSX is an OpenXML ZIP container, must start with PK\x03\x04
        if not raw_bytes.startswith(b"PK\x03\x04"):
            raise FileSecurityException(
                message="Corrupted XLSX file: Missing valid OpenXML ZIP header.",
                code="CORRUPTED_FILE",
                status_code=422
            )
    elif ext == ".xls":
        # XLS is an OLE Compound Document, must start with \xd0\xcf\x11\xe0
        if not raw_bytes.startswith(b"\xd0\xcf\x11\xe0"):
            raise FileSecurityException(
                message="Corrupted XLS file: Missing valid OLE Compound Binary header.",
                code="CORRUPTED_FILE",
                status_code=422
            )
    elif ext == ".csv":
        # CSV text file should not contain null bytes in first 512 bytes
        sample = raw_bytes[:512]
        if b"\x00" in sample:
            raise FileSecurityException(
                message="Corrupted CSV file: Binary null bytes detected in text stream.",
                code="CORRUPTED_FILE",
                status_code=422
            )


# In-Memory Sliding Window Rate Limiter for Gemini Requests
class SlidingWindowRateLimiter:
    """
    Sliding window rate limiter to prevent abuse of LLM endpoints.
    Tracks timestamps of requests per client identifier within a 60-second window.
    """
    def __init__(self, requests_per_minute: int = 30):
        self.requests_per_minute = requests_per_minute
        self.client_records: Dict[str, List[float]] = defaultdict(list)
        self.lock = asyncio.Lock()

    async def acquire(self, client_id: str):
        now = time.time()
        window_start = now - 60.0

        async with self.lock:
            # Purge timestamps older than 60s
            timestamps = [t for t in self.client_records[client_id] if t > window_start]
            
            if len(timestamps) >= self.requests_per_minute:
                app_logger.warning(
                    f"Rate limit exceeded for client '{client_id}': {len(timestamps)} requests in 60s window (limit: {self.requests_per_minute})"
                )
                raise RateLimitException(
                    message=f"AI request rate limit exceeded ({self.requests_per_minute} req/min). Please wait a few seconds before trying again."
                )

            timestamps.append(now)
            self.client_records[client_id] = timestamps

gemini_rate_limiter = SlidingWindowRateLimiter(
    requests_per_minute=int(os.environ.get("GEMINI_RATE_LIMIT_PER_MINUTE", "30"))
)

async def execute_with_timeout(coro, timeout_seconds: float = 30.0, task_name: str = "Operation"):
    """Execute an async coroutine with a strict timeout boundary."""
    try:
        return await asyncio.wait_for(coro, timeout=timeout_seconds)
    except asyncio.TimeoutError:
        app_logger.warning(f"{task_name} timed out after {timeout_seconds} seconds.")
        raise RequestTimeoutException(
            message=f"{task_name} timed out after {timeout_seconds:.0f} seconds. Please try again with a simpler query."
        )
