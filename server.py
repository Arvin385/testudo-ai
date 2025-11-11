# server.py
from fastapi import FastAPI
from agent.planner import plan
from agent.executor import execute
from agent.explainer import explain

app = FastAPI()

@app.post("/run")
def run_agent(user_input: dict):
    user_query = user_input.get("query", "")
    errors: list[tuple[str, dict]] = [("1", {"1" : "1"})]
    while True:
        plan_data, agent_chat = plan(user_query)
        result, errors = execute(plan_data)
        if (len(errors) <= 0): 
            break
        else:
            agent_chat += "\n When running the commands, you ran into the below errors. Please make new requests to the tools accordingly:\n\n"
            for err in errors:
                err_msg = f"Error on tool {err[0]}: {err[1]}"
                agent_chat += err_msg
                print(err_msg)
            
    agent_output = explain(agent_chat, result)
    return result, agent_output

if __name__ == "__main__":
    #import uvicorn
    #uvicorn.run(app, host="0.0.0.0", port=8000)

    user_input = {

        "query" : input()
    }
    print(run_agent(user_input))