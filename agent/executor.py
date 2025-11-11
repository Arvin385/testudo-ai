# executor.py
from tools import tool_registry

def execute(plan):
    """
    Executes one or more tool calls from the plan.
    If plan contains 'plan': [ ...steps... ], runs them in order.
    """
    # Handle both single-step and multi-step formats
    steps = plan.get("plan", [plan])
    # Array to store error/success outputs
    all_results: list[dict] = []
    # Array to store how well/badly it does
    all_failures = []

    
    for step in steps:
        tool_name = step.get("tool")
        params = step.get("params", {})

        if tool_name not in tool_registry:
            all_results.append({
                "status": "error",
                "error_message": f"Unknown tool {tool_name}"
            })
            continue
        
        tool_func = tool_registry[tool_name]["func"]
        required_params = tool_registry[tool_name]["spec"]["parameters"]
        new_reqs = [p[0] for p in required_params]

        # Check for missing parameters
        missing = [p for p in new_reqs if p not in params]
        if missing:
            all_results.append({
                "status": "error",
                "error_message": f"Missing parameters: {missing}"
            })
            continue

        # Execute tool and capture result
        try:
            result = tool_func(**params)
        except Exception as e:
            result = {"status": "error", "error_message": str(e)}
            

        all_results.append({
            "tool": tool_name,
            "result": result
        })
        
    for result in all_results:
        if result["result"]["status"] == "error":
            all_failures.append((result["tool"], result["result"]["error_message"]))
    
    # If multiple steps, return a list; if single, just the first result
    return all_results, all_failures
