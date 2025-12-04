# Code for a tool to the allow the LLM to get knowledge from the central dict
from tools.tooling import Tool
from tools.tooling import tool
import settings

@tool
def get_knowledge(identifier: str):
    """
    Gets information from the knowledge base as saved by the LLM.
    
    """
    value = settings.KNOWLEDGE_BASE.get(identifier, "None")
    if value == "None" or value is None:
        raise ValueError(f"'{identifier}' not found in knowledge base.")
    else:
        return value
    

TOOL_SPEC = get_knowledge.tool_spec()