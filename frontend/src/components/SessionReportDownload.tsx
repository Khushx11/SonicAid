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
  const disabled = history.length === 0;

  const onDownload = () => {
    if (disabled) return;
    const csv = toCsv(history);
    const blob = new Blob([csv], { type: "text/csv;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `sonicaid-session-${new Date().toISOString().slice(0, 19).replace(/:/g, "-")}.csv`;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <button
      type="button"
      className="btn-download"
      onClick={onDownload}
      disabled={disabled}
      aria-label={disabled ? "No session data to export" : `Download session CSV (${history.length} prediction${history.length !== 1 ? "s" : ""})`}
    >
      <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden="true">
        <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
        <polyline points="7 10 12 15 17 10"/>
        <line x1="12" y1="15" x2="12" y2="3"/>
      </svg>
      {disabled ? "Export CSV" : `Export CSV (${history.length})`}
    </button>
  );
}
