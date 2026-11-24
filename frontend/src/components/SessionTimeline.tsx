import type { PredictionMessage } from "../hooks/useWebSocketStream";

type Props = {
  history: PredictionMessage[];
};

export default function SessionTimeline({ history }: Props) {
  const recent = history.slice(-30);
  return (
    <div>
      <div className="row">
        <span className="pill">Session timeline</span>
        <span className="pill">events: {history.length}</span>
      </div>
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "1fr 1fr 1fr",
          gap: 10,
          marginTop: 10,
        }}
      >
        {recent.map((p, idx) => (
          <div
            key={`${p.window_start}-${idx}`}
            style={{
              padding: 10,
              borderRadius: 12,
              border: "1px solid rgba(255,255,255,0.12)",
              background: "rgba(255,255,255,0.06)",
            }}
          >
            <div style={{ fontWeight: 650 }}>{p.primary_class}</div>
            <div style={{ opacity: 0.85, fontSize: 12 }}>
              emotion: {p.emotion ?? "not measured"}
            </div>
            <div style={{ opacity: 0.8, fontSize: 12 }}>
              noise: {p.noise_intensity?.toFixed(2) ?? "—"} · engage:{" "}
              {p.engagement_score?.toFixed(2) ?? "—"}
            </div>
            <div style={{ opacity: 0.75, fontSize: 12 }}>
              latency: {p.latency_ms.toFixed(1)}ms
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

