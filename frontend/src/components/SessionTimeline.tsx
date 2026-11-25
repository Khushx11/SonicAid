import type { PredictionMessage } from "../hooks/useWebSocketStream";

export default function SessionTimeline({ history }: { history: PredictionMessage[] }) {
  if (history.length === 0) {
    return (
      <div className="timeline-empty" aria-live="polite">
        Predictions will appear here as audio windows are processed.
      </div>
    );
  }

  return (
    <div className="timeline-scroll">
      <table aria-label="Session prediction history">
        <thead>
          <tr>
            <th scope="col">Window</th>
            <th scope="col">Sound class</th>
            <th scope="col">Confidence</th>
            <th scope="col">Latency</th>
          </tr>
        </thead>
        <tbody>
          {history.slice(-30).reverse().map((p) => {
            const pct = Math.max(0, Math.min(1, p.primary_confidence));
            const pctStr = (pct * 100).toFixed(1);
            return (
              <tr key={`${p.session_id}-${p.window_start}`}>
                <td style={{ color: "var(--text-muted)", fontSize: "0.8rem" }}>
                  {p.window_start.toFixed(1)}–{p.window_end.toFixed(1)} s
                </td>
                <td className="td-class">
                  {p.primary_class.replace(/_/g, " ")}
                </td>
                <td>
                  <span className="td-confidence">{pctStr}%</span>
                  <span className="mini-bar" aria-hidden="true">
                    <span
                      className="mini-bar-fill"
                      style={{
                        width: `${pct * 100}%`,
                        background: pct >= 0.7 ? "var(--accent-green)" : pct >= 0.4 ? "var(--accent-amber)" : "var(--accent-red)",
                      }}
                    />
                  </span>
                </td>
                <td className="td-latency">{p.latency_ms.toFixed(1)} ms</td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
