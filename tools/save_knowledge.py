# Code for a tool to the allow the LLM to save knowledge to a central dict
from tools.tooling import Tool
from tools.tooling import tool
import settings

# Note: This is a proxy for end_task, with different instructions
@tool
def save_knowledge(identifier: str) -> str:
    """
    Saves the return value of the previous tool into a variable, accessible via the identifier.
    This information is then later accessible by calling get_knowledge later or using $identifier in 

    Use this if planning on using any tools with reused outputs. For example, in calculating 1+(2-3),
    save the output of sub(2,3) and feed it as a parameter to the add function.
        Ex: x=sub(2,3); add(1,$x). 
    
    """
    value = settings.KNOWLEDGE_BASE.get(identifier, "None")
    if value == "None" or value is None:
        return f"Value saved to identifier {identifier} with no issues.", identifier
    else:
        return f"Value saved to identifier {identifier}, overriding previous value of {value}.", identifier
    

TOOL_SPEC = save_knowledge.tool_spec()