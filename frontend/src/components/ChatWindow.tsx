import { useState } from 'react'
import './ChatWindow.css'

interface Message {
  id: string
  role: 'user' | 'agent'
  content: string
  timestamp: Date
}

function ChatWindow() {
  const [messages] = useState<Message[]>([
    // Sample messages for demo - remove later
    {
      id: '1',
      role: 'agent',
      content: 'Hello! How can I assist you today?',
      timestamp: new Date()
    }
  ])

  return (
    <div className="chat-window">
      <div className="chat-header">
        <h2>Chat</h2>
      </div>

      <div className="messages-container">
        {messages.map((message) => (
          <div
            key={message.id}
            className={`message ${message.role}`}
          >
            <div className="message-content">
              {message.content}
            </div>
            <div className="message-timestamp">
              {message.timestamp.toLocaleTimeString()}
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}

export default ChatWindow
