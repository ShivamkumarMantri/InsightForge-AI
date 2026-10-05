import math
import re
import numpy as np
import pandas as pd
from typing import Dict, Any, List, Optional
from app.core.errors import UnsupportedOperationException, InsightForgeAPIException
from app.core.logging import app_logger

BLOCKED_PATTERNS = [
    r"\b(os|subprocess|sys|shutil|pty|builtins)\b",
    r"\b(eval|exec|compile|__import__|importlib)\b",
    r"\b(open|read|write|remove|unlink|mkdir|rmdir)\s*\(",
    r"\b(socket|requests|urllib|http|httpx|aiohttp)\b",
    r"\b(bash|sh|cmd|powershell|curl|wget)\b",
]

def check_for_dangerous_patterns(obj: Any):
    """Scan all input structures to strictly prevent execution vectors, shell commands, or network calls."""
    if isinstance(obj, str):
        for pat in BLOCKED_PATTERNS:
            if re.search(pat, obj, re.IGNORECASE):
                app_logger.error(f"Security block triggered by pattern '{pat}' in input: {obj}")
                raise InsightForgeAPIException(
                    message="Security violation: Prohibited system command, execution vector, or network call detected.",
                    code="FORBIDDEN_OPERATION",
                    status_code=403
                )
    elif isinstance(obj, dict):
        for k, v in obj.items():
            check_for_dangerous_patterns(k)
            check_for_dangerous_patterns(v)
    elif isinstance(obj, list):
        for item in obj:
            check_for_dangerous_patterns(item)

ALLOWED_OPERATIONS = {
    "groupby",
    "grouping",
    "date_grouping",
    "date grouping",
    "aggregation",
    "sort",
    "sorting",
    "filter",
    "filtering",
    "correlation",
    "summary_statistic",
    "counting",
    "count",
    "mean",
    "median",
    "min",
    "max",
    "min/max",
    "top_k",
    "scatter",
    "histogram",
    "comparison",
    "driver_analysis"
}

ALLOWED_AGG_FUNCS = {"sum", "mean", "median", "count", "min", "max", "std"}

def format_number(val: Any) -> str:
    """Format numeric values with commas and clean currency/decimal styling."""
    if val is None or pd.isna(val):
        return "N/A"
    try:
        num = float(val)
        if abs(num) >= 1_000_000:
            return f"${num:,.2f}" if "price" in str(val).lower() or "rev" in str(val).lower() else f"{num:,.2f}"
        if num.is_integer():
            return f"{int(num):,}"
        return f"{num:,.2f}"
    except (ValueError, TypeError):
        return str(val)

def format_compact_metric(val: Any, is_currency: bool = True) -> str:
    """Format large numbers into high-impact compact KPI strings like $2.4M or 1.2K."""
    if val is None or pd.isna(val):
        return "N/A"
    try:
        num = float(val)
        prefix = "$" if is_currency else ""
        if abs(num) >= 1_000_000_000:
            return f"{prefix}{num / 1_000_000_000:.2f}B"
        if abs(num) >= 1_000_000:
            return f"{prefix}{num / 1_000_000:.2f}M"
        if abs(num) >= 10_000:
            return f"{prefix}{num / 1_000:.1f}K"
        if num.is_integer():
            return f"{prefix}{int(num):,}"
        return f"{prefix}{num:.2f}"
    except (ValueError, TypeError):
        return str(val)

