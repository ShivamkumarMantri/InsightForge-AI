import os
import uuid
import datetime
from typing import Dict, Any, List, Optional

class Conversation:
    def __init__(self, conversation_id: str, dataset_id: str, filename: str = "dataset.csv"):
        self.conversation_id = conversation_id
        self.dataset_id = dataset_id
        self.filename = filename
        self.created_at = datetime.datetime.now().isoformat()
        self.updated_at = datetime.datetime.now().isoformat()
        self.messages: List[Dict[str, Any]] = []
        # Active context tracked across conversation turns
        self.active_context: Dict[str, Any] = {
            "active_entity": None,          # e.g. {"type": "region", "name": "East", "column": "region"}
            "comparison_entities": None,    # e.g. ["East", "South"]
            "active_dimension": None,       # e.g. "region"
            "active_metric": "revenue",     # e.g. "revenue"
            "active_filter": None,          # e.g. {"region": "East"}
            "last_operation": None,         # e.g. "groupby" | "date_grouping" | "comparison"
            "last_question": None,
            "last_answer": None,
            "last_top_item": None
        }

    def add_user_message(self, text: str) -> Dict[str, Any]:
        msg_id = str(uuid.uuid4())
        msg = {
            "id": msg_id,
            "role": "user",
            "text": text,
            "timestamp": datetime.datetime.now().isoformat()
        }
        self.messages.append(msg)
        self.updated_at = datetime.datetime.now().isoformat()
        self.active_context["last_question"] = text
        return msg

    def add_assistant_message(self, analysis_result: Dict[str, Any]) -> Dict[str, Any]:
        msg_id = str(uuid.uuid4())
        msg = {
            "id": msg_id,
            "role": "assistant",
            "text": analysis_result.get("answer", ""),
            "timestamp": datetime.datetime.now().isoformat(),
            "analysis": analysis_result
        }
        self.messages.append(msg)
        self.updated_at = datetime.datetime.now().isoformat()
        self.active_context["last_answer"] = analysis_result.get("answer")

        # Update active entities and context from the analysis plan
        plan = analysis_result.get("plan", {})
        top_item = analysis_result.get("top_item")
        if not top_item:
            # Check data rows if available
            data = analysis_result.get("data", [])
            if data and isinstance(data, list) and len(data) > 0 and isinstance(data[0], dict):
                group_col = plan.get("group_by") or plan.get("dimension")
                top_item = data[0].get("name") or (data[0].get(group_col) if group_col else None)

        # Ignore if top_item looks like a pure metric string ($30.63M, etc.)
        if top_item and any(str(top_item).startswith(p) for p in ["$", "+$", "-$", "%"]):
            top_item = None

        # Update active entity if plan specified or result revealed a top entity
        if plan.get("active_entity") and isinstance(plan.get("active_entity"), dict) and plan.get("active_entity").get("name"):
            self.active_context["active_entity"] = plan["active_entity"]
        elif (plan.get("group_by") or plan.get("dimension")) and top_item and str(top_item).lower() != "none":
            dim = plan.get("group_by") or plan.get("dimension")
            self.active_context["active_entity"] = {
                "type": dim,
                "name": str(top_item),
                "column": dim
            }
            self.active_context["active_dimension"] = dim

        if plan.get("comparison_entities"):
            self.active_context["comparison_entities"] = plan["comparison_entities"]

        if plan.get("target_column"):
            self.active_context["active_metric"] = plan["target_column"]

        if plan.get("filter"):
            self.active_context["active_filter"] = plan["filter"]
        elif plan.get("operation") == "groupby" and not plan.get("filter"):
            # Clear filter if a general groupby query occurred
            pass

        if plan.get("operation"):
            self.active_context["last_operation"] = plan["operation"]

        return msg

    def get_context_summary(self) -> Dict[str, Any]:
        """Compact summary of active context passed to Gemini instead of raw full history."""
        # Retrieve last 2 turns
        recent_turns = []
        for m in self.messages[-4:]:
            recent_turns.append({
                "role": m["role"],
                "text": m["text"]
            })

        return {
            "active_entity": self.active_context.get("active_entity"),
            "comparison_entities": self.active_context.get("comparison_entities"),
            "active_dimension": self.active_context.get("active_dimension"),
            "active_metric": self.active_context.get("active_metric", "revenue"),
            "active_filter": self.active_context.get("active_filter"),
            "last_operation": self.active_context.get("last_operation"),
            "last_question": self.active_context.get("last_question"),
            "last_answer": self.active_context.get("last_answer"),
            "recent_turns": recent_turns
        }

    def to_dict(self) -> Dict[str, Any]:
        return {
            "conversation_id": self.conversation_id,
            "dataset_id": self.dataset_id,
            "filename": self.filename,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "message_count": len(self.messages),
            "messages": self.messages,
            "active_context": self.active_context
        }


# Global in-memory conversation registry
_CONVERSATIONS: Dict[str, Conversation] = {}

def get_or_create_conversation(
    conversation_id: Optional[str],
    dataset_id: str,
    filename: str = "dataset.csv"
) -> Conversation:
    """Retrieve existing conversation or create a new initialized conversation."""
    if conversation_id and conversation_id in _CONVERSATIONS:
        conv = _CONVERSATIONS[conversation_id]
        if dataset_id and conv.dataset_id != dataset_id:
            conv.dataset_id = dataset_id
            conv.filename = filename
        return conv

    new_id = conversation_id or str(uuid.uuid4())
    conv = Conversation(conversation_id=new_id, dataset_id=dataset_id, filename=filename)
    _CONVERSATIONS[new_id] = conv
    return conv

def get_conversation(conversation_id: str) -> Optional[Conversation]:
    return _CONVERSATIONS.get(conversation_id)

def list_conversations(dataset_id: Optional[str] = None) -> List[Dict[str, Any]]:
    """List recent conversation sessions with metadata."""
    results = []
    for conv in sorted(_CONVERSATIONS.values(), key=lambda c: c.updated_at, reverse=True):
        if dataset_id and conv.dataset_id != dataset_id:
            continue
        last_question = conv.active_context.get("last_question")
        if not last_question and conv.messages:
            last_question = conv.messages[-1].get("text", "")
        results.append({
            "conversation_id": conv.conversation_id,
            "dataset_id": conv.dataset_id,
            "filename": conv.filename,
            "last_question": last_question or "New session",
            "updated_at": conv.updated_at,
            "turns_count": len(conv.messages)
        })
    return results

def delete_conversation(conversation_id: str) -> bool:
    if conversation_id in _CONVERSATIONS:
        del _CONVERSATIONS[conversation_id]
        return True
    return False
