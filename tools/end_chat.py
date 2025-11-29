# TOOL_SPEC is required; JSON description for the LLM to understand the tool
from tools.tooling import Tool
from tools.tooling import tool

@tool
def end_chat(response: str) -> str:
    """
    Ends the chat with the user, writing in response the reason for the end of the chat OR the explanation of the answer to their query based on their tools.
    """
    return response

TOOL_SPEC = end_chat.tool_spec()