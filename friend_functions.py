"""
Convenience functions for the friend system.
These provide a simple interface for the main functionalities.
"""

import json
import os
from friend_system import FriendSystem
from typing import Dict, List, Optional

# Global friend system instance (initialized with MongoDB)
_mongodb_uri = os.getenv("MONGODB_URI", "mongodb+srv://testudoAIteam:fepgg9v5rA9ptcId@userdata.7nyu4ck.mongodb.net/?appName=UserData")
_friend_system = FriendSystem(mongodb_uri=_mongodb_uri)


def send_friend_request(from_user_id: str, to_identifier: str) -> str:
    """
    Send a friend request to a specific person by their name or ID.
    
    Args:
        from_user_id: Your user ID
        to_identifier: The name or ID of the person you want to friend
        
    Returns:
        JSON string with success message and request details
        
    Example:
        >>> send_friend_request("user123", "John Doe")
        '{"success": true, "message": "Friend request sent to John Doe", ...}'
    """
    try:
        request = _friend_system.send_friend_request(from_user_id, to_identifier)
        to_user = _friend_system._find_user(to_identifier)
        result = {
            "success": True,
            "message": f"Friend request sent to {to_user.name}",
            "request": {
                "from": from_user_id,
                "to": to_user.id,
                "to_name": to_user.name,
                "timestamp": request.timestamp.isoformat()
            }
        }
        return json.dumps(result, indent=2)
    except ValueError as e:
        result = {
            "success": False,
            "error": str(e)
        }
        return json.dumps(result, indent=2)


def view_friend_requests(user_id: str) -> str:
    """
    View all pending friend requests you have received.
    
    Args:
        user_id: Your user ID
        
    Returns:
        JSON string with list of pending friend requests
        
    Example:
        >>> view_friend_requests("user123")
        '{"success": true, "requests": [...], "count": 1}'
    """
    try:
        requests = _friend_system.view_friend_requests(user_id)
        # Convert datetime objects to ISO format strings
        formatted_requests = []
        for req in requests:
            formatted_req = req.copy()
            if isinstance(formatted_req.get("timestamp"), str):
                formatted_requests.append(formatted_req)
            else:
                formatted_req["timestamp"] = formatted_req["timestamp"].isoformat()
                formatted_requests.append(formatted_req)
        
        result = {
            "success": True,
            "requests": formatted_requests,
            "count": len(formatted_requests)
        }
        return json.dumps(result, indent=2)
    except ValueError as e:
        result = {
            "success": False,
            "error": str(e)
        }
        return json.dumps(result, indent=2)


def accept_friend_request(user_id: str, request_index: Optional[int] = None, 
                         from_identifier: Optional[str] = None) -> str:
    """
    Accept a friend request.
    
    You can accept by either:
    - Providing the request_index from view_friend_requests()
    - Providing the from_identifier (name or ID) of the person who sent the request
    
    Args:
        user_id: Your user ID
        request_index: Index of the request (optional)
        from_identifier: Name or ID of the sender (optional)
        
    Returns:
        JSON string with success message and friendship details
        
    Example:
        >>> accept_friend_request("user123", from_identifier="Jane Smith")
        '{"success": true, "message": "You are now friends with Jane Smith", ...}'
    """
    try:
        friendship = _friend_system.accept_friend_request(
            user_id, request_index, from_identifier
        )
        friend_id = friendship.user1_id if friendship.user2_id == user_id else friendship.user2_id
        friend_user = _friend_system._find_user(friend_id)
        result = {
            "success": True,
            "message": f"You are now friends with {friend_user.name}",
            "friendship": {
                "user1_id": friendship.user1_id,
                "user2_id": friendship.user2_id,
                "created_at": friendship.created_at.isoformat()
            }
        }
        return json.dumps(result, indent=2)
    except ValueError as e:
        result = {
            "success": False,
            "error": str(e)
        }
        return json.dumps(result, indent=2)


def get_friend_schedule(user_id: str, friend_identifier: str) -> str:
    """
    Get a friend's schedule using their name or ID.
    You must be friends with the person to view their schedule.
    
    Args:
        user_id: Your user ID
        friend_identifier: The name or ID of your friend
        
    Returns:
        JSON string with the friend's schedule
        
    Example:
        >>> get_friend_schedule("user123", "Jane Smith")
        '{"success": true, "friend_name": "Jane Smith", "schedule": {...}}'
    """
    try:
        schedule = _friend_system.get_friend_schedule(user_id, friend_identifier)
        friend = _friend_system._find_user(friend_identifier)
        result = {
            "success": True,
            "friend_id": friend.id,
            "friend_name": friend.name,
            "schedule": schedule
        }
        return json.dumps(result, indent=2)
    except ValueError as e:
        result = {
            "success": False,
            "error": str(e)
        }
        return json.dumps(result, indent=2)


def add_user(user_id: str, name: str, schedule: Optional[Dict] = None) -> str:
    """
    Add a new user to the system (helper function).
    
    Args:
        user_id: Unique user ID
        name: User's name
        schedule: Optional schedule dictionary
        
    Returns:
        JSON string with success message
    """
    try:
        user = _friend_system.add_user(user_id, name, schedule)
        result = {
            "success": True,
            "message": f"User {user.name} added successfully",
            "user_id": user.id
        }
        return json.dumps(result, indent=2)
    except ValueError as e:
        result = {
            "success": False,
            "error": str(e)
        }
        return json.dumps(result, indent=2)


def set_user_schedule(user_id: str, schedule: Dict) -> str:
    """
    Set or update a user's schedule.
    
    Args:
        user_id: User ID
        schedule: Schedule dictionary
        
    Returns:
        JSON string with success message
    """
    try:
        _friend_system.set_user_schedule(user_id, schedule)
        result = {
            "success": True,
            "message": "Schedule updated successfully"
        }
        return json.dumps(result, indent=2)
    except ValueError as e:
        result = {
            "success": False,
            "error": str(e)
        }
        return json.dumps(result, indent=2)


def get_friends(user_id: str) -> str:
    """
    Get a list of all friends for a user.
    
    Args:
        user_id: User ID
        
    Returns:
        JSON string with list of friends
    """
    try:
        friends = _friend_system.get_friends(user_id)
        result = {
            "success": True,
            "friends": friends,
            "count": len(friends)
        }
        return json.dumps(result, indent=2)
    except ValueError as e:
        result = {
            "success": False,
            "error": str(e)
        }
        return json.dumps(result, indent=2)


def get_user_data(identifier: str) -> str:
    """
    Get a user's data from MongoDB by their name or ID.
    This retrieves the actual data stored in the database (id, name, schedule).
    
    Args:
        identifier: The user's ID or name (e.g., "bob" or "bob456")
        
    Returns:
        JSON string with user data from the database
        
    Example:
        >>> get_user_data("bob")
        '{"success": true, "user": {"id": "bob456", "name": "Bob", "schedule": {...}}}'
        
        >>> get_user_data("bob456")
        '{"success": true, "user": {"id": "bob456", "name": "Bob", "schedule": {...}}}'
    """
    try:
        user = _friend_system.get_user(identifier)
        result = {
            "success": True,
            "user": {
                "id": user.id,
                "name": user.name,
                "schedule": user.schedule
            }
        }
        return json.dumps(result, indent=2)
    except ValueError as e:
        result = {
            "success": False,
            "error": str(e)
        }
        return json.dumps(result, indent=2)

