import { useEffect, useRef } from "react";

type Props = {
  lastPcm16?: Int16Array | null;
};

function stftMagnitude(x: Float32Array, fftSize: number, hop: number) {
  // Minimal, CPU-friendly spectrogram for UI only (not model features).
  // Uses a naive DFT per bin for demo; replace with FFT library for scale.
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

    const w = (canvas.width = 900);
    const h = (canvas.height = 180);
    ctx.clearRect(0, 0, w, h);
    ctx.fillStyle = "rgba(0,0,0,0.25)";
    ctx.fillRect(0, 0, w, h);

    if (!lastPcm16 || lastPcm16.length < 2048) return;
    const x = new Float32Array(lastPcm16.length);
    for (let i = 0; i < lastPcm16.length; i++) x[i] = lastPcm16[i] / 32768;

    const fftSize = 256;
    const hop = 128;
    const spec = stftMagnitude(x, fftSize, hop);
    if (spec.length === 0) return;

    const frames = spec.length;
    const bins = spec[0].length;
    let max = 1e-9;
    for (let t = 0; t < frames; t++) {
      for (let b = 0; b < bins; b++) max = Math.max(max, spec[t][b]);
    }

    const img = ctx.createImageData(w, h);
    for (let px = 0; px < w; px++) {
      const t = Math.floor((px / w) * frames);
      for (let py = 0; py < h; py++) {
        const b = Math.floor(((h - 1 - py) / h) * bins);
        const v = spec[t][b] / max;
        const c = Math.floor(255 * Math.pow(v, 0.35));
        const i = (py * w + px) * 4;
        img.data[i + 0] = c;
        img.data[i + 1] = Math.min(255, Math.floor(c * 0.8 + 30));
        img.data[i + 2] = 255 - c;
        img.data[i + 3] = 255;
      }
    }
    ctx.putImageData(img, 0, 0);
  }, [lastPcm16]);

  return (
    <div>
      <div className="row">
        <span className="pill">Spectrogram (live)</span>
      </div>
      <canvas ref={canvasRef} />
    </div>
  );
}

