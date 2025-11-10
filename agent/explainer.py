import os
import json
from tools import tool_registry
from dotenv import load_dotenv
from google import genai
from agent.planner import query_gemini

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
MODEL_NAME = "gemini-2.5-flash"

client = genai.Client(api_key=GEMINI_API_KEY)

def explain(agent_chat: str, result: list):
    agent_chat = agent_chat + "\n\nRESULTS: \n"
    for res in result:
        agent_chat += "\n" + str(res)
    agent_chat += "\n\n" + "Given the above output, tell the user the result of their query. "
    return query_gemini(agent_chat)