import './App.css'
import ChatWindow from './components/ChatWindow'
import ChatInput from './components/ChatInput'

function App() {
  return (
    <div className="app-container">
      <ChatWindow />

      <div className="content">
        {/* Your content will go here */}
      </div>

      <ChatInput />
    </div>
  )
}

export default App
