# executor.py
from tools import tool_registry

def execute(plan):
    tool_name = plan.get("tool")
    params = plan.get("params", {})

    if tool_name not in tool_registry:
        return {"status": "error", "error_message": f"Unknown tool {tool_name}"}

    tool_func = tool_registry[tool_name]["func"]
    required_params = tool_registry[tool_name]["spec"]["parameters"]

    # check for missing parameters
    missing = [p for p in required_params if p not in params]
    if missing:
        return {"status": "error", "error_message": f"Missing parameters: {missing}"}

    # execute tool
    return tool_func(**params)
