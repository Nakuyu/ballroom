from __future__ import annotations

import random
import math
from collections import defaultdict

from .world import World
from .agent import Agent


def compute_polarization(world: World) -> float:
    all_positions: list[float] = []
    for agent in world.all_agents():
        for pos in agent.beliefs.positions.values():
            all_positions.append(pos)
    if not all_positions:
        return 0.0
    mean = sum(all_positions) / len(all_positions)
    variance = sum((p - mean) ** 2 for p in all_positions) / len(all_positions)
    return math.sqrt(variance)


def compute_influence(world: World) -> dict[str, float]:
    scores: dict[str, float] = {}
    for agent in world.all_agents():
        posts = [p for p in world.posts if p.author_id == agent.id]
        engagement = sum(len(p.likes) + 2 * len(p.comments) for p in posts)
        scores[agent.id] = len(agent.followers) * 0.5 + engagement * 0.1
        agent.influence = scores[agent.id]
    return scores


def compute_echo_chamber_coefficient(world: World) -> float:
    if not world.posts:
        return 0.0
    same = 0
    total = 0
    for agent in world.all_agents():
        feed = world.get_feed(agent.id, limit=100)
        for post in feed:
            total += 1
            author = world.get_agent(post.author_id)
            if author and author.faction and author.faction == agent.faction:
                same += 1
    return same / total if total > 0 else 0.0


def compute_topic_alignment(world: World) -> dict[str, float]:
    by_topic: dict[str, list[float]] = defaultdict(list)
    for agent in world.all_agents():
        for topic, pos in agent.beliefs.positions.items():
            by_topic[topic].append(pos)
    return {
        topic: math.sqrt(sum((p - sum(positions) / len(positions)) ** 2 for p in positions) / len(positions))
        for topic, positions in by_topic.items()
    }


def compute_faction_belief_distance(world: World) -> dict[tuple[str, str], float]:
    factions: dict[str, list[Agent]] = defaultdict(list)
    for agent in world.all_agents():
        if agent.faction:
            factions[agent.faction].append(agent)
    if len(factions) < 2:
        return {}
    faction_centroids: dict[str, dict[str, float]] = {}
    for faction, agents in factions.items():
        centroid: dict[str, float] = {}
        topics = set()
        for a in agents:
            topics.update(a.beliefs.positions.keys())
        for topic in topics:
            vals = [a.beliefs.positions.get(topic, 0.0) for a in agents]
            centroid[topic] = sum(vals) / len(vals)
        faction_centroids[faction] = centroid
    pairs: dict[tuple[str, str], float] = {}
    faction_list = sorted(faction_centroids.keys())
    for i, f1 in enumerate(faction_list):
        for f2 in faction_list[i + 1 :]:
            c1 = faction_centroids[f1]
            c2 = faction_centroids[f2]
            shared = set(c1.keys()) & set(c2.keys())
            if not shared:
                continue
            dist = math.sqrt(sum((c1[t] - c2[t]) ** 2 for t in shared) / len(shared))
            pairs[(f1, f2)] = dist
    return pairs


def print_metrics(world: World, tick: Optional[int] = None) -> None:
    print()
    print("=" * 60)
    label = f"Tick {tick}" if tick is not None else "Final"
    print(f"METRICS ({label})")
    print("=" * 60)
    print(f"Polarization (std dev of beliefs): {compute_polarization(world):.3f}")
    print(f"Echo chamber coefficient: {compute_echo_chamber_coefficient(world):.3f}")
    print()
    print("Topic polarization:")
    for topic, score in sorted(compute_topic_alignment(world).items()):
        print(f"  {topic}: {score:.3f}")
    print()
    print("Faction belief distance:")
    for (f1, f2), dist in compute_faction_belief_distance(world).items():
        print(f"  {f1} <-> {f2}: {dist:.3f}")
    print()
    print("Influence ranking:")
    for agent_id, score in sorted(compute_influence(world).items(), key=lambda x: -x[1]):
        agent = world.get_agent(agent_id)
        print(f"  {agent.name} ({agent.faction or 'Independent'}): {score:.2f}")
    print("=" * 60)
    print()
