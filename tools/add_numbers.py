# TOOL_SPEC is required; JSON description for the LLM to understand the tool
from tools.tooling import Tool
from tools.tooling import tool
import math
import random


# =========================
# Existing Tools
# =========================

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



# =========================
# New: Root & Exponential
# =========================

@tool
def sqrt_number(a: float) -> float:
    """
    Returns the square root of a.
    """
    return math.sqrt(float(a))

@tool
def nth_root(a: float, n: float) -> float:
    """
    Returns the n-th root of a.
    """
    if float(n) == 0:
        raise ZeroDivisionError("Cannot take the 0th root.")
    return float(a) ** (1.0 / float(n))

@tool
def exp_number(a: float) -> float:
    """
    Returns e raised to the power of a.
    """
    return math.exp(float(a))



# =========================
# New: Logarithms
# =========================

@tool
def log_number(a: float) -> float:
    """
    Returns the natural logarithm of a.
    """
    return math.log(float(a))

@tool
def log_base(a: float, base: float) -> float:
    """
    Returns the logarithm of a with the given base.
    """
    return math.log(float(a), float(base))



# =========================
# New: Rounding & Formatting
# =========================

@tool
def round_number(a: float, decimals: int = 0) -> float:
    """
    Rounds number a to the given number of decimals.
    """
    return round(float(a), int(decimals))

@tool
def floor_number(a: float) -> float:
    """
    Returns the floor of a.
    """
    return math.floor(float(a))

@tool
def ceil_number(a: float) -> float:
    """
    Returns the ceiling of a.
    """
    return math.ceil(float(a))



# =========================
# New: Absolute & Sign
# =========================

@tool
def abs_number(a: float) -> float:
    """
    Returns the absolute value of a.
    """
    return abs(float(a))

@tool
def sign_number(a: float) -> float:
    """
    Returns -1, 0, or 1 depending on the sign of a.
    """
    val = float(a)
    if val > 0:
        return 1.0
    if val < 0:
        return -1.0
    return 0.0



# =========================
# New: Trigonometric
# =========================

@tool
def sin_number(a: float) -> float:
    """
    Returns sin(a).
    """
    return math.sin(float(a))

@tool
def cos_number(a: float) -> float:
    """
    Returns cos(a).
    """
    return math.cos(float(a))

@tool
def tan_number(a: float) -> float:
    """
    Returns tan(a).
    """
    return math.tan(float(a))

@tool
def asin_number(a: float) -> float:
    """
    Returns arcsin(a).
    """
    return math.asin(float(a))

@tool
def acos_number(a: float) -> float:
    """
    Returns arccos(a).
    """
    return math.acos(float(a))

@tool
def atan_number(a: float) -> float:
    """
    Returns arctan(a).
    """
    return math.atan(float(a))



# =========================
# New: Hyperbolic Trigonometry
# =========================

@tool
def sinh_number(a: float) -> float:
    """
    Returns the hyperbolic sine of a.
    """
    return math.sinh(float(a))

@tool
def cosh_number(a: float) -> float:
    """
    Returns the hyperbolic cosine of a.
    """
    return math.cosh(float(a))

@tool
def tanh_number(a: float) -> float:
    """
    Returns the hyperbolic tangent of a.
    """
    return math.tanh(float(a))



# =========================
# New: Statistics
# =========================

@tool
def mean_list(values: list) -> float:
    """
    Returns the mean of a list of numbers.
    """
    vals = [float(v) for v in values]
    return sum(vals) / len(vals)

@tool
def median_list(values: list) -> float:
    """
    Returns the median of a list of numbers.
    """
    vals = sorted(float(v) for v in values)
    n = len(vals)
    mid = n // 2

    if n % 2 == 0:
        return (vals[mid - 1] + vals[mid]) / 2.0
    return vals[mid]

@tool
def sum_list(values: list) -> float:
    """
    Returns the sum of a list of numbers.
    """
    return sum(float(v) for v in values)

@tool
def prod_list(values: list) -> float:
    """
    Returns the product of a list of numbers.
    """
    p = 1.0
    for v in values:
        p *= float(v)
    return p



