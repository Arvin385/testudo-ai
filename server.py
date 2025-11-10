# server.py
from fastapi import FastAPI
from agent.planner import plan
from agent.executor import execute
from agent.explainer import explain

app = FastAPI()

@app.post("/run")
def run_agent(user_input: dict):
    user_query = user_input.get("query", "")
    plan_data, agent_chat = plan(user_query)
    result = execute(plan_data)
    agent_output = explain(agent_chat, result)
    return result, agent_output

if __name__ == "__main__":
    #import uvicorn
    #uvicorn.run(app, host="0.0.0.0", port=8000)

    user_input = {

        "query" : input()
    }
    print(run_agent(user_input))