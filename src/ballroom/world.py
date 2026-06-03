from __future__ import annotations

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field

from .agent import Agent


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

    def add_post(self, author_id: str, content: str, topic_tags: Optional[list[str]] = None) -> Post:
        post = Post(
            id=f"p{len(self.posts)}",
            author_id=author_id,
            content=content,
            timestamp=datetime.now(),
            topic_tags=topic_tags or [],
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
        candidates = [
            p
            for p in self.posts
            if p.author_id in agent.following and p.author_id != agent_id
        ]
        candidates.sort(key=lambda p: (len(p.likes) + len(p.comments), p.timestamp), reverse=True)
        return candidates[:limit]

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
