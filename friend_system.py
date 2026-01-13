"""
Friend system functionality: sending requests, viewing/accepting requests, and getting friend schedules.
"""

from typing import Optional, List, Dict
from models import User, FriendRequest, Friendship
from datetime import datetime
from database import get_db_connection
from pymongo.database import Database


class FriendSystem:
    """Manages friend requests, friendships, and schedule access."""
    
    def __init__(self, mongodb_uri: Optional[str] = None, db_name: str = "testudo_ai"):
        """
        Initialize the friend system with MongoDB connection.
        
        Args:
            mongodb_uri: MongoDB connection URI (optional, uses MONGODB_URI env var if not provided)
            db_name: Database name (default: testudo_ai)
        """
        self.conn = get_db_connection(mongodb_uri, db_name)
        self.db = self.conn.get_database()
        self.users_collection = self.db.users
        self.friend_requests_collection = self.db.friend_requests
        self.friendships_collection = self.db.friendships
        
        # Create indexes for better query performance
        self.users_collection.create_index("id", unique=True)
        self.users_collection.create_index("name", unique=True)
        self.friend_requests_collection.create_index([("from_user_id", 1), ("to_user_id", 1)])
        self.friendships_collection.create_index([("user1_id", 1), ("user2_id", 1)])
    
    def _user_to_dict(self, user: User) -> Dict:
        """Convert User object to dictionary for MongoDB storage."""
        return {
            "id": user.id,
            "name": user.name,
            "schedule": user.schedule
        }
    
    def _dict_to_user(self, doc: Dict) -> User:
        """Convert MongoDB document to User object."""
        return User(
            id=doc["id"],
            name=doc["name"],
            schedule=doc.get("schedule", {})
        )
    
    def _friend_request_to_dict(self, request: FriendRequest) -> Dict:
        """Convert FriendRequest object to dictionary for MongoDB storage."""
        return {
            "from_user_id": request.from_user_id,
            "to_user_id": request.to_user_id,
            "timestamp": request.timestamp,
            "status": request.status
        }
    
    def _dict_to_friend_request(self, doc: Dict) -> FriendRequest:
        """Convert MongoDB document to FriendRequest object."""
        return FriendRequest(
            from_user_id=doc["from_user_id"],
            to_user_id=doc["to_user_id"],
            timestamp=doc.get("timestamp", datetime.now()),
            status=doc.get("status", "pending")
        )
    
    def _friendship_to_dict(self, friendship: Friendship) -> Dict:
        """Convert Friendship object to dictionary for MongoDB storage."""
        return {
            "user1_id": friendship.user1_id,
            "user2_id": friendship.user2_id,
            "created_at": friendship.created_at
        }
    
    def _dict_to_friendship(self, doc: Dict) -> Friendship:
        """Convert MongoDB document to Friendship object."""
        return Friendship(
            user1_id=doc["user1_id"],
            user2_id=doc["user2_id"],
            created_at=doc.get("created_at", datetime.now())
        )
    
    def add_user(self, user_id: str, name: str, schedule: Optional[Dict] = None) -> User:
        """Add a new user to the system."""
        # Check if user with ID already exists
        if self.users_collection.find_one({"id": user_id}):
            raise ValueError(f"User with ID {user_id} already exists")
        # Check if user with name already exists
        if self.users_collection.find_one({"name": name}):
            raise ValueError(f"User with name {name} already exists")
        
        user = User(id=user_id, name=name, schedule=schedule or {})
        self.users_collection.insert_one(self._user_to_dict(user))
        return user
    
    def _find_user(self, identifier: str) -> Optional[User]:
        """Find a user by ID or name."""
        # Try ID first
        doc = self.users_collection.find_one({"id": identifier})
        if doc:
            return self._dict_to_user(doc)
        # Try name
        doc = self.users_collection.find_one({"name": identifier})
        if doc:
            return self._dict_to_user(doc)
        return None
    
    def get_user(self, identifier: str) -> User:
        """
        Get a user's data from MongoDB by their ID or name.
        
        Args:
            identifier: The user's ID or name
            
        Returns:
            User object with id, name, and schedule from the database
            
        Raises:
            ValueError: If user with the given identifier is not found in the database
        """
        user = self._find_user(identifier)
        if user is None:
            raise ValueError(f"User with identifier '{identifier}' not found in database")
        return user
    
    def send_friend_request(self, from_user_id: str, to_identifier: str) -> FriendRequest:
        """
        Send a friend request to a user by their name or ID.
        
        Args:
            from_user_id: The ID of the user sending the request
            to_identifier: The name or ID of the user to send the request to
            
        Returns:
            The created FriendRequest object
            
        Raises:
            ValueError: If users don't exist, already friends, or request already exists
        """
        # Validate sender exists in database
        from_user_doc = self.users_collection.find_one({"id": from_user_id})
        if not from_user_doc:
            raise ValueError(f"User with ID {from_user_id} does not exist in database")
        
        # Find recipient in database - must exist to send request
        to_user = self._find_user(to_identifier)
        if to_user is None:
            raise ValueError(f"User with identifier '{to_identifier}' not found in database. Please verify the person's name or ID is correct.")
        
        to_user_id = to_user.id
        
        # Check if trying to friend themselves
        if from_user_id == to_user_id:
            raise ValueError("Cannot send friend request to yourself")
        
        # Check if already friends
        if self._are_friends(from_user_id, to_user_id):
            raise ValueError(f"You are already friends with {to_user.name}")
        
        # Check if request already exists (pending)
        existing_request = self._find_pending_request(from_user_id, to_user_id)
        if existing_request:
            raise ValueError(f"Friend request already sent to {to_user.name}")
        
        # Check if there's a reverse request
        reverse_request = self._find_pending_request(to_user_id, from_user_id)
        if reverse_request:
            raise ValueError(f"{to_user.name} has already sent you a friend request. Accept it instead.")
        
        # Create and store the friend request
        request = FriendRequest(from_user_id=from_user_id, to_user_id=to_user_id)
        self.friend_requests_collection.insert_one(self._friend_request_to_dict(request))
        return request
    
    def _find_pending_request(self, from_user_id: str, to_user_id: str) -> Optional[FriendRequest]:
        """Find a pending friend request between two users."""
        doc = self.friend_requests_collection.find_one({
            "from_user_id": from_user_id,
            "to_user_id": to_user_id,
            "status": "pending"
        })
        if doc:
            return self._dict_to_friend_request(doc)
        return None
    
    def _are_friends(self, user1_id: str, user2_id: str) -> bool:
        """Check if two users are friends."""
        friendship = self.friendships_collection.find_one({
            "$or": [
                {"user1_id": user1_id, "user2_id": user2_id},
                {"user1_id": user2_id, "user2_id": user1_id}
            ]
        })
        return friendship is not None
    
    def view_friend_requests(self, user_id: str) -> List[Dict]:
        """
        View all pending friend requests received by a user.
        
        Args:
            user_id: The ID of the user to view requests for
            
        Returns:
            List of dictionaries containing request information
        """
        if not self.users_collection.find_one({"id": user_id}):
            raise ValueError(f"User with ID {user_id} does not exist in database")
        
        requests = []
        pending_requests = self.friend_requests_collection.find({
            "to_user_id": user_id,
            "status": "pending"
        })
        
        for request_doc in pending_requests:
            request = self._dict_to_friend_request(request_doc)
            from_user_doc = self.users_collection.find_one({"id": request.from_user_id})
            if from_user_doc:
                from_user = self._dict_to_user(from_user_doc)
                requests.append({
                    "request_id": len(requests),  # Simple index-based ID
                    "from_user_id": request.from_user_id,
                    "from_user_name": from_user.name,
                    "timestamp": request.timestamp
                })
        
        return requests
    
    def accept_friend_request(self, user_id: str, request_index: Optional[int] = None, 
                             from_identifier: Optional[str] = None) -> Friendship:
        """
        Accept a friend request.
        
        Args:
            user_id: The ID of the user accepting the request
            request_index: Index of the request from view_friend_requests (optional)
            from_identifier: Name or ID of the user who sent the request (optional)
            
        Returns:
            The created Friendship object
            
        Raises:
            ValueError: If user doesn't exist or request not found
        """
        if not self.users_collection.find_one({"id": user_id}):
            raise ValueError(f"User with ID {user_id} does not exist in database")
        
        # Find the request
        request_doc = None
        
        if request_index is not None:
            # Find by index
            pending_requests = list(self.friend_requests_collection.find({
                "to_user_id": user_id,
                "status": "pending"
            }))
            if 0 <= request_index < len(pending_requests):
                request_doc = pending_requests[request_index]
        elif from_identifier is not None:
            # Find by sender identifier
            from_user = self._find_user(from_identifier)
            if from_user:
                request_doc = self.friend_requests_collection.find_one({
                    "from_user_id": from_user.id,
                    "to_user_id": user_id,
                    "status": "pending"
                })
        
        if request_doc is None:
            raise ValueError("Friend request not found")
        
        request = self._dict_to_friend_request(request_doc)
        
        if request.status != "pending":
            raise ValueError("This friend request has already been processed")
        
        # Mark request as accepted in database
        self.friend_requests_collection.update_one(
            {"_id": request_doc["_id"]},
            {"$set": {"status": "accepted"}}
        )
        
        # Create friendship
        friendship = Friendship(user1_id=request.from_user_id, user2_id=request.to_user_id)
        self.friendships_collection.insert_one(self._friendship_to_dict(friendship))
        
        return friendship
    
    def get_friend_schedule(self, user_id: str, friend_identifier: str) -> Dict:
        """
        Get a friend's schedule by their name or ID.
        
        Args:
            user_id: The ID of the user requesting the schedule
            friend_identifier: The name or ID of the friend
            
        Returns:
            Dictionary containing the friend's schedule
            
        Raises:
            ValueError: If users don't exist or are not friends
        """
        if not self.users_collection.find_one({"id": user_id}):
            raise ValueError(f"User with ID {user_id} does not exist in database")
        
        friend = self._find_user(friend_identifier)
        if friend is None:
            raise ValueError(f"User with identifier '{friend_identifier}' not found in database. Please verify the person's name or ID is correct.")
        
        # Check if they are friends
        if not self._are_friends(user_id, friend.id):
            raise ValueError(f"You are not friends with {friend.name}. Send a friend request first.")
        
        return friend.schedule
    
    def set_user_schedule(self, user_id: str, schedule: Dict) -> None:
        """Set or update a user's schedule."""
        if not self.users_collection.find_one({"id": user_id}):
            raise ValueError(f"User with ID {user_id} does not exist in database")
        self.users_collection.update_one(
            {"id": user_id},
            {"$set": {"schedule": schedule}}
        )
    
    def get_friends(self, user_id: str) -> List[Dict]:
        """Get a list of all friends for a user."""
        if not self.users_collection.find_one({"id": user_id}):
            raise ValueError(f"User with ID {user_id} does not exist in database")
        
        friends = []
        friendships = self.friendships_collection.find({
            "$or": [
                {"user1_id": user_id},
                {"user2_id": user_id}
            ]
        })
        
        for friendship_doc in friendships:
            friendship = self._dict_to_friendship(friendship_doc)
            friend_id = friendship.user2_id if friendship.user1_id == user_id else friendship.user1_id
            friend_doc = self.users_collection.find_one({"id": friend_id})
            if friend_doc:
                friend_user = self._dict_to_user(friend_doc)
                friends.append({"id": friend_user.id, "name": friend_user.name})
        
        return friends

