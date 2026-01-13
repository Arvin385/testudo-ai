"""
Data models for the friend system.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional
from datetime import datetime


@dataclass
class User:
    """Represents a user in the system."""
    id: str
    name: str
    schedule: Dict = field(default_factory=dict)  # Schedule stored as a dictionary
    
    def __str__(self):
        return f"User(id={self.id}, name={self.name})"


@dataclass
class FriendRequest:
    """Represents a friend request between two users."""
    from_user_id: str
    to_user_id: str
    timestamp: datetime = field(default_factory=datetime.now)
    status: str = "pending"  # pending, accepted, rejected
    
    def __str__(self):
        return f"FriendRequest(from={self.from_user_id}, to={self.to_user_id}, status={self.status})"


@dataclass
class Friendship:
    """Represents an established friendship between two users."""
    user1_id: str
    user2_id: str
    created_at: datetime = field(default_factory=datetime.now)
    
    def __str__(self):
        return f"Friendship(user1={self.user1_id}, user2={self.user2_id})"

