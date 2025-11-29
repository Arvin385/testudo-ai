# TOOL_SPEC is required; JSON description for the LLM to understand the tool
from tools.tooling import Tool
from tools.tooling import tool

@tool
def add_numbers(a: float, b: float) -> float:
    """
    Adds two numbers and returns the result.
    """
    return float(a) + float(b)

@tool
def sub_numbers(a: float, b: float) -> float:
    """
    Subtracts b from a and returns the result.
    """
    return float(a) - float(b)

@tool
def mul_numbers(a: float, b: float) -> float:
    """
    Multiplies two numbers and returns the result.
    """
    return float(a) * float(b)

@tool
def div_numbers(a: float, b: float) -> float:
    """
    Divides a by b and returns the result.
    Raises ZeroDivisionError if b is zero.
    """
    if float(b) == 0:
        raise ZeroDivisionError("Division by zero is not allowed.")
    return float(a) / float(b)

@tool
def pow_numbers(a: float, b: float) -> float:
    """
    Raises a to the power of b and returns the result.
    """
    return float(a) ** float(b)

@tool
def mod_numbers(a: float, b: float) -> float:
    """
    Returns a modulo b.
    Raises ZeroDivisionError if b is zero.
    """
    if float(b) == 0:
        raise ZeroDivisionError("Modulo by zero is not allowed.")
    return float(a) % float(b)

TOOL_SPEC = [
    add_numbers.tool_spec(),
    sub_numbers.tool_spec(),
    mul_numbers.tool_spec(),
    div_numbers.tool_spec(),
    pow_numbers.tool_spec(),
    mod_numbers.tool_spec()
]
