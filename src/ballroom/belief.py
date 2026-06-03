from __future__ import annotations

import math
from pydantic import BaseModel, Field


class BeliefVector(BaseModel):
    positions: dict[str, float] = Field(default_factory=dict)
    confidence: dict[str, float] = Field(default_factory=dict)
    load_bearing: dict[str, bool] = Field(default_factory=dict)

    def set(
        self,
        topic: str,
        position: float,
        confidence: float = 0.5,
        load_bearing: bool = False,
    ) -> None:
        self.positions[topic] = max(-1.0, min(1.0, position))
        self.confidence[topic] = max(0.0, min(1.0, confidence))
        self.load_bearing[topic] = load_bearing

    def update(
        self,
        topic: str,
        evidence: float,
        trust: float = 0.5,
        learning_rate: float = 0.1,
    ) -> None:
        if topic not in self.positions:
            self.positions[topic] = 0.0
            self.confidence[topic] = 0.5
            self.load_bearing[topic] = False

        load_factor = 0.3 if self.load_bearing.get(topic, False) else 1.0
        delta = evidence * trust * learning_rate * load_factor
        self.positions[topic] = max(-1.0, min(1.0, self.positions[topic] + delta))
        self.confidence[topic] = self.confidence[topic] * 0.99 + abs(evidence) * 0.05
        self.confidence[topic] = max(0.1, min(1.0, self.confidence[topic]))

    def get(self, topic: str) -> float:
        return self.positions.get(topic, 0.0)

    def confidence_for(self, topic: str) -> float:
        return self.confidence.get(topic, 0.5)

    def is_load_bearing(self, topic: str) -> bool:
        return self.load_bearing.get(topic, False)

    def distance_to(self, other: "BeliefVector") -> float:
        shared = set(self.positions.keys()) & set(other.positions.keys())
        if not shared:
            return 0.0
        total = sum(
            (self.positions[t] - other.positions[t]) ** 2 for t in shared
        )
        return math.sqrt(total) / math.sqrt(len(shared))

    def topics(self) -> list[str]:
        return sorted(self.positions.keys())

    def to_prompt(self) -> str:
        if not self.positions:
            return "  (no established beliefs yet)"
        lines = []
        for topic in sorted(self.positions.keys()):
            pos = self.positions[topic]
            conf = self.confidence.get(topic, 0.5)
            load = " [load-bearing]" if self.load_bearing.get(topic, False) else ""
            direction = "+" if pos > 0 else "-" if pos < 0 else "0"
            intensity = (
                "strongly"
                if abs(pos) > 0.6
                else "moderately"
                if abs(pos) > 0.3
                else "slightly"
            )
            stance = (
                "supportive"
                if pos > 0
                else "opposed"
                if pos < 0
                else "neutral"
            )
            lines.append(
                f"  {topic}: {direction}{abs(pos):.2f} "
                f"({intensity} {stance}, confidence: {conf:.2f}){load}"
            )
        return "\n".join(lines)
