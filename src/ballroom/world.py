from __future__ import annotations

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field

from .agent import Agent

TOPIC_KEYWORDS = {
    "wealth_inequality": ["wealth", "inequality", "rich", "poor", "gap", "class"],
    "job_automation": ["automation", "job", "replace", "worker", "unemployment"],
    "corporate_power": ["corporate", "company", "big tech", "monopoly", "power"],
    "economic_growth": ["growth", "economy", "gdp", "prosperity", "progress"],
    "government_role": ["government", "regulation", "policy", "law", "state"],
    "individual_freedom": ["freedom", "liberty", "rights", "choice", "autonomy"],
    "collective_action": ["collective", "together", "community", "solidarity"],
    "education_system": ["education", "school", "teacher", "student", "learning"],
    "healthcare": ["health", "medical", "hospital", "care", "insurance"],
    "community_values": ["community", "neighbor", "local", "connection"],
    "work_life_balance": ["work-life", "balance", "hustle", "overtime", "rest"],
    "creative_autonomy": ["creative", "art", "artist", "design", "copyright"],
    "traditional_values": ["tradition", "traditional", "values", "heritage"],
    "social_change": ["change", "reform", "progress", "evolution", "revolution"],
    "expert_authority": ["expert", "scientist", "research", "evidence", "data"],
    "personal_experience": ["experience", "personal", "anecdote", "story"],
    "ai_safety": ["ai safety", "alignment", "existential risk", "x-risk"],
    "open_source": ["open source", "open-source", "free software", "gpl"],
    "regulation": ["regulate", "regulation", "compliance", "oversight"],
    "deployment_speed": ["deploy", "ship", "speed", "fast", "move fast"],
    "human_replacement": ["replace", "replacement", "displace", "job loss"],
}


class Post(BaseModel):
    id: str
    author_id: str
    content: str
    timestamp: datetime
    topic_tags: list[str] = Field(default_factory=list)
    likes: set[str] = Field(default_factory=set)
    comments: list[str] = Field(default_factory=list)


class Event(BaseModel):
    timestamp: datetime
    tick: int
    agent_id: str
    event_type: str
    details: dict = Field(default_factory=dict)


class World:
    def __init__(self, agents: list[Agent]):
        self.agents: dict[str, Agent] = {a.id: a for a in agents}
        self.posts: list[Post] = []
        self.events: list[Event] = []
        self.tick: int = 0

    def auto_tag_content(self, content: str) -> list[str]:
        content_lower = content.lower()
        tags = []
        for topic, keywords in TOPIC_KEYWORDS.items():
            if any(keyword in content_lower for keyword in keywords):
                tags.append(topic)
        return tags[:3]

    def add_post(self, author_id: str, content: str, topic_tags: Optional[list[str]] = None) -> Post:
        if topic_tags is None:
            topic_tags = self.auto_tag_content(content)
        post = Post(
            id=f"p{len(self.posts)}",
            author_id=author_id,
            content=content,
            timestamp=datetime.now(),
            topic_tags=topic_tags,
        )
        self.posts.append(post)
        return post

    def add_event(self, agent_id: str, event_type: str, details: Optional[dict] = None) -> None:
        event = Event(
            timestamp=datetime.now(),
            tick=self.tick,
            agent_id=agent_id,
            event_type=event_type,
            details=details or {},
        )
        self.events.append(event)

    def add_follow(self, follower_id: str, followee_id: str) -> bool:
        if follower_id == followee_id:
            return False
        if followee_id not in self.agents:
            return False
        if followee_id in self.agents[follower_id].following:
            return False
        self.agents[follower_id].following.add(followee_id)
        self.agents[followee_id].followers.add(follower_id)
        return True

    def remove_follow(self, follower_id: str, followee_id: str) -> bool:
        if followee_id in self.agents[follower_id].following:
            self.agents[follower_id].following.discard(followee_id)
            self.agents[followee_id].followers.discard(follower_id)
            return True
        return False

    def get_post(self, post_id: str) -> Optional[Post]:
        for p in self.posts:
            if p.id == post_id:
                return p
        return None

    def get_feed(self, agent_id: str, limit: int = 5) -> list[Post]:
        agent = self.agents.get(agent_id)
        if not agent:
            return []

        all_posts = [
            p for p in self.posts
            if p.author_id != agent_id
        ]

        if not agent.following:
            all_posts.sort(
                key=lambda p: (len(p.likes) + 2 * len(p.comments), p.timestamp),
                reverse=True,
            )
            return all_posts[:limit]

        followed_posts = [
            p for p in all_posts
            if p.author_id in agent.following
        ]
        global_posts = [
            p for p in all_posts
            if p.author_id not in agent.following
        ]

        followed_posts.sort(
            key=lambda p: (len(p.likes) + 2 * len(p.comments), p.timestamp),
            reverse=True,
        )
        global_posts.sort(
            key=lambda p: (len(p.likes) + 2 * len(p.comments), p.timestamp),
            reverse=True,
        )

        followed_limit = min(limit, max(3, limit // 2))
        global_limit = limit - followed_limit

        result = followed_posts[:followed_limit]
        result.extend(global_posts[:global_limit])

        return result

    def get_discover_feed(self, agent_id: str, limit: int = 5) -> list[Post]:
        agent = self.agents.get(agent_id)
        if not agent:
            return []

        candidate_posts = [
            p for p in self.posts
            if p.author_id != agent_id and p.author_id not in agent.following
        ]

        def score_post(post: Post) -> float:
            engagement = len(post.likes) + 2 * len(post.comments)
            author = self.agents.get(post.author_id)
            faction_match = 1.0 if (author and author.faction == agent.faction) else 0.0
            topic_overlap = 0.0
            if post.topic_tags:
                agent_topics = set(agent.beliefs.positions.keys())
                post_topics = set(post.topic_tags)
                overlap = len(agent_topics & post_topics)
                topic_overlap = overlap / max(len(post_topics), 1)
            return engagement * 0.4 + faction_match * 3.0 + topic_overlap * 2.0

        candidate_posts.sort(key=score_post, reverse=True)
        return candidate_posts[:limit]

    def get_agent(self, agent_id: str) -> Optional[Agent]:
        return self.agents.get(agent_id)

    def all_agents(self) -> list[Agent]:
        return list(self.agents.values())

    def stats(self) -> dict:
        return {
            "tick": self.tick,
            "agents": len(self.agents),
            "posts": len(self.posts),
            "events": len(self.events),
            "follows": sum(len(a.following) for a in self.agents.values()),
        }
