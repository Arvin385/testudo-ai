# TOOL_SPEC is required; JSON description for the LLM to understand the tool
from tools.tooling import Tool
from tools.tooling import tool
from ..server import send_question

@tool
def ask_user(question: str) -> str:
    """
    Asks the user any open ended question as desired by the LLM.
    Returns the user's output as a string. 
    """
    output = send_question(question)
    resp = input(question + "\nU> ")
    return "\"" + resp + "\""

TOOL_SPEC=ask_user.tool_spec()