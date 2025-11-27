from flask import Flask, request, jsonify
import os
import json
import settings

app = Flask(__name__)

messages: list[str] = []

@app.route("/send-question", methods=['POST'])
def send_question(question: str):
    return {
        "question" : question
    }
    
    # data will look like this: {"query": <user_query>}
    # run data through backend and return result

@app.route("/prompt-llm", methods=["GET"])
def prompt_llm():
    # global messages
    settings.messages = request.args.get("messages", "none")
    
    # Some error handling for empty requests
    if (settings.messages == "none"):
        return {
            "messages" : [
                {"role" : "user", "content" : "none"},
                {"role" : "agent", "content" : "I'm sorry, I didn't get that. What would you like to do?"}
                ]
        }
        
    # Some error handling for empty messages
    for msg in settings.messages:
        if (msg["content"] == "" or msg["content"] is None):
            msg["content"] = "none"
    
    settings.messages = new_run_agent()[1]
    return settings.messages
    
# Strategy: 
# Replace while loop with a consistent output request
# Have a variable for keep_thinking and show_user
# keep_thinking tells the frontend to re-request that prompt
# show_users tells the frontend to show the user the output in all its glory

# Easier:
# Messages array
# Users: Agent, Tools, User
# Every time ask_question or end_convo is called, send the whole array
# To talk to the agent, feed in the whole discussion

# server.py
# from fastapi import FastAPI
from agent.planner import new_plan
from agent.executor import new_execute
# from agent.explainer import explain

def new_run_agent():
    # Using messages, assuming it is defined outside
    # global messages
    plan_data = None
    all_results = []
    
    while True:
        plan_data = new_plan(settings.messages)
        
        results, errored, ended = new_execute(plan_data)
        
        if ended:
            break
        
        all_results += results
        
        settings.messages.append({})
        settings.messages[-1]["role"] = "tools"
        settings.messages[-1]["content"] = ""
        
        
        for res in results:
            settings.messages[-1]["content"] += "\n" + str(res)
        
        if errored:
            settings.messages.append({
                "role" : "admin",
                "content" : "When running the commands, some of the above tools ran into errors. Please make new requests to the tools accordingly."
            })
            continue
        
    # end_result = ""
    # for res in results:
    #     if res["tool"] == "end_chat":
    #         end_result = str(res["result"]["output"])
    # settings.messages.append({"uewoiqeuwq"})
    return all_results, settings.messages

# if __name__ == "__main__": 
#     port = int(os.environ.get("PORT", 8080))
#     app.run(host="localhost", port=port)


# server.py
from fastapi import FastAPI
from agent.planner import plan
from agent.executor import execute
from agent.explainer import explain

app = FastAPI()

@app.post("/run")
def run_agent(user_query: str):
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
    settings.messages = [
        {
            "role" : "admin",
            "content" : "Introduce yourself as Testudo AI, the agentic assistant for all UMD students to love! You will help them with their pursuits on campus. Tell them what you can do. Be sure to include information about how I can type 'end' to end the conversation."
        }
    ]
    
    new_run_agent()
    
    print(settings.messages[-1]["content"])
    while True:
        print()
        user_input = {
            "role" : "user",
            "content" : input("USER#> ")
        }
        if (user_input["content"] == "end"):
            break
        settings.messages.append(user_input)
        output = new_run_agent()
        # print("============JSON DATA============")
        # for o in output[0]:
        #     print(json.dumps(o, indent=4))
        # print("=================================")
        # print()
        print(settings.messages[-1]["content"])
