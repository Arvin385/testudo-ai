import './ChatWindow.css'
import type { Message } from '../types/message'

interface ChatWindowProps {
  messages: Message[]
}

function ChatWindow({ messages }: ChatWindowProps) {
  return (
    <div className="chat-window">
      <div className="chat-header">
        <h2>Testudo AI</h2>
      </div>

      <div className="messages-container">
        {messages
          .filter((message) => message.role === 'user' || message.role === 'agent')
          .map((message, index) => (
            <div
              key={index}
              className={`message ${message.role}`}
            >
              <div className="message-content">
                {message.content}
              </div>
            </div>
          ))}
      </div>
    </div>
  )
}

export default ChatWindow
