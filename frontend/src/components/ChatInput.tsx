import { useState, useRef, useEffect } from 'react'
import './ChatInput.css'

interface ChatInputProps {
  onSendMessage: (text: string) => void
  isLoading: boolean
}

function ChatInput({ onSendMessage, isLoading }: ChatInputProps) {
  const [height, setHeight] = useState(80)
  const [text, setText] = useState('')
  const isDragging = useRef(false)
  const startY = useRef(0)
  const startHeight = useRef(0)

  const handleMouseDown = (e: React.MouseEvent) => {
    isDragging.current = true
    startY.current = e.clientY
    startHeight.current = height
    document.body.style.cursor = 'ns-resize'
    document.body.style.userSelect = 'none'
  }

  const handleSend = () => {
    if (!text.trim() || isLoading) return
    onSendMessage(text)
    setText('')
  }

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  useEffect(() => {
    const handleMouseMove = (e: MouseEvent) => {
      if (!isDragging.current) return

      const deltaY = startY.current - e.clientY
      const newHeight = Math.min(Math.max(startHeight.current + deltaY, 80), 400)
      setHeight(newHeight)
    }

    const handleMouseUp = () => {
      isDragging.current = false
      document.body.style.cursor = ''
      document.body.style.userSelect = ''
    }

    window.addEventListener('mousemove', handleMouseMove)
    window.addEventListener('mouseup', handleMouseUp)

    return () => {
      window.removeEventListener('mousemove', handleMouseMove)
      window.removeEventListener('mouseup', handleMouseUp)
    }
  }, [height])

  return (
    <div className="textarea-container">
      <div
        className="resize-handle"
        onMouseDown={handleMouseDown}
      >
        <div className="resize-handle-line"></div>
      </div>
      <textarea
        className="fixed-textarea"
        placeholder={isLoading ? "Generating..." : "Type your message... (Enter to send, Shift+Enter for new line)"}
        style={{ height: `${height}px` }}
        value={text}
        onChange={(e) => setText(e.target.value)}
        onKeyPress={handleKeyPress}
        disabled={isLoading}
      />
    </div>
  )
}

export default ChatInput
