import React from "react";

const styles = {
  container: {
    display: "flex",
    justifyContent: "center",
    padding: "1rem",
  },
  chatWindow: {
    width: "100%",
    maxWidth: "500px",
    height: "400px",
    border: "1px solid #e5e7eb",
    borderRadius: "12px",
    padding: "1rem",
    overflowY: "auto",
    backgroundColor: "#f9fafb",
  },
  messageRow: {
    display: "flex",
    marginBottom: "0.75rem",
  },
  messageBubble: {
    maxWidth: "70%",
    padding: "0.6rem 0.9rem",
    borderRadius: "16px",
    fontSize: "0.95rem",
    lineHeight: "1.3",
    wordBreak: "break-word",
  },
};


export default function ChatFrame({ messages }) {
  return (
    <div style={styles.container}>
      <div style={styles.chatWindow}>
        {messages.map((msg, index) => {
          if (msg.role !== "user" && msg.role !=="agent" && msg.role !== "system") {
            return (<></>);
          }

          const isUser1 = msg.role !== "user";

          return (
            <div
              key={index}
              style={{
                ...styles.messageRow,
                justifyContent: isUser1 ? "flex-start" : "flex-end",
              }}
            >
              <div
                style={{
                  ...styles.messageBubble,
                  backgroundColor: isUser1 ? "#e5e7eb" : "#3b82f6",
                  color: isUser1 ? "#000" : "#fff",
                }}
              >
                {msg.content}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
