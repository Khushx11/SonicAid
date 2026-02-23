import type { PredictionMessage } from "../hooks/useWebSocketStream";

type Props = {
  latest: PredictionMessage | null;
};

export default function AttentionHeatmap({ latest }: Props) {
  const has = !!latest?.attention_heatmap;
  return (
    <div>
      <div className="row">
        <span className="pill">Attention heatmap</span>
        <span className="pill">{has ? "available" : "not available"}</span>
      </div>
      <div style={{ opacity: 0.85, marginTop: 10 }}>
        {has
          ? "Heatmap payload received (rendering hook to be added when backend exports attention maps)."
          : "Backend currently does not export attention maps in this scaffold."}
      </div>
    </div>
  );
}

