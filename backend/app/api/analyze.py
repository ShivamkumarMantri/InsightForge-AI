import re
from fastapi import APIRouter, Request, status
from pydantic import BaseModel, Field, field_validator
from app.data.storage import get_dataset
from app.services.profiler import generate_ai_context
from app.agents.gemini_analyst import plan_analysis_with_gemini
from app.execution.safe_executor import execute_analysis_plan
from app.core.errors import DatasetNotFoundException, InsightForgeAPIException
from app.core.logging import app_logger
from app.core.security import execute_with_timeout

router = APIRouter(prefix="/api", tags=["AI Analyst"])

class AnalyzeRequest(BaseModel):
    dataset_id: str = Field(..., min_length=5, max_length=100, description="Unique dataset ID")
    question: str = Field(..., min_length=2, max_length=1000, description="Natural language analytical query")

    @field_validator("dataset_id")
    def validate_id(cls, v: str) -> str:
        if not re.match(r"^[a-zA-Z0-9_-]+$", v):
            raise ValueError("Dataset ID must contain only alphanumeric characters, underscores, and hyphens.")
        return v

@router.post("/analyze", status_code=status.HTTP_200_OK)
async def analyze_dataset(req_data: AnalyzeRequest, request: Request):
    """
    Execute AI-guided natural language data analysis securely:
    1. Loads dataset from storage.
    2. Builds compact schema/profile context for Gemini.
    3. Gemini formulates a structured analysis plan validated with Pydantic.
    4. Safe execution engine runs only approved Pandas operations.
    5. Returns verified insights, calculations, and visualization specification.
    """
    entry = get_dataset(req_data.dataset_id)
    if not entry:
        raise DatasetNotFoundException(req_data.dataset_id)

    df = entry["df"]
    filename = entry["filename"]

    if df.empty or len(df.columns) == 0:
        raise InsightForgeAPIException(
            message="The active dataset contains no rows or columns to analyze.",
            code="EMPTY_DATASET",
            status_code=400
        )

    try:
        # 1. Compact schema context
        ai_context = generate_ai_context(df, filename)

        # 2. Plan analysis with Gemini + Pydantic validation + timeout
        conv_ctx = {"client_ip": request.client.host if request.client else "unknown"}
        plan = await execute_with_timeout(
            plan_analysis_with_gemini(req_data.question, ai_context, conv_ctx),
            timeout_seconds=30.0,
            task_name="Natural language query analysis"
        )

        # 3. Execute plan safely with Pandas
        execution_result = execute_analysis_plan(df, plan)

        app_logger.info(
            f"Query analyzed for {filename}: '{req_data.question[:40]}'",
            extra={"extra_data": {"dataset_id": req_data.dataset_id, "operation": plan.get("operation")}}
        )

        # Combine into complete analytical payload
        return {
            "success": True,
            "dataset_id": req_data.dataset_id,
            "filename": filename,
            "question": req_data.question,
            "answer": execution_result.get("answer", execution_result.get("key_insight")),
            "insight": execution_result.get("insight", execution_result.get("key_insight")),
            "key_metric": execution_result.get("key_metric", execution_result.get("summary_value")),
            "why_it_matters": execution_result.get("why_it_matters", "Significant data driver within the analyzed dataset."),
            "data": execution_result.get("data", execution_result.get("result_table", [])),
            "visualization": execution_result["visualization"],
            "calculation_steps": execution_result.get("calculation_steps", []),
            "plan": {
                "intent": plan.get("intent", "aggregation"),
                "analysis": plan.get("analysis", "Pandas Analytical Query"),
                "operation": plan.get("operation", "groupby"),
                "columns": plan.get("columns", []),
                "visualization": execution_result["visualization"]
            },
            # Backwards compatibility
            "legacy_answer": {
                "key_insight": execution_result.get("insight", execution_result.get("key_insight")),
                "calculation_explanation": execution_result.get("calculation_explanation"),
                "summary_value": execution_result.get("key_metric", execution_result.get("summary_value")),
                "top_item": execution_result.get("top_item"),
                "result_table": execution_result.get("data", [])
            }
        }
    except InsightForgeAPIException:
        raise
    except Exception as exc:
        app_logger.error(f"Error during AI analysis of '{req_data.dataset_id}': {exc}", exc_info=True)
        raise InsightForgeAPIException(
            message="An error occurred while executing the analytical query. Please verify the question and try again.",
            code="ANALYSIS_EXECUTION_ERROR",
            status_code=500
        )
