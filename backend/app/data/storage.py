import os
import time
import tempfile
from typing import Dict, Any, Optional
import pandas as pd
from app.core.security import sanitize_filename, is_safe_path, validate_dataset_id
from app.core.errors import FileSecurityException
from app.core.logging import app_logger

# In-memory storage for active datasets during session
_DATASET_STORE: Dict[str, Dict[str, Any]] = {}
_TEMP_DIR = os.path.abspath(os.path.join(tempfile.gettempdir(), "insightforge_datasets"))
os.makedirs(_TEMP_DIR, exist_ok=True)

def save_dataset(
    dataset_id: str,
    df: pd.DataFrame,
    filename: str,
    raw_bytes: Optional[bytes] = None
) -> Dict[str, Any]:
    """Store dataset in memory and save a sanitized, path-traversal-proof temporary copy to disk."""
    if not validate_dataset_id(dataset_id):
        raise FileSecurityException("Invalid dataset identifier format.", code="INVALID_DATASET_ID", status_code=400)

    safe_name = sanitize_filename(filename)
    safe_file_id = f"{dataset_id}_{safe_name}"
    temp_path = os.path.abspath(os.path.join(_TEMP_DIR, safe_file_id))

    # Path Traversal Security Assertion: temp_path MUST reside inside _TEMP_DIR
    if not is_safe_path(_TEMP_DIR, temp_path):
        app_logger.error(f"Path traversal attempt detected with filename: {filename}")
        temp_path = os.path.join(_TEMP_DIR, f"{dataset_id}_sanitized.csv")

    try:
        if raw_bytes:
            with open(temp_path, "wb") as f:
                f.write(raw_bytes)
        else:
            df.to_pickle(temp_path + ".pkl")
    except Exception as e:
        app_logger.warning(f"Could not persist temporary file copy to disk: {e}")

    entry = {
        "dataset_id": dataset_id,
        "filename": safe_name,
        "df": df,
        "rows": int(len(df)),
        "columns": int(len(df.columns)),
        "column_names": [str(c) for c in df.columns],
        "dtypes": {str(k): str(v) for k, v in df.dtypes.items()},
        "file_path": temp_path,
        "created_at": time.time()
    }
    _DATASET_STORE[dataset_id] = entry
    app_logger.info(
        f"Dataset saved: {safe_name} ({entry['rows']} rows, {entry['columns']} cols)",
        extra={"extra_data": {"dataset_id": dataset_id, "filename": safe_name, "rows": entry['rows']}}
    )
    return entry

def get_dataset(dataset_id: str) -> Optional[Dict[str, Any]]:
    """Retrieve a stored dataset entry by its unique ID."""
    if not validate_dataset_id(dataset_id):
        return None
    return _DATASET_STORE.get(dataset_id)

def list_datasets() -> Dict[str, Dict[str, Any]]:
    """List all currently loaded datasets."""
    return _DATASET_STORE

def delete_dataset(dataset_id: str) -> bool:
    """Safely delete a stored dataset and remove its temporary file from disk."""
    if not validate_dataset_id(dataset_id):
        return False
    entry = _DATASET_STORE.pop(dataset_id, None)
    if not entry:
        return False

    temp_path = entry.get("file_path")
    if temp_path and os.path.exists(temp_path) and is_safe_path(_TEMP_DIR, temp_path):
        try:
            os.remove(temp_path)
            app_logger.info(f"Temporary file deleted: {temp_path}")
        except Exception as e:
            app_logger.warning(f"Failed to remove temporary file {temp_path}: {e}")

    app_logger.info(f"Dataset purged: {dataset_id}")
    return True

def cleanup_expired_datasets(max_age_seconds: int = 7200):
    """Purge datasets older than max_age_seconds (default 2 hours)."""
    now = time.time()
    expired_ids = [
        d_id for d_id, entry in _DATASET_STORE.items()
        if now - entry.get("created_at", now) > max_age_seconds
    ]
    for d_id in expired_ids:
        delete_dataset(d_id)
