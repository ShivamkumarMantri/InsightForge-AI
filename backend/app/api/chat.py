import re
from fastapi import APIRouter, Request, status
from pydantic import BaseModel, Field, field_validator
from typing import Optional, List, Dict, Any
from app.data.storage import get_dataset
from app.services.profiler import generate_ai_context
from app.agents.conversation_manager import (
    get_or_create_conversation,
    get_conversation,
    list_conversations,
    delete_conversation
)
from app.agents.gemini_analyst import plan_analysis_with_gemini, generate_contextual_suggestions
from app.execution.safe_executor import execute_analysis_plan
from app.core.errors import DatasetNotFoundException, InsightForgeAPIException
from app.core.logging import app_logger
from app.core.security import execute_with_timeout

router = APIRouter(prefix="/api/chat", tags=["Conversational AI Analyst"])

class ChatRequest(BaseModel):
    dataset_id: str = Field(..., min_length=5, max_length=100, description="Unique dataset ID")
    conversation_id: Optional[str] = Field(None, max_length=100, description="Existing conversation session ID or null for new")
    message: str = Field(..., min_length=1, max_length=1000, description="User conversational prompt or follow-up question")

    @field_validator("dataset_id")
    def validate_dataset_id(cls, v: str) -> str:
        if not re.match(r"^[a-zA-Z0-9_-]+$", v):
            raise ValueError("Dataset ID must contain only alphanumeric characters, underscores, and hyphens.")
        return v

    @field_validator("conversation_id")
    def validate_conv_id(cls, v: Optional[str]) -> Optional[str]:
        if v and not re.match(r"^[a-zA-Z0-9_-]+$", v):
            raise ValueError("Conversation ID must contain only alphanumeric characters, underscores, and hyphens.")
        return v

@router.post("", status_code=status.HTTP_200_OK)
@router.post("/", status_code=status.HTTP_200_OK, include_in_schema=False)
async def chat_with_analyst(req_data: ChatRequest, request: Request):
    """
    Conversational analysis endpoint maintaining context across queries:
    1. Loads or initializes conversation session.
    2. Retrieves active context summary.
    3. Resolves referential pronouns ('it', 'its', 'compare it with South').
    4. Executes approved Pandas analysis safely with Pydantic validation.
    5. Stores user & assistant turns in session memory.
    6. Dynamically derives follow-up suggestions based on findings.
    """
    entry = get_dataset(req_data.dataset_id)
    if not entry:
        raise DatasetNotFoundException(req_data.dataset_id)

    df = entry["df"]
    filename = entry["filename"]

    # 1. Retrieve or initialize conversation
    conv = get_or_create_conversation(req_data.conversation_id, req_data.dataset_id, filename)
    conv.add_user_message(req_data.message)

    try:
        # 2. Extract compact schema and active conversational context summary
        ai_context = generate_ai_context(df, filename)
        conv_summary = conv.get_context_summary()
        conv_summary["client_ip"] = request.client.host if request.client else "unknown"

        # 3. Plan analysis with conversational awareness + Pydantic validation + timeout
        plan = await execute_with_timeout(
            plan_analysis_with_gemini(req_data.message, ai_context, conv_summary),
            timeout_seconds=30.0,
            task_name="Conversational AI planning"
        )

        # 4. Safely execute Pandas operation
        execution_result = execute_analysis_plan(df, plan)

        # 5. Generate 2-3 dynamic contextual suggestions
        top_item = execution_result.get("top_item")
        suggestions = generate_contextual_suggestions(plan, top_item, conv_summary)

        context_used = bool(plan.get("context_used") or execution_result.get("context_used"))

        response_payload = {
            "success": True,
            "conversation_id": conv.conversation_id,
            "dataset_id": req_data.dataset_id,
            "filename": filename,
            "message": req_data.message,
            "answer": execution_result.get("answer", execution_result.get("key_insight")),
            "insight": execution_result.get("insight", execution_result.get("key_insight")),
            "key_metric": execution_result.get("key_metric", "-"),
            "why_it_matters": execution_result.get("why_it_matters", ""),
            "data": execution_result.get("data", []),
            "visualization": execution_result.get("visualization", {}),
            "context_used": context_used,
            "suggestions": suggestions,
            "calculation_steps": execution_result.get("calculation_steps", []),
            "top_item": execution_result.get("top_item"),
            "active_context": conv.active_context,
            "plan": plan
        }

        # 6. Record turn into conversation state
        conv.add_assistant_message(response_payload)

        app_logger.info(
            f"Chat turn executed for session '{conv.conversation_id[:8]}...': '{req_data.message[:40]}'",
            extra={"extra_data": {"dataset_id": req_data.dataset_id, "operation": plan.get("operation")}}
        )

        return response_payload
    except InsightForgeAPIException:
        raise
    except Exception as exc:
        app_logger.error(f"Error during conversational turn: {exc}", exc_info=True)
        raise InsightForgeAPIException(
            message="An error occurred while analyzing your conversational query. Please try rephrasing.",
            code="CHAT_EXECUTION_ERROR",
            status_code=500
        )

@router.get("/history", status_code=status.HTTP_200_OK)
def get_recent_conversations(dataset_id: Optional[str] = None):
    """List recent conversation sessions."""
    return list_conversations(dataset_id)

@router.get("/{conversation_id}", status_code=status.HTTP_200_OK)
def get_conversation_session(conversation_id: str):
    """Retrieve full message history for a specific conversation session."""
    conv = get_conversation(conversation_id)
    if not conv:
        raise InsightForgeAPIException(
            message=f"Conversation session '{conversation_id}' was not found.",
            code="CONVERSATION_NOT_FOUND",
            status_code=404
        )
    return conv.to_dict()

@router.delete("/{conversation_id}", status_code=status.HTTP_200_OK)
def clear_conversation_session(conversation_id: str):
    """Clear conversation session from memory."""
    success = delete_conversation(conversation_id)
    if not success:
        raise InsightForgeAPIException(
            message=f"Conversation session '{conversation_id}' was not found.",
            code="CONVERSATION_NOT_FOUND",
            status_code=404
        )
    return {"success": True, "conversation_id": conversation_id}
