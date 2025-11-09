# TOOL_SPEC is required; JSON description for the LLM to understand the tool
from tools.tooling import Tool
from tools.tooling import tool

@tool
def add_numbers(a: float, b: float) -> float:
    """
    Example tool function for dynamic agent:
    Adds two numbers and returns a dictionary with the result.
    """
    try:
        result = float(a) + float(b)
        return {"result": result, "status": "success"}
    except Exception as e:
        return {"status": "error", "error_message": str(e)}

TOOL_SPEC = add_numbers.tool_spec()