def execute_analysis_plan(df: pd.DataFrame, plan: Dict[str, Any]) -> Dict[str, Any]:
    """
    Safely execute a structured analysis plan on a Pandas DataFrame.
    Strictly forbids arbitrary code execution; only executes pre-approved Pandas operations.
    Supports filters, comparisons, driver analyses, date groupings, distributions, and rankings.
    """
    # 0. Check if clarification is needed (Rule 9: Never invent context)
    if plan.get("need_clarification"):
        msg = plan.get("answer") or "I'm not sure what you'd like me to analyze. Which product or region do you mean?"
        return {
            "answer": msg,
            "insight": msg,
            "key_metric": "-",
            "why_it_matters": "Contextual clarification required before proceeding with targeted calculation.",
            "calculation_explanation": "Awaiting unambiguous entity clarification from user.",
            "calculation_steps": [
                "Detected referential pronoun or relative question in user query",
                "Scanned active conversation state for antecedent entity",
                "Found no prior matching entity in memory",
                "Requested specific product or region clarification"
            ],
            "summary_value": "-",
            "top_item": None,
            "data": [],
            "result_table": [],
            "context_used": False,
            "visualization": {
                "type": "none",
                "title": "Clarification Required",
                "x": "",
                "y": "",
                "data": []
            }
        }

    # 0. Safety validation & security scanning
    check_for_dangerous_patterns(plan)

    raw_op = plan.get("operation", "summary_statistic")
    if not isinstance(raw_op, str) or raw_op.lower() not in ALLOWED_OPERATIONS:
        app_logger.warning(f"Unsupported operation requested: '{raw_op}'")
        raise UnsupportedOperationException(str(raw_op))

    op = raw_op.lower()
    intent = plan.get("intent", "aggregation")
    columns = plan.get("columns", [])
    target_col = plan.get("target_column")
    group_by = plan.get("group_by")
    agg_func = plan.get("agg_func", "sum").lower()
    limit = plan.get("limit", 10)
    sort_order = plan.get("sort_order", "desc").lower()
    date_freq = plan.get("date_freq", "M")
    vis_spec = plan.get("visualization", {})
    requested_vis_type = vis_spec.get("type", "").lower()
    custom_title = vis_spec.get("title")
    filters = plan.get("filter") or {}

    if agg_func not in ALLOWED_AGG_FUNCS:
        agg_func = "sum"

    # Normalize column names in df (case-insensitive lookup helper)
    col_map = {str(c).lower(): str(c) for c in df.columns}
    def resolve_col(c: Optional[str]) -> Optional[str]:
        if not c:
            return None
        return col_map.get(str(c).lower(), c)

    target_col = resolve_col(target_col)
    if isinstance(group_by, list):
        group_by = [resolve_col(g) for g in group_by if resolve_col(g) in df.columns]
        group_by = group_by[0] if group_by else None
    else:
        group_by = resolve_col(group_by)

    # Apply contextual filters if present (e.g. region == 'East')
    working_df = df.copy()
    filter_desc = []
    if isinstance(filters, dict) and filters:
        for f_col, f_val in filters.items():
            rc = resolve_col(f_col)
            if rc and rc in working_df.columns and f_val is not None:
                working_df = working_df[working_df[rc].astype(str).str.lower() == str(f_val).lower()]
                filter_desc.append(f"{rc} = '{f_val}'")

    # Normalize operation aliases
    if op in ["filtering", "filter"]:
        op = "filter"
    elif op in ["grouping", "groupby"]:
        op = "groupby"
    elif op in ["sorting", "sort"]:
        op = "sort"
    elif op in ["counting", "count"]:
        op = "summary_statistic"
        agg_func = "count"
    elif op in ["mean", "median", "min", "max"]:
        agg_func = op
        op = "summary_statistic"
    elif op in ["min/max"]:
        op = "summary_statistic"
        agg_func = "max"
    elif op in ["date grouping", "date_grouping"]:
        op = "date_grouping"

    # 0a. Explicit Filter Operation
    if op == "filter":
        sample_rows = []
        target_records = working_df.head(limit or 15)
        for _, row in target_records.iterrows():
            item = {}
            for col in working_df.columns:
                val = row[col]
                if pd.isna(val):
                    item[str(col)] = None
                elif isinstance(val, (int, float, np.integer, np.floating)):
                    item[str(col)] = round(float(val), 2)
                else:
                    item[str(col)] = str(val)
            sample_rows.append(item)

        total_matches = len(working_df)
        filt_summary = ", ".join(filter_desc) if filter_desc else "active filter criteria"
        answer = f"Found {total_matches:,} records matching {filt_summary}."
        insight = f"Filtered {len(df):,} total records down to {total_matches:,} matching entries based on {filt_summary}."
        key_metric = f"{total_matches:,} records"
        why_it_matters = f"Provides targeted visibility into the subset matching {filt_summary}."
        calc_steps = [
            f"Evaluated criteria: {filt_summary}",
            f"Filtered DataFrame from {len(df):,} rows to {total_matches:,} records",
            f"Extracted sample records for inspection"
        ]
        return {
            "answer": answer,
            "insight": insight,
            "key_metric": key_metric,
            "why_it_matters": why_it_matters,
            "calculation_explanation": f"Filtered records according to {filt_summary}.",
            "calculation_steps": calc_steps,
            "summary_value": key_metric,
            "top_item": f"{total_matches} rows",
            "data": sample_rows,
            "result_table": sample_rows,
            "context_used": True,
            "visualization": {
                "type": "bar" if group_by else "metric",
                "title": custom_title or f"Filtered Records: {filt_summary}",
                "x": group_by or "records",
                "y": target_col or "count",
                "data": sample_rows
            }
        }

    # 0. Correlation Operation
    if op == "correlation":
        num_cols = working_df.select_dtypes(include=[np.number]).columns.tolist()
        cols_requested = [resolve_col(c) for c in columns if resolve_col(c) in num_cols]
        if len(cols_requested) >= 2:
            col1, col2 = cols_requested[0], cols_requested[1]
        elif target_col and len(num_cols) >= 2:
            col1 = target_col
            col2 = next((c for c in num_cols if c != col1), num_cols[1])
        elif len(num_cols) >= 2:
            col1, col2 = num_cols[0], num_cols[1]
        else:
            col1, col2 = (num_cols[0], num_cols[0]) if num_cols else ("val1", "val2")

        if col1 in working_df.columns and col2 in working_df.columns:
            clean_sub = working_df[[col1, col2]].dropna()
            r_val = float(clean_sub[col1].corr(clean_sub[col2]))
            if math.isnan(r_val):
                r_val = 0.0
            r_rounded = round(r_val, 3)

            direction = "positive" if r_rounded > 0 else ("negative" if r_rounded < 0 else "neutral")
            abs_r = abs(r_rounded)
            if abs_r >= 0.7:
                strength = "strong"
            elif abs_r >= 0.4:
                strength = "moderate"
            elif abs_r >= 0.15:
                strength = "weak"
            else:
                strength = "negligible"

            scatter_data = []
            for idx_s, r in clean_sub.head(40).iterrows():
                scatter_data.append({
                    "name": f"Item {idx_s}",
                    "x": round(float(r[col1]), 2),
                    "y": round(float(r[col2]), 2),
                    "value": round(float(r[col2]), 2)
                })

            answer = f"The correlation between {col1.replace('_', ' ')} and {col2.replace('_', ' ')} is {r_rounded:+.2f} ({strength} {direction} correlation)."
            insight = f"Calculated Pearson r = {r_rounded:+.2f} across {len(clean_sub):,} valid records, indicating a {strength} {direction} linear relationship between '{col1}' and '{col2}'."
            why_it_matters = f"Identifies whether changes in '{col1}' reliably correspond to proportional changes in '{col2}' across the dataset."
            calc_steps = [
                f"Isolated numerical series for '{col1}' and '{col2}'",
                f"Filtered to {len(clean_sub):,} complete paired records",
                f"Calculated covariance and standard deviations for Pearson correlation",
                f"Yielded r = {r_rounded:+.2f} ({strength.capitalize()} {direction})"
            ]
            title = custom_title or f"Correlation: {col1.replace('_', ' ').title()} vs {col2.replace('_', ' ').title()}"

            return {
                "answer": answer,
                "insight": insight,
                "key_metric": f"r = {r_rounded:+.2f}",
                "why_it_matters": why_it_matters,
                "calculation_explanation": f"Computed Pearson correlation coefficient r = {r_rounded:+.2f}.",
                "calculation_steps": calc_steps,
                "summary_value": f"r = {r_rounded:+.2f}",
                "top_item": f"{strength.capitalize()} {direction}",
                "data": scatter_data,
                "result_table": [
                    {"metric": "Pearson Correlation (r)", "value": r_rounded},
                    {"metric": "Relationship Strength", "value": f"{strength.capitalize()} {direction}"},
                    {"metric": "Paired Sample Count", "value": len(clean_sub)}
                ],
                "context_used": bool(filters),
                "visualization": {
                    "type": "scatter",
                    "title": title,
                    "x": col1,
                    "y": col2,
                    "data": scatter_data
                }
            }

    # 1. Comparison Operation (e.g. Compare it with South)
    if op == "comparison":
        entities = plan.get("comparison_entities") or plan.get("entities") or []
        dim_col = group_by or "region"
        dim_col = resolve_col(dim_col) or "region"

        if not target_col:
            target_col = next((c for c in df.columns if any(kw in c.lower() for kw in ["revenue", "sales", "amount", "total"])), "revenue")

        # Fallback entities if not populated
        if not entities or len(entities) < 2:
            unique_dims = [str(u) for u in df[dim_col].dropna().unique().tolist()]
            if len(entities) == 1:
                other = next((u for u in unique_dims if u.lower() != entities[0].lower()), unique_dims[0])
                entities = [entities[0], other]
            else:
                entities = unique_dims[:2]

        e1 = str(entities[0])
        e2 = str(entities[1])

        # Aggregate for e1 and e2
        agg_series = df.groupby(dim_col)[target_col].agg(agg_func)
        val1 = 0.0
        val2 = 0.0
        for idx_val, val in agg_series.items():
            if str(idx_val).strip().lower() == e1.strip().lower():
                val1 = round(float(val), 2)
            elif str(idx_val).strip().lower() == e2.strip().lower():
                val2 = round(float(val), 2)

        delta = round(abs(val1 - val2), 2)
        winner = e1 if val1 >= val2 else e2
        loser = e2 if val1 >= val2 else e1
        higher_v = val1 if val1 >= val2 else val2
        lower_v = val2 if val1 >= val2 else val1
        pct_lead = round((delta / lower_v) * 100, 1) if lower_v > 0 else 0.0

        vis_data = [
            {"name": e1, dim_col: e1, "value": val1, target_col: val1},
            {"name": e2, dim_col: e2, "value": val2, target_col: val2}
        ]

        is_currency = any(k in target_col.lower() for k in ["revenue", "sales", "price", "cost"])
        key_metric = f"+{format_compact_metric(delta, is_currency=is_currency)} ({winner})"

        answer = f"'{winner}' generated higher {target_col.replace('_', ' ')} than '{loser}'."
        insight = f"'{winner}' produced {format_number(higher_v)} versus '{loser}' with {format_number(lower_v)}, creating a net variance of {format_number(delta)} (+{pct_lead}%)."
        why_it_matters = f"'{winner}' yields a {pct_lead}% revenue advantage over '{loser}', highlighting key market performance disparity."
        calc_explanation = f"Extracted metrics for '{e1}' and '{e2}', computed total {target_col.replace('_', ' ')} for each, and derived comparative variance."
        calc_steps = [
            f"Filtered records to comparison markets '{e1}' and '{e2}'",
            f"Calculated total {target_col.replace('_', ' ')} ({agg_func}) for each region",
            f"Computed variance delta: {format_number(delta)} (+{pct_lead}%)",
            f"Confirmed '{winner}' as the leading market"
        ]

        title = custom_title or f"{target_col.replace('_', ' ').title()} Comparison: {e1} vs {e2}"

        return {
            "answer": answer,
            "insight": insight,
            "key_metric": key_metric,
            "why_it_matters": why_it_matters,
            "calculation_explanation": calc_explanation,
            "calculation_steps": calc_steps,
            "summary_value": key_metric,
            "top_item": winner,
            "data": vis_data,
            "result_table": vis_data,
            "context_used": True,
            "visualization": {
                "type": "bar",
                "title": title,
                "x": dim_col,
                "y": target_col,
                "data": vis_data
            }
        }

    # 2. Driver Analysis Operation (e.g. Which product is driving that difference?)
    if op == "driver_analysis":
        entities = plan.get("comparison_entities") or plan.get("entities") or ["East", "South"]
        compare_col = plan.get("compare_column") or "region"
        compare_col = resolve_col(compare_col) or "region"
        driver_dim = plan.get("dimension") or group_by or "product"
        driver_dim = resolve_col(driver_dim) or "product"

        if not target_col:
            target_col = next((c for c in df.columns if any(kw in c.lower() for kw in ["revenue", "sales", "amount", "total"])), "revenue")

        e1 = str(entities[0]) if len(entities) > 0 else "East"
        e2 = str(entities[1]) if len(entities) > 1 else "South"

        # Filter to e1 and e2
        sub_df = df[df[compare_col].astype(str).str.lower().isin([e1.lower(), e2.lower()])]
        grouped = sub_df.groupby([driver_dim, compare_col])[target_col].agg(agg_func).unstack(fill_value=0)

        e1_col = next((c for c in grouped.columns if str(c).lower() == e1.lower()), grouped.columns[0] if len(grouped.columns) > 0 else None)
        e2_col = next((c for c in grouped.columns if str(c).lower() == e2.lower()), grouped.columns[1] if len(grouped.columns) > 1 else None)

        if e1_col is not None and e2_col is not None:
            grouped["delta"] = grouped[e1_col] - grouped[e2_col]
        else:
            grouped["delta"] = grouped.iloc[:, 0]

        grouped = grouped.sort_values(by="delta", ascending=False)

        top_driver_name = str(grouped.index[0])
        top_driver_delta = round(float(grouped.loc[top_driver_name, "delta"]), 2)
        top_driver_e1 = round(float(grouped.loc[top_driver_name, e1_col]), 2)
        top_driver_e2 = round(float(grouped.loc[top_driver_name, e2_col]), 2)

        vis_data = []
        for item_name, row in grouped.head(6).iterrows():
            vis_data.append({
                driver_dim: str(item_name),
                "name": str(item_name),
                f"{e1}": round(float(row[e1_col]), 2),
                f"{e2}": round(float(row[e2_col]), 2),
                "difference": round(float(row["delta"]), 2),
                "value": round(float(row["delta"]), 2)
            })

        is_currency = any(k in target_col.lower() for k in ["revenue", "sales", "price", "cost"])
        key_metric = f"+{format_compact_metric(top_driver_delta, is_currency=is_currency)}"

        answer = f"'{top_driver_name}' is the primary product driving the difference between {e1} and {e2}."
        insight = f"'{top_driver_name}' generated {format_number(top_driver_e1)} in {e1} versus {format_number(top_driver_e2)} in {e2}, accounting for a {format_number(top_driver_delta)} net lead."
        why_it_matters = f"Product performance in '{top_driver_name}' explains the primary share of {e1}'s total revenue lead over {e2}."
        calc_explanation = f"Segmented data between '{e1}' and '{e2}', computed product revenues in each market, and sorted by variance delta."
        calc_steps = [
            f"Segmented dataset for markets '{e1}' and '{e2}'",
            f"Grouped total {target_col.replace('_', ' ')} by '{driver_dim}' across both regions",
            f"Computed product-level variance delta ({e1} - {e2})",
            f"Identified '{top_driver_name}' as the primary variance driver ({format_number(top_driver_delta)})"
        ]

        title = custom_title or f"Revenue Difference by Product: {e1} vs {e2}"

        return {
            "answer": answer,
            "insight": insight,
            "key_metric": key_metric,
            "why_it_matters": why_it_matters,
            "calculation_explanation": calc_explanation,
            "calculation_steps": calc_steps,
            "summary_value": key_metric,
            "top_item": top_driver_name,
            "data": vis_data,
            "result_table": vis_data,
            "context_used": True,
            "visualization": {
                "type": "bar",
                "title": title,
                "x": driver_dim,
                "y": "difference",
                "data": vis_data
            }
        }

    # 3. Date Grouping Operation (Line / Area charts with optional filter)
    if op == "date_grouping" or (group_by and any(kw in str(group_by).lower() for kw in ["date", "time"])):
        date_col = group_by or next((c for c in working_df.columns if any(kw in c.lower() for kw in ["date", "time"])), None)
        if not target_col:
            target_col = next((c for c in working_df.columns if any(kw in c.lower() for kw in ["revenue", "sales", "amount", "total"])), None)
        if not target_col:
            num_cols = working_df.select_dtypes(include=[np.number]).columns
            target_col = num_cols[0] if len(num_cols) > 0 else working_df.columns[0]

        if date_col and target_col:
            temp_df = working_df[[date_col, target_col]].copy()
            temp_df[date_col] = pd.to_datetime(temp_df[date_col], errors='coerce')
            temp_df = temp_df.dropna(subset=[date_col, target_col])
            
            temp_df['period'] = temp_df[date_col].dt.to_period(date_freq).astype(str)
            grouped = temp_df.groupby('period')[target_col].agg(agg_func).reset_index()
            grouped = grouped.sort_values(by='period')

            result_table = []
            vis_data = []
            for _, r in grouped.iterrows():
                val = round(float(r[target_col]), 2)
                row_item = {
                    "period": str(r['period']),
                    "name": str(r['period']),
                    "value": val,
                    target_col: val
                }
                result_table.append(row_item)
                vis_data.append(row_item)

            total_val = round(float(grouped[target_col].sum()), 2)
            peak_row = grouped.loc[grouped[target_col].idxmax()]
            peak_period = str(peak_row['period'])
            peak_val = round(float(peak_row[target_col]), 2)
            is_currency = any(k in target_col.lower() for k in ["revenue", "sales", "price", "cost"])
            pct_peak = round((peak_val / total_val) * 100, 1) if total_val > 0 else 0

            chart_type = "area" if requested_vis_type == "area" else "line"
            entity_tag = f" for {filters.get('region') or filters.get('product')}" if filters else ""
            title = custom_title or f"Monthly {target_col.replace('_', ' ').title()}{entity_tag} Over Time"

            answer = f"Monthly {target_col.replace('_', ' ')}{entity_tag} peaked in {peak_period} at {format_number(peak_val)}."
            insight = f"Peak performance occurred in {peak_period} with {format_number(peak_val)} {target_col.replace('_', ' ')}. Total volume across {len(grouped)} periods reached {format_number(total_val)}."
            key_metric = format_compact_metric(peak_val, is_currency=is_currency)
            why_it_matters = f"{peak_period} contributed {pct_peak}% of total cumulative volume ({format_number(total_val)})."
            calc_explanation = f"Filtered records ({', '.join(filter_desc) if filter_desc else 'full dataset'}), parsed '{date_col}' into calendar months, and computed {agg_func}() of '{target_col}'."
            calc_steps = [
                f"Applied scope: {', '.join(filter_desc) if filter_desc else 'entire active dataset'}",
                f"Parsed '{date_col}' into monthly calendar buckets",
                f"Aggregated {target_col.replace('_', ' ')} using {agg_func}() for each month",
                f"Identified {peak_period} as the peak volume cycle ({pct_peak}% share)"
            ]

            return {
                "answer": answer,
                "insight": insight,
                "key_metric": key_metric,
                "why_it_matters": why_it_matters,
                "calculation_explanation": calc_explanation,
                "calculation_steps": calc_steps,
                "summary_value": format_number(total_val),
                "top_item": peak_period,
                "data": vis_data,
                "result_table": result_table,
                "context_used": bool(filters),
                "visualization": {
                    "type": chart_type,
                    "title": title,
                    "x": "period",
                    "y": target_col,
                    "data": vis_data
                }
            }

    # 4. Groupby & Aggregation / Top K (Bar or Pie)
    if op in ["groupby", "top_k", "sort"] or group_by:
        if not group_by:
            cat_cols = working_df.select_dtypes(include=['object', 'category']).columns.tolist()
            group_by = cat_cols[0] if cat_cols else working_df.columns[0]
        if not target_col:
            num_cols = working_df.select_dtypes(include=[np.number]).columns.tolist()
            target_col = next((c for c in num_cols if any(k in c.lower() for kw in ["revenue", "sales", "price"])), num_cols[0] if num_cols else working_df.columns[1])

        # Perform groupby aggregation
        agg_series = working_df.groupby(group_by)[target_col].agg(agg_func)
        if sort_order == "desc":
            agg_series = agg_series.sort_values(ascending=False)
        else:
            agg_series = agg_series.sort_values(ascending=True)

        grand_total = float(working_df[target_col].sum()) if agg_func == "sum" else float(agg_series.sum())

        if limit and limit > 0:
            agg_series = agg_series.head(limit)

        result_table = []
        vis_data = []
        for cat_name, val in agg_series.items():
            clean_val = round(float(val), 2) if not pd.isna(val) else 0.0
            row_dict = {
                group_by: str(cat_name),
                "name": str(cat_name),
                target_col: clean_val,
                "value": clean_val
            }
            result_table.append(row_dict)
            vis_data.append(row_dict)

        top_item = result_table[0]["name"] if result_table else "None"
        top_val = result_table[0]["value"] if result_table else 0.0
        pct = round((top_val / grand_total) * 100, 1) if grand_total > 0 else 0
        is_currency = any(k in target_col.lower() for k in ["revenue", "sales", "price", "cost"])

        chart_type = "pie" if requested_vis_type in ["pie", "donut"] else "bar"
        entity_scope = f" in {', '.join(filter_desc)}" if filter_desc else ""
        title = custom_title or f"{target_col.replace('_', ' ').title()} by {group_by.replace('_', ' ').title()}{entity_scope}"

        answer = f"'{top_item}' generated the highest {target_col.replace('_', ' ')}{entity_scope}."
        insight = f"'{top_item}' leads in performance, generating {format_number(top_val)} in total {target_col.replace('_', ' ')} ({agg_func})."
        key_metric = format_compact_metric(top_val, is_currency=is_currency)
        why_it_matters = f"'{top_item}' contributed {pct}% of total {target_col.replace('_', ' ')} across {len(result_table)} categories."
        calc_explanation = f"Grouped records by '{group_by}', calculated the {agg_func}() of '{target_col}', and sorted in {sort_order}ending order."
        calc_steps = [
            f"Segmented data records by '{group_by}'",
            f"Calculated total {target_col.replace('_', ' ')} ({agg_func}) for each category",
            f"Sorted in {sort_order}ending order",
            f"Selected '{top_item}' as the top category ({pct}% share)"
        ]

        return {
            "answer": answer,
            "insight": insight,
            "key_metric": key_metric,
            "why_it_matters": why_it_matters,
            "calculation_explanation": calc_explanation,
            "calculation_steps": calc_steps,
            "summary_value": format_number(top_val),
            "top_item": top_item,
            "data": vis_data,
            "result_table": result_table,
            "context_used": bool(filters),
            "visualization": {
                "type": chart_type,
                "title": title,
                "x": group_by,
                "y": target_col,
                "data": vis_data
            }
        }

    # 5. Summary Statistic
    if not target_col:
        num_cols = working_df.select_dtypes(include=[np.number]).columns.tolist()
        target_col = num_cols[0] if num_cols else working_df.columns[0]

    series = pd.to_numeric(working_df[target_col], errors='coerce').dropna()
    if agg_func == "mean":
        metric_val = round(float(series.mean()), 2)
    elif agg_func == "median":
        metric_val = round(float(series.median()), 2)
    elif agg_func == "min":
        metric_val = round(float(series.min()), 2)
    elif agg_func == "max":
        metric_val = round(float(series.max()), 2)
    elif agg_func == "count":
        metric_val = int(len(series))
    else:
        metric_val = round(float(series.sum()), 2)

    is_currency = any(k in target_col.lower() for k in ["revenue", "sales", "price", "cost"])
    key_metric = format_compact_metric(metric_val, is_currency=is_currency)
    answer = f"The {agg_func} {target_col.replace('_', ' ')} is {format_number(metric_val)}."
    insight = f"The dataset-wide {agg_func} value of '{target_col.replace('_', ' ')}' across {len(series):,} valid rows is {format_number(metric_val)}."
    why_it_matters = f"Serves as the organizational benchmark across the active scope."
    calc_explanation = f"Computed statistical {agg_func}() across {len(series):,} valid rows of '{target_col}'."
    calc_steps = [
        f"Filtered valid numerical entries in '{target_col}'",
        f"Identified {len(series):,} non-null records",
        f"Applied statistical {agg_func}() reduction function",
        f"Yielded benchmark {agg_func} of {format_number(metric_val)}"
    ]

    title = custom_title or f"Average {target_col.replace('_', ' ').title()}"

    return {
        "answer": answer,
        "insight": insight,
        "key_metric": key_metric,
        "why_it_matters": why_it_matters,
        "calculation_explanation": calc_explanation,
        "calculation_steps": calc_steps,
        "summary_value": format_number(metric_val),
        "top_item": target_col,
        "data": [{"name": target_col, "value": metric_val}],
        "result_table": [{"metric": f"{agg_func.capitalize()} of {target_col}", "value": metric_val}],
        "context_used": bool(filters),
        "visualization": {
            "type": "metric",
            "title": title,
            "x": target_col,
            "y": "value",
            "data": [{"name": target_col, "value": metric_val}]
        }
    }
