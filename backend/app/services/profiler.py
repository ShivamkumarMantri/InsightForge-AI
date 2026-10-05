import math
import numpy as np
import pandas as pd
from typing import Dict, Any, List, Optional

def detect_column_type(series: pd.Series, col_name: str) -> str:
    """
    Detect the semantic type of a column:
    'numeric', 'datetime', 'boolean', or 'categorical'.
    """
    # 1. Check boolean
    if pd.api.types.is_bool_dtype(series):
        return "boolean"

    # 2. Check numeric
    if pd.api.types.is_numeric_dtype(series):
        return "numeric"

    # 3. Check datetime
    if pd.api.types.is_datetime64_any_dtype(series):
        return "datetime"

    # If object or string, check if it's a date
    col_name_lower = col_name.lower()
    is_date_name = any(kw in col_name_lower for kw in ["date", "time", "timestamp", "year", "month", "day", "created", "updated"])
    
    non_null_samples = series.dropna().astype(str).head(30)
    if len(non_null_samples) > 0:
        # Don't classify pure numeric strings as datetime (e.g. '1234')
        if not all(s.strip().isdigit() for s in non_null_samples):
            try:
                # Attempt parsing non-null sample
                parsed = pd.to_datetime(non_null_samples, errors='coerce', format='mixed')
                valid_ratio = parsed.notna().sum() / len(non_null_samples)
                if valid_ratio >= 0.8:
                    return "datetime"
            except Exception:
                pass

    return "categorical"

def clean_stat_val(val: Any) -> Optional[float]:
    """Ensure float values are JSON serializable (handling NaN, inf, -inf)."""
    if val is None or pd.isna(val) or math.isnan(val) or math.isinf(val):
        return None
    return round(float(val), 2)

def generate_ai_context(df: pd.DataFrame, filename: str) -> Dict[str, Any]:
    """
    Produce a compact, high-density structured dataset schema for Gemini LLM.
    Does NOT contain full dataset rows to remain lightweight and token-efficient.
    """
    rows = int(len(df))
    columns = int(len(df.columns))

    numeric_cols = []
    categorical_cols = []
    date_cols = []
    columns_info = []
    missing_dict = {}

    for col in df.columns:
        col_str = str(col)
        series = df[col]
        col_type = detect_column_type(series, col_str)
        missing_count = int(series.isna().sum())
        missing_dict[col_str] = missing_count

        info_entry: Dict[str, Any] = {
            "name": col_str,
            "type": col_type,
            "pandas_dtype": str(series.dtype),
            "unique_values": int(series.nunique(dropna=True)),
            "missing_count": missing_count
        }

        if col_type == "numeric":
            numeric_cols.append(col_str)
            clean_series = pd.to_numeric(series, errors='coerce').dropna()
            if len(clean_series) > 0:
                info_entry["min"] = clean_stat_val(clean_series.min())
                info_entry["max"] = clean_stat_val(clean_series.max())
                info_entry["mean"] = clean_stat_val(clean_series.mean())
                info_entry["median"] = clean_stat_val(clean_series.median())
        elif col_type == "datetime":
            date_cols.append(col_str)
            try:
                dt_series = pd.to_datetime(series, errors='coerce').dropna()
                if len(dt_series) > 0:
                    info_entry["min_date"] = str(dt_series.min())
                    info_entry["max_date"] = str(dt_series.max())
            except Exception:
                pass
        else:
            categorical_cols.append(col_str)
            # Top categories for AI context
            top_vals = series.dropna().value_counts().head(5).index.tolist()
            info_entry["top_categories"] = [str(v) for v in top_vals]

        columns_info.append(info_entry)

    return {
        "dataset": filename,
        "rows": rows,
        "columns": columns,
        "columns_info": columns_info,
        "numeric_columns": numeric_cols,
        "categorical_columns": categorical_cols,
        "date_columns": date_cols,
        "missing_values": missing_dict
    }

