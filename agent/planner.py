# planner.py

import os
import json
from tools import tool_registry
from google import genai
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


def query_gemini(prompt_text: str) -> str:
    """
    Send a prompt to Gemini API and return the text output.
    """
    response = client.models.generate_content(
        model=MODEL_NAME,
        contents=prompt_text,
        config={
            "response_mime_type": "application/json",
            "response_json_schema": JSONPlan.model_json_schema(),
        }
    )

    # The SDK returns a structured object
    text_output = response.text.strip()
    return text_output


load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
MODEL_NAME = "gemini-2.5-flash"

client = genai.Client(api_key=GEMINI_API_KEY)

def query_gemini(prompt_text: str) -> str:
    """
    Generate a JSON plan from Gemini API.
    """
    # Build a prompt describing available tools
    tool_descriptions = "\n".join(
        [f"- {t['spec']['name']}: {t['spec']['description']}" for t in tool_registry.values()]
    )

    prompt = (
        f"You are an AI agent planner. "
        f"The user gave the query: '{user_query}'.\n"
        f"Available tools:\n{tool_descriptions}\n"
        f"Return a JSON object with keys 'tool' and 'params'. "
        f"'tool' must be one of the available tool names, and 'params' must contain "
        f"all required parameters. 'params' must be outputted as a dictionary with the key as the required parameters "
        f"and the value as the the value of the corresponding parameter.  If that parameter is not provided by the output, "
        f"don't include it in the created dictionary."
        f"Make sure parameter names exactly match the tool specifications (for example, 'a' and 'b' for add_numbers).\n"
    )

    gemini_output = query_gemini(prompt)

    print("Gemini raw output:", gemini_output)

    # --- Simple cleanup ---
    cleaned_output = gemini_output.strip()
    if cleaned_output.startswith("```"):
        cleaned_output = cleaned_output.split("```")[1]  # take text between fences
    cleaned_output = cleaned_output.replace("json", "", 1).strip()

    # Safely parse JSON output
    try:
        plan_data = json.loads(cleaned_output)
    except json.JSONDecodeError as e:
        raise ValueError(f"Gemini did not return valid JSON: {e}\nOutput: {gemini_output}")

    if not isinstance(plan_data, dict) or "tool" not in plan_data or "params" not in plan_data:
        raise ValueError(f"Gemini returned invalid plan format: {plan_data}")

    return plan_data
