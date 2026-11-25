import { useState } from "react";
import AudioCapture from "./components/AudioCapture";
import WaveformView from "./components/WaveformView";
import SpectrogramView from "./components/SpectrogramView";
import ClassProbabilitiesChart from "./components/ClassProbabilitiesChart";
import SessionTimeline from "./components/SessionTimeline";
import SessionReportDownload from "./components/SessionReportDownload";
import { API_BASE } from "./api/client";
import { useWebSocketStream } from "./hooks/useWebSocketStream";

const streamUrl = new URL("/ws/stream", API_BASE);
streamUrl.protocol = streamUrl.protocol === "https:" ? "wss:" : "ws:";

export default function App() {
  const [lastPcm, setLastPcm] = useState<Int16Array | null>(null);
  const stream = useWebSocketStream(streamUrl.toString());

  return (
    <div className="app-shell">
      {/* ── Top nav ───────────────────────── */}
      <nav className="top-nav">
        <a href="/" className="brand-logo" aria-label="SonicAid home">
          <div className="brand-icon" aria-hidden="true">
            <svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
              <path d="M9 18V6l7 3-7 3" strokeLinecap="round" strokeLinejoin="round"/>
              <path d="M4 12h1M19 12h1M12 4v1M12 19v1" strokeLinecap="round"/>
            </svg>
          </div>
          <span className="brand-wordmark">Sonic<span>Aid</span></span>
        </a>
        <div className="nav-links">
          <a
            href="https://github.com/Khushx11/SonicAid/blob/main/docs/esc10_model_card.md"
            className="nav-link"
            target="_blank"
            rel="noopener noreferrer"
          >
            <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden="true">
              <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
              <polyline points="14 2 14 8 20 8"/>
            </svg>
            Model card
          </a>
          <a
            href="https://github.com/Khushx11/SonicAid"
            className="nav-link"
            target="_blank"
            rel="noopener noreferrer"
          >
            <svg width="13" height="13" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">
              <path d="M12 0C5.37 0 0 5.37 0 12c0 5.3 3.438 9.8 8.207 11.387.6.113.793-.26.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.09-.745.083-.73.083-.73 1.205.085 1.84 1.237 1.84 1.237 1.07 1.834 2.807 1.304 3.492.997.108-.775.418-1.305.762-1.605-2.665-.3-5.467-1.333-5.467-5.93 0-1.31.467-2.38 1.235-3.22-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.3 1.23A11.51 11.51 0 0 1 12 5.803c1.02.005 2.047.138 3.006.404 2.29-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.91 1.235 3.22 0 4.61-2.807 5.625-5.479 5.92.43.372.823 1.102.823 2.222v3.293c0 .32.192.694.8.576C20.566 21.797 24 17.3 24 12c0-6.63-5.37-12-12-12z"/>
            </svg>
            GitHub
          </a>
        </div>
      </nav>

      {/* ── Hero ──────────────────────────── */}
      <header className="hero">
        <div className="hero-eyebrow">ESC-10 Audio Classification</div>
        <h1 className="hero-title">Environmental Sound Monitor</h1>
        <p className="hero-subtitle">
          Stream live microphone audio and get real-time classification across 10 environmental sound categories.
        </p>
      </header>

      {/* ── Capture card ──────────────────── */}
      <AudioCapture onLastPcm={setLastPcm} stream={stream} />

      {/* ── Main two-column grid ───────────── */}
      <div className="main-grid">
        {/* Signal column */}
        <section className="card" aria-label="Microphone signal">
          <div className="card-header">
            <h2 className="card-title">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden="true">
                <polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/>
              </svg>
              Signal
            </h2>
          </div>
          <WaveformView lastPcm16={lastPcm} />
          <SpectrogramView lastPcm16={lastPcm} />
        </section>

        {/* Classification column */}
        <section className="card prediction-card" aria-label="Latest classification">
          <div className="card-header">
            <h2 className="card-title">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden="true">
                <circle cx="12" cy="12" r="10"/>
                <line x1="12" y1="8" x2="12" y2="12"/>
                <line x1="12" y1="16" x2="12.01" y2="16"/>
              </svg>
              Classification
            </h2>
          </div>
          <ClassProbabilitiesChart latest={stream.latestPrediction} />
        </section>
      </div>

      {/* ── Session timeline ───────────────── */}
      <section className="card timeline-card" aria-label="Session timeline">
        <div className="card-header">
          <h2 className="card-title">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden="true">
              <line x1="8" y1="6" x2="21" y2="6"/>
              <line x1="8" y1="12" x2="21" y2="12"/>
              <line x1="8" y1="18" x2="21" y2="18"/>
              <line x1="3" y1="6" x2="3.01" y2="6"/>
              <line x1="3" y1="12" x2="3.01" y2="12"/>
              <line x1="3" y1="18" x2="3.01" y2="18"/>
            </svg>
            Session timeline
          </h2>
          <SessionReportDownload history={stream.history} />
        </div>
        <SessionTimeline history={stream.history} />
      </section>

      {/* ── Footer ────────────────────────── */}
      <footer className="app-footer">
        <span>
          SonicAid · ESC-10 Environmental Sound Classification ·{" "}
          <a href="https://iosrjen.org/Papers/vol15_issue6/A15060105.pdf" target="_blank" rel="noopener noreferrer">
            Published paper ↗
          </a>
        </span>
        <span>Khush Bhavin Maru · Adelaide University MAAIM · MIT License</span>
      </footer>
    </div>
  );
}
