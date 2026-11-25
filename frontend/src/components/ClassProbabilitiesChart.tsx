import { useRef, useEffect } from "react";
import type { PredictionMessage } from "../hooks/useWebSocketStream";

type Props = {
  latest: PredictionMessage | null;
};

// ESC-10 emoji map for quick visual identification
const CLASS_EMOJI: Record<string, string> = {
  dog: "🐕",
  chainsaw: "🪚",
  crackling_fire: "🔥",
  helicopter: "🚁",
  rain: "🌧️",
  crying_baby: "👶",
  clock_tick: "🕐",
  sneezing: "🤧",
  rooster: "🐓",
  sea_waves: "🌊",
};

// Color coding by confidence level
function confidenceColor(p: number): string {
  if (p >= 0.7) return "var(--accent-green)";
  if (p >= 0.4) return "var(--accent-amber)";
  return "var(--accent-red)";
}

function confidenceLabel(p: number): string {
  if (p >= 0.7) return "High confidence";
  if (p >= 0.4) return "Moderate";
  return "Low confidence";
}

export default function ClassProbabilitiesChart({ latest }: Props) {
  const prevClass = useRef<string | null>(null);
  const animKey = latest?.primary_class ?? "";

  const isNewClass = latest && latest.primary_class !== prevClass.current;
  if (latest) prevClass.current = latest.primary_class;

  if (!latest) {
    return (
      <div className="prediction-empty" aria-live="polite" aria-label="Waiting for first prediction">
        <div className="prediction-empty-icon" aria-hidden="true">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
            <path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z"/>
            <path d="M19 10v2a7 7 0 0 1-14 0v-2"/>
            <line x1="12" y1="19" x2="12" y2="23"/>
            <line x1="8" y1="23" x2="16" y2="23"/>
          </svg>
        </div>
        <span>Waiting for prediction…</span>
        <span style={{fontSize:"0.75rem"}}>Start capture and wait 5 s</span>
      </div>
    );
  }

  const { primary_class, primary_confidence } = latest;
  const displayName = primary_class.replace(/_/g, " ");
  const pct = Math.max(0, Math.min(1, primary_confidence));
  const pctStr = (pct * 100).toFixed(1);
  const emoji = CLASS_EMOJI[primary_class] ?? "🔊";
  const color = confidenceColor(pct);
  const confLabel = confidenceLabel(pct);

  return (
    <div
      className={isNewClass ? "prediction-animate" : ""}
      key={animKey}
      style={{ display: "flex", flexDirection: "column", gap: "1rem" }}
      aria-live="polite"
      aria-label={`Detected: ${displayName} at ${pctStr}% confidence`}
    >
      {/* Emoji + class name */}
      <div style={{ display: "flex", alignItems: "flex-start", gap: "0.75rem" }}>
        <span
          style={{ fontSize: "2.5rem", lineHeight: 1, flexShrink: 0 }}
          role="img"
          aria-label={displayName}
        >
          {emoji}
        </span>
        <div>
          <div style={{ fontSize: "0.72rem", fontWeight: 600, letterSpacing: "0.06em", textTransform: "uppercase", color: "var(--text-muted)", marginBottom: "4px" }}>
            Detected sound
          </div>
          <p className="prediction-class-name">{displayName}</p>
        </div>
      </div>

      {/* Confidence */}
      <div>
        <div className="prediction-confidence-row" style={{ marginBottom: "8px" }}>
          <span className="prediction-confidence-label">{confLabel}</span>
          <span className="prediction-confidence-value" style={{ color }}>
            {pctStr}%
          </span>
        </div>
        <div className="confidence-track" role="progressbar" aria-valuenow={Math.round(pct * 100)} aria-valuemin={0} aria-valuemax={100} aria-label="Confidence">
          <div
            className="confidence-fill"
            style={{
              width: `${pct * 100}%`,
              background: `linear-gradient(90deg, ${color} 0%, ${color}cc 100%)`,
            }}
          />
        </div>
      </div>

      {/* Disclaimer */}
      <p className="prediction-disclaimer">
        Score is uncalibrated. Unfamiliar sounds may still receive a label.
        Scores below 40% are likely unreliable.
      </p>
    </div>
  );
}
