# TOOL_SPEC is required; JSON description for the LLM to understand the tool
from tools.tooling import Tool
from tools.tooling import tool

@tool
def add_numbers(a: float, b: float) -> float:
    """
    Example tool function for dynamic agent:
    Adds two numbers and returns a dictionary with the result.
    """
    return float(a) + float(b)

TOOL_SPEC = add_numbers.tool_spec()