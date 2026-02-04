# planner.py

import os
import json
from tools import tool_registry
import google.genai as genai
from pydantic import BaseModel, Field
from typing import Dict
from dotenv import load_dotenv

load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
MODEL_NAME = "gemini-2.5-flash"
client = genai.Client(api_key=GEMINI_API_KEY)


class JSONPlan(BaseModel):
    tool: str = Field(description="Name of tool to execute.")
    params: Dict[str,str]


def extract_json_objects(text: str) -> list[dict]:
    """
    Extracts only top-level (outermost) JSON objects or arrays from a text string.
    Nested JSON objects within other JSONs are ignored.

    Args:
        text (str): A string containing one or more JSON objects or arrays,
                    possibly mixed with other text.

    Returns:
        list: A list of successfully parsed top-level JSON objects (dicts or lists).
    """
    json_objects: list[dict] = []
    stack = []
    start_idx = None
    in_string = False
    escape = False

    for i, ch in enumerate(text):
        if ch == '"' and not escape:
            in_string = not in_string
        elif ch == '\\' and not escape:
            escape = True
            continue

        if not in_string:
            if ch in '{[':
                # If this is the start of a new outermost JSON, mark it
                if not stack:
                    start_idx = i
                stack.append(ch)
            elif ch in '}]' and stack:
                opening = stack.pop()
                # Ensure proper matching of brackets
                if (opening == '{' and ch != '}') or (opening == '[' and ch != ']'):
                    stack.clear()
                    start_idx = None
                    continue
                # If stack is now empty, we’ve closed a top-level JSON
                if not stack and start_idx is not None:
                    candidate = text[start_idx:i + 1]
                    try:
                        obj = json.loads(candidate)
                        # print("OBJ IN USE: " + str(obj))
                        json_objects.append(obj)
                    except json.JSONDecodeError:
                        pass
                    start_idx = None

        escape = False

    return json_objects

def _call_gemini_raw(prompt_text: str) -> str:
    """
    send the prompt to Gemini and return raw text
    """
    response = client.models.generate_content(
        model=MODEL_NAME,
        contents=prompt_text,
        config={
            "response_mime_type": "application/json",
            "response_json_schema": JSONPlan.model_json_schema(),
        }
    )
    return response.text.strip()

def query_gemini(prompt_text: str) -> str:
    """
    Send a prompt to Gemini API and return the text output.
    """
    response = client.models.generate_content(
        model=MODEL_NAME,
        contents=prompt_text
    )

    # The SDK returns a structured object
    text_output = response.text.strip()
    return text_output

def new_plan(messages: list[dict]):
    """
    build plan based on prior conversation
    call Gemini
    parse output
    return dict
    """
    
    tool_descriptions: str = "\n".join(
        [f"- {t['spec']['name']}: {t['spec']['description']}" for t in tool_registry.values()]
    )

    # System prompt for gemini
    prompt: str = (
        f"**SYSTEM PROMPT**"
        f"You are an AI agent planner. "
        f"You have these available tools:\n{tool_descriptions}\n"
        f"Return a JSON object with a key 'plan'. "
        f"'plan' must be a list of one or more steps. Each step is an object with keys 'tool' and 'params'. "
        f"'tool' must be one of the available tool names, and 'params' must contain all required parameters. "
        f"If the user asks for multiple actions, include multiple steps in the plan in logical order."
        f"Feed all your jsons in between three ticks: ```{{json}}```"
        f"Make sure parameter names exactly match the tool specifications (for example, 'a' and 'b' for add_numbers).\n"
        f"And if you NO LONGER need to use tools to answer the user's question, type END TOOLING in all caps."
    )
    
    agent_chat: str = ""
    agent_chat += prompt + "\n\n"
    
    # Loop through the messages, add them to the ongoing chat
    for message in messages:
        agent_chat += "**" + message["role"].upper() + "**:\n"
        agent_chat += message["content"] + "\n\n"
            
        
    gemini_output = _call_gemini_raw(agent_chat)

    # print("HERE'S THE AGENT CHAT: " + agent_chat)
    # print("========================AGENT-CHAT========================")
    # print(agent_chat)
    # print("======================GEMINI-OUTPUT=======================")
    # print(gemini_output)
    # print("==========================================================")
    # print("Here's my raw output: " + gemini_output)
    # --- Simple cleanup ---
    plan_data = extract_json_objects(gemini_output)
    # print("Here's the plan: " + str(plan_data))

    return plan_data