# =========================
# New: Vector/Array Operations
# =========================

@tool
def vector_add(a: list, b: list) -> list:
    """
    Adds two vectors elementwise.
    """
    return [float(x) + float(y) for x, y in zip(a, b)]

@tool
def vector_sub(a: list, b: list) -> list:
    """
    Subtracts vector b from vector a elementwise.
    """
    return [float(x) - float(y) for x, y in zip(a, b)]

@tool
def dot_product(a: list, b: list) -> float:
    """
    Returns the dot product of two vectors.
    """
    return sum(float(x) * float(y) for x, y in zip(a, b))

@tool
def vector_magnitude(a: list) -> float:
    """
    Returns the magnitude of vector a.
    """
    return math.sqrt(sum(float(x) ** 2 for x in a))



# =========================
# New: Boolean & Comparison
# =========================

@tool
def max_number(a: float, b: float) -> float:
    """
    Returns the maximum of a and b.
    """
    return max(float(a), float(b))

@tool
def min_number(a: float, b: float) -> float:
    """
    Returns the minimum of a and b.
    """
    return min(float(a), float(b))

@tool
def equals(a: float, b: float) -> bool:
    """
    Returns True if a == b.
    """
    return float(a) == float(b)

@tool
def greater_than(a: float, b: float) -> bool:
    """
    Returns True if a > b.
    """
    return float(a) > float(b)



# =========================
# New: Miscellaneous
# =========================

@tool
def clamp_number(a: float, min_val: float, max_val: float) -> float:
    """
    Clamps a between min_val and max_val.
    """
    return max(float(min_val), min(float(a), float(max_val)))

@tool
def random_number(min_val: float, max_val: float) -> float:
    """
    Returns a random float between min_val and max_val.
    """
    return random.uniform(float(min_val), float(max_val))

@tool
def factorial_number(a: float) -> float:
    """
    Returns factorial of a (must be an integer >= 0).
    """
    if float(a) < 0 or int(a) != a:
        raise ValueError("Factorial requires a non-negative integer.")
    return math.factorial(int(a))

@tool
def gcd_numbers(a: float, b: float) -> float:
    """
    Returns the greatest common divisor of a and b.
    """
    return math.gcd(int(float(a)), int(float(b)))

@tool
def lcm_numbers(a: float, b: float) -> float:
    """
    Returns the least common multiple of a and b.
    """
    a_i = int(float(a))
    b_i = int(float(b))
    return abs(a_i * b_i) // math.gcd(a_i, b_i)



# =========================
# TOOL SPEC EXPORT
# =========================

TOOL_SPEC = [
    add_numbers.tool_spec(),
    sub_numbers.tool_spec(),
    mul_numbers.tool_spec(),
    div_numbers.tool_spec(),
    pow_numbers.tool_spec(),
    mod_numbers.tool_spec(),

    sqrt_number.tool_spec(),
    nth_root.tool_spec(),
    exp_number.tool_spec(),

    log_number.tool_spec(),
    log_base.tool_spec(),

    round_number.tool_spec(),
    floor_number.tool_spec(),
    ceil_number.tool_spec(),

    abs_number.tool_spec(),
    sign_number.tool_spec(),

    sin_number.tool_spec(),
    cos_number.tool_spec(),
    tan_number.tool_spec(),
    asin_number.tool_spec(),
    acos_number.tool_spec(),
    atan_number.tool_spec(),

    sinh_number.tool_spec(),
    cosh_number.tool_spec(),
    tanh_number.tool_spec(),

    mean_list.tool_spec(),
    median_list.tool_spec(),
    sum_list.tool_spec(),
    prod_list.tool_spec(),

    vector_add.tool_spec(),
    vector_sub.tool_spec(),
    dot_product.tool_spec(),
    vector_magnitude.tool_spec(),

    max_number.tool_spec(),
    min_number.tool_spec(),
    equals.tool_spec(),
    greater_than.tool_spec(),

    clamp_number.tool_spec(),
    random_number.tool_spec(),
    factorial_number.tool_spec(),
    gcd_numbers.tool_spec(),
    lcm_numbers.tool_spec(),
]
