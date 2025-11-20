# server.py
from fastapi import FastAPI
from agent.planner import plan
from agent.executor import execute
from agent.explainer import explain
import json

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
    print(run_agent({"query" : "Introduce yourself as Testudo AI, the agentic assistant for all UMD students to love! You will help them with their pursuits on campus. Tell them what you can do. Be sure to include information about how I can type 'end' to end the conversation."})[1])
        
    while True:
        print()
        user_input = {
            "query" : input("USER#> ")
        }
        if (user_input["query"] == "end"):
            break
        output = run_agent(user_input)
        print("============JSON DATA============")
        for o in output[0]:
            print(json.dumps(o, indent=4))
        # print(output[0])
        print("=================================")
        print()
        print(output[1])