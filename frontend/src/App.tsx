import { useState } from "react";
// import reactLogo from "./assets/react.svg";
// import viteLogo from "/vite.svg";
import "./App.css";
import Dictaphone from "./components/Dictaphone";
import Elevenlabs from "./components/Elevenlabs";

function App() {
  const [TTS, setTTS] = useState(false);

  return (
    <>
      <div id="container">
        {!TTS && <Dictaphone />}
        {TTS && <Elevenlabs />}
        <div className="card">
          <button className={TTS ? "" : "active"} onClick={() => setTTS(false)}>
            Speech to Text
          </button>
          <button className={TTS ? "active" : ""} onClick={() => setTTS(true)}>
            Text to speech
          </button>
          <p>TTS/SST Demo</p>
        </div>
      </div>
    </>
  );
}

export default App;
