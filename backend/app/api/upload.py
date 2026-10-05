import io
import os
import uuid
import pandas as pd
from fastapi import APIRouter, File, UploadFile, status
from pydantic import BaseModel
from app.data.storage import save_dataset
from app.core.security import validate_uploaded_file, sanitize_filename, MAX_FILE_SIZE_BYTES
from app.core.errors import FileSecurityException
from app.core.logging import app_logger

router = APIRouter(prefix="/api", tags=["Datasets"])

class UploadResponse(BaseModel):
    dataset_id: str
    filename: str
    rows: int
    columns: int

@router.post("/upload", response_model=UploadResponse, status_code=status.HTTP_200_OK)
async def upload_dataset(file: UploadFile = File(...)):
    """
    Securely upload, validate, and parse a dataset file (CSV, XLSX, XLS).
    Security checks:
    - Allowed extension only (.csv, .xlsx, .xls)
    - Max size 25 MB chunked validation
    - MIME type & binary magic byte inspection (blocking executables & shell scripts)
    - Safe filename sanitization (prevent path traversal)
    - Rejection of corrupted or empty files
    - Storage strictly in controlled temporary directory
    """
    original_filename = file.filename or "dataset.csv"
    safe_filename = sanitize_filename(original_filename)

    # 1. Read bytes chunk-by-chunk with size guard to prevent memory bombs
    chunk_size = 1024 * 1024  # 1 MB chunks
    raw_buffer = bytearray()
    
    try:
        while True:
            chunk = await file.read(chunk_size)
            if not chunk:
                break
            raw_buffer.extend(chunk)
            if len(raw_buffer) > MAX_FILE_SIZE_BYTES:
                raise FileSecurityException(
                    message=f"File exceeds the maximum permitted size of 25 MB.",
                    code="PAYLOAD_TOO_LARGE",
                    status_code=413
                )
    except FileSecurityException:
        raise
    except Exception as e:
        app_logger.error(f"Failed to read upload stream: {e}")
        raise FileSecurityException(
            message="Failed to read the uploaded file stream.",
            code="STREAM_READ_ERROR",
            status_code=400
        )

    raw_bytes = bytes(raw_buffer)

    # 2. Comprehensive security & signature validation
    validate_uploaded_file(raw_bytes, safe_filename, file.content_type)

    # 3. Load with Pandas securely
    _, ext = os.path.splitext(safe_filename.lower())
    try:
        if ext == ".csv":
            try:
                df = pd.read_csv(io.BytesIO(raw_bytes))
            except UnicodeDecodeError:
                try:
                    df = pd.read_csv(io.BytesIO(raw_bytes), encoding="utf-8-sig")
                except UnicodeDecodeError:
                    df = pd.read_csv(io.BytesIO(raw_bytes), encoding="latin1")
        elif ext in [".xlsx", ".xls"]:
            df = pd.read_excel(io.BytesIO(raw_bytes))
        else:
            raise FileSecurityException(
                message=f"Unsupported format '{ext}'. InsightForge supports CSV, XLSX, and XLS datasets.",
                code="UNSUPPORTED_FORMAT",
                status_code=400
            )
    except FileSecurityException:
        raise
    except pd.errors.EmptyDataError:
        raise FileSecurityException(
            message="The uploaded dataset is empty or contains no parseable columns.",
            code="EMPTY_FILE",
            status_code=400
        )
    except Exception as exc:
        app_logger.warning(f"File parsing failed for {safe_filename}: {exc}")
        raise FileSecurityException(
            message="Unable to parse dataset. The file appears to be corrupted, unreadable, or invalid.",
            code="CORRUPTED_FILE",
            status_code=422
        )

    # 4. Validate dataset is non-empty
    if df.empty or len(df.columns) == 0:
        raise FileSecurityException(
            message="The uploaded dataset contains no data rows or columns.",
            code="EMPTY_DATASET",
            status_code=400
        )

    dataset_id = str(uuid.uuid4())
    rows_count = int(len(df))
    cols_count = int(len(df.columns))

    # 5. Persist securely in controlled storage layer
    save_dataset(
        dataset_id=dataset_id,
        df=df,
        filename=safe_filename,
        raw_bytes=raw_bytes
    )

    app_logger.info(
        f"Upload successful: {safe_filename} (ID: {dataset_id}, {rows_count} rows, {cols_count} cols)",
        extra={"extra_data": {"dataset_id": dataset_id, "filename": safe_filename, "size_bytes": len(raw_bytes)}}
    )

    return UploadResponse(
        dataset_id=dataset_id,
        filename=safe_filename,
        rows=rows_count,
        columns=cols_count
    )

def find_sample_dataset_path() -> str:
    """
    Search multiple candidate locations for sample_data/sales.csv across
    local development, Render monorepo deployment, and Docker container environments.
    """
    current_dir = os.path.dirname(os.path.abspath(__file__))
    candidates = [
        # 1. Monorepo root / sample_data / sales.csv (4 levels up from app/api)
        os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(current_dir))), "sample_data", "sales.csv"),
        # 2. backend / sample_data / sales.csv (3 levels up from app/api)
        os.path.join(os.path.dirname(os.path.dirname(current_dir)), "sample_data", "sales.csv"),
        # 3. app / sample_data / sales.csv (2 levels up from app/api)
        os.path.join(os.path.dirname(current_dir), "sample_data", "sales.csv"),
        # 4. Working directory / sample_data / sales.csv
        os.path.join(os.getcwd(), "sample_data", "sales.csv"),
        # 5. Parent of working directory / sample_data / sales.csv
        os.path.join(os.path.dirname(os.getcwd()), "sample_data", "sales.csv"),
        # 6. Docker container WORKDIR /app/sample_data/sales.csv
        "/app/sample_data/sales.csv"
    ]

    for candidate in candidates:
        if candidate and os.path.isfile(candidate):
            return candidate

    return ""

@router.get("/sample", response_model=UploadResponse, status_code=status.HTTP_200_OK)
@router.get("/sample-data", response_model=UploadResponse, status_code=status.HTTP_200_OK)
async def load_sample_dataset():
    """
    Load the bundled sample_data/sales.csv dataset securely into session memory.
    """
    sample_path = find_sample_dataset_path()

    if not sample_path or not os.path.exists(sample_path):
        app_logger.error(f"Sample dataset 'sales.csv' could not be located in any candidate directory.")
        raise FileSecurityException(
            message="Sample dataset 'sales.csv' not found on server.",
            code="FILE_NOT_FOUND",
            status_code=404
        )

    with open(sample_path, "rb") as f:
        raw_bytes = f.read()


    try:
        df = pd.read_csv(io.BytesIO(raw_bytes))
    except Exception as exc:
        raise FileSecurityException(
            message="Unable to parse sample dataset.",
            code="CORRUPTED_FILE",
            status_code=422
        )

    dataset_id = str(uuid.uuid4())
    rows_count = int(len(df))
    cols_count = int(len(df.columns))

    save_dataset(
        dataset_id=dataset_id,
        df=df,
        filename="sales.csv",
        raw_bytes=raw_bytes
    )

    app_logger.info(f"Sample dataset loaded: sales.csv (ID: {dataset_id})")

    return UploadResponse(
        dataset_id=dataset_id,
        filename="sales.csv",
        rows=rows_count,
        columns=cols_count
    )
