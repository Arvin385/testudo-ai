# server.py
from fastapi import FastAPI
from agent.planner import plan
from agent.executor import execute
from agent.explainer import explain

app = FastAPI()

@app.post("/run")
def run_agent(user_input: dict):
    user_query = user_input.get("query", "")
    
    keep_old_chat: bool = False
    agent_output = ""
    plan_data = None
    agent_chat = None
    all_results = []
    
    while True:
        plan_data, agent_chat = plan(user_query, agent_chat=agent_chat)
        
        results, errored, ended = execute(plan_data)
        
        all_results += results
        
        agent_chat = agent_chat + "\n\nHere are the results of the commands you most recently ran: \n"
        for res in results:
            agent_chat += "\n" + str(res)
        
        if errored:
            agent_chat += "\n When running the commands, some of the above tools ran into errors. Please make new requests to the tools accordingly:\n\n" 
            continue
        
        if ended:
            break
        
    agent_output = explain(agent_chat)
    
    end_result = ""
    for res in results:
        if res["tool"] == "end_chat":
            end_result = str(res["result"]["output"])
    
    return all_results, end_result

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