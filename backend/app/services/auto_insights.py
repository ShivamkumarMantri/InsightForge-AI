import os
import math
import json
import logging
import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

def format_currency_compact(val: float) -> str:
    """Format large numbers into elegant compact representations ($30.63M, $110.97K, etc.)."""
    try:
        num = float(val)
        prefix = "$"
        if num < 0:
            prefix = "-$"
            num = abs(num)
        if num >= 1_000_000_000:
            return f"{prefix}{num / 1_000_000_000:.2f}B"
        if num >= 1_000_000:
            return f"{prefix}{num / 1_000_000:.2f}M"
        if num >= 10_000:
            return f"{prefix}{num / 1_000:.1f}K"
        if num.is_integer():
            return f"{prefix}{int(num):,}"
        return f"{prefix}{num:,.2f}"
    except (ValueError, TypeError):
        return str(val)

def format_number_compact(val: float) -> str:
    """Format counts without dollar signs."""
    try:
        num = float(val)
        if num >= 1_000_000:
            return f"{num / 1_000_000:.2f}M"
        if num >= 10_000:
            return f"{num / 1_000:.1f}K"
        if num.is_integer():
            return f"{int(num):,}"
        return f"{num:,.2f}"
    except (ValueError, TypeError):
        return str(val)

def clean_val(v: Any) -> Optional[float]:
    if v is None or pd.isna(v) or math.isnan(v) or math.isinf(v):
        return None
    return round(float(v), 2)

def detect_primary_columns(df: pd.DataFrame) -> Dict[str, Optional[str]]:
    """Intelligently identify target numeric, temporal, and categorical dimensions."""
    col_map = {str(c).lower(): str(c) for c in df.columns}
    
    # Target column (Revenue / Sales / Amount)
    target_col = None
    for kw in ["revenue", "sales", "total_amount", "amount", "order_value", "total", "price"]:
        matched = next((orig for low, orig in col_map.items() if kw in low), None)
        if matched and pd.api.types.is_numeric_dtype(df[matched]):
            target_col = matched
            break
    if not target_col:
        num_cols = df.select_dtypes(include=[np.number]).columns
        target_col = str(num_cols[0]) if len(num_cols) > 0 else None

    # Date column
    date_col = None
    for kw in ["date", "time", "created_at", "order_date", "timestamp"]:
        matched = next((orig for low, orig in col_map.items() if kw in low), None)
        if matched:
            date_col = matched
            break
    if not date_col:
        for c in df.columns:
            if "date" in str(c).lower() or pd.api.types.is_datetime64_any_dtype(df[c]):
                date_col = str(c)
                break

    # Product / Item column
    product_col = None
    for kw in ["product", "item", "sku", "service", "model"]:
        matched = next((orig for low, orig in col_map.items() if kw in low), None)
        if matched:
            product_col = matched
            break
    if not product_col:
        obj_cols = df.select_dtypes(include=['object', 'category']).columns
        for c in obj_cols:
            if c != date_col and df[c].nunique() > 1:
                product_col = str(c)
                break

    # Region / Category column
    region_col = None
    for kw in ["region", "territory", "market", "country", "state", "city", "zone"]:
        matched = next((orig for low, orig in col_map.items() if kw in low), None)
        if matched and matched != product_col:
            region_col = matched
            break
    if not region_col:
        for kw in ["category", "segment", "division", "channel"]:
            matched = next((orig for low, orig in col_map.items() if kw in low), None)
            if matched and matched != product_col:
                region_col = matched
                break

    return {
        "target_col": target_col,
        "date_col": date_col,
        "product_col": product_col,
        "region_col": region_col
    }

