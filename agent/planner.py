import os
import json
from tools import tool_registry
from dotenv import load_dotenv
from google import genai

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
MODEL_NAME = "gemini-2.5-flash"

client = genai.Client(api_key=GEMINI_API_KEY)

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


def plan(user_query: str) -> tuple[dict, str]:
    """
    Generate a JSON plan from Gemini API.
    """
    # Build a prompt describing available tools
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

    gemini_output = query_gemini(prompt)

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

    # ✅ Support both single-step and multi-step formats
    if isinstance(plan_data, dict) and "tool" in plan_data:
        # old format → wrap in plan list
        plan_data = {"plan": [plan_data]}

    if not isinstance(plan_data, dict) or "plan" not in plan_data:
        raise ValueError(f"Gemini returned invalid plan format: {plan_data}")

    return plan_data, prompt + "\n\n YOUR SUGGESTED PLAN: \n" + gemini_output

