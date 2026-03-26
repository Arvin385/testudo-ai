import { useState } from 'react'
import './App.css'
import ChatWindow from './components/ChatWindow'
import ChatInput from './components/ChatInput'
import type { Message } from './types/message'

function App() {
  const [messages, setMessages] = useState<Message[]>([
    {
      role: 'admin',
      content: 'Introduce yourself as Testudo AI, the agentic assistant for all UMD students to love! You will help them with their pursuits on campus. Tell them what you can do. Be descriptive and very kind throughout the interaction.'
    }
  ])
  const [isLoading, setIsLoading] = useState(false)

  const handleSendMessage = async (text: string) => {
    if (!text.trim()) return

    // Add user message to the chat
    const newMessages = [...messages, { role: 'user' as const, content: text }]
    setMessages(newMessages)
    setIsLoading(true)

    console.log('Asking LLM...')

    try {
      const response = await fetch(
        'http://127.0.0.1:5000/prompt-llm',
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ messages: newMessages }),
        }
      )

      // If the response is nonexistent, throw an error
      if (!response) {
        throw new Error('Agent returned empty context')
      }

      // If the data is nonexistent or invalid, throw an error
      const data = await response.json()
      if (!data.messages || !(data.messages instanceof Array)) {
        throw new Error('Agent returned empty/invalid context')
      } else {
        setMessages(data.messages)
      }

    } catch (error) {
      console.error('Error:', error)
      alert(`Agent could not be reached with error: ${error}`)

      const errorMessages = [...newMessages, {
        role: 'system' as const,
        content: 'We apologize, the agent couldn\'t handle that request. Please try again momentarily.'
      }]
      setMessages(errorMessages)
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="app-container">
      <ChatWindow messages={messages} />

      <div className="content">
        {/* Your content will go here */}
      </div>

      <ChatInput onSendMessage={handleSendMessage} isLoading={isLoading} />
    </div>
  )
}

export default App