def calculate_executive_metrics(df: pd.DataFrame, primary_cols: Dict[str, Optional[str]]) -> Dict[str, Any]:
    """Calculate executive KPIs, growth rates, aggregations, and IQR outliers via Pandas."""
    target_col = primary_cols["target_col"]
    date_col = primary_cols["date_col"]
    product_col = primary_cols["product_col"]
    region_col = primary_cols["region_col"]

    total_rows = int(len(df))
    duplicate_count = int(df.duplicated().sum())
    total_missing = int(df.isna().sum().sum())
    total_cells = int(total_rows * len(df.columns)) if total_rows > 0 else 1
    missing_pct = round((total_missing / total_cells) * 100, 2)
    quality_score = max(0, min(100, int(100 - (missing_pct * 5) - ((duplicate_count / max(1, total_rows)) * 100))))

    df = df.copy()
    if target_col and target_col in df.columns:
        df[target_col] = pd.to_numeric(df[target_col], errors='coerce').fillna(0)
        num_series = df[target_col]
        total_revenue = round(float(num_series.sum()), 2)
        avg_order_value = round(float(num_series.mean()), 2)
    else:
        total_revenue = 0.0
        avg_order_value = 0.0

    # 2. Growth Rate % & Temporal Trend
    trend_data = []
    growth_rate = 0.0
    growth_trend = "neutral"
    peak_period = None
    peak_val = 0.0
    trough_period = None
    trough_val = 0.0

    if date_col and target_col and date_col in df.columns:
        try:
            temp_df = df[[date_col, target_col]].copy()
            temp_df[date_col] = pd.to_datetime(temp_df[date_col], errors='coerce')
            temp_df = temp_df.dropna(subset=[date_col, target_col])
            temp_df['period'] = temp_df[date_col].dt.to_period('M').astype(str)
            monthly = temp_df.groupby('period')[target_col].sum().reset_index().sort_values(by='period')

            if len(monthly) >= 2:
                last_m = float(monthly.iloc[-1][target_col])
                prev_m = float(monthly.iloc[-2][target_col])
                if prev_m > 0:
                    growth_rate = round(((last_m - prev_m) / prev_m) * 100, 1)
                    growth_trend = "up" if growth_rate > 0 else ("down" if growth_rate < 0 else "neutral")
            
            for _, r in monthly.iterrows():
                val = round(float(r[target_col]), 2)
                trend_data.append({
                    "period": str(r["period"]),
                    "name": str(r["period"]),
                    "revenue": val,
                    "value": val
                })

            if len(monthly) > 0:
                p_max = monthly.loc[monthly[target_col].idxmax()]
                peak_period = str(p_max["period"])
                peak_val = round(float(p_max[target_col]), 2)
                p_min = monthly.loc[monthly[target_col].idxmin()]
                trough_period = str(p_min["period"])
                trough_val = round(float(p_min[target_col]), 2)
        except Exception as e:
            logger.warning(f"Error computing temporal trend: {e}")

    # Fallback trend if no date column
    if not trend_data and target_col:
        # Segment into 10 equal batches
        batch_size = max(1, total_rows // 10)
        df_batches = [df.iloc[i:i + batch_size] for i in range(0, total_rows, batch_size)]
        for b_idx, b in enumerate(df_batches[:10]):
            b_val = round(float(pd.to_numeric(b[target_col], errors='coerce').sum()), 2)
            trend_data.append({
                "period": f"Batch {b_idx + 1}",
                "name": f"Batch {b_idx + 1}",
                "revenue": b_val,
                "value": b_val
            })

    # 3. Top Products Breakdown
    top_products_data = []
    top_product_name = "N/A"
    top_product_rev = 0.0
    top_product_share = 0.0

    if product_col and target_col and product_col in df.columns:
        prod_agg = df.groupby(product_col)[target_col].sum().sort_values(ascending=False)
        if len(prod_agg) > 0:
            top_product_name = str(prod_agg.index[0])
            top_product_rev = round(float(prod_agg.iloc[0]), 2)
            if total_revenue > 0:
                top_product_share = round((top_product_rev / total_revenue) * 100, 1)

        for p_name, val in prod_agg.head(5).items():
            top_products_data.append({
                product_col: str(p_name),
                "name": str(p_name),
                "revenue": round(float(val), 2),
                "value": round(float(val), 2)
            })

    # 4. Regional / Category Performance
    regional_data = []
    top_region_name = "N/A"
    top_region_rev = 0.0
    top_region_share = 0.0

    if region_col and target_col and region_col in df.columns:
        reg_agg = df.groupby(region_col)[target_col].sum().sort_values(ascending=False)
        if len(reg_agg) > 0:
            top_region_name = str(reg_agg.index[0])
            top_region_rev = round(float(reg_agg.iloc[0]), 2)
            if total_revenue > 0:
                top_region_share = round((top_region_rev / total_revenue) * 100, 1)

        for r_name, val in reg_agg.head(6).items():
            regional_data.append({
                region_col: str(r_name),
                "name": str(r_name),
                "revenue": round(float(val), 2),
                "value": round(float(val), 2)
            })

    # 5. Outlier Detection using Interquartile Range (IQR)
    outliers_info = {
        "column": target_col,
        "q1": 0.0,
        "q3": 0.0,
        "iqr": 0.0,
        "lower_bound": 0.0,
        "upper_bound": 0.0,
        "outlier_count": 0,
        "outlier_pct": 0.0,
        "max_outlier": None,
        "min_outlier": None,
        "samples": []
    }

    if target_col and target_col in df.columns:
        num_clean = pd.to_numeric(df[target_col], errors='coerce').dropna()
        if len(num_clean) >= 4:
            q1 = float(num_clean.quantile(0.25))
            q3 = float(num_clean.quantile(0.75))
            iqr = q3 - q1
            lower_b = q1 - (1.5 * iqr)
            upper_b = q3 + (1.5 * iqr)
            outlier_rows = df[(df[target_col] < lower_b) | (df[target_col] > upper_b)]
            outlier_count = int(len(outlier_rows))
            outlier_pct = round((outlier_count / len(num_clean)) * 100, 2)

            max_out = round(float(outlier_rows[target_col].max()), 2) if outlier_count > 0 else None
            min_out = round(float(outlier_rows[target_col].min()), 2) if outlier_count > 0 else None

            sample_records = []
            for _, r in outlier_rows.head(4).iterrows():
                sample_records.append({
                    "id": str(r.name),
                    "value": round(float(r[target_col]), 2),
                    "formatted": format_currency_compact(r[target_col]),
                    "product": str(r.get(product_col, "Item")),
                    "region": str(r.get(region_col, "Global"))
                })

            outliers_info = {
                "column": target_col,
                "q1": round(q1, 2),
                "q3": round(q3, 2),
                "iqr": round(iqr, 2),
                "lower_bound": round(lower_b, 2),
                "upper_bound": round(upper_b, 2),
                "outlier_count": outlier_count,
                "outlier_pct": outlier_pct,
                "max_outlier": max_out,
                "min_outlier": min_out,
                "samples": sample_records
            }

    # 6. Revenue Concentration / Drivers
    driver_summary = {
        "primary_product": top_product_name,
        "product_share": top_product_share,
        "primary_region": top_region_name,
        "region_share": top_region_share,
        "pareto_driver": f"{top_product_name} generates {top_product_share}% of all revenue"
    }

    return {
        "kpis": {
            "total_revenue": {
                "raw": total_revenue,
                "formatted": format_currency_compact(total_revenue),
                "label": "Total Revenue"
            },
            "total_orders": {
                "raw": total_rows,
                "formatted": f"{total_rows:,}",
                "label": "Total Orders"
            },
            "average_order_value": {
                "raw": avg_order_value,
                "formatted": format_currency_compact(avg_order_value),
                "label": "Average Order Value"
            },
            "growth_rate": {
                "raw": growth_rate,
                "formatted": f"{'+' if growth_rate > 0 else ''}{growth_rate}%",
                "trend": growth_trend,
                "label": "Growth Rate"
            }
        },
        "charts": {
            "revenue_trend": {
                "visualization": {
                    "type": "area",
                    "title": "Revenue Trajectory Over Time",
                    "x": "period",
                    "y": "revenue",
                    "data": trend_data
                },
                "data": trend_data,
                "peak_period": peak_period,
                "peak_val": peak_val,
                "trough_period": trough_period,
                "trough_val": trough_val
            },
            "top_products": {
                "visualization": {
                    "type": "bar",
                    "title": f"Top 5 {product_col.title() if product_col else 'Product'}s by Revenue",
                    "x": product_col or "product",
                    "y": "revenue",
                    "data": top_products_data
                },
                "data": top_products_data
            },
            "regional_performance": {
                "visualization": {
                    "type": "bar",
                    "title": f"{region_col.title() if region_col else 'Regional'} Revenue Performance",
                    "x": region_col or "region",
                    "y": "revenue",
                    "data": regional_data
                },
                "data": regional_data
            }
        },
        "anomalies": outliers_info,
        "drivers": driver_summary,
        "data_quality": {
            "score": quality_score,
            "status": "Optimal" if quality_score >= 95 else ("Healthy" if quality_score >= 80 else "Attention Needed"),
            "duplicate_rows": duplicate_count,
            "missing_cells": total_missing,
            "missing_pct": missing_pct,
            "total_rows": total_rows,
            "total_columns": int(len(df.columns))
        }
    }

async def generate_ai_discovered_insights(
    calculated_results: Dict[str, Any],
    filename: str
) -> List[Dict[str, Any]]:
    """
    Formulate the 5 'AI DISCOVERED' executive insights:
    - Key trend
    - Top performer
    - Important driver
    - Anomaly
    - Data-quality issue
    Synthesized strictly from the verified Pandas calculated results.
    """
    kpis = calculated_results["kpis"]
    trend_info = calculated_results["charts"]["revenue_trend"]
    drivers = calculated_results["drivers"]
    anomalies = calculated_results["anomalies"]
    quality = calculated_results["data_quality"]

    total_rev_fmt = kpis["total_revenue"]["formatted"]
    growth_fmt = kpis["growth_rate"]["formatted"]
    peak_p = trend_info.get("peak_period") or "peak cycle"
    peak_v = format_currency_compact(trend_info.get("peak_val", 0))

    top_prod = drivers["primary_product"]
    prod_share = drivers["product_share"]
    top_reg = drivers["primary_region"]
    reg_share = drivers["region_share"]

    outlier_cnt = anomalies["outlier_count"]
    upper_b = format_currency_compact(anomalies["upper_bound"])
    max_out = format_currency_compact(anomalies["max_outlier"]) if anomalies["max_outlier"] else None

    # Deterministic base insights (anchor ground truth)
    fallback_insights = [
        {
            "id": "trend",
            "type": "trend",
            "title": "Key Trend",
            "badge": "Trajectory",
            "category": "Temporal Acceleration",
            "statement": f"Monthly revenue peaked in {peak_p} at {peak_v}, recording a {growth_fmt} month-over-month trajectory.",
            "detail": f"Performance across cycles reached {total_rev_fmt} in total revenue."
        },
        {
            "id": "performer",
            "type": "performer",
            "title": "Top Performer",
            "badge": "Market Leader",
            "category": "Volume Champion",
            "statement": f"{top_prod} is the dominant revenue engine, delivering {prod_share}% of total gross volume.",
            "detail": f"Consistently leads sales performance across all operating segments."
        },
        {
            "id": "driver",
            "type": "driver",
            "title": "Important Driver",
            "badge": "Concentration",
            "category": "Regional Strength",
            "statement": f"{top_reg} region commands {reg_share}% of total organizational revenue, acting as the primary geographic pillar.",
            "detail": f"Combined with {top_prod}, forms the core commercial driver."
        },
        {
            "id": "anomaly",
            "type": "anomaly",
            "title": "Anomaly",
            "badge": "IQR Outlier",
            "category": "Distributional Skew",
            "statement": f"Detected {outlier_cnt} statistical outliers exceeding the IQR upper threshold ({upper_b})" + (f", peaking at {max_out}." if max_out else "."),
            "detail": f"Represents {anomalies['outlier_pct']}% of transactions warranting audit review."
        },
        {
            "id": "quality",
            "type": "quality",
            "title": "Data Quality",
            "badge": "Integrity Score",
            "category": "Hygiene Verification",
            "statement": (
                f"Data quality alert ({quality['score']}/100): detected {quality['duplicate_rows']} duplicate records and {quality['missing_cells']} missing values ({quality['missing_pct']}%) across {quality['total_rows']:,} rows."
                if (quality['missing_cells'] > 0 or quality['duplicate_rows'] > 0)
                else f"Optimal dataset integrity ({quality['score']}/100) with 0 duplicate rows and 0% missing values across {quality['total_rows']:,} records."
            ),
            "detail": (
                "Data hygiene requires deduplication or imputation prior to operational pipeline automation."
                if (quality['missing_cells'] > 0 or quality['duplicate_rows'] > 0)
                else "Data schema is fully clean and compliant for executive reporting."
            )
        }
    ]

    api_key = os.environ.get("GEMINI_API_KEY", "").strip()
    model_name = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash").strip()

    if not api_key or api_key == "your_new_key_here":
        return fallback_insights

    try:
        from google import genai
        from google.genai import types

        client = genai.Client(api_key=api_key)

        prompt = f"""
You are the Chief AI Data Analyst for InsightForge AI.
Below are calculated, verified statistical results from dataset '{filename}'.

CALCULATED METRICS & FACTS:
- Total Revenue: {total_rev_fmt}
- Total Orders: {kpis['total_orders']['formatted']}
- Average Order Value: {kpis['average_order_value']['formatted']}
- Growth Rate: {growth_fmt}
- Peak Period: {peak_p} ({peak_v})
- Top Product: {top_prod} ({prod_share}% of revenue)
- Top Region: {top_reg} ({reg_share}% of revenue)
- Outliers (IQR): {outlier_cnt} records ({anomalies['outlier_pct']}%), Upper Bound: {upper_b}, Max: {max_out}
- Data Quality: Score {quality['score']}/100, {quality['duplicate_rows']} duplicates, {quality['missing_pct']}% missing cells

CRITICAL RULES:
1. NEVER invent numbers. Use ONLY the exact figures provided above.
2. Produce exactly 5 concise, executive, high-impact statements:
   - Key trend
   - Top performer
   - Important driver
   - Anomaly
   - Data-quality issue

Return JSON adhering strictly to:
[
  {{ "type": "trend", "title": "Key Trend", "badge": "Trajectory", "category": "Temporal Acceleration", "statement": "concise executive sentence with exact numbers", "detail": "supporting context" }},
  {{ "type": "performer", "title": "Top Performer", "badge": "Market Leader", "category": "Volume Champion", "statement": "...", "detail": "..." }},
  {{ "type": "driver", "title": "Important Driver", "badge": "Concentration", "category": "Regional Strength", "statement": "...", "detail": "..." }},
  {{ "type": "anomaly", "title": "Anomaly", "badge": "IQR Outlier", "category": "Distributional Skew", "statement": "...", "detail": "..." }},
  {{ "type": "quality", "title": "Data Quality", "badge": "Integrity Score", "category": "Hygiene Verification", "statement": "...", "detail": "..." }}
]
Return ONLY JSON. No markdown code fence.
"""
        from app.models.analysis_plan import SingleAutoInsightModel
        from app.core.security import execute_with_timeout, gemini_rate_limiter
        from app.core.logging import app_logger

        await gemini_rate_limiter.acquire("executive_insights")

        async def call_gemini_insights():
            return client.models.generate_content(
                model=model_name,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    temperature=0.1
                )
            )

        response = await execute_with_timeout(call_gemini_insights(), timeout_seconds=30.0, task_name="Executive Insights Synthesis")
        clean_text = response.text.strip()
        parsed = json.loads(clean_text)
        if isinstance(parsed, list) and len(parsed) == 5:
            validated_insights = [SingleAutoInsightModel.model_validate(item).model_dump() for item in parsed]
            return validated_insights
        return fallback_insights
    except Exception as e:
        logger.warning(f"Gemini executive insights synthesis failed or rejected validation: {e}. Using deterministic calculations.")
        return fallback_insights

async def build_executive_dashboard(df: pd.DataFrame, filename: str, dataset_id: str) -> Dict[str, Any]:
    """
    Main orchestration entry point:
    1. Computes all Pandas metrics, Recharts chart specs, and IQR outliers.
    2. Synthesizes the 5 AI Discovered executive insights.
    """
    primary_cols = detect_primary_columns(df)
    calculated_results = calculate_executive_metrics(df, primary_cols)
    ai_insights = await generate_ai_discovered_insights(calculated_results, filename)

    return {
        "dataset_id": dataset_id,
        "filename": filename,
        "primary_columns": primary_cols,
        "kpis": calculated_results["kpis"],
        "charts": calculated_results["charts"],
        "ai_discovered": ai_insights,
        "anomalies": calculated_results["anomalies"],
        "drivers": calculated_results["drivers"],
        "data_quality": calculated_results["data_quality"]
    }
