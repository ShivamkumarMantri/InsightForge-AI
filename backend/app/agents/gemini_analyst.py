import os
import re
import json
import logging
from typing import Dict, Any, List, Optional
from dotenv import load_dotenv
from app.core.logging import app_logger

load_dotenv()
logger = logging.getLogger(__name__)

def generate_contextual_suggestions(
    plan: Dict[str, Any],
    top_item: Optional[str] = None,
    conv_ctx: Optional[Dict[str, Any]] = None
) -> List[str]:
    """Dynamically formulate 2-3 hyper-relevant follow-up suggestions based on the active analysis."""
    op = plan.get("operation", "")
    group_by = plan.get("group_by", "")
    target_col = plan.get("target_column", "revenue")
    comp_entities = plan.get("comparison_entities") or []
    item_str = str(top_item or plan.get("active_entity", {}).get("name") or "East")

    if op == "driver_analysis":
        e1 = comp_entities[0] if len(comp_entities) > 0 else "East"
        e2 = comp_entities[1] if len(comp_entities) > 1 else "South"
        return [
            "Show me the top 5 products.",
            f"Show monthly sales for {item_str}.",
            f"Compare quantity sold in {e1} vs {e2}."
        ]

    if op == "comparison":
        e2 = comp_entities[1] if len(comp_entities) > 1 else "South"
        return [
            "Which product is driving that difference?",
            f"Show monthly trend for {e2}.",
            "Show me the top 5 products."
        ]

    if op == "date_grouping":
        filter_entity = plan.get("filter", {}).get("region") or plan.get("filter", {}).get("product")
        if filter_entity:
            return [
                "Compare it with South.",
                f"What products drove {filter_entity} revenue?",
                "Show me the top 5 products."
            ]
        return [
            "Which region generated the highest revenue?",
            "What is the average quantity sold?",
            "Show me the top 5 products."
        ]

    if group_by == "region":
        return [
            "Show me its monthly trend.",
            f"Compare {item_str} vs South.",
            f"What products drove {item_str} revenue?"
        ]

    if group_by == "product":
        return [
            f"Show monthly sales for {item_str}.",
            f"Which region buys the most {item_str}?",
            "Compare it with South."
        ]

    return [
        "Which region generated the highest revenue?",
        "Show monthly revenue.",
        "Give me the top 5 products."
    ]


