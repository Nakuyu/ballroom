from __future__ import annotations

import argparse
import json
import os
import random
import sys
from pathlib import Path

from .agent import Agent
from .belief import BeliefVector
from .belief_generator import generate_beliefs, load_topics, load_faction_defaults
from .config import Config
from .llm import LLMClient, MockLLMClient
from .scheduler import Scheduler
from .world import World
from .analytics import print_metrics


def load_agents(path: Path, data_dir: Path | None = None) -> list[Agent]:
    if data_dir is None:
        data_dir = path.parent

    topics = load_topics(data_dir)
    faction_defaults = load_faction_defaults(data_dir)

    with open(path) as f:
        data = json.load(f)
    agents: list[Agent] = []
    for entry in data:
        agent = Agent(
            id=entry["id"],
            name=entry["name"],
            role=entry["role"],
            faction=entry.get("faction"),
            personality=entry.get("personality", {}),
            goals=entry.get("goals", []),
            identity=entry.get("identity", ""),
            style=entry.get("style", "measured"),
            belief_overrides=entry.get("belief_overrides", {}),
            load_bearing_topics=entry.get("load_bearing_topics", []),
        )
        agent.beliefs = generate_beliefs(
            faction=agent.faction,
            overrides=agent.belief_overrides,
            load_bearing=agent.load_bearing_topics,
            faction_defaults=faction_defaults,
            topics=topics,
        )
        agents.append(agent)
    return agents


def seed_follows(world: World, density: float = 0.4) -> None:
    agent_ids = [a.id for a in world.all_agents()]
    for aid in agent_ids:
        for other in agent_ids:
            if aid == other:
                continue
            if random.random() < density / len(agent_ids):
                world.add_follow(aid, other)


def save_events(world: World, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    data = [e.model_dump(mode="json") for e in world.events]
    with open(path, "w") as f:
        json.dump(data, f, indent=2, default=str)


def save_state(world: World, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    state = {
        "tick": world.tick,
        "stats": world.stats(),
        "agents": {
            a.id: {
                "name": a.name,
                "faction": a.faction,
                "beliefs": a.beliefs.model_dump(),
                "followers": list(a.followers),
                "following": list(a.following),
                "influence": a.influence,
                "post_count": a.post_count,
                "comment_count": a.comment_count,
                "like_count": a.like_count,
            }
            for a in world.all_agents()
        },
        "posts": [p.model_dump(mode="json") for p in world.posts],
    }
    with open(path, "w") as f:
        json.dump(state, f, indent=2, default=str)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="ballroom",
        description="Multi-agent social network simulation.",
    )
    parser.add_argument("--mock", action="store_true", help="Run without LLM calls (deterministic stubs).")
    parser.add_argument("--ticks", type=int, default=None, help="Override TOTAL_TICKS.")
    parser.add_argument("--agents", type=str, default=None, help="Path to agents.json.")
    parser.add_argument("--seed", type=int, default=None, help="Random seed for reproducibility.")
    parser.add_argument("--quiet", action="store_true", help="Suppress per-tick logs.")
    args = parser.parse_args(argv)

    if args.seed is not None:
        random.seed(args.seed)

    config = Config.load()
    if args.ticks is not None:
        config.total_ticks = args.ticks

    agents_path = Path(args.agents) if args.agents else Path(__file__).parent.parent.parent / "data" / "agents.json"
    if not agents_path.exists():
        print(f"error: agents file not found: {agents_path}", file=sys.stderr)
        return 1

    data_dir = agents_path.parent
    agents = load_agents(agents_path, data_dir)
    world = World(agents)
    seed_follows(world, density=0.4)

    if args.mock:
        llm = MockLLMClient(config)
    else:
        if not config.openrouter_api_key and config.llm_provider == "openrouter":
            print("error: OPENROUTER_API_KEY not set. Use --mock for testing without API.", file=sys.stderr)
            return 1
        llm = LLMClient(config)

    scheduler = Scheduler(world, llm, config)
    scheduler.run(config.total_ticks, verbose=not args.quiet)

    print_metrics(world)

    log_path = Path(__file__).parent.parent.parent / config.log_path
    save_events(world, log_path / "events.json")
    save_state(world, log_path / "state.json")
    print(f"\nLogs written to {log_path}/")
    sys.stdout.flush()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
