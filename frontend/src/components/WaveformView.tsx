import { useEffect, useRef } from "react";

type Props = {
  lastPcm16?: Int16Array | null;
};

export default function WaveformView({ lastPcm16 }: Props) {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    const dpr = window.devicePixelRatio || 1;
    const rect = canvas.getBoundingClientRect();
    canvas.width = Math.max(1, Math.round(rect.width * dpr));
    canvas.height = Math.round(128 * dpr);
    ctx.scale(dpr, dpr);

    const W = rect.width;
    const H = 128;

    ctx.clearRect(0, 0, W, H);

    // Background
    const bg = ctx.createLinearGradient(0, 0, 0, H);
    bg.addColorStop(0, "rgba(8,13,19,0.9)");
    bg.addColorStop(1, "rgba(8,13,19,0.7)");
    ctx.fillStyle = bg;
    ctx.fillRect(0, 0, W, H);

    // Centre grid line
    ctx.strokeStyle = "rgba(255,255,255,0.05)";
    ctx.lineWidth = 1;
    ctx.beginPath();
    ctx.moveTo(0, H / 2);
    ctx.lineTo(W, H / 2);
    ctx.stroke();

    if (!lastPcm16 || lastPcm16.length === 0) {
      // Flat line placeholder
      ctx.strokeStyle = "rgba(62,207,191,0.2)";
      ctx.lineWidth = 1.5;
      ctx.beginPath();
      ctx.moveTo(0, H / 2);
      ctx.lineTo(W, H / 2);
      ctx.stroke();
      return;
    }

    // Gradient stroke
    const grad = ctx.createLinearGradient(0, 0, W, 0);
    grad.addColorStop(0, "rgba(79,163,224,0.8)");
    grad.addColorStop(0.5, "rgba(62,207,191,0.95)");
    grad.addColorStop(1, "rgba(79,163,224,0.8)");

    ctx.strokeStyle = grad;
    ctx.lineWidth = 1.5;
    ctx.lineJoin = "round";
    ctx.beginPath();

    const step = lastPcm16.length / Math.ceil(W);
    for (let x = 0; x < W; x++) {
      const i = Math.floor(x * step);
      const v = lastPcm16[i] / 32768;
      const y = H / 2 + v * (H * 0.42);
      if (x === 0) ctx.moveTo(x, y);
      else ctx.lineTo(x, y);
    }
    ctx.stroke();

    // Mirror fill for depth
    ctx.globalAlpha = 0.08;
    ctx.fillStyle = grad;
    ctx.beginPath();
    for (let x = 0; x < W; x++) {
      const i = Math.floor(x * step);
      const v = lastPcm16[i] / 32768;
      const y = H / 2 + v * (H * 0.42);
      if (x === 0) ctx.moveTo(x, y);
      else ctx.lineTo(x, y);
    }
    ctx.lineTo(W, H / 2);
    ctx.lineTo(0, H / 2);
    ctx.closePath();
    ctx.fill();
    ctx.globalAlpha = 1;
  }, [lastPcm16]);

  return (
    <div className="canvas-wrapper">
      <span className="canvas-label" aria-hidden="true">Waveform</span>
      <canvas
        ref={canvasRef}
        aria-label="Live microphone waveform"
        role="img"
        style={{ height: "128px" }}
      />
    </div>
  );
}
