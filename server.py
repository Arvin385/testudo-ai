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
    
    keep_old_chat: bool = False
    agent_output = ""
    plan_data = None
    agent_chat = None
    
    while True:
        if agent_chat is not None:
            plan_data, agent_chat = plan(user_query, gemini_output=agent_chat)
        else:
            plan_data, agent_chat = plan(user_query)
        result, errors = execute(plan_data)
        
        # agent_chat = agent_chat + "\n\nRESULTS: \n"
        for res in result:
            agent_chat += "\n" + str(res)
        
        if (len(errors) > 0):
            agent_chat += "\n When running the commands, some of the above tools ran into errors. Please make new requests to the tools accordingly:\n\n" 
        
        agent_output = explain(agent_chat)
        # print("Intermediary agent output" + agent_output)
        if "```" in agent_output:
            agent_chat += "\n\n" + agent_output
        else:
            break
        
    agent_output = explain(agent_chat)
    
    # print("AGENT CHAT: " + agent_chat)
    
    return result, agent_output

if __name__ == "__main__":
    #import uvicorn
    #uvicorn.run(app, host="0.0.0.0", port=8000)

    user_input = {
        "query" : input()
    }
    output = run_agent(user_input)
    print("============JSON DATA============")
    print(output[0])
    print("=================================")
    print()
    print(output[1])