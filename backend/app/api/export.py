import io
import csv
import json
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Query, Response, status
from fastapi.responses import StreamingResponse, JSONResponse
from app.data.storage import get_dataset
from app.services.auto_insights import build_executive_dashboard
from app.services.pdf_report_generator import generate_pdf_report_bytes
from app.core.errors import DatasetNotFoundException, InsightForgeAPIException
from app.core.logging import app_logger

router = APIRouter(prefix="/api/dataset", tags=["Export & AI Reports"])

@router.get("/{dataset_id}/export/pdf", status_code=status.HTTP_200_OK)
async def export_dataset_pdf(dataset_id: str):
    """
    Generate and stream an executive AI-powered PDF report containing verified calculations:
    - Dataset overview & scope
    - Key Performance Indicators (Total Revenue, Orders, AOV, Growth Rate)
    - Top 5 Products with revenue & market share
    - Regional Performance distribution
    - Temporal Trends & Pareto driver
    - AI Discovered Insights (Trend, Performer, Driver, Anomaly, Quality)
    - Statistical Anomalies (IQR outlier audit & sample records)
    - Data Quality Scorecard & Schema Hygiene
    """
    entry = get_dataset(dataset_id)
    if not entry:
        raise DatasetNotFoundException(dataset_id)

    df = entry["df"]
    filename = entry["filename"]

    try:
        dashboard_data = await build_executive_dashboard(df, filename, dataset_id)
        pdf_bytes = generate_pdf_report_bytes(dashboard_data)

        safe_filename = filename.replace(" ", "_").replace(".csv", "").replace(".xlsx", "")
        export_name = f"InsightForge_Report_{safe_filename}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"

        app_logger.info(f"Generated PDF report for dataset '{filename}' ({len(pdf_bytes)} bytes)")

        return StreamingResponse(
            io.BytesIO(pdf_bytes),
            media_type="application/pdf",
            headers={
                "Content-Disposition": f'attachment; filename="{export_name}"',
                "Access-Control-Expose-Headers": "Content-Disposition"
            }
        )
    except Exception as exc:
        app_logger.error(f"Error generating PDF report for '{dataset_id}': {exc}", exc_info=True)
        raise InsightForgeAPIException(
            message="An error occurred while generating the executive PDF report.",
            code="PDF_GENERATION_ERROR",
            status_code=500
        )

@router.get("/{dataset_id}/export/summary", status_code=status.HTTP_200_OK)
async def export_dashboard_summary(dataset_id: str, format: str = Query(default="json", enum=["json", "text"])):
    """
    Export the comprehensive executive dashboard summary.
    """
    entry = get_dataset(dataset_id)
    if not entry:
        raise DatasetNotFoundException(dataset_id)

    df = entry["df"]
    filename = entry["filename"]

    try:
        dashboard_data = await build_executive_dashboard(df, filename, dataset_id)

        if format == "text":
            kpis = dashboard_data["kpis"]
            ai_discovered = dashboard_data.get("ai_discovered", [])
            anomalies = dashboard_data.get("anomalies", {})
            quality = dashboard_data.get("data_quality", {})

            lines = [
                f"=== INSIGHTFORGE AI EXECUTIVE SUMMARY: {filename} ===",
                f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                "",
                "--- KEY PERFORMANCE INDICATORS ---",
                f"Total Revenue: {kpis['total_revenue']['formatted']}",
                f"Total Orders: {kpis['total_orders']['formatted']}",
                f"Average Order Value: {kpis['average_order_value']['formatted']}",
                f"Growth Rate: {kpis['growth_rate']['formatted']} ({kpis['growth_rate']['trend']})",
                "",
                "--- AI DISCOVERED INSIGHTS ---"
            ]
            for item in ai_discovered:
                lines.append(f"[{item.get('badge', 'INSIGHT')}] {item.get('title')}: {item.get('statement')}")
                if item.get("detail"):
                    lines.append(f"   Context: {item.get('detail')}")

            lines.extend([
                "",
                "--- STATISTICAL ANOMALIES (IQR) ---",
                f"Outlier Count: {anomalies.get('outlier_count', 0)} ({anomalies.get('outlier_pct', 0)}%)",
                f"Upper Bound: ${anomalies.get('upper_bound', 0):,}",
                f"Max Outlier: ${anomalies.get('max_outlier', 0):,}" if anomalies.get('max_outlier') else "Max Outlier: None",
                "",
                "--- DATA QUALITY AUDIT ---",
                f"Quality Score: {quality.get('score', 100)}/100 ({quality.get('status', 'Optimal')})",
                f"Duplicate Rows: {quality.get('duplicate_rows', 0)}",
                f"Missing Cells: {quality.get('missing_cells', 0)} ({quality.get('missing_pct', 0)}%)",
                f"Records Ingested: {quality.get('total_rows', 0):,} rows across {quality.get('total_columns', 0)} columns"
            ])

            text_content = "\n".join(lines)
            safe_name = filename.replace(" ", "_").replace(".csv", "").replace(".xlsx", "")
            return Response(
                content=text_content,
                media_type="text/plain",
                headers={
                    "Content-Disposition": f'attachment; filename="InsightForge_Summary_{safe_name}.txt"'
                }
            )

        return {
            "success": True,
            "export_timestamp": datetime.now().isoformat(),
            "summary": dashboard_data
        }
    except Exception as exc:
        app_logger.error(f"Error exporting dashboard summary for '{dataset_id}': {exc}", exc_info=True)
        raise InsightForgeAPIException(
            message="An error occurred while exporting the executive dashboard summary.",
            code="SUMMARY_EXPORT_ERROR",
            status_code=500
        )

