import { useEffect, useRef, useState } from "react";

export type PredictionMessage = {
  session_id: string;
  window_start: number;
  window_end: number;
  primary_class: string;
  primary_confidence: number;
  emotion: string | null;
  env_tags: string[];
  noise_intensity: number | null;
  engagement_score: number | null;
  latency_ms: number;
  attention_heatmap?: number[][] | null;
};

export type StreamStatus = "connecting" | "ready" | "model_unavailable" | "disconnected";

export function useWebSocketStream(url: string) {
  const wsRef = useRef<WebSocket | null>(null);
  const [connected, setConnected] = useState(false);
  const [status, setStatus] = useState<StreamStatus>("connecting");
  const [latestPrediction, setLatestPrediction] = useState<PredictionMessage | null>(null);
  const [history, setHistory] = useState<PredictionMessage[]>([]);

  useEffect(() => {
    const ws = new WebSocket(url);
    ws.binaryType = "arraybuffer";
    ws.onopen = () => setConnected(true);
    ws.onmessage = (event) => {
      try {
        const message: unknown = JSON.parse(event.data as string);
        if (typeof message !== "object" || message === null) return;
        if ("type" in message && message.type === "status") {
          if ("status" in message && message.status === "ready") setStatus("ready");
          if ("status" in message && message.status === "model_unavailable")
            setStatus("model_unavailable");
          return;
        }
        if ("primary_class" in message && "primary_confidence" in message) {
          const prediction = message as PredictionMessage;
          setLatestPrediction(prediction);
          setHistory((previous) => [...previous, prediction].slice(-500));
        }
      } catch {
        // Invalid server message: do not insert it into the prediction timeline.
      }
    };
    ws.onclose = () => {
      setConnected(false);
      setStatus((previous) =>
        previous === "model_unavailable" ? previous : "disconnected"
      );
    };
    ws.onerror = () => {
      setConnected(false);
      setStatus((previous) =>
        previous === "model_unavailable" ? previous : "disconnected"
      );
    };
    wsRef.current = ws;
    return () => {
      wsRef.current = null;
      ws.close();
    };
  }, [url]);

  function sendChunk(chunk: ArrayBuffer) {
    if (status === "ready" && wsRef.current?.readyState === WebSocket.OPEN)
      wsRef.current.send(chunk);
  }

  return { connected, status, sendChunk, latestPrediction, history };
}
