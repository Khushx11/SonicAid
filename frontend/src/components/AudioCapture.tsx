import { useEffect, useState } from "react";
import { useAudioCapture } from "../hooks/useAudioCapture";
import { useWebSocketStream } from "../hooks/useWebSocketStream";

type StreamClient = ReturnType<typeof useWebSocketStream>;

type Props = {
  onLastPcm: (pcm: Int16Array | null) => void;
  stream: StreamClient;
};

function StatusBadge({ connected, status, running, starting }: { connected: boolean; status: string; running: boolean; starting: boolean }) {
  const isActive = running && connected;

  return (
    <div className="status-bar" role="status" aria-live="polite" aria-label="Connection and capture status">
      {/* WebSocket connection */}
      <span className={`status-badge ${connected ? "badge-success" : "badge-error"}`}>
        <span className={`status-dot ${isActive ? "dot-pulse" : ""}`} aria-hidden="true" />
        {connected ? "Connected" : "Offline"}
      </span>

      {/* Model state */}
      {status === "ready" && (
        <span className="status-badge badge-cyan">
          <span className="status-dot" aria-hidden="true" />
          Model ready
        </span>
      )}
      {status === "model_unavailable" && (
        <span className="status-badge badge-warning">
          <span className="status-dot" aria-hidden="true" />
          No checkpoint
        </span>
      )}
      {status === "connecting" && (
        <span className="status-badge badge-neutral">
          <span className="status-dot" aria-hidden="true" />
          Connecting…
        </span>
      )}
      {status === "disconnected" && (
        <span className="status-badge badge-error">
          <span className="status-dot" aria-hidden="true" />
          Disconnected
        </span>
      )}

      {/* Microphone */}
      {!starting && (
        <span className={`status-badge ${running ? "badge-cyan" : "badge-neutral"}`}>
          <span className={`status-dot ${running ? "dot-pulse" : ""}`} aria-hidden="true" />
          {running ? "Microphone on" : "Microphone off"}
        </span>
      )}
      {starting && (
        <span className="status-badge badge-neutral">
          <span className="status-dot" aria-hidden="true" />
          Requesting mic…
        </span>
      )}
    </div>
  );
}

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

  const canStart = !audio.running && !audio.starting && connected && status === "ready";

  return (
    <div className="capture-card">
      <div className="capture-card-header">
        <h2 className="capture-card-title">Live Capture</h2>
        <StatusBadge
          connected={connected}
          status={status}
          running={audio.running}
          starting={audio.starting}
        />
      </div>

      <div className="capture-controls">
        <button
          className="btn btn-primary"
          onClick={audio.start}
          disabled={!canStart}
          aria-label="Start microphone capture"
        >
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden="true">
            <circle cx="12" cy="12" r="10"/>
            <polygon points="10 8 16 12 10 16 10 8"/>
          </svg>
          {audio.starting ? "Requesting mic…" : "Start capture"}
        </button>

        <button
          className="btn btn-secondary"
          onClick={endCapture}
          disabled={!audio.running && !audio.starting}
          aria-label="Stop microphone capture and reset session"
        >
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden="true">
            <rect x="3" y="3" width="18" height="18" rx="2" ry="2"/>
          </svg>
          Stop
        </button>

        {(status === "disconnected" || status === "model_unavailable") && (
          <button
            type="button"
            className="btn btn-ghost"
            onClick={restart}
            aria-label="Reconnect to backend"
          >
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden="true">
              <polyline points="1 4 1 10 7 10"/>
              <path d="M3.51 15a9 9 0 1 0 .49-3.74"/>
            </svg>
            Reconnect
          </button>
        )}

        {sentChunks > 0 && (
          <span className="chunk-counter">
            {sentChunks} chunk{sentChunks !== 1 ? "s" : ""} sent
          </span>
        )}
      </div>

      <p className="capture-card-hint">
        Classification begins after the first 5-second audio window is processed.
      </p>

      {audio.error && (
        <div className="alert-error" role="alert">
          <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden="true" style={{flexShrink:0,marginTop:1}}>
            <circle cx="12" cy="12" r="10"/>
            <line x1="15" y1="9" x2="9" y2="15"/>
            <line x1="9" y1="9" x2="15" y2="15"/>
          </svg>
          {audio.error}
        </div>
      )}

      {status === "model_unavailable" && (
        <div className="model-unavailable" role="status">
          <strong>No trained checkpoint installed.</strong> Download the ESC-10 model artifact
          and set <code>SONICAID_ESC10_MODEL</code> on the backend before capturing audio.
          Classification is disabled until a checkpoint is loaded.
        </div>
      )}
    </div>
  );
}
