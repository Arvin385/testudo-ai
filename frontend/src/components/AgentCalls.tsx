import /*React,*/ { useState } from "react";

const AgentCalls = () => {
  const [messages, setMessages] = useState([{
                "role" : "admin",
                "content" : "Introduce yourself as Testudo AI, the agentic assistant for all UMD students to love! You will help them with their pursuits on campus. Tell them what you can do. Be descriptive and very kind throughout the interaction."
            }]);
  const [text, setText] = useState("");
  const [isLoading, setIsLoading] = useState(false);

  const speak = async () => {
    if (!messages) return;
    if (!text) return;

    //Update the message with the new user text
    const newMessages = messages;
    newMessages.push({
        "role" : "user",
        "content" : text
    });
    setMessages(newMessages);

    setIsLoading(true);
    
    console.log("Asking LLM...");

    //Use try/catch and fetch to prompt the llm
    try {
      const response = await fetch(
        "http://127.0.0.1:5000/prompt-llm", // Voice ID
        {
          method: "POST",
          headers: { "Content-Type" : "application/json" },
          body: JSON.stringify({"messages": messages}),
        }
      );
      
      //If the response is nonexistent, throw an error
      if (!response) {
        throw new Error("Agent returned empty context");
      }

      //If the data is nonexistent or invalid, throw an error
      const data = await response.json();
      if (!data.messages || !(data.messages instanceof Array)) {
        throw new Error("Agent returned empty/invalid context");
      } else {
        setMessages(data.messages);
      }

    //In the case of errors, handle issues for users with alerts
    } catch (error) {
      console.error("Error:", error);
      alert(`Agent could not be reached with error: ${error}`);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div
      style={{
        padding: "2rem",
        fontFamily: "sans-serif",
        display: "flex",
        alignItems: "center",
        flexDirection: "column",
      }}
    >
      <h1 id="purple-text">ACM Testudo AI Demo</h1>
      <textarea
        value={text}
        onChange={(e) => setText(e.target.value)}
        placeholder="Type something... (We have limited tokens though so chill)"
        rows={4}
        style={{ width: "100%", fontSize: "1rem", marginBottom: "1rem" }}
      />
      <br />
      <button onClick={speak} disabled={isLoading}>
        {isLoading ? "Generating..." : "Ask LLM"}
      </button>
    <p>{JSON.stringify(messages)}</p>
    </div>
  );
};

export default AgentCalls;