def semantic_rule_planner(
    question: str,
    ai_context: Dict[str, Any],
    conv_ctx: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Context-aware analytical parser mapping natural language & conversational references
    ('it', 'its', 'compare it with South', 'which product is driving that difference')
    to strictly validated Pandas execution plans.
    """
    q = question.lower().strip()
    conv_ctx = conv_ctx or {}
    active_entity = conv_ctx.get("active_entity")
    comparison_entities = conv_ctx.get("comparison_entities")
    last_filter = conv_ctx.get("active_filter")

    columns_info = ai_context.get("columns_info", [])
    col_names = [c["name"] for c in columns_info]
    num_cols = ai_context.get("numeric_columns", [])
    cat_cols = ai_context.get("categorical_columns", [])
    date_cols = ai_context.get("date_columns", [])

    # Identify pronouns / references
    has_pronoun = bool(re.search(r'\b(it|its|they|them|that|this|those)\b', q))

    # ---------------------------------------------------------
    # RULE 9: Gemini must not invent context
    # If pronoun is used without antecedent in context -> Clarification
    # ---------------------------------------------------------
    if has_pronoun and not active_entity and not comparison_entities:
        if not any(cat in q for cat in ["product", "region", "category", "sales", "revenue", "order"]):
            return {
                "need_clarification": True,
                "answer": "I'm not sure what you'd like me to analyze. Which product or region do you mean?",
                "context_used": False
            }

    # 1. Driver Analysis Query: "Which product is driving that difference?" or "what drives the gap"
    if any(k in q for k in ["driving that difference", "driving the difference", "driving that gap", "what drives the difference", "driving difference"]):
        comp = comparison_entities or ["East", "South"]
        return {
            "intent": "driver_analysis",
            "analysis": f"Product-level variance breakdown between {comp[0]} and {comp[1]}",
            "operation": "driver_analysis",
            "dimension": "product",
            "compare_column": "region",
            "comparison_entities": comp,
            "target_column": "revenue",
            "context_used": True,
            "active_entity": active_entity,
            "visualization": {
                "type": "bar",
                "title": f"Revenue Difference by Product: {comp[0]} vs {comp[1]}",
                "x": "product",
                "y": "difference"
            }
        }

    # 2. Comparison Query: "Compare it with South." or "compare East vs South"
    if "compare" in q or " vs " in q or " versus " in q:
        target_entities = []
        # Check mentioned regions
        for r_name in ["east", "west", "north", "south"]:
            if r_name in q:
                target_entities.append(r_name.capitalize())

        # If user said "compare it with South", antecedent entity is active_entity
        if len(target_entities) == 1 and active_entity:
            prior_name = active_entity.get("name", "East")
            target_entities = [prior_name, target_entities[0]]
        elif len(target_entities) < 2 and active_entity:
            target_entities = [active_entity.get("name", "East"), "South"]
        elif not target_entities:
            target_entities = ["East", "South"]

        return {
            "intent": "comparison",
            "analysis": f"Comparative performance analysis between {target_entities[0]} and {target_entities[1]}",
            "operation": "comparison",
            "group_by": "region",
            "target_column": "revenue",
            "comparison_entities": target_entities,
            "context_used": True,
            "active_entity": active_entity,
            "visualization": {
                "type": "bar",
                "title": f"Revenue Comparison: {target_entities[0]} vs {target_entities[1]}",
                "x": "region",
                "y": "revenue"
            }
        }

    # 3. Contextual Follow-up Monthly Trend: "Show me its monthly trend." / "Show its sales"
    if any(k in q for k in ["trend", "monthly", "over time"]) and has_pronoun and active_entity:
        entity_name = active_entity.get("name", "East")
        entity_col = active_entity.get("column", "region")
        date_col = date_cols[0] if date_cols else "date"

        return {
            "intent": "trend",
            "analysis": f"Monthly revenue trend for {entity_name}",
            "operation": "date_grouping",
            "group_by": date_col,
            "target_column": "revenue",
            "agg_func": "sum",
            "date_freq": "M",
            "filter": {entity_col: entity_name},
            "context_used": True,
            "active_entity": active_entity,
            "columns": [date_col, "revenue"],
            "visualization": {
                "type": "line",
                "title": f"Monthly Revenue for {entity_name} Over Time",
                "x": "period",
                "y": "revenue"
            }
        }

    # 4. Standard Date / Monthly queries without pronoun
    if any(kw in q for kw in ["month", "monthly", "trend", "over time", "timeline", "daily", "year"]) and not has_pronoun:
        date_col = date_cols[0] if date_cols else next((c for c in col_names if "date" in c.lower()), "date")
        target_col = "revenue"
        chart_type = "area" if "area" in q or "volume" in q else "line"
        return {
            "intent": "trend",
            "analysis": f"Monthly {target_col} trend over time",
            "operation": "date_grouping",
            "group_by": date_col,
            "target_column": target_col,
            "agg_func": "sum",
            "date_freq": "M",
            "columns": [date_col, target_col],
            "context_used": False,
            "visualization": {
                "type": chart_type,
                "title": f"Monthly {target_col.title()} Over Time",
                "x": "period",
                "y": target_col
            }
        }

    # 5. Top K queries (e.g. "Show me the top 5 products.", "top 10")
    if "top" in q or "best" in q or "highest" in q or "lowest" in q:
        top_match = re.search(r"top\s*(\d+)", q)
        limit = int(top_match.group(1)) if top_match else 10
        sort_order = "asc" if any(w in q for w in ["declining", "lowest", "least", "bottom", "worst"]) else "desc"

        # Determine target dimension
        group_col = "product"
        if "region" in q:
            group_col = "region"
        elif "rep" in q or "salesperson" in q:
            group_col = "sales_rep"
        elif "customer" in q:
            group_col = "customer"
        elif "category" in q:
            group_col = "category"

        target_col = "revenue"
        for nc in num_cols:
            if nc.lower() in q:
                target_col = nc
                break

        return {
            "intent": "ranking",
            "analysis": f"Top {limit} {group_col}s ranked by {target_col}",
            "operation": "groupby",
            "group_by": group_col,
            "target_column": target_col,
            "agg_func": "sum",
            "sort_order": sort_order,
            "limit": limit,
            "columns": [group_col, target_col],
            "context_used": False,
            "visualization": {
                "type": "bar",
                "title": f"Top {limit} {group_col.title()}s by {target_col.title()}",
                "x": group_col,
                "y": target_col
            }
        }

    # 6. Average / Statistical single-value query
    if any(kw in q for kw in ["average", "mean", "median", "quantity sold", "order value"]) and not any(kw in q for kw in [" by ", " each ", " per "]):
        agg = "mean"
        if "median" in q:
            agg = "median"
        elif "min" in q or "lowest" in q:
            agg = "min"
        elif "max" in q:
            agg = "max"

        target_col = "quantity" if "quantity" in q else ("revenue" if "order value" in q or "revenue" in q else (num_cols[0] if num_cols else "quantity"))
        return {
            "intent": "summary_statistic",
            "analysis": f"Dataset-wide {agg} of {target_col}",
            "operation": "summary_statistic",
            "group_by": None,
            "target_column": target_col,
            "agg_func": agg,
            "columns": [target_col],
            "context_used": False,
            "visualization": {
                "type": "metric",
                "title": f"Average {target_col.title()}",
                "x": target_col,
                "y": "value"
            }
        }

    # 6b. Correlation Query
    if "correlation" in q or "correlat" in q:
        found_num = [c for c in num_cols if c.lower() in q]
        col1 = found_num[0] if len(found_num) > 0 else (num_cols[0] if len(num_cols) > 0 else "quantity")
        col2 = found_num[1] if len(found_num) > 1 else (num_cols[1] if len(num_cols) > 1 else "revenue")
        return {
            "intent": "correlation",
            "analysis": f"Pearson correlation between {col1} and {col2}",
            "operation": "correlation",
            "group_by": col1,
            "target_column": col2,
            "columns": [col1, col2],
            "context_used": False,
            "visualization": {
                "type": "scatter",
                "title": f"Correlation: {col1.title()} vs {col2.title()}",
                "x": col1,
                "y": col2
            }
        }

    # 7. Default Categorical Groupby Query
    group_col = "product"
    if "region" in q:
        group_col = "region"
    elif "customer" in q:
        group_col = "customer"
    elif "category" in q:
        group_col = "category"
    elif "rep" in q:
        group_col = "sales_rep"

    target_col = "revenue"
    return {
        "intent": "aggregation",
        "analysis": f"{target_col.capitalize()} grouped by {group_col}",
        "operation": "groupby",
        "group_by": group_col,
        "target_column": target_col,
        "agg_func": "sum",
        "sort_order": "desc",
        "limit": 10,
        "columns": [group_col, target_col],
        "context_used": False,
        "visualization": {
            "type": "bar",
            "title": f"{target_col.title()} by {group_col.title()}",
            "x": group_col,
            "y": target_col
        }
    }


async def plan_analysis_with_gemini(
    question: str,
    ai_context: Dict[str, Any],
    conv_ctx: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Connect to Google Gemini Python SDK (google-genai) to formulate the analysis plan,
    incorporating conversational context summary and strict safety boundaries.
    """
    api_key = os.environ.get("GEMINI_API_KEY", "").strip()
    model_name = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash").strip()
    conv_ctx = conv_ctx or {}

    # Check Rule 9 directly:
    q_lower = question.lower().strip()
    has_pronoun = bool(re.search(r'\b(it|its|they|them|that|this|those)\b', q_lower))
    active_entity = conv_ctx.get("active_entity")
    comp_entities = conv_ctx.get("comparison_entities")

    if has_pronoun and not active_entity and not comp_entities:
        if not any(k in q_lower for k in ["product", "region", "category", "sales", "revenue"]):
            return {
                "need_clarification": True,
                "answer": "I'm not sure what you'd like me to analyze. Which product or region do you mean?",
                "context_used": False
            }

    if not api_key or api_key == "your_new_key_here":
        app_logger.info("Using built-in deterministic semantic planner (GEMINI_API_KEY not configured).")
        return semantic_rule_planner(question, ai_context, conv_ctx)

    try:
        from google import genai
        from google.genai import types
        from app.models.analysis_plan import GeminiAnalysisPlanModel
        from app.core.security import gemini_rate_limiter, execute_with_timeout

        # Rate limiting check
        client_ip = conv_ctx.get("client_ip", "default_client")
        await gemini_rate_limiter.acquire(client_ip)

        client = genai.Client(api_key=api_key)

        prompt = f"""
You are the AI Data Analyst for InsightForge AI.
The user is asking a conversational question about a structured dataset.

DATASET SCHEMA & SUMMARY:
{json.dumps(ai_context, indent=2)}

CONVERSATION CONTEXT:
{json.dumps(conv_ctx, indent=2)}

USER QUESTION:
"{question}"

IMPORTANT CONTEXTUAL RESOLUTION RULES:
1. If the user refers to "it", "its", "that region", "this product", resolve it using active_entity or comparison_entities in CONVERSATION CONTEXT.
2. If the user asks "Compare it with South" and previous active entity is "East", plan a "comparison" operation with entities ["East", "South"].
3. If the user asks "Which product is driving that difference?", plan a "driver_analysis" operation with comparison_entities ["East", "South"] and dimension="product".
4. If the user refers to "it" but there is NO active entity in CONVERSATION CONTEXT, set "need_clarification": true and "answer": "I'm not sure what you'd like me to analyze. Which product or region do you mean?".

Generate a strictly valid JSON analysis plan conforming to this schema:
{{
  "intent": "aggregation" | "ranking" | "trend" | "summary_statistic" | "correlation" | "distribution" | "comparison" | "driver_analysis",
  "analysis": "Concise summary of the analysis to perform",
  "operation": "groupby" | "date_grouping" | "comparison" | "driver_analysis" | "summary_statistic" | "scatter" | "histogram" | "correlation",
  "columns": ["list", "of", "relevant", "columns"],
  "group_by": "categorical_or_date_column_or_null",
  "target_column": "numeric_column_name_to_compute",
  "agg_func": "sum" | "mean" | "median" | "count" | "min" | "max",
  "comparison_entities": ["Entity1", "Entity2"] (if comparison or driver_analysis),
  "filter": {{"column_name": "entity_value"}} (if filtering to a single entity),
  "dimension": "product" (sub-dimension for driver_analysis),
  "date_freq": "M",
  "sort_order": "desc" | "asc",
  "limit": 5 or 10 or null,
  "need_clarification": false,
  "context_used": true | false,
  "visualization": {{
    "type": "bar" | "line" | "area" | "pie" | "scatter" | "histogram" | "metric",
    "title": "Clean concise chart title",
    "x": "x_axis_column_or_dimension",
    "y": "y_axis_column_or_metric"
  }}
}}
Return ONLY JSON. Do not include markdown codeblocks or preamble.
"""
        async def call_gemini():
            return client.models.generate_content(
                model=model_name,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    temperature=0.1
                )
            )

        # Enforce 30s timeout boundary
        response = await execute_with_timeout(call_gemini(), timeout_seconds=30.0, task_name="Gemini Analysis Planning")

        clean_text = response.text.strip()
        if clean_text.startswith("```"):
            clean_text = re.sub(r"^```(?:json)?\s*", "", clean_text)
            clean_text = re.sub(r"\s*```$", "", clean_text)

        parsed_raw = json.loads(clean_text)
        
        # Pydantic Output Validation (Reject malformed or unexpected responses)
        validated_plan = GeminiAnalysisPlanModel.model_validate(parsed_raw)
        app_logger.info(f"Gemini analysis plan successfully validated for query: '{question[:40]}'")
        return validated_plan.model_dump()
    except Exception as exc:
        app_logger.warning(f"Gemini planning failed or rejected validation: {exc}. Safely falling back to deterministic semantic rule planner.")
        return semantic_rule_planner(question, ai_context, conv_ctx)
