# Friend System CLI Usage Guide

## Interactive Mode (Recommended for Testing)

Run the CLI in interactive mode to test all functionalities:

```bash
python test_friend_system.py
```

Then you can type commands interactively:

```
friend_system> add_user alice123 Alice
friend_system> add_user bob456 Bob
friend_system> send_request alice123 Bob
friend_system> view_requests bob456
friend_system> accept_request bob456 Alice
friend_system> get_schedule bob456 Alice
friend_system> exit
```

## Command-Line Mode (Single Commands)

You can also run individual commands directly:

```bash
# Add a user
python test_friend_system.py add_user alice123 Alice

# Add a user with schedule
python test_friend_system.py add_user alice123 Alice '{"Monday":["9:00 AM - Math 101"]}'

# Send a friend request
python test_friend_system.py send_request alice123 Bob

# View friend requests
python test_friend_system.py view_requests bob456

# Accept a friend request (by index)
python test_friend_system.py accept_request bob456 0

# Accept a friend request (by name/ID)
python test_friend_system.py accept_request bob456 Alice

# Get friend's schedule
python test_friend_system.py get_schedule bob456 Alice

# Set user schedule
python test_friend_system.py set_schedule alice123 '{"Monday":["9:00 AM - Math 101"]}'

# Get list of friends
python test_friend_system.py get_friends alice123
```

## Example Testing Session

Here's a complete example session:

```bash
$ python test_friend_system.py

friend_system> add_user alice123 Alice '{"Monday":["9:00 AM - Math 101","2:00 PM - Physics 201"],"Tuesday":["10:00 AM - Chemistry 101"]}'

friend_system> add_user bob456 Bob '{"Monday":["8:00 AM - History 201"],"Wednesday":["1:00 PM - English 101"]}'

friend_system> send_request alice123 Bob

friend_system> view_requests bob456

friend_system> accept_request bob456 Alice

friend_system> get_schedule bob456 Alice

friend_system> get_friends alice123

friend_system> exit
```

## Notes

- All responses are in JSON format
- In interactive mode, data persists between commands
- In command-line mode, each invocation is independent (new instance)
- Use quotes around JSON strings when passing schedules
- You can use either user names or IDs for identifiers

