import type { PredictionMessage } from "../hooks/useWebSocketStream";

export default function SessionTimeline({ history }: { history: PredictionMessage[] }) {
  if (history.length === 0) {
    return <p className="muted">Predictions will appear here as the model processes audio.</p>;
  }

  return (
    <div className="table-scroll">
      <table>
        <thead><tr><th>Audio window</th><th>Top class</th><th>Model score</th><th>Inference time</th></tr></thead>
        <tbody>
          {history.slice(-30).reverse().map((prediction) => (
            <tr key={`${prediction.session_id}-${prediction.window_start}`}>
              <td>{prediction.window_start.toFixed(1)}–{prediction.window_end.toFixed(1)} s</td>
              <td>{prediction.primary_class.replaceAll("_", " ")}</td>
              <td>{(prediction.primary_confidence * 100).toFixed(1)}%</td>
              <td>{prediction.latency_ms.toFixed(1)} ms</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
