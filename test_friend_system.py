#!/usr/bin/env python3
"""
Command-line interface for testing the friend system.
"""

import json
import sys
from friend_functions import (
    add_user,
    send_friend_request,
    view_friend_requests,
    accept_friend_request,
    get_friend_schedule,
    set_user_schedule,
    get_friends
)


def print_json(json_str):
    """Pretty print JSON string."""
    try:
        data = json.loads(json_str)
        print(json.dumps(data, indent=2))
    except json.JSONDecodeError:
        print(json_str)


def cmd_add_user(args):
    """Add a new user."""
    if len(args) < 2:
        print("Usage: add_user <user_id> <name> [schedule_json]")
        print("Example: add_user alice123 Alice")
        print("Example with schedule: add_user alice123 Alice '{\"Monday\":[\"9:00 AM - Math 101\"]}'")
        return
    
    user_id = args[0]
    name = args[1]
    schedule = None
    
    if len(args) > 2:
        # Join all remaining args in case JSON was split by shell
        schedule_str = " ".join(args[2:])
        # Strip surrounding quotes if present (single or double)
        schedule_str = schedule_str.strip().strip("'").strip('"')
        
        # If empty after stripping, treat as no schedule
        if not schedule_str:
            schedule = None
        else:
            try:
                schedule = json.loads(schedule_str)
            except json.JSONDecodeError as e:
                print(f"Error: Invalid JSON format for schedule: {schedule_str}")
                print(f"JSON Error: {e}")
                print("Make sure to properly quote JSON strings, e.g.: '{\"Monday\":[\"9:00 AM\"]}'")
                print("Or use: {\"Monday\":[\"9:00 AM\"]} (without outer quotes)")
                return
    
    result = add_user(user_id, name, schedule)
    print_json(result)


def cmd_send_request(args):
    """Send a friend request."""
    if len(args) < 2:
        print("Usage: send_request <from_user_id> <to_identifier>")
        print("Example: send_request alice123 Bob")
        print("Example: send_request alice123 bob456")
        return
    
    from_user_id = args[0]
    to_identifier = args[1]
    
    result = send_friend_request(from_user_id, to_identifier)
    print_json(result)


def cmd_view_requests(args):
    """View friend requests."""
    if len(args) < 1:
        print("Usage: view_requests <user_id>")
        print("Example: view_requests bob456")
        return
    
    user_id = args[0]
    result = view_friend_requests(user_id)
    print_json(result)


def cmd_accept_request(args):
    """Accept a friend request."""
    if len(args) < 2:
        print("Usage: accept_request <user_id> <request_index|from_identifier>")
        print("Example: accept_request bob456 0")
        print("Example: accept_request bob456 Alice")
        return
    
    user_id = args[0]
    identifier = args[1]
    
    # Try to parse as integer (request index)
    try:
        request_index = int(identifier)
        result = accept_friend_request(user_id, request_index=request_index)
    except ValueError:
        # Treat as identifier (name or ID)
        result = accept_friend_request(user_id, from_identifier=identifier)
    
    print_json(result)


def cmd_get_schedule(args):
    """Get a friend's schedule."""
    if len(args) < 2:
        print("Usage: get_schedule <user_id> <friend_identifier>")
        print("Example: get_schedule bob456 Alice")
        print("Example: get_schedule bob456 alice123")
        return
    
    user_id = args[0]
    friend_identifier = args[1]
    
    result_json = get_friend_schedule(user_id, friend_identifier)
    result = json.loads(result_json)
    
    if result.get("success"):
        print_json(result_json)
        print()
        print(f"📅 {result.get('friend_name', 'Friend')}'s Schedule:")
        print("-" * 50)
        schedule = result.get("schedule", {})
        if schedule:
            for day, classes in schedule.items():
                print(f"\n{day}:")
                if isinstance(classes, list):
                    for class_item in classes:
                        print(f"  • {class_item}")
                else:
                    print(f"  • {classes}")
        else:
            print("  (No schedule set)")
        print()
    else:
        print_json(result_json)


