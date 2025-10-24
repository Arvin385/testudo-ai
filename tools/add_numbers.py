# TOOL_SPEC is required; JSON description for the LLM to understand the tool
TOOL_SPEC = {
    "name": "add_numbers",
    "description": "Adds two numbers together and returns the result.",
    "parameters": ["a", "b"]  # names of required parameters
}

def add_numbers(a, b):
    """
    Example tool function for dynamic agent:
    Adds two numbers and returns a dictionary with the result.
    """
    try:
        result = float(a) + float(b)
        return {"result": result, "status": "success"}
    except Exception as e:
        return {"status": "error", "error_message": str(e)}
