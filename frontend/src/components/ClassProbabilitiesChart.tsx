import type { PredictionMessage } from "../hooks/useWebSocketStream";

type Props = {
  latest: PredictionMessage | null;
};

export default function ClassProbabilitiesChart({ latest }: Props) {
  // Only the winning class is emitted. SVC probabilities are not calibrated for clinical use.
  const items = latest
    ? [{ label: latest.primary_class, p: latest.primary_confidence }]
    : [];

  return (
    <div>
      <div className="row">
        <span className="pill">Top environmental sound estimate</span>
      </div>
      {items.length === 0 ? (
        <div style={{ opacity: 0.8 }}>Waiting for predictions…</div>
      ) : (
        <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
          {items.map((it) => (
            <div key={it.label}>
              <div className="row" style={{ justifyContent: "space-between" }}>
                <div style={{ fontWeight: 600 }}>{it.label}</div>
                <div style={{ opacity: 0.9 }}>{(it.p * 100).toFixed(1)}%</div>
              </div>
              <div
                style={{
                  height: 10,
                  borderRadius: 999,
                  background: "rgba(255,255,255,0.10)",
                  overflow: "hidden",
                }}
              >
                <div
                  style={{
                    width: `${Math.max(0, Math.min(1, it.p)) * 100}%`,
                    height: "100%",
                    background: "rgba(72, 222, 128, 0.85)",
                  }}
                />
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

