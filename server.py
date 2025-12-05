from flask import Flask, request, jsonify
import os
import json
import settings

from agent.planner import new_plan
from agent.executor import new_execute

app = Flask(__name__)

@app.route("/prompt-llm", methods=["GET"])
def prompt_llm():
    # get the messages from the json body
    body = request.get_json()
    settings.messages = body.get("messages", "none")
    
    # No info at the start of the convo--prompt the LLM to self-introduce
    if (settings.messages == "none"):
        settings.messages = [
            {
                "role" : "admin",
                "content" : "Introduce yourself as Testudo AI, the agentic assistant for all UMD students to love! You will help them with their pursuits on campus. Tell them what you can do. Be descriptive and very kind throughout the interaction."
            }
        ]
        
    # Some error handling for empty messages
    for msg in settings.messages:
        if (msg["content"] == "" or msg["content"] is None):
            msg["content"] = "none"
    
    output = new_run_agent()
    
    # print("============JSON DATA============")
    # for o in output[0]:
    #     print(json.dumps(o, indent=4))
    # print("=================================")
    # print()
    
    settings.messages = output[1]
    return {"messages" : settings.messages}

def new_run_agent():
    # Using messages, assuming it is defined outside
    # global messages
    plan_data = None
    all_results = []
    
    while True:
        # Plan and execute agent instructions
        plan_data = new_plan(settings.messages)
        results, errored, ended = new_execute(plan_data)
        all_results += results
        
        # End the loop as requested by the LLM
        if ended:
            break
        
        # Write information about the tools used as desired
        settings.messages.append({})
        settings.messages[-1]["role"] = "tools"
        settings.messages[-1]["content"] = ""
        
        # Loop through results, fill up the tools message with info about each
        for res in results:
            settings.messages[-1]["content"] += "\n" + str(res)
        
        # Leave a message to the agent from the 'admin' telling the agent to fix its mistakes if there was an error
        if errored:
            settings.messages.append({
                "role" : "admin",
                "content" : "When running the commands, some of the above tools ran into errors. Please make new requests to the tools accordingly."
            })
            continue

    return all_results, settings.messages


if __name__ == "__main__": 
    # port = int(os.environ.get("PORT", 8080))
    # app.run(host="localhost", port=port)
    
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
        print("============JSON DATA============")
        for o in output[0]:
            print(json.dumps(o, indent=4))
        print("=================================")
        print()
        print(settings.messages[-1]["content"])
