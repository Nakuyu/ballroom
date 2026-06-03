from __future__ import annotations

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field

from .belief import BeliefVector


class Memory(BaseModel):
    timestamp: datetime
    event_type: str
    subject: str
    content: str
    sentiment: float = 0.0
    importance: float = 0.5


class Relationship(BaseModel):
    agent_id: str
    trust: float = 0.5
    sentiment: float = 0.0
    interactions: int = 0
    last_interaction: Optional[datetime] = None


class Agent(BaseModel):
    id: str
    name: str
    role: str
    faction: Optional[str] = None
    personality: dict = Field(default_factory=dict)
    goals: list[str] = Field(default_factory=list)
    identity: str = ""
    style: str = "measured"
    beliefs: BeliefVector = Field(default_factory=BeliefVector)
    memory: list[Memory] = Field(default_factory=list)
    relationships: dict[str, Relationship] = Field(default_factory=dict)
    following: set[str] = Field(default_factory=set)
    followers: set[str] = Field(default_factory=set)
    influence: float = 0.0
    post_count: int = 0
    comment_count: int = 0
    like_count: int = 0

    def remember(
        self,
        event_type: str,
        subject: str,
        content: str,
        sentiment: float = 0.0,
        importance: float = 0.5,
    ) -> None:
        mem = Memory(
            timestamp=datetime.now(),
            event_type=event_type,
            subject=subject,
            content=content,
            sentiment=sentiment,
            importance=importance,
        )
        self.memory.append(mem)
        if len(self.memory) > 100:
            self.memory = sorted(
                self.memory,
                key=lambda m: (m.importance, m.timestamp),
                reverse=True,
            )[:80]

    def get_relationship(self, other_id: str) -> Relationship:
        if other_id not in self.relationships:
            self.relationships[other_id] = Relationship(agent_id=other_id)
        return self.relationships[other_id]

    def update_relationship(
        self,
        other_id: str,
        trust_delta: float = 0.0,
        sentiment_delta: float = 0.0,
    ) -> None:
        rel = self.get_relationship(other_id)
        rel.trust = max(0.0, min(1.0, rel.trust + trust_delta))
        rel.sentiment = max(-1.0, min(1.0, rel.sentiment + sentiment_delta))
        rel.interactions += 1
        rel.last_interaction = datetime.now()

    def recent_memories(self, limit: int = 5) -> list[Memory]:
        return sorted(self.memory, key=lambda m: m.timestamp, reverse=True)[:limit]

    def persona_prompt(self) -> str:
        personality = ", ".join(
            f"{k}={v}" for k, v in self.personality.items()
        )
        goals = "\n".join(f"  - {g}" for g in self.goals) or "  (no explicit goals)"
        return (
            f"Name: {self.name}\n"
            f"Role: {self.role}\n"
            f"Faction: {self.faction or 'Independent'}\n"
            f"Identity: {self.identity}\n"
            f"Personality: {personality}\n"
            f"Speaking style: {self.style}\n"
            f"Goals:\n{goals}"
        )
