import type { PredictionMessage } from "../hooks/useWebSocketStream";

type Props = {
  history: PredictionMessage[];
};

function toCsv(history: PredictionMessage[]) {
  const header = [
    "session_id",
    "window_start",
    "window_end",
    "primary_class",
    "primary_confidence",
    "emotion",
    "noise_intensity",
    "engagement_score",
    "latency_ms",
  ];
  const rows = history.map((p) => [
    p.session_id,
    p.window_start,
    p.window_end,
    p.primary_class,
    p.primary_confidence,
    p.emotion,
    p.noise_intensity,
    p.engagement_score,
    p.latency_ms,
  ]);
  return [header, ...rows].map((r) => r.join(",")).join("\n");
}

export default function SessionReportDownload({ history }: Props) {
  const onDownload = () => {
    const csv = toCsv(history);
    const blob = new Blob([csv], { type: "text/csv;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `sonicaid_session_${Date.now()}.csv`;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="row" style={{ justifyContent: "space-between" }}>
      <button className="btn" onClick={onDownload} disabled={history.length === 0}>
        Download CSV
      </button>
    </div>
  );
}

