import { useEffect, useRef, useState } from "react";

export type PredictionMessage = {
  session_id: string;
  window_start: number;
  window_end: number;
  primary_class: string;
  primary_confidence: number;
  emotion: string;
  env_tags: string[];
  noise_intensity: number;
  engagement_score: number;
  latency_ms: number;
  attention_heatmap?: number[][];
};

export function useWebSocketStream(url: string) {
  const wsRef = useRef<WebSocket | null>(null);
  const [connected, setConnected] = useState(false);
  const [latestPrediction, setLatestPrediction] =
    useState<PredictionMessage | null>(null);
  const [history, setHistory] = useState<PredictionMessage[]>([]);

  useEffect(() => {
    const ws = new WebSocket(url);
    ws.binaryType = "arraybuffer";
    ws.onopen = () => setConnected(true);
    ws.onmessage = (event) => {
      const data = JSON.parse(event.data) as PredictionMessage;
      setLatestPrediction(data);
      setHistory((h) => [...h, data].slice(-500));
    };
    ws.onclose = () => setConnected(false);
    ws.onerror = () => setConnected(false);
    wsRef.current = ws;
    return () => ws.close();
  }, [url]);

  function sendChunk(chunk: ArrayBuffer) {
    wsRef.current?.send(chunk);
  }

  return { connected, sendChunk, latestPrediction, history };
}

