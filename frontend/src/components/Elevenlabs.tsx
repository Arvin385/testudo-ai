import /*React,*/ { useState } from "react";

const Elevenlabs = () => {
  const [text, setText] = useState("");
  const [isLoading, setIsLoading] = useState(false);

  const speak = async () => {
    if (!text.trim()) return;

    setIsLoading(true);

    try {
      const response = await fetch(
        "https://api.elevenlabs.io/v1/text-to-speech/zZLmKvCp1i04X8E0FJ8B", // Voice ID
        {
          method: "POST",
          headers: {
            "xi-api-key": "sk_8d2189115a7f78f8fe6d7dbcde48749c684a6f0b0f6b2b9b",
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            text,
            model_id: "eleven_multilingual_v2",
          }),
        }
      );

      const arrayBuffer = await response.arrayBuffer();
      const blob = new Blob([arrayBuffer], { type: "audio/mpeg" });
      const url = URL.createObjectURL(blob);
      const audio = new Audio(url);
      audio.play();
    } catch (error) {
      console.error("Error:", error);
      alert("Failed to generate speech");
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
      <h1 id="purple-text">ACM TTS Demo</h1>
      <textarea
        value={text}
        onChange={(e) => setText(e.target.value)}
        placeholder="Type something... (We have limited tokens though so chill)"
        rows={4}
        style={{ width: "100%", fontSize: "1rem", marginBottom: "1rem" }}
      />
      <br />
      <button onClick={speak} disabled={isLoading}>
        {isLoading ? "Generating..." : "Speak"}
      </button>
    </div>
  );
};

export default Elevenlabs;
