# Quick Start Guide - Friend System CLI

## Starting Interactive Mode

Simply run:
```bash
python test_friend_system.py
```

## Example Interactive Session

Here's a complete example session you can follow:

```bash
$ python test_friend_system.py
```

Then type these commands one by one:

```
friend_system> add_user alice123 Alice '{"Monday":["9:00 AM - Math 101","2:00 PM - Physics 201"],"Tuesday":["10:00 AM - Chemistry 101"]}'

friend_system> add_user bob456 Bob '{"Monday":["8:00 AM - History 201"],"Wednesday":["1:00 PM - English 101"]}'

friend_system> send_request alice123 Bob

friend_system> view_requests bob456

friend_system> accept_request bob456 Alice

friend_system> get_schedule bob456 Alice

friend_system> get_friends alice123

friend_system> exit
```

## All Available Commands

### 1. Add a user
```
add_user <user_id> <name> [schedule_json]
```
Examples:
```
add_user alice123 Alice
add_user bob456 Bob '{"Monday":["9:00 AM - Math 101"]}'
```

### 2. Send a friend request
```
send_request <from_user_id> <to_identifier>
```
Examples:
```
send_request alice123 Bob
send_request alice123 bob456
```

### 3. View friend requests
```
view_requests <user_id>
```
Example:
```
view_requests bob456
```

### 4. Accept a friend request
```
accept_request <user_id> <request_index|from_identifier>
```
Examples:
```
accept_request bob456 0
accept_request bob456 Alice
```

### 5. Get a friend's schedule
```
get_schedule <user_id> <friend_identifier>
```
Examples:
```
get_schedule bob456 Alice
get_schedule bob456 alice123
```

### 6. Set/update a user's schedule
```
set_schedule <user_id> <schedule_json>
```
Example:
```
set_schedule alice123 '{"Monday":["9:00 AM - Math 101"],"Tuesday":["10:00 AM - Chemistry"]}'
```

### 7. Get list of friends
```
get_friends <user_id>
```
Example:
```
get_friends alice123
```

### 8. Get help
```
help
```

### 9. Exit
```
exit
```
or
```
quit
```

## Tips

- All responses are in JSON format
- You can use either user names or IDs for identifiers
- Schedules are optional when creating users - use `set_schedule` to add them later
- You must be friends before viewing someone's schedule
- Type `help` anytime to see all commands

