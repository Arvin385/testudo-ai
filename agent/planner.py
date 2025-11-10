# planner.py

import os
import json
from tools import tool_registry
from google import genai
from pydantic import BaseModel, Field
from typing import Dict
from dotenv import load_dotenv
from pathlib import Path

load_dotenv()
GEMINI_API_KEY = os.getenv("AIzaSyB81EdQKm2usXlAlmeAvR-IXE-6XHakZ5E")
MODEL_NAME = "gemini-2.5-flash"
client = genai.Client(api_key=GEMINI_API_KEY)


class JSONPlan(BaseModel):
    tool: str = Field(description="Name of tool to execute.")
    params: Dict[str,str]


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
#This function will create a txt that will log the input prompt and output. This file could serve as a basic idea for memory.


def plan(user_query: str) -> tuple[dict, str]:
    """
    build prompt using EXACT SAME TEXT you had before
    call Gemini
    parse output
    return dict
    """
    
    tool_descriptions = "\n".join(
        [f"- {t['spec']['name']}: {t['spec']['description']}" for t in tool_registry.values()]
    )

    # System prompt for gemini
    prompt = (
        f"You are an AI agent planner. "
        f"The user gave the query: '{user_query}'.\n"
        f"Available tools:\n{tool_descriptions}\n"
        f"Return a JSON object with a key 'plan'. "
        f"'plan' must be a list of one or more steps. Each step is an object with keys 'tool' and 'params'. "
        f"'tool' must be one of the available tool names, and 'params' must contain all required parameters. "
        f"If the user asks for multiple actions, include multiple steps in the plan in logical order."
        f"all required parameters."
        f"Make sure parameter names exactly match the tool specifications (for example, 'a' and 'b' for add_numbers).\n"
    )
    
    cached = check_cache(user_query)
    if cached:
        # cached is the raw LLM output json string
        plan_data = json.loads(cached)
        return plan_data, "cached result"
    
    gemini_output = _call_gemini_raw(prompt)

    # --- Simple cleanup ---
    cleaned_output = gemini_output.strip()
    if cleaned_output.startswith("```"):
        cleaned_output = cleaned_output.split("```")[1]
    cleaned_output = cleaned_output.replace("json", "", 1).strip()

    try:
        plan_data = json.loads(cleaned_output)
    except json.JSONDecodeError as e:
        raise ValueError(f"Gemini did not return valid JSON: {e}\nOutput: {cleaned_output}")

    # ✅ Support both single-step and multi-step formats
    if isinstance(plan_data, dict) and "tool" in plan_data:
        # old format → wrap in plan list
        plan_data = {"plan": [plan_data]}

    if not isinstance(plan_data, dict) or "plan" not in plan_data:
        raise ValueError(f"Gemini returned invalid plan format: {plan_data}")
    
    logger(user_query, gemini_output)
    return plan_data, prompt + "\n\n YOUR SUGGESTED PLAN: \n" + gemini_output

def check_cache(q: str):
    file = Path("logs.txt")
    if not file.exists():
        return None
    
    text = file.read_text()
    # simplest: each block separated by --- 
    blocks = text.split("---")
    for block in blocks:
        if q in block:
            # extract output following "LLM output:"
            parts = block.split("LLM output:")
            if len(parts) == 2:
                output = parts[1].strip()
                return output
    return None

def logger(user_prompt, llm_output):
    file = Path("logs.txt")
    with file.open("a") as f:   # append, not write, so you don’t overwrite history
        f.write(f"User prompt: {user_prompt}\nLLM output: {llm_output}\n---\n")
