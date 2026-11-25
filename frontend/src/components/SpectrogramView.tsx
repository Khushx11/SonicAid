import { useEffect, useRef } from "react";

type Props = {
  lastPcm16?: Int16Array | null;
};

function stftMagnitude(x: Float32Array, fftSize: number, hop: number) {
  // Minimal, CPU-friendly spectrogram for UI only (not model features).
  const frames = Math.max(0, Math.floor((x.length - fftSize) / hop) + 1);
  const bins = fftSize / 2;
  const out: number[][] = Array.from({ length: frames }, () =>
    Array.from({ length: bins }, () => 0),
  );
  for (let f = 0; f < frames; f++) {
    const start = f * hop;
    for (let k = 0; k < bins; k++) {
      let re = 0;
      let im = 0;
      for (let n = 0; n < fftSize; n++) {
        const w = 0.5 - 0.5 * Math.cos((2 * Math.PI * n) / (fftSize - 1));
        const sample = x[start + n] * w;
        const ang = (-2 * Math.PI * k * n) / fftSize;
        re += sample * Math.cos(ang);
        im += sample * Math.sin(ang);
      }
      const mag = Math.sqrt(re * re + im * im);
      out[f][k] = mag;
    }
  }
  return out;
}

export default function SpectrogramView({ lastPcm16 }: Props) {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    const dpr = window.devicePixelRatio || 1;
    const rect = canvas.getBoundingClientRect();
    const W = Math.max(1, Math.round(rect.width * dpr));
    const H = Math.round(128 * dpr);
    canvas.width = W;
    canvas.height = H;

    ctx.clearRect(0, 0, W, H);
    ctx.fillStyle = "rgba(8,13,19,0.9)";
    ctx.fillRect(0, 0, W, H);

    if (!lastPcm16 || lastPcm16.length < 2048) {
      // Placeholder: show a grid hint
      ctx.strokeStyle = "rgba(255,255,255,0.04)";
      ctx.lineWidth = 1;
      for (let y = 0; y < H; y += 32 * dpr) {
        ctx.beginPath();
        ctx.moveTo(0, y);
        ctx.lineTo(W, y);
        ctx.stroke();
      }
      return;
    }

    const x = new Float32Array(lastPcm16.length);
    for (let i = 0; i < lastPcm16.length; i++) x[i] = lastPcm16[i] / 32768;

    const fftSize = 256;
    const hop = 128;
    const spec = stftMagnitude(x, fftSize, hop);
    if (spec.length === 0) return;

    const frames = spec.length;
    const bins = spec[0].length;
    let max = 1e-9;
    for (let t = 0; t < frames; t++)
      for (let b = 0; b < bins; b++) max = Math.max(max, spec[t][b]);

    const img = ctx.createImageData(W, H);
    for (let px = 0; px < W; px++) {
      const t = Math.min(frames - 1, Math.floor((px / W) * frames));
      for (let py = 0; py < H; py++) {
        const b = Math.min(bins - 1, Math.floor(((H - 1 - py) / H) * bins));
        const v = Math.pow(spec[t][b] / max, 0.38);
        const idx = (py * W + px) * 4;

        // Viridis-inspired palette: dark blue → teal → yellow
        if (v < 0.25) {
          const t2 = v / 0.25;
          img.data[idx]     = Math.round(68 * (1 - t2) + 59 * t2);
          img.data[idx + 1] = Math.round(1  * (1 - t2) + 82 * t2);
          img.data[idx + 2] = Math.round(84 * (1 - t2) + 139 * t2);
        } else if (v < 0.5) {
          const t2 = (v - 0.25) / 0.25;
          img.data[idx]     = Math.round(59  * (1 - t2) + 33  * t2);
          img.data[idx + 1] = Math.round(82  * (1 - t2) + 145 * t2);
          img.data[idx + 2] = Math.round(139 * (1 - t2) + 140 * t2);
        } else if (v < 0.75) {
          const t2 = (v - 0.5) / 0.25;
          img.data[idx]     = Math.round(33  * (1 - t2) + 94  * t2);
          img.data[idx + 1] = Math.round(145 * (1 - t2) + 201 * t2);
          img.data[idx + 2] = Math.round(140 * (1 - t2) + 97  * t2);
        } else {
          const t2 = (v - 0.75) / 0.25;
          img.data[idx]     = Math.round(94  * (1 - t2) + 253 * t2);
          img.data[idx + 1] = Math.round(201 * (1 - t2) + 231 * t2);
          img.data[idx + 2] = Math.round(97  * (1 - t2) + 37  * t2);
        }
        img.data[idx + 3] = 255;
      }
    }
    ctx.putImageData(img, 0, 0);
  }, [lastPcm16]);

  return (
    <div className="canvas-wrapper">
      <span className="canvas-label" aria-hidden="true">Spectrogram</span>
      <canvas
        ref={canvasRef}
        aria-label="Live audio spectrogram"
        role="img"
        style={{ height: "128px" }}
      />
    </div>
  );
}
