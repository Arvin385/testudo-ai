# server.py
from fastapi import FastAPI
from planner import plan
from executor import execute

app = FastAPI()

@app.post("/run")
async def run_agent(user_input: dict):
    user_query = user_input.get("query", "")
    plan_data = plan(user_query)
    result = execute(plan_data)
    return {"plan": plan_data, "result": result}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
