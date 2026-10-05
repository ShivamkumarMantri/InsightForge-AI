from fastapi import APIRouter, Query, status
from typing import Optional
from app.data.storage import get_dataset, delete_dataset
from app.services.profiler import profile_dataset, get_preview_rows
from app.services.auto_insights import build_executive_dashboard
from app.core.errors import DatasetNotFoundException, InsightForgeAPIException
from app.core.logging import app_logger

router = APIRouter(prefix="/api/dataset", tags=["Dataset Intelligence"])

@router.get("/{dataset_id}/profile", status_code=status.HTTP_200_OK)
async def get_dataset_profile(dataset_id: str):
    """
    Generate automatic analytical profile for an uploaded dataset.
    Calculates rows, columns, missing values, duplicates, column types,
    and summary statistics (mean, median, min, max).
    """
    entry = get_dataset(dataset_id)
    if not entry:
        raise DatasetNotFoundException(dataset_id)

    df = entry["df"]
    filename = entry["filename"]

    try:
        profile_data = profile_dataset(df, filename, dataset_id)
        app_logger.info(
            f"Dataset profiled: {filename} (ID: {dataset_id})",
            extra={"extra_data": {"dataset_id": dataset_id, "rows": entry["rows"]}}
        )
        return profile_data
    except Exception as exc:
        app_logger.error(f"Error profiling dataset '{dataset_id}': {exc}", exc_info=True)
        raise InsightForgeAPIException(
            message=f"An error occurred while profiling the dataset.",
            code="PROFILING_ERROR",
            status_code=500
        )

@router.get("/{dataset_id}/preview", status_code=status.HTTP_200_OK)
async def get_dataset_preview(
    dataset_id: str,
    limit: int = Query(default=15, ge=1, le=100, description="Number of preview rows to fetch (1-100)")
):
    """
    Retrieve preview sample rows for horizontally scrollable data inspection table.
    """
    entry = get_dataset(dataset_id)
    if not entry:
        raise DatasetNotFoundException(dataset_id)

    df = entry["df"]
    filename = entry["filename"]

    try:
        columns_list = [str(c) for c in df.columns]
        rows_data = get_preview_rows(df, limit=limit)

        return {
            "dataset_id": dataset_id,
            "filename": filename,
            "columns": columns_list,
            "rows": rows_data,
            "total_rows": int(len(df)),
            "preview_count": len(rows_data)
        }
    except Exception as exc:
        app_logger.error(f"Error generating preview for '{dataset_id}': {exc}", exc_info=True)
        raise InsightForgeAPIException(
            message="An error occurred while generating data preview.",
            code="PREVIEW_ERROR",
            status_code=500
        )

@router.get("/{dataset_id}/dashboard", status_code=status.HTTP_200_OK)
async def get_dataset_dashboard(dataset_id: str):
    """
    Generate complete AI Auto Insights + Executive Dashboard for an uploaded dataset.
    Calculates executive KPIs (Revenue, Orders, AOV, Growth),
    charts (Revenue Trend, Top Products, Regional Performance),
    AI Discovered Insights (Trend, Performer, Driver, Anomaly, Quality),
    IQR Anomalies, Drivers, and Data Quality.
    """
    entry = get_dataset(dataset_id)
    if not entry:
        raise DatasetNotFoundException(dataset_id)

    df = entry["df"]
    filename = entry["filename"]

    try:
        dashboard_data = await build_executive_dashboard(df, filename, dataset_id)
        app_logger.info(f"Executive dashboard generated for {filename} (ID: {dataset_id})")
        return dashboard_data
    except Exception as exc:
        app_logger.error(f"Error building executive dashboard for '{dataset_id}': {exc}", exc_info=True)
        raise InsightForgeAPIException(
            message="An error occurred while synthesizing the executive dashboard.",
            code="DASHBOARD_ERROR",
            status_code=500
        )

@router.get("/{dataset_id}/auto-insights", status_code=status.HTTP_200_OK)
async def get_dataset_auto_insights(dataset_id: str):
    """Alias for /api/dataset/{dataset_id}/dashboard."""
    return await get_dataset_dashboard(dataset_id)

@router.delete("/{dataset_id}", status_code=status.HTTP_200_OK)
def remove_dataset(dataset_id: str):
    """
    Securely delete dataset from memory and remove temporary files from disk.
    Requirement 6: Delete temporary files when appropriate.
    """
    success = delete_dataset(dataset_id)
    if not success:
        raise DatasetNotFoundException(dataset_id)
    return {
        "success": True,
        "message": f"Dataset '{dataset_id}' and all associated temporary files were safely deleted.",
        "dataset_id": dataset_id
    }
