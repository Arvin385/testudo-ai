#!/usr/bin/env python3
"""
Test script to demonstrate common issues and their solutions.
"""

from friend_functions import *
import json

def print_json(json_str):
    """Pretty print JSON string."""
    try:
        data = json.loads(json_str)
        print(json.dumps(data, indent=2))
    except json.JSONDecodeError:
        print(json_str)

print("=" * 70)
print("Common Issues and Solutions")
print("=" * 70)
print()

# Issue 1: User created without schedule
print("ISSUE 1: User created without a schedule")
print("-" * 70)
add_user("user1", "User1")
add_user("user2", "User2")
send_friend_request("user1", "user2")
accept_friend_request("user2", from_identifier="user1")
result = json.loads(get_friend_schedule("user2", "user1"))
print("Result when getting schedule:")
print_json(get_friend_schedule("user2", "user1"))
print("\n✓ Solution: Use 'set_schedule' to add a schedule after creating user")
print()

# Solution: Set schedule after creation
print("SOLUTION: Setting schedule after user creation")
print("-" * 70)
set_user_schedule("user1", {
    "Monday": ["9:00 AM - Math 101"],
    "Tuesday": ["10:00 AM - Chemistry 101"]
})
result = json.loads(get_friend_schedule("user2", "user1"))
print("Now the schedule shows:")
print_json(get_friend_schedule("user2", "user1"))
print()

# Issue 2: Trying to get schedule before being friends
print("\nISSUE 2: Trying to get schedule before being friends")
print("-" * 70)
add_user("user3", "User3", {"Monday": ["9:00 AM - Class"]})
add_user("user4", "User4")
result = json.loads(get_friend_schedule("user4", "user3"))
print("Result:")
print_json(get_friend_schedule("user4", "user3"))
print("\n✓ Solution: Send and accept friend request first")
print()

# Solution: Friend first, then get schedule
print("SOLUTION: Friend first, then get schedule")
print("-" * 70)
send_friend_request("user3", "user4")
accept_friend_request("user4", from_identifier="user3")
result = json.loads(get_friend_schedule("user4", "user3"))
print("Now it works:")
print_json(get_friend_schedule("user4", "user3"))
print()

# Best Practice: Create user with schedule
print("\nBEST PRACTICE: Create user with schedule from the start")
print("-" * 70)
add_user("user5", "User5", {
    "Monday": ["9:00 AM - Math 101", "2:00 PM - Physics 201"],
    "Tuesday": ["10:00 AM - Chemistry 101"],
    "Wednesday": ["9:00 AM - Math 101"]
})
add_user("user6", "User6")
send_friend_request("user5", "user6")
accept_friend_request("user6", from_identifier="user5")
result = json.loads(get_friend_schedule("user6", "user5"))
print("Schedule is immediately available:")
print_json(get_friend_schedule("user6", "user5"))
print()

print("=" * 70)
print("Summary:")
print("=" * 70)
print("1. If schedule is empty {}, use 'set_schedule' to add one")
print("2. You must be friends before you can view someone's schedule")
print("3. Best practice: Add schedule when creating user with 'add_user'")
print("=" * 70)

