import { useEffect, useState } from "react";
import { useAudioCapture } from "../hooks/useAudioCapture";
import { useWebSocketStream } from "../hooks/useWebSocketStream";

type StreamClient = ReturnType<typeof useWebSocketStream>;

type Props = {
  onLastPcm: (pcm: Int16Array | null) => void;
  stream: StreamClient;
};

export default function AudioCapture({ onLastPcm, stream }: Props) {
  const { connected, status, sendChunk, restart } = stream;

  const [sentChunks, setSentChunks] = useState(0);

  const audio = useAudioCapture({
    sampleRate: 16000,
    onPcmChunk: (buf) => {
      const pcm = new Int16Array(buf);
      onLastPcm(pcm);
      sendChunk(buf);
      setSentChunks((x) => x + 1);
    },
  });

  const { stop } = audio;
  useEffect(() => {
    if (!connected || status !== "ready") {
      stop();
      onLastPcm(null);
    }
  }, [connected, status, stop, onLastPcm]);

  function endCapture() {
    stop();
    onLastPcm(null);
    setSentChunks(0);
    restart();
  }

  return (
    <div className="card">
      <div className="row" style={{ justifyContent: "space-between" }}>
        <h2>Live capture</h2>
        <div className="row">
          <span className="pill">{connected ? "Connected" : "Offline"}</span>
          <span className="pill">Model {status.replaceAll("_", " ")}</span>
          <span className="pill">Microphone {audio.running ? "on" : "off"}</span>
        </div>
      </div>
      <div className="row" style={{ marginTop: 12 }}>
        <button className="btn" onClick={audio.start} disabled={audio.running || audio.starting || !connected || status !== "ready"}>
          {audio.starting ? "Waiting for microphone" : "Start"}
        </button>
        <button className="btn" onClick={endCapture} disabled={!audio.running && !audio.starting}>
          Stop
        </button>
        {(status === "disconnected" || status === "model_unavailable") && (
          <button type="button" className="btn" onClick={restart}>Reconnect</button>
        )}
        <span className="pill">{sentChunks} audio chunks</span>
      </div>
      <p className="muted">The classifier starts after five seconds of audio.</p>

      {audio.error && <p role="alert">{audio.error}</p>}

      {status === "model_unavailable" ? (
        <div style={{ marginTop: 12, fontSize: 13 }}>
          No trained checkpoint is installed. Download the ESC-10 model artifact and set
          SONICAID_ESC10_MODEL on the backend before starting audio capture.
        </div>
      ) : null}
    </div>
  );
}