@router.get("/{dataset_id}/export/csv", status_code=status.HTTP_200_OK)
async def export_dashboard_table_csv(
    dataset_id: str,
    table: str = Query(default="top_products", enum=["top_products", "regional", "trend", "anomalies", "kpis"])
):
    """
    Download specific dashboard table as verified CSV data.
    """
    entry = get_dataset(dataset_id)
    if not entry:
        raise DatasetNotFoundException(dataset_id)

    df = entry["df"]
    filename = entry["filename"]

    try:
        dashboard_data = await build_executive_dashboard(df, filename, dataset_id)
        output = io.StringIO()
        writer = csv.writer(output)

        if table == "top_products":
            writer.writerow(["Product", "Revenue", "Value"])
            for p in dashboard_data.get("charts", {}).get("top_products", {}).get("data", []):
                writer.writerow([p.get("name") or p.get("product"), p.get("revenue") or p.get("value"), p.get("value")])
        elif table == "regional":
            writer.writerow(["Region", "Revenue", "Value"])
            for r in dashboard_data.get("charts", {}).get("regional_performance", {}).get("data", []):
                writer.writerow([r.get("name") or r.get("region"), r.get("revenue") or r.get("value"), r.get("value")])
        elif table == "trend":
            writer.writerow(["Period", "Revenue", "Value"])
            for t in dashboard_data.get("charts", {}).get("revenue_trend", {}).get("data", []):
                writer.writerow([t.get("period") or t.get("name"), t.get("revenue") or t.get("value"), t.get("value")])
        elif table == "anomalies":
            writer.writerow(["Row ID", "Product", "Region", "Value", "Formatted"])
            for s in dashboard_data.get("anomalies", {}).get("samples", []):
                writer.writerow([s.get("id"), s.get("product"), s.get("region"), s.get("value"), s.get("formatted")])
        elif table == "kpis":
            writer.writerow(["KPI", "Value", "Formatted", "Trend"])
            kpis = dashboard_data.get("kpis", {})
            for k_key, k_obj in kpis.items():
                writer.writerow([k_obj.get("label", k_key), k_obj.get("raw"), k_obj.get("formatted"), k_obj.get("trend", "")])

        csv_content = output.getvalue()
        safe_name = filename.replace(" ", "_").replace(".csv", "").replace(".xlsx", "")
        export_name = f"InsightForge_{safe_name}_{table}_{datetime.now().strftime('%Y%m%d')}.csv"

        return Response(
            content=csv_content,
            media_type="text/csv",
            headers={
                "Content-Disposition": f'attachment; filename="{export_name}"',
                "Access-Control-Expose-Headers": "Content-Disposition"
            }
        )
    except Exception as exc:
        app_logger.error(f"Error exporting CSV for '{dataset_id}' ({table}): {exc}", exc_info=True)
        raise InsightForgeAPIException(
            message=f"An error occurred while exporting {table} table.",
            code="CSV_EXPORT_ERROR",
            status_code=500
        )
