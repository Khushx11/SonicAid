import { useState } from "react";
import AudioCapture from "./components/AudioCapture";
import WaveformView from "./components/WaveformView";
import SpectrogramView from "./components/SpectrogramView";
import ClassProbabilitiesChart from "./components/ClassProbabilitiesChart";
import SessionTimeline from "./components/SessionTimeline";
import SessionReportDownload from "./components/SessionReportDownload";
import { API_BASE } from "./api/client";
import { useWebSocketStream } from "./hooks/useWebSocketStream";

const streamUrl = new URL("/ws/stream", API_BASE);
streamUrl.protocol = streamUrl.protocol === "https:" ? "wss:" : "ws:";

export default function App() {
  const [lastPcm, setLastPcm] = useState<Int16Array | null>(null);
  const stream = useWebSocketStream(streamUrl.toString());

  return (
    <main className="container">
      <header className="page-header">
        <div>
          <p className="brand">SonicAid</p>
          <h1>Environmental sound monitor</h1>
          <p>Classify live microphone audio into ten ESC-10 sound categories.</p>
        </div>
        <a href="https://github.com/Khushx11/SonicAid/blob/main/docs/esc10_model_card.md">
          Model card ↗
        </a>
      </header>

      <AudioCapture onLastPcm={setLastPcm} stream={stream} />

      <div className="grid">
        <section className="card signal" aria-label="Microphone signal">
          <h2>Microphone signal</h2>
          <WaveformView lastPcm16={lastPcm} />
          <SpectrogramView lastPcm16={lastPcm} />
        </section>
        <section className="card" aria-label="Latest classification">
          <h2>Latest classification</h2>
          <ClassProbabilitiesChart latest={stream.latestPrediction} />
          <p className="muted">The score is uncalibrated. Unfamiliar sounds can still receive a label.</p>
        </section>
      </div>

      <section className="card" aria-label="Session timeline">
        <div className="section-header">
          <h2>Session timeline</h2>
          <SessionReportDownload history={stream.history} />
        </div>
        <SessionTimeline history={stream.history} />
      </section>
    </main>
  );
}
