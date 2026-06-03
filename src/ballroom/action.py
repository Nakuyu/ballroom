from __future__ import annotations

from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field, field_validator


class ActionType(str, Enum):
    POST = "POST"
    COMMENT = "COMMENT"
    LIKE = "LIKE"
    FOLLOW = "FOLLOW"
    UNFOLLOW = "UNFOLLOW"
    IGNORE = "IGNORE"


class Action(BaseModel):
    type: ActionType
    target_id: Optional[str] = None
    content: Optional[str] = None
    reasoning: str = ""
    confidence: float = 1.0

    @field_validator("type", mode="before")
    @classmethod
    def _upper(cls, v):
        if isinstance(v, str):
            return v.upper()
        return v

    @classmethod
    def from_llm(cls, response: dict) -> "Action":
        raw_type = str(response.get("action", "IGNORE")).upper()
        try:
            action_type = ActionType(raw_type)
        except ValueError:
            action_type = ActionType.IGNORE
        return cls(
            type=action_type,
            target_id=response.get("target_id") or response.get("target"),
            content=response.get("content"),
            reasoning=response.get("reasoning", ""),
            confidence=float(response.get("confidence", 1.0)),
        )

    def is_valid(self) -> bool:
        if self.type in (ActionType.POST, ActionType.COMMENT):
            return bool(self.content and self.content.strip())
        if self.type in (ActionType.LIKE, ActionType.FOLLOW, ActionType.UNFOLLOW):
            return bool(self.target_id)
        return True


def build_action_schema() -> dict:
    return {
        "type": "object",
        "properties": {
            "action": {
                "type": "string",
                "enum": [t.value for t in ActionType],
            },
            "target_id": {"type": ["string", "null"]},
            "content": {"type": ["string", "null"]},
            "reasoning": {"type": "string"},
            "confidence": {"type": "number", "minimum": 0, "maximum": 1},
        },
        "required": ["action", "reasoning"],
        "additionalProperties": False,
    }
