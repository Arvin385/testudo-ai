import json

def extract_json_objects(text: str):
    """
    Extracts all valid JSON objects or arrays from a text string,
    correctly handling nested and multiline JSON structures.

    Args:
        text (str): A string potentially containing one or more JSON objects
                    or arrays mixed with other text.

    Returns:
        list: A list of successfully parsed JSON objects (dicts or lists).
    """
    json_objects = []
    stack = []
    start_idx = None
    in_string = False
    escape = False

    for i, ch in enumerate(text):
        if ch == '"' and not escape:
            in_string = not in_string
        elif ch == '\\' and not escape:
            escape = True
            continue

        if not in_string:
            if ch in '{[':
                if not stack:
                    start_idx = i
                stack.append(ch)
            elif ch in '}]' and stack:
                opening = stack.pop()
                # ensure brackets match properly
                if (opening == '{' and ch != '}') or (opening == '[' and ch != ']'):
                    stack.clear()
                    start_idx = None
                    continue
                if not stack and start_idx is not None:
                    candidate = text[start_idx:i + 1]
                    try:
                        obj = json.loads(candidate)
                        json_objects.append(obj)
                    except json.JSONDecodeError:
                        pass  # not a valid JSON
                    start_idx = None

        escape = False  # reset escape flag after each character

    return json_objects


# Example usage
if __name__ == "__main__":
    messy_output = '''
    Random text...
    {
      "user": "Alice",
      "details": {
        "age": 30,
        "hobbies": ["reading", "traveling"],
        "address": {
          "city": "College Park",
          "state": "MD"
        }
      }
    }
    Something else...
    [
      {"bus": "115", "time": "10:00"},
      {"bus": "117", "time": "10:15"}
    ]
    '''

    results = extract_json_objects(messy_output)
    print(json.dumps(results, indent=2))
