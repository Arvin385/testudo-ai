# TOOL_SPEC is required; JSON description for the LLM to understand the tool
from tools.tooling import Tool
from tools.tooling import tool
import settings

# Note: This is a proxy for end_task, with different instructions
@tool
def ask_user(question: str) -> str:
    """
    Asks the user any open ended question as desired by the LLM by returning temporary control back to the user.
    NOTE: 
    As this command returns temporary control back to the user immediately, it will be the only command accepted in the present execution cycle. 
    The user will get control to respond to your question and only THEN can you call tools again. 
    ONLY call this tool in a specific cycle and no other tools, all other tools used concurrently will be ignored. 
    
    """
    settings.messages.append({
        "role": "agent",
        "content" : question
    })
    return settings.messages[-1]

TOOL_SPEC=ask_user.tool_spec()