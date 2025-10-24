# planner.py

from tools import tool_registry

def plan(user_query):
    """
    Mock dynamic planner for testing.
    In practice, send user_query + TOOL_SPEC to Gemini API to get a JSON plan.
    """

    # Example: detect addition request
    if "add" in user_query.lower():
        # extract numbers from user input (simplified)
        import re
        nums = re.findall(r"[-+]?\d*\.\d+|\d+", user_query)
        if len(nums) >= 2:
            return {
                "tool": "add_numbers",
                "params": {"a": nums[0], "b": nums[1]}
            }

    return {"tool": "unknown", "params": {}}
