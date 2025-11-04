# TOOL_SPEC is required; JSON description for the LLM to understand the tool
TOOL_SPEC = {
    "name": "definition",
    "description": "Looks up the definition of a given word from a predefined dictionary.",
    "parameters": ["word"]  # required parameter
}

def definition(word):
    """
    Looks up the definition of a word from a predefined dictionary.
    Returns a dictionary with the definition or an error message if not found.
    """
    try:
        dictionary = {
            "algorithm": "A set of rules or steps used to solve a problem or perform a computation.",
            "data": "Information that is processed or stored by a computer.",
            "variable": "A named storage location that holds a value in a program.",
            "function": "A block of reusable code that performs a specific task.",
            "class": "A blueprint for creating objects, providing initial values for state and implementations of behavior."
        }

        word_lower = word.lower()
        if word_lower in dictionary:
            return {"word": word_lower, "definition": dictionary[word_lower], "status": "success"}
        else:
            return {"status": "error", "error_message": f"No definition found for '{word}'."}
    except Exception as e:
        return {"status": "error", "error_message": str(e)}
