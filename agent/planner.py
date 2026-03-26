# planner.py

import os
import json
from tools import tool_registry
from google import genai
from pydantic import BaseModel, Field
from typing import Any
from dotenv import load_dotenv
from time import sleep

load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
MODEL_NAME = "gemini-2.5-flash-lite"
# MODEL_NAME = "gemma-3-27b"
client = genai.Client(api_key=GEMINI_API_KEY)

# System prompt for gemini
SYSTEM_PROMPT:str = f"""============SYSTEM PROMPT=============
You are an AI agent planner for UMD students, with tools as described as below. 
As you make use of the tools, use the following guidelines:
'plan' must be a list of one or more steps. Each step is an object with keys 'tool' and 'params'. 
'tool' must be one of the available tool names, and 'params' must contain all required parameters.
If the user asks for multiple actions, include multiple steps in the plan in logical order.
Feed all your jsons in between three ticks: ```{{json}}```
Make sure parameter names exactly match the tool specifications (for example, 'a' and 'b' for add_numbers).
Also, ensure you follow the specified types in each tool spec. If a type is _empty, it's a placeholder, so use your best judgement.
And make sure that once you're done or want to hand control back to the user, you use end_tooling or ask_user as outlined below.
\n==============TOOL SPECS==============
"""


for tool in tool_registry.values():
    SYSTEM_PROMPT += f"*******(TOOL)  {tool['spec']['name']}:\n"
    SYSTEM_PROMPT += f"     (params): {tool['spec']['parameters']}\n"
    SYSTEM_PROMPT += f"    (returns): {tool['spec']['outputs']}\n"
    SYSTEM_PROMPT += f"(description): {tool['spec']['description']}\n"
    SYSTEM_PROMPT += "\n"
    
SYSTEM_PROMPT += "\n==============USER CHATS==============\n\n"

JSON_SCHEMA: str = '"{{tool}}": "<tool-name>", '

class PlanStep(BaseModel):
    tool: str = Field(description="Name of tool to execute.", title="Tool Name")
    params: dict[str, Any] = Field(description="Parameters of tool to be used", title = "Parameters")

class JSONPlan(BaseModel):
    plans: list[PlanStep] = Field(description="Plan including all steps (tools) to be used", title="Plan")

def _call_gemini_raw(prompt_text: str) -> str:
    """
    send the prompt to Gemini and return raw text
    """
    dev_continue = input(f"Model called on input w/ length {len(prompt_text)}. Hit 's' + enter to show: ")
    
    if (dev_continue == "s"):
        print(prompt_text)
        print(JSONPlan.model_json_schema())
        input("Press enter to continue.")
        
    response = client.models.generate_content(
        model=MODEL_NAME,
        contents=prompt_text,
        config={
            "response_mime_type": "application/json",
            "response_json_schema": JSONPlan.model_json_schema(),
        }
    )
    
    dev_continue = input(f"Model sent output w/ length {len(response.text.strip())}. Hit 's' + enter to show: ")
    if (dev_continue == 's'):
        print(response.text.strip())
        input("Press enter to continue")
        
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

def new_plan(messages: list[dict]) -> list[dict]:
    """
    build plan based on prior conversation
    call Gemini
    parse output
    return dict
    """
    
    # tool_descriptions: str = "\n".join(
    #     [f"- {t['spec']['name']}: {t['spec']['description']}" for t in tool_registry.values()]
    # )
    
    agent_chat: str = SYSTEM_PROMPT 
    
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
    plan_data = json.loads(gemini_output)["plans"]
    # print("Here's the plan: " + str(plan_data))

    return plan_data