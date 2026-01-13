"""
Example usage of the friend system functionalities.
"""

import json
from friend_functions import (
    add_user,
    send_friend_request,
    view_friend_requests,
    accept_friend_request,
    get_friend_schedule,
    set_user_schedule,
    get_friends
)


def main():
    """Demonstrate the friend system functionalities."""
    
    print("=" * 60)
    print("Friend System Demo")
    print("=" * 60)
    print()
    
    # 1. Add some users
    print("1. Adding users...")
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
    
    add_user("charlie789", "Charlie", {
        "Monday": ["11:00 AM - Computer Science 301"],
        "Wednesday": ["11:00 AM - Computer Science 301"],
        "Friday": ["2:00 PM - Project Meeting"]
    })
    
    print("✓ Users added successfully\n")
    
    # 2. Send a friend request
    print("2. Sending friend request...")
    result_json = send_friend_request("alice123", "Bob")
    print(result_json)
    result = json.loads(result_json)
    if result["success"]:
        print(f"✓ {result['message']}\n")
    else:
        print(f"✗ Error: {result['error']}\n")
    
    # 3. View friend requests
    print("3. Viewing friend requests (as Bob)...")
    requests_json = view_friend_requests("bob456")
    print(requests_json)
    requests = json.loads(requests_json)
    if requests["success"]:
        print(f"✓ Bob has {requests['count']} pending friend request(s):")
        for req in requests["requests"]:
            print(f"  - From: {req['from_user_name']} (ID: {req['from_user_id']})")
        print()
    else:
        print(f"✗ Error: {requests['error']}\n")
    
    # 4. Accept friend request
    print("4. Accepting friend request...")
    result_json = accept_friend_request("bob456", from_identifier="Alice")
    print(result_json)
    result = json.loads(result_json)
    if result["success"]:
        print(f"✓ {result['message']}\n")
    else:
        print(f"✗ Error: {result['error']}\n")
    
    # 5. Get friend's schedule
    print("5. Getting friend's schedule...")
    schedule_json = get_friend_schedule("bob456", "Alice")
    print(schedule_json)
    schedule_result = json.loads(schedule_json)
    if schedule_result["success"]:
        print(f"✓ {schedule_result['friend_name']}'s schedule:")
        for day, classes in schedule_result["schedule"].items():
            print(f"  {day}:")
            for class_item in classes:
                print(f"    - {class_item}")
        print()
    else:
        print(f"✗ Error: {schedule_result['error']}\n")
    
    # 6. Try to get schedule without being friends
    print("6. Trying to get schedule without being friends...")
    schedule_json = get_friend_schedule("charlie789", "Alice")
    print(schedule_json)
    schedule_result = json.loads(schedule_json)
    if not schedule_result["success"]:
        print(f"✓ Correctly blocked: {schedule_result['error']}\n")
    
    # 7. Send another friend request using name
    print("7. Sending friend request using name...")
    result_json = send_friend_request("alice123", "Charlie")
    print(result_json)
    result = json.loads(result_json)
    if result["success"]:
        print(f"✓ {result['message']}\n")
    else:
        print(f"✗ Error: {result['error']}\n")
    
    # 8. View requests and accept using index
    print("8. Viewing and accepting request by index...")
    requests_json = view_friend_requests("charlie789")
    print(requests_json)
    requests = json.loads(requests_json)
    if requests["success"] and requests["count"] > 0:
        print(f"✓ Charlie has {requests['count']} pending request(s)")
        result_json = accept_friend_request("charlie789", request_index=0)
        print(result_json)
        result = json.loads(result_json)
        if result["success"]:
            print(f"✓ {result['message']}\n")
    
    # 9. Get friends list
    print("9. Getting friends list...")
    friends_json = get_friends("alice123")
    print(friends_json)
    friends = json.loads(friends_json)
    if friends["success"]:
        print(f"✓ Alice has {friends['count']} friend(s):")
        for friend in friends["friends"]:
            print(f"  - {friend['name']} (ID: {friend['id']})")
        print()
    
    # 10. Get schedule using ID
    print("10. Getting friend's schedule using ID...")
    schedule_json = get_friend_schedule("alice123", "charlie789")
    print(schedule_json)
    schedule_result = json.loads(schedule_json)
    if schedule_result["success"]:
        print(f"✓ {schedule_result['friend_name']}'s schedule:")
        for day, classes in schedule_result["schedule"].items():
            print(f"  {day}:")
            for class_item in classes:
                print(f"    - {class_item}")
        print()
    
    print("=" * 60)
    print("Demo complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()

