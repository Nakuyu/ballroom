from __future__ import annotations

import json
import os
import sys
import time
from typing import Optional

from openai import OpenAI

from .config import Config


class LLMClient:
    def __init__(self, config: Config, max_retries: int = 3):
        self.config = config
        self.provider = config.llm_provider
        self.model = config.resolve_model()
        self.client = self._build_client()
        self.max_retries = max_retries

    def _build_client(self) -> OpenAI:
        if self.provider == "openrouter":
            return OpenAI(
                base_url=self.config.openrouter_base_url,
                api_key=self.config.openrouter_api_key,
            )
        if self.provider == "opencode":
            return OpenAI(
                base_url=self.config.opencode_base_url,
                api_key=self.config.opencode_api_key,
            )
        raise ValueError(f"Unknown provider: {self.provider}")

    def chat(
        self,
        system: str,
        user: str,
        json_mode: bool = True,
        temperature: float = 0.7,
        max_tokens: int = 600,
    ) -> dict:
        messages = [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ]
        kwargs = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        if json_mode:
            kwargs["response_format"] = {"type": "json_object"}

        last_error = None
        for attempt in range(self.max_retries):
            try:
                response = self.client.chat.completions.create(**kwargs)
                content = response.choices[0].message.content
                if json_mode:
                    return self._parse_json(content)
                return {"content": content}
            except Exception as e:
                last_error = e
                if attempt < self.max_retries - 1:
                    delay = 2 ** attempt
                    time.sleep(delay)

        return {
            "action": "IGNORE",
            "reasoning": f"LLM call failed after {self.max_retries} attempts: {last_error}",
        }

    def _parse_json(self, content: str) -> dict:
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            pass
        start = content.find("{")
        end = content.rfind("}")
        if start >= 0 and end > start:
            try:
                return json.loads(content[start : end + 1])
            except json.JSONDecodeError:
                pass
        return {
            "action": "IGNORE",
            "reasoning": f"Failed to parse LLM response: {content[:80]}",
        }


class MockLLMClient:
    def __init__(self, config: Config):
        self.config = config
        self.model = "mock"

    def chat(
        self,
        system: str,
        user: str,
        json_mode: bool = True,
        temperature: float = 0.7,
        max_tokens: int = 600,
    ) -> dict:
        if "Should any of your beliefs shift" in user:
            return self._mock_belief_update()
        return self._heuristic_action(system, user)

    def _mock_belief_update(self) -> dict:
        import random

        updates = []
        topics = ["ai_safety", "open_source", "regulation", "deployment_speed", "human_replacement"]
        for topic in topics:
            if random.random() < 0.3:
                delta = random.uniform(-0.1, 0.1)
                updates.append({
                    "topic": topic,
                    "delta": round(delta, 2),
                    "reasoning": f"Mock: adjustment on {topic}"
                })
        return {"updates": updates}

    def _heuristic_action(self, system: str, user: str) -> dict:
        import random

        rand = random.random()
        post_match = "POST" in user.upper() and "feed" in user.lower()
        has_feed = "[1]" in user or "no posts" in user.lower()

        if rand < 0.45 and has_feed:
            return {
                "action": "POST",
                "content": self._stub_post(system),
                "reasoning": "Mock: generating a post to test the pipeline.",
                "confidence": 0.7,
            }
        if rand < 0.65 and "[1]" in user:
            return {
                "action": "COMMENT",
                "target_id": "p0",
                "content": self._stub_comment(system),
                "reasoning": "Mock: commenting on the top feed item.",
                "confidence": 0.6,
            }
        if rand < 0.78 and "[1]" in user:
            import random as rnd
            target = f"p{rnd.randint(0, 2)}"
            return {
                "action": "LIKE",
                "target_id": target,
                "reasoning": "Mock: liking a feed item.",
                "confidence": 0.5,
            }
        if rand < 0.88:
            import random as rnd
            candidates = ["alice", "bob", "carol", "dave", "eve", "frank"]
            target = rnd.choice(candidates)
            return {
                "action": "FOLLOW",
                "target_id": target,
                "reasoning": "Mock: following a peer.",
                "confidence": 0.5,
            }
        return {
            "action": "IGNORE",
            "reasoning": "Mock: staying silent this tick.",
            "confidence": 0.3,
        }

    def _stub_post(self, system: str) -> str:
        import random

        s = system.lower()
        if "engineer" in s or "founder" in s:
            options = [
                "Build fast, ship faster. Iteration beats perfection.",
                "Small teams can outcompete anyone if they move fast enough.",
                "Shipping beats planning. You can always iterate.",
                "Speed is a feature. Ship it and learn from real users.",
                "The best code is the code that actually ships.",
            ]
        elif "regulator" in s or "policy" in s or "researcher" in s:
            options = [
                "We need evidence before scale. Hasty decisions cause harm.",
                "Safety isn't the enemy of progress — recklessness is.",
                "The track record of unregulated tech is not encouraging.",
                "We need guardrails, not just velocity.",
                "Moving fast and breaking things is not a responsible approach to AI.",
            ]
        elif "designer" in s:
            options = [
                "Real users, real feedback. Everything else is speculation.",
                "We should talk to the people actually affected by this.",
                "If we don't understand the use cases, we're building blind.",
                "The best interfaces are invisible. The worst are confusing.",
            ]
        else:
            options = [
                "Thinking out loud here. What do others think?",
                "Interesting developments lately. Let's discuss.",
                "I have some thoughts on this but want to hear others first.",
            ]
        return random.choice(options)

    def _stub_comment(self, system: str) -> str:
        import random

        options = [
            "Strongly disagree. The evidence points the other way.",
            "I see it differently. Here's why...",
            "This ignores the broader context entirely.",
            "Interesting, but I think you're missing a key point.",
            "The data doesn't support this claim.",
            "Fair point, though I'd push back on a few things.",
            "This is exactly the kind of thinking we need more of.",
            "Not sure I agree. The tradeoffs are more complex than that.",
        ]
        return random.choice(options)
