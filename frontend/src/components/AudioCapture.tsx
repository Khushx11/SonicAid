import { useRef, useState } from "react";
import { useAudioCapture } from "../hooks/useAudioCapture";
import { useWebSocketStream } from "../hooks/useWebSocketStream";

type StreamClient = ReturnType<typeof useWebSocketStream>;

type Props = {
  onLastPcm: (pcm: Int16Array | null) => void;
  stream: StreamClient;
};

export default function AudioCapture({ onLastPcm, stream }: Props) {
  const { connected, status, sendChunk, latestPrediction, history } = stream;

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
          <span className="pill">model: {status}</span>
          <span className="pill">mic: {audio.running ? "on" : "off"}</span>
        </div>
      </div>
      <div className="row" style={{ marginTop: 12 }}>
        <button className="btn" onClick={audio.start} disabled={audio.running || status !== "ready"}>
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
        ESC-10 environmental sound recognition uses real checkpoint-backed predictions after a
        five-second audio window. It does not measure emotion or therapy outcomes.
      </div>

      {status === "model_unavailable" ? (
        <div style={{ marginTop: 12, fontSize: 13 }}>
          No trained checkpoint is installed. Download the ESC-10 model artifact and set
          SONICAID_ESC10_MODEL on the backend before starting audio capture.
        </div>
      ) : null}
      <div style={{ marginTop: 12, opacity: 0.85, fontSize: 12 }}>
        history size: {history.length}
      </div>
    </div>
  );
}

