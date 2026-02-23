import { useMemo, useRef, useState } from "react";
import { API_BASE } from "../api/client";
import { useAudioCapture } from "../hooks/useAudioCapture";
import { useWebSocketStream } from "../hooks/useWebSocketStream";

type Props = {
  onLastPcm: (pcm: Int16Array | null) => void;
};

export default function AudioCapture({ onLastPcm }: Props) {
  const wsUrl = useMemo(() => {
    const u = new URL(API_BASE);
    u.protocol = u.protocol === "https:" ? "wss:" : "ws:";
    u.pathname = "/ws/stream";
    return u.toString();
  }, []);

  const { connected, sendChunk, latestPrediction, history } =
    useWebSocketStream(wsUrl);

  const lastPcmRef = useRef<Int16Array | null>(null);
  const [sentChunks, setSentChunks] = useState(0);

  const audio = useAudioCapture({
    sampleRate: 16000,
    onPcmChunk: (buf) => {
      const pcm = new Int16Array(buf);
      lastPcmRef.current = pcm;
      onLastPcm(pcm);
      sendChunk(buf);
      setSentChunks((x) => x + 1);
    },
  });

  return (
    <div className="card">
      <div className="row" style={{ justifyContent: "space-between" }}>
        <div style={{ fontWeight: 700, fontSize: 18 }}>Live streaming</div>
        <div className="row">
          <span className="pill">ws: {connected ? "connected" : "offline"}</span>
          <span className="pill">mic: {audio.running ? "on" : "off"}</span>
        </div>
      </div>
      <div className="row" style={{ marginTop: 12 }}>
        <button className="btn" onClick={audio.start} disabled={audio.running}>
          Start
        </button>
        <button className="btn" onClick={audio.stop} disabled={!audio.running}>
          Stop
        </button>
        <span className="pill">chunks sent: {sentChunks}</span>
        {latestPrediction ? (
          <span className="pill">
            {latestPrediction.primary_class} ·{" "}
            {(latestPrediction.primary_confidence * 100).toFixed(1)}% ·{" "}
            {latestPrediction.latency_ms.toFixed(1)}ms
          </span>
        ) : (
          <span className="pill">waiting for prediction</span>
        )}
      </div>

      <div style={{ marginTop: 12, opacity: 0.85, fontSize: 12 }}>
        Note: This demo streams raw PCM16 chunks; the backend currently returns mocked
        predictions until the model is fully wired for streaming.
      </div>

      <div style={{ marginTop: 12, opacity: 0.85, fontSize: 12 }}>
        history size: {history.length}
      </div>
    </div>
  );
}

