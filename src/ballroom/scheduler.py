from __future__ import annotations

import random
from typing import Optional

from .llm import LLMClient, MockLLMClient
from .prompts import build_system_prompt, build_action_prompt
from .action import Action, ActionType
from .world import World
from .agent import Agent
from .analytics import print_metrics


class Scheduler:
    def __init__(self, world: World, llm, config):
        self.world = world
        self.llm = llm
        self.config = config
        self.action_count = 0
        self.error_count = 0

    def run(self, total_ticks: int, verbose: bool = True) -> None:
        if verbose:
            print()
            print("=" * 60)
            print(f"Ballroom v0.1.0 — {len(self.world.agents)} agents, {total_ticks} ticks")
            print(f"Provider: {self.config.llm_provider} | Model: {self._model_name()}")
            print("=" * 60)
            print()

        for tick in range(total_ticks):
            self.world.tick = tick
            self.tick()
            if verbose and (tick + 1) % 10 == 0:
                self._print_status(tick + 1)

    def _model_name(self) -> str:
        if isinstance(self.llm, MockLLMClient):
            return "mock"
        return self.llm.model

    def tick(self) -> None:
        agent_ids = list(self.world.agents.keys())
        random.shuffle(agent_ids)
        for agent_id in agent_ids:
            if random.random() < self.config.action_probability:
                self.agent_step(agent_id)
        for agent in self.world.all_agents():
            agent.decay_memory()

    def agent_step(self, agent_id: str) -> None:
        agent = self.world.agents[agent_id]

        system = build_system_prompt(agent)
        user = build_action_prompt(agent, self.world)

        try:
            response = self.llm.chat(system, user, json_mode=True, temperature=0.8)
        except Exception as e:
            self.error_count += 1
            print(f"  [error] LLM call failed for {agent.name}: {e}")
            return

        action = Action.from_llm(response)
        if not action.is_valid():
            return
        self.apply_action(agent, action)
        self.action_count += 1

    def apply_action(self, agent: Agent, action: Action) -> None:
        tick = self.world.tick

        if action.type == ActionType.POST and action.content:
            post = self.world.add_post(agent.id, action.content)
            agent.post_count += 1
            self.world.add_event(
                agent.id,
                "post",
                {"post_id": post.id, "content": action.content[:80]},
            )
            agent.remember("action", "self", f"You posted: {action.content[:80]}", importance=0.6)
            print(f"  [t={tick:03d}] {agent.name} POSTED: \"{action.content[:60]}\"")

        elif action.type == ActionType.COMMENT and action.target_id and action.content:
            target = self.world.get_post(action.target_id)
            if not target:
                return
            comment_post = self.world.add_post(
                agent.id, f"@{target.author_id}: {action.content}"
            )
            target.comments.append(comment_post.id)
            agent.comment_count += 1
            self.world.add_event(
                agent.id,
                "comment",
                {"post_id": target.id, "to": target.author_id, "content": action.content[:60]},
            )
            sentiment = self._infer_sentiment(action.content)
            agent.update_relationship(target.author_id, trust_delta=0.01, sentiment_delta=sentiment * 0.05)
            self.world.agents[target.author_id].update_relationship(
                agent.id, trust_delta=0.01, sentiment_delta=sentiment * 0.05
            )
            agent.remember(
                "interaction",
                target.author_id,
                f"You commented on their post: {action.content[:60]}",
                sentiment=sentiment,
                importance=0.5,
            )
            self.world.agents[target.author_id].remember(
                "interaction",
                agent.id,
                f"{agent.name} commented on your post: {action.content[:60]}",
                sentiment=sentiment,
                importance=0.5,
            )
            print(
                f"  [t={tick:03d}] {agent.name} -> @{target.author_id}: "
                f"\"{action.content[:50]}\""
            )

        elif action.type == ActionType.LIKE and action.target_id:
            target = self.world.get_post(action.target_id)
            if not target or agent.id in target.likes:
                return
            target.likes.add(agent.id)
            agent.like_count += 1
            self.world.add_event(agent.id, "like", {"post_id": target.id, "to": target.author_id})
            agent.update_relationship(target.author_id, trust_delta=0.005, sentiment_delta=0.02)
            print(f"  [t={tick:03d}] {agent.name} LIKED @{target.author_id}'s post")

        elif action.type == ActionType.FOLLOW and action.target_id:
            target = self.world.get_agent(action.target_id)
            if not target or target.id == agent.id:
                return
            if self.world.add_follow(agent.id, target.id):
                self.world.add_event(agent.id, "follow", {"target": target.id})
                agent.remember("action", target.id, f"You followed {target.name}", importance=0.4)
                print(f"  [t={tick:03d}] {agent.name} FOLLOWED @{target.id}")

        elif action.type == ActionType.UNFOLLOW and action.target_id:
            if self.world.remove_follow(agent.id, action.target_id):
                self.world.add_event(agent.id, "unfollow", {"target": action.target_id})
                print(f"  [t={tick:03d}] {agent.name} UNFOLLOWED @{action.target_id}")

        elif action.type == ActionType.IGNORE:
            pass

    def _infer_sentiment(self, content: str) -> float:
        c = content.lower()
        positive = ["agree", "great", "good", "yes", "support", "love", "exactly", "right", "+1", "true"]
        negative = ["disagree", "wrong", "no", "bad", "hate", "stupid", "nope", "false", "ridiculous", "overhyped"]
        score = 0.0
        for p in positive:
            if p in c:
                score += 0.3
        for n in negative:
            if n in c:
                score -= 0.3
        return max(-1.0, min(1.0, score))

    def _print_status(self, tick: int) -> None:
        stats = self.world.stats()
        print()
        print(f"--- Status @ tick {tick} ---")
        print(
            f"  Posts: {stats['posts']} | Events: {stats['events']} | "
            f"Follows: {stats['follows']} | Actions: {self.action_count} | Errors: {self.error_count}"
        )
        for agent in self.world.all_agents():
            print(
                f"  {agent.name}: {agent.post_count}P / {agent.comment_count}C / "
                f"{agent.like_count}L | followers={len(agent.followers)}"
            )
        print()
