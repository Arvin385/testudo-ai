#!/usr/bin/env python3
"""
Quick test script to demonstrate the friend system with schedules.
"""

from friend_functions import *
import json

print("=" * 60)
print("Friend System - Schedule Test")
print("=" * 60)
print()

# 1. Add users with schedules
print("1. Adding users with schedules...")
add_user("alice123", "Alice", {
    "Monday": ["9:00 AM - Math 101", "2:00 PM - Physics 201"],
    "Tuesday": ["10:00 AM - Chemistry 101", "3:00 PM - Lab"],
    "Wednesday": ["9:00 AM - Math 101", "2:00 PM - Physics 201"],
    "Thursday": ["10:00 AM - Chemistry 101"],
    "Friday": ["11:00 AM - Study Group"]
})

add_user("bob456", "Bob", {
    "Monday": ["8:00 AM - History 201", "1:00 PM - English 101"],
    "Wednesday": ["8:00 AM - History 201", "1:00 PM - English 101"],
    "Friday": ["10:00 AM - Art Studio"]
})

print("✓ Users added\n")

# 2. Send friend request
print("2. Sending friend request...")
result = json.loads(send_friend_request("alice123", "Bob"))
print(f"✓ {result['message']}\n")

# 3. View requests
print("3. Viewing friend requests...")
requests = json.loads(view_friend_requests("bob456"))
print(f"✓ Bob has {requests['count']} pending request(s)\n")

# 4. Accept request
print("4. Accepting friend request...")
result = json.loads(accept_friend_request("bob456", from_identifier="Alice"))
print(f"✓ {result['message']}\n")

# 5. Get schedule - this is the key part!
print("5. Getting friend's schedule...")
print("-" * 60)
schedule_result = json.loads(get_friend_schedule("bob456", "Alice"))
print()

if schedule_result["success"]:
    print(f"📅 {schedule_result['friend_name']}'s Schedule:")
    print("=" * 60)
    schedule = schedule_result.get("schedule", {})
    
    if schedule:
        for day, classes in schedule.items():
            print(f"\n{day}:")
            if isinstance(classes, list):
                for class_item in classes:
                    print(f"  • {class_item}")
            else:
                print(f"  • {classes}")
    else:
        print("\n  (No schedule set)")
    
    print("\n" + "=" * 60)
else:
    print(f"✗ Error: {schedule_result['error']}")

print("\n✓ Test complete!")

