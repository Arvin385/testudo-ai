# TOOL_SPEC is required; JSON description for the LLM to understand the tool
from tools.tooling import Tool
from tools.tooling import tool
import settings

@tool
def end_task(response: str) -> str:
    """
    Ends the chat with the user, writing in response the reason for the end of the chat OR the explanation of the answer to their query based on their tools.
    NOTE: Calling this tool in any execution cycle BLOCKS the use of any other tools. Only call this after you are sure you want to give control back to user entirely and are fully done with the prompted task.
    """
    global messages
    settings.messages.append({
        "role": "agent",
        "content" : response
    })
    # print("Ended Chat: ")
    # print(settings.messages[-1])
    return settings.messages[-1]

TOOL_SPEC = end_task.tool_spec()