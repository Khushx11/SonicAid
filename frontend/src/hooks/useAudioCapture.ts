import { useCallback, useEffect, useRef, useState } from "react";

type AudioCaptureOpts = {
  sampleRate: number;
  onPcmChunk: (chunk: ArrayBuffer) => void;
};

type Capture = {
  stream?: MediaStream;
  context?: AudioContext;
  processor?: AudioWorkletNode;
};

function release(capture: Capture) {
  if (capture.processor) {
    capture.processor.port.onmessage = null;
    capture.processor.port.close();
    capture.processor.disconnect();
  }
  capture.stream?.getTracks().forEach((track) => track.stop());
  void capture.context?.close().catch(() => {});
}

function captureError(cause: unknown) {
  if (cause instanceof DOMException) {
    const messages: Record<string, string> = {
      NotAllowedError: "Microphone permission was denied. Allow access in your browser and try again.",
      NotFoundError: "No microphone was found. Connect or enable an input device and try again.",
      NotReadableError: "The microphone could not be opened. Check that it is available and permitted.",
      NotSupportedError: "This browser session could not start microphone capture. Check your input device or try a supported browser.",
    };
    if (messages[cause.name]) return messages[cause.name];
  }
  return cause instanceof Error ? cause.message : "Microphone capture failed.";
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

      const context = new AudioContext();
      capture.context = context;
      await context.audioWorklet.addModule(`${import.meta.env.BASE_URL}microphone-processor.js`);
      if (captureRef.current !== capture) return;

      const source = context.createMediaStreamSource(stream);
      const processor = new AudioWorkletNode(context, "sonicaid-microphone", {
        channelCount: 1,
        channelCountMode: "explicit",
        processorOptions: { sampleRate },
      });
      capture.processor = processor;
      processor.port.onmessage = ({ data }: MessageEvent<ArrayBuffer>) => {
        if (captureRef.current === capture) onPcmChunk(data);
      };

      if (context.sampleRate > sampleRate) {
        // Attenuate frequencies above the model's Nyquist limit before decimation.
        const lowpass = context.createBiquadFilter();
        lowpass.type = "lowpass";
        lowpass.frequency.value = sampleRate * 0.45;
        lowpass.Q.value = Math.SQRT1_2;
        source.connect(lowpass).connect(processor);
      } else {
        source.connect(processor);
      }
      // The worklet leaves its output silent, so microphone audio is never played back.
      processor.connect(context.destination);
      await context.resume();
      if (captureRef.current !== capture) return;
      setRunning(true);
      setStarting(false);
    } catch (cause) {
      if (captureRef.current === capture) {
        dispose();
        setStarting(false);
        setError(captureError(cause));
      }
    }
  }, [dispose, onPcmChunk, sampleRate]);

  return { running, starting, error, start, stop };
}
