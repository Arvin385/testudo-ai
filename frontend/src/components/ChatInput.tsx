import './ChatInput.css'

function ChatInput() {
  return (
    <div className="textarea-container">
      <textarea
        className="fixed-textarea"
        placeholder="Type your message..."
      />
    </div>
  )
}

export default ChatInput
