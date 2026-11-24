import { useCallback, useEffect, useRef, useState } from "react";

type AudioCaptureOpts = {
  sampleRate: number;
  onPcmChunk: (chunk: ArrayBuffer) => void;
};

type Capture = {
  stream?: MediaStream;
  context?: AudioContext;
  processor?: ScriptProcessorNode;
};

function release(capture: Capture) {
  if (capture.processor) {
    capture.processor.onaudioprocess = null;
    capture.processor.disconnect();
  }
  capture.stream?.getTracks().forEach((track) => track.stop());
  void capture.context?.close().catch(() => {});
}

export function useAudioCapture({ sampleRate, onPcmChunk }: AudioCaptureOpts) {
  const [running, setRunning] = useState(false);
  const [starting, setStarting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const captureRef = useRef<Capture | null>(null);

  const dispose = useCallback(() => {
    const capture = captureRef.current;
    captureRef.current = null;
    if (capture) release(capture);
  }, []);

  useEffect(() => dispose, [dispose]);

  const stop = useCallback(() => {
    dispose();
    setRunning(false);
    setStarting(false);
  }, [dispose]);

  const start = useCallback(async () => {
    if (captureRef.current) return;
    const capture: Capture = {};
    captureRef.current = capture;
    setStarting(true);
    setError(null);

    try {
      if (!navigator.mediaDevices?.getUserMedia) {
        throw new Error("Microphone access requires a supported browser on localhost or HTTPS.");
      }

      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      capture.stream = stream;
      if (captureRef.current !== capture) {
        release(capture);
        return;
      }

      const context = new AudioContext({ sampleRate });
      capture.context = context;
      if (context.sampleRate !== sampleRate) {
        throw new Error("This browser could not provide the audio sample rate required by the model.");
      }
      const source = context.createMediaStreamSource(stream);
      const processor = context.createScriptProcessor(4096, 1, 1);
      capture.processor = processor;

      processor.onaudioprocess = (event) => {
        if (captureRef.current !== capture) return;
        const input = event.inputBuffer.getChannelData(0);
        const pcm = new ArrayBuffer(input.length * 2);
        const view = new DataView(pcm);
        for (let i = 0; i < input.length; i++) {
          const sample = Math.max(-1, Math.min(1, input[i]));
          view.setInt16(i * 2, sample < 0 ? sample * 0x8000 : sample * 0x7fff, true);
        }
        onPcmChunk(pcm);
      };

      source.connect(processor);
      processor.connect(context.destination);
      setRunning(true);
      setStarting(false);
    } catch (cause) {
      if (captureRef.current === capture) {
        dispose();
        setStarting(false);
        setError(cause instanceof DOMException && cause.name === "NotAllowedError"
          ? "Microphone permission was denied. Allow access in your browser and try again."
          : cause instanceof Error ? cause.message : "Microphone capture failed.");
      }
    }
  }, [dispose, onPcmChunk, sampleRate]);

  return { running, starting, error, start, stop };
}
