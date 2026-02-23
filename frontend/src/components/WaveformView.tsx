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

    const w = (canvas.width = 900);
    const h = (canvas.height = 180);
    ctx.clearRect(0, 0, w, h);
    ctx.fillStyle = "rgba(0,0,0,0.25)";
    ctx.fillRect(0, 0, w, h);

    if (!lastPcm16 || lastPcm16.length === 0) return;

    ctx.strokeStyle = "rgba(88, 168, 255, 0.95)";
    ctx.lineWidth = 2;
    ctx.beginPath();

    const step = Math.max(1, Math.floor(lastPcm16.length / w));
    for (let x = 0; x < w; x++) {
      const i = x * step;
      const v = lastPcm16[i] / 32768;
      const y = h / 2 + v * (h * 0.4);
      if (x === 0) ctx.moveTo(x, y);
      else ctx.lineTo(x, y);
    }
    ctx.stroke();
  }, [lastPcm16]);

  return (
    <div>
      <div className="row">
        <span className="pill">Waveform</span>
      </div>
      <canvas ref={canvasRef} />
    </div>
  );
}

