from __future__ import annotations

import os
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()


@dataclass
class Config:
    llm_provider: str
    llm_model: str
    openrouter_api_key: str
    openrouter_base_url: str
    opencode_base_url: str
    opencode_api_key: str
    opencode_model: str
    total_ticks: int
    action_probability: float
    log_path: str
    log_events: bool

    @classmethod
    def load(cls) -> "Config":
        return cls(
            llm_provider=os.getenv("LLM_PROVIDER", "openrouter"),
            llm_model=os.getenv("LLM_MODEL", ""),
            openrouter_api_key=os.getenv("OPENROUTER_API_KEY", ""),
            openrouter_base_url=os.getenv(
                "OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1"
            ),
            opencode_base_url=os.getenv("OPENCODE_BASE_URL", "http://localhost:8080/v1"),
            opencode_api_key=os.getenv("OPENCODE_API_KEY", "dummy"),
            opencode_model=os.getenv("OPENCODE_MODEL", "default"),
            total_ticks=int(os.getenv("TOTAL_TICKS", "100")),
            action_probability=float(os.getenv("ACTION_PROBABILITY", "0.7")),
            log_path=os.getenv("LOG_PATH", "logs"),
            log_events=os.getenv("LOG_EVENTS", "true").lower() == "true",
        )

    def resolve_model(self) -> str:
        if self.llm_model:
            return self.llm_model
        if self.llm_provider == "openrouter":
            return os.getenv("OPENROUTER_MODEL", "anthropic/claude-3.5-sonnet")
        if self.llm_provider == "opencode":
            return self.opencode_model
        return "anthropic/claude-3.5-sonnet"
