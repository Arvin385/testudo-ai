# executor.py
from tools import tool_registry
import settings

def new_execute(plan: list[dict]) -> tuple[list[dict], bool, bool]:
    """
    Executes one or more tool calls from the plan.
    If plan contains 'plan': [ ...steps... ], runs them in order.
    """
    # Array to store error/success outputs
    all_results: list[dict] = []
    # Empty variable to store the output of the previous function (in case save_knowledge is called)
    prev_output = None
    
    # Loop through the tools, if we find an ask_user cmd or an end_task cmd, only allow that to be ran
    for p in plan:
        if (p["tool"] == "ask_user" or p["tool"] == "end_task"):
            plan = [p]
            break
    
    for step in plan:
        
        # Get info about the tool to be used
        tool_name = step.get("tool")
        params = step.get("params", {})
        
        bad_params: list[str] = []
        # Fill in saved knowledge if needed
        for param in params:
            if isinstance(params[param], str):
                # If the LLM used a $ to decorate it as a variable:
                if params[param][0] == "$": 
                    # Get it from the knowledge base
                    value = settings.KNOWLEDGE_BASE.get(params[param][1:], None)
                    
                    # Note the error if the value is not present. 
                    if value is None:
                        bad_params.append(params[param][1:])
                    else:
                        params[param] = value
                        

        # If we haven't heard of this tool before, error on it
        if tool_name not in tool_registry:
            prev_output = None
            all_results.append({
                "tool" : tool_name, "params" : params,
                "result" : {
                    "status": "error",
                    "error_message": f"Unknown tool {tool_name}"
            }})
            continue
        
        tool_func = tool_registry[tool_name]["func"]
        required_params = tool_registry[tool_name]["spec"]["parameters"]
        new_reqs = [p[0] for p in required_params]

        # Check for missing parameters
        missing = [p for p in new_reqs if p not in params]
        if missing:
            prev_output = None
            all_results.append({
                "tool" : tool_name, "params" : params,
                "result" : {
                "status": "error",
                "error_message": f"Missing parameters: {missing}"
            }})
            continue

        # Execute tool and capture result
        try:
            result = {"output": tool_func(**params), "status" : "success"}
        except Exception as e:
            result = {"status": "error", "error_message": str(e)}
            prev_output = None
            
        # If there was no error and the save knowledge tool was called:
        if (result["status"] != "error" and tool_name == "save_knowledge"):
            if prev_output is None:
                result["output"] = "ERROR: Previous function did not return any value. This is likely due to an error in the previous function."
            else:
                identifier = result["output"][1]
                settings.KNOWLEDGE_BASE[identifier] = prev_output
        
        all_results.append({
            "tool": tool_name, 
            "params" : params,
            "result": result
        })
        
    errored = False
    ended = False
    for result in all_results:
        
        if result["result"]["status"] == "error":
            errored = True
            
        # Using elif so the chat doesn't end if end_chat was used incorrectly
        elif result["tool"] == "end_task" or result["tool"] == "ask_user":
            ended = True

    return all_results, errored, ended