# TOOL_SPEC is required; JSON description for the LLM to understand the tool
from tools.tooling import Tool
from tools.tooling import tool
import requests

@tool
def definition(word: str) -> str:
    """
    Looks up the definition of a word using the Free Dictionary API.
    Returns a dictionary with the definition or an error message if not found.
    """
    
    url = f"https://api.dictionaryapi.dev/api/v2/entries/en/{word}"
    response = requests.get(url)
    
    if response.status_code == 200:
        data = response.json()
        # Extract the first definition from the first meaning
        meaning = data[0]['meanings'][0]
        definition_text = meaning['definitions'][0]['definition']
        part_of_speech = meaning['partOfSpeech']
        
        return {
            "word": word,
            "part_of_speech": part_of_speech,
            "definition": definition_text,
            "status": "success"
        }
    elif response.status_code == 404:
        raise Exception(f"No definition found for '{word}' in the online dictionary.") 
    else:
        raise Exception(f"API returned status code {response.status_code}.")


TOOL_SPEC = definition.tool_spec()