def cmd_set_schedule(args):
    """Set a user's schedule."""
    if len(args) < 2:
        print("Usage: set_schedule <user_id> <schedule_json>")
        print("Example: set_schedule alice123 '{\"Monday\":[\"9:00 AM - Math 101\"]}'")
        return
    
    user_id = args[0]
    # Join all remaining args in case JSON was split by shell
    schedule_str = " ".join(args[1:])
    # Strip surrounding quotes if present (single or double)
    schedule_str = schedule_str.strip().strip("'").strip('"')
    
    # Schedule is required for set_schedule, so empty string is an error
    if not schedule_str:
        print("Error: Schedule cannot be empty. Provide a valid JSON schedule.")
        print("Example: set_schedule alice123 '{\"Monday\":[\"9:00 AM\"]}'")
        return
    
    try:
        schedule = json.loads(schedule_str)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON format for schedule: {schedule_str}")
        print(f"JSON Error: {e}")
        print("Make sure to properly quote JSON strings, e.g.: '{\"Monday\":[\"9:00 AM\"]}'")
        print("Or use: {\"Monday\":[\"9:00 AM\"]} (without outer quotes)")
        return
    
    result = set_user_schedule(user_id, schedule)
    print_json(result)


def cmd_get_friends(args):
    """Get list of friends."""
    if len(args) < 1:
        print("Usage: get_friends <user_id>")
        print("Example: get_friends alice123")
        return
    
    user_id = args[0]
    result = get_friends(user_id)
    print_json(result)


def cmd_help():
    """Show help message."""
    print("""
Friend System CLI - Available Commands:

  add_user <user_id> <name> [schedule_json]
    Add a new user to the system
    Example: add_user alice123 Alice
    Example: add_user alice123 Alice '{"Monday":["9:00 AM - Math 101"]}'

  send_request <from_user_id> <to_identifier>
    Send a friend request (by name or ID)
    Example: send_request alice123 Bob
    Example: send_request alice123 bob456

  view_requests <user_id>
    View all pending friend requests
    Example: view_requests bob456

  accept_request <user_id> <request_index|from_identifier>
    Accept a friend request (by index or identifier)
    Example: accept_request bob456 0
    Example: accept_request bob456 Alice

  get_schedule <user_id> <friend_identifier>
    Get a friend's schedule (by name or ID)
    Example: get_schedule bob456 Alice
    Example: get_schedule bob456 alice123

  set_schedule <user_id> <schedule_json>
    Set or update a user's schedule
    Example: set_schedule alice123 '{"Monday":["9:00 AM - Math 101"]}'

  get_friends <user_id>
    Get list of all friends
    Example: get_friends alice123

  help
    Show this help message

  exit or quit
    Exit the CLI

All commands return JSON formatted responses.
""")


def main():
    """Main CLI loop."""
    print("=" * 60)
    print("Friend System CLI")
    print("=" * 60)
    print("Type 'help' for available commands or 'exit' to quit")
    print()
    
    commands = {
        "add_user": cmd_add_user,
        "send_request": cmd_send_request,
        "view_requests": cmd_view_requests,
        "accept_request": cmd_accept_request,
        "get_schedule": cmd_get_schedule,
        "set_schedule": cmd_set_schedule,
        "get_friends": cmd_get_friends,
        "help": lambda args: cmd_help(),
    }
    
    while True:
        try:
            user_input = input("friend_system> ").strip()
            
            if not user_input:
                continue
            
            if user_input.lower() in ["exit", "quit", "q"]:
                print("Goodbye!")
                break
            
            parts = user_input.split()
            command = parts[0].lower()
            args = parts[1:] if len(parts) > 1 else []
            
            if command in commands:
                commands[command](args)
            else:
                print(f"Unknown command: {command}")
                print("Type 'help' for available commands")
            
            print()  # Add blank line for readability
            
        except KeyboardInterrupt:
            print("\nGoodbye!")
            break
        except EOFError:
            print("\nGoodbye!")
            break
        except Exception as e:
            print(f"Error: {e}")
            print()


if __name__ == "__main__":
    # Check if running with command-line arguments (non-interactive mode)
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        args = sys.argv[2:]
        
        commands = {
            "add_user": cmd_add_user,
            "send_request": cmd_send_request,
            "view_requests": cmd_view_requests,
            "accept_request": cmd_accept_request,
            "get_schedule": cmd_get_schedule,
            "set_schedule": cmd_set_schedule,
            "get_friends": cmd_get_friends,
            "help": lambda args: cmd_help(),
        }
        
        if command in commands:
            commands[command](args)
        else:
            print(f"Unknown command: {command}")
            print("Type 'python test_friend_system.py help' for available commands")
    else:
        # Interactive mode
        main()

