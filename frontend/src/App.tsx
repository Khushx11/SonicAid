import { useState } from "react";
import AudioCapture from "./components/AudioCapture";
import WaveformView from "./components/WaveformView";
import SpectrogramView from "./components/SpectrogramView";
import ClassProbabilitiesChart from "./components/ClassProbabilitiesChart";
import SessionTimeline from "./components/SessionTimeline";
import AttentionHeatmap from "./components/AttentionHeatmap";
import SessionReportDownload from "./components/SessionReportDownload";
import { API_BASE } from "./api/client";
import { useWebSocketStream } from "./hooks/useWebSocketStream";

export default function App() {
  const [lastPcm, setLastPcm] = useState<Int16Array | null>(null);

  const wsUrl = (() => {
    const u = new URL(API_BASE);
    u.protocol = u.protocol === "https:" ? "wss:" : "ws:";
    u.pathname = "/ws/stream";
    return u.toString();
  })();

  // Single source of truth for predictions (UI panels read from this).
  const { latestPrediction, history } = useWebSocketStream(wsUrl);

  return (
    <div className="container">
      <div className="row" style={{ justifyContent: "space-between" }}>
        <div>
          <div style={{ fontSize: 22, fontWeight: 800 }}>SonicAid Next-Gen</div>
          <div style={{ opacity: 0.8 }}>
            Near real-time audio intelligence for ASD sensory therapy
          </div>
        </div>
        <div className="row">
          <span className="pill">API: {API_BASE}</span>
        </div>
      </div>

      <div style={{ height: 14 }} />

      <AudioCapture onLastPcm={setLastPcm} />

      <div style={{ height: 14 }} />

      <div className="grid">
        <div className="card">
          <WaveformView lastPcm16={lastPcm} />
          <div style={{ height: 12 }} />
          <SpectrogramView lastPcm16={lastPcm} />
        </div>

        <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
          <div className="card">
            <ClassProbabilitiesChart latest={latestPrediction} />
            <div style={{ height: 12 }} />
            <div className="row">
              <span className="pill">
                emotion: {latestPrediction?.emotion ?? "—"}
              </span>
              <span className="pill">
                noise:{" "}
                {latestPrediction ? latestPrediction.noise_intensity.toFixed(2) : "—"}
              </span>
              <span className="pill">
                engagement:{" "}
                {latestPrediction ? latestPrediction.engagement_score.toFixed(2) : "—"}
              </span>
            </div>
            <div style={{ height: 12 }} />
            <SessionReportDownload history={history} />
          </div>

          <div className="card">
            <AttentionHeatmap latest={latestPrediction} />
          </div>
        </div>
      </div>

      <div style={{ height: 14 }} />

      <div className="card">
        <SessionTimeline history={history} />
      </div>
    </div>
  );
}

