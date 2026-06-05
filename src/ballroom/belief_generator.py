from __future__ import annotations

import json
import random
from pathlib import Path
from typing import Optional

from .belief import BeliefVector


def load_topics(data_dir: Path) -> list[dict]:
    topics_file = data_dir / "topics.json"
    if not topics_file.exists():
        return []
    with open(topics_file) as f:
        return json.load(f).get("topics", [])


def load_faction_defaults(data_dir: Path) -> dict[str, dict[str, float]]:
    defaults_file = data_dir / "faction_defaults.json"
    if not defaults_file.exists():
        return {}
    with open(defaults_file) as f:
        return json.load(f)


def generate_beliefs(
    faction: Optional[str],
    overrides: dict[str, float],
    load_bearing: list[str],
    faction_defaults: dict[str, dict[str, float]],
    topics: list[dict],
    noise: float = 0.1,
) -> BeliefVector:
    beliefs = BeliefVector()

    faction_pos = faction_defaults.get(faction, {}) if faction else {}

    for topic_def in topics:
        topic = topic_def["name"]
        base = faction_pos.get(topic, 0.0)
        override = overrides.get(topic, 0.0)

        if topic in overrides:
            position = override
        else:
            position = base + random.uniform(-noise, noise)

        position = max(-1.0, min(1.0, position))

        confidence = 0.5 + abs(position) * 0.3 + random.uniform(-0.1, 0.1)
        confidence = max(0.1, min(1.0, confidence))

        beliefs.set(
            topic,
            position,
            confidence=confidence,
            load_bearing=topic in load_bearing,
        )

    return beliefs