def profile_dataset(df: pd.DataFrame, filename: str, dataset_id: str) -> Dict[str, Any]:
    """
    Comprehensive profiling of a dataset for the InsightForge AI platform.
    """
    total_rows = int(len(df))
    total_columns = int(len(df.columns))

    if total_rows == 0 or total_columns == 0:
        return {
            "dataset_id": dataset_id,
            "filename": filename,
            "overview": {
                "total_rows": 0,
                "total_columns": 0,
                "missing_values": 0,
                "duplicate_rows": 0,
                "numeric_columns_count": 0,
                "categorical_columns_count": 0,
                "date_columns_count": 0
            },
            "columns": [],
            "column_types_summary": {
                "numeric": [],
                "categorical": [],
                "datetime": []
            },
            "ai_context": generate_ai_context(df, filename)
        }

    # Count duplicates and total missing
    duplicate_rows = int(df.duplicated().sum()) if total_rows > 0 else 0
    total_missing = int(df.isna().sum().sum())

    numeric_cols_list = []
    categorical_cols_list = []
    date_cols_list = []
    columns_detail = []

    for col in df.columns:
        col_name = str(col)
        series = df[col]
        col_type = detect_column_type(series, col_name)

        if col_type == "numeric":
            numeric_cols_list.append(col_name)
        elif col_type == "datetime":
            date_cols_list.append(col_name)
        else:
            categorical_cols_list.append(col_name)

        missing_count = int(series.isna().sum())
        missing_pct = round((missing_count / total_rows) * 100, 1) if total_rows > 0 else 0.0
        unique_cnt = int(series.nunique(dropna=True))

        # Distinct example values (up to 4)
        non_null_unique = series.dropna().unique()
        examples = []
        for val in non_null_unique[:4]:
            if isinstance(val, (float, np.floating)):
                examples.append(f"{val:,.2f}" if not math.isnan(val) else "NaN")
            else:
                examples.append(str(val))

        stats = None
        if col_type == "numeric":
            clean_num = pd.to_numeric(series, errors='coerce').dropna()
            if len(clean_num) > 0:
                stats = {
                    "mean": clean_stat_val(clean_num.mean()),
                    "median": clean_stat_val(clean_num.median()),
                    "min": clean_stat_val(clean_num.min()),
                    "max": clean_stat_val(clean_num.max()),
                    "std": clean_stat_val(clean_num.std())
                }

        columns_detail.append({
            "name": col_name,
            "data_type": col_type,
            "pandas_dtype": str(series.dtype),
            "unique_values": unique_cnt,
            "missing_count": missing_count,
            "missing_percentage": missing_pct,
            "examples": examples,
            "stats": stats
        })

    overview = {
        "total_rows": total_rows,
        "total_columns": total_columns,
        "missing_values": total_missing,
        "duplicate_rows": duplicate_rows,
        "numeric_columns_count": len(numeric_cols_list),
        "categorical_columns_count": len(categorical_cols_list),
        "date_columns_count": len(date_cols_list)
    }

    column_types_summary = {
        "numeric": numeric_cols_list,
        "categorical": categorical_cols_list,
        "datetime": date_cols_list
    }

    ai_ctx = generate_ai_context(df, filename)

    return {
        "dataset_id": dataset_id,
        "filename": filename,
        "rows": total_rows,
        "overview": overview,
        "columns": columns_detail,
        "column_types_summary": column_types_summary,
        "ai_context": ai_ctx
    }

def get_preview_rows(df: pd.DataFrame, limit: int = 15) -> List[Dict[str, Any]]:
    """
    Return clean, JSON-serializable preview rows for the data table.
    Safely converts NaN, inf, NaT and timestamps.
    """
    capped_limit = min(max(1, limit), 50)
    sample_df = df.head(capped_limit)

    records = []
    for _, row in sample_df.iterrows():
        clean_row = {}
        for col, val in row.items():
            col_str = str(col)
            if pd.isna(val) or val is None:
                clean_row[col_str] = "-"
            elif isinstance(val, (float, np.floating)):
                clean_row[col_str] = round(float(val), 2)
            elif isinstance(val, (int, np.integer)):
                clean_row[col_str] = int(val)
            elif isinstance(val, pd.Timestamp):
                clean_row[col_str] = val.strftime("%Y-%m-%d")
            else:
                clean_row[col_str] = str(val)
        records.append(clean_row)

    return records
