# TOOL_SPEC is required; JSON description for the LLM to understand the tool
from tools.tooling import Tool
from tools.tooling import tool
from ..server import messages

# Note: This is a dummy tool, the LLM calls this tool but we control it behind the scenes
@tool
def ask_user(question: str) -> str:
    """
    Asks the user any open ended question as desired by the LLM by returning temporary control back to the user.
    NOTE: As this command returns temporary control back to the user immediately, it will be the only command accepted in the present execution cycle. ONLY call this tool in a specific and no other tools, all other tools used concurrently will be ignored. 
    
    """
    global messages
    messages.append({
        "role": "agent",
        "content" : question
    })
    return messages[-1]

TOOL_SPEC=ask_user.tool_spec()