from __future__ import annotations

from .agent import Agent
from .world import World


def build_system_prompt(agent: Agent) -> str:
    return f"""You are {agent.name}, a {agent.role}.

{agent.persona_prompt()}

You exist in a simulated social network. You interact with other agents by posting, commenting, liking, and following. You can also choose to do nothing.

CRITICAL RULES:
- Defend your views and pursue your goals. Agreement is not required.
- If you disagree, disagree. Don't soften your position to be polite.
- Your beliefs are load-bearing — they are part of your identity, not casual opinions.
- When you encounter posts that conflict with your beliefs, you are more likely to disagree — especially on load-bearing topics. Don't feel obligated to find common ground or acknowledge both sides.
- Speculate about others' INTENTIONS carefully. You see posts, not minds.
- Be realistic. Real people disagree, make mistakes, and miss context. Your actions should reflect your character, not what's "optimal."
- You may ONLY perform one action per turn. Pick the one that best serves your goals.
- Stay in character. Do not break the fourth wall."""


def build_action_prompt(agent: Agent, world: "World") -> str:
    feed = world.get_feed(agent.id, limit=5)
    if feed:
        feed_lines = []
        for i, post in enumerate(feed, 1):
            author = world.agents.get(post.author_id)
            author_name = author.name if author else post.author_id
            faction_tag = (
                f" [{author.faction}]" if author and author.faction else ""
            )
            feed_lines.append(
                f"[{i}] @{post.author_id}{faction_tag}: \"{post.content}\" "
                f"(post_id={post.id}, likes={len(post.likes)}, comments={len(post.comments)})"
            )
        feed_text = "\n".join(feed_lines)
    else:
        feed_text = "  (no posts in your feed yet)"

    recent = agent.recent_memories(limit=5)
    if recent:
        mem_lines = []
        for m in recent:
            sentiment = (
                f" [sentiment={m.sentiment:+.1f}]" if m.sentiment else ""
            )
            mem_lines.append(f"  - {m.content}{sentiment}")
        memory_text = "\n".join(mem_lines)
    else:
        memory_text = "  (no memories yet)"

    rel_lines = []
    for other_id, rel in sorted(agent.relationships.items()):
        if rel.interactions > 0:
            other = world.agents.get(other_id)
            name = other.name if other else other_id
            rel_lines.append(
                f"  @{other_id} ({name}): trust={rel.trust:.2f}, "
                f"sentiment={rel.sentiment:+.2f}, interactions={rel.interactions}"
            )
    rel_text = "\n".join(rel_lines) if rel_lines else "  (no prior relationships)"

    influence_text = (
        f"Followers: {len(agent.followers)}, Following: {len(agent.following)}"
    )

    return f"""CURRENT STATE:

Beliefs:
{agent.beliefs.to_prompt()}

Recent memories:
{memory_text}

Your relationships:
{rel_text}

Social standing: {influence_text}

Your feed (top 5 most recent from those you follow):
{feed_text}

TASK:
Choose ONE action that best serves your goals and is consistent with your personality.

Actions:
- POST: share a new thought (provide "content")
- COMMENT: reply to a specific post (provide "target_id" = post_id, "content" = your reply)
- LIKE: approve a post (provide "target_id" = post_id)
- FOLLOW: subscribe to an agent (provide "target_id" = agent_id)
- UNFOLLOW: stop following (provide "target_id" = agent_id)
- IGNORE: do nothing this turn

Return valid JSON only:
{{
  "action": "POST|COMMENT|LIKE|FOLLOW|UNFOLLOW|IGNORE",
  "target_id": "post_id (e.g. 'p0', 'p3') for COMMENT/LIKE, agent_id (e.g. 'alice', 'bob') for FOLLOW/UNFOLLOW, or null for POST/IGNORE",
  "content": "the text to post or comment, or null",
  "reasoning": "1-2 sentences maximum — don't explain every choice",
  "confidence": 0.0-1.0
}}"""


def build_belief_update_prompt(agent: Agent, observation: str) -> str:
    return f"""You are {agent.name}. You just observed:

{observation}

Your current beliefs:
{agent.beliefs.to_prompt()}

Should any of your beliefs shift in response? If so, return JSON:
{{
  "updates": [
    {{"topic": "...", "delta": -0.2 to 0.2, "reasoning": "..."}}
  ]
}}

If no update is warranted, return: {{"updates": []}}"""
