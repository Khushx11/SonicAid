import { useCallback, useRef, useState } from "react";

type AudioCaptureOpts = {
  sampleRate: number;
  onPcmChunk: (chunk: ArrayBuffer) => void;
};

export function useAudioCapture(opts: AudioCaptureOpts) {
  const [running, setRunning] = useState(false);
  const audioContextRef = useRef<AudioContext | null>(null);
  const processorRef = useRef<ScriptProcessorNode | null>(null);
  const streamRef = useRef<MediaStream | null>(null);

  const start = useCallback(async () => {
    if (running) return;
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    streamRef.current = stream;

    const audioContext = new AudioContext({ sampleRate: opts.sampleRate });
    audioContextRef.current = audioContext;
    const source = audioContext.createMediaStreamSource(stream);

    // ScriptProcessorNode is deprecated but widely supported; upgrade to AudioWorklet later.
    const processor = audioContext.createScriptProcessor(4096, 1, 1);
    processorRef.current = processor;

    processor.onaudioprocess = (e) => {
      const input = e.inputBuffer.getChannelData(0);
      const pcm16 = new Int16Array(input.length);
      for (let i = 0; i < input.length; i++) {
        const s = Math.max(-1, Math.min(1, input[i]));
        pcm16[i] = s < 0 ? s * 0x8000 : s * 0x7fff;
      }
      opts.onPcmChunk(pcm16.buffer);
    };

    source.connect(processor);
    processor.connect(audioContext.destination);
    setRunning(true);
  }, [opts, running]);

  const stop = useCallback(() => {
    processorRef.current?.disconnect();
    processorRef.current = null;
    audioContextRef.current?.close();
    audioContextRef.current = null;
    streamRef.current?.getTracks().forEach((t) => t.stop());
    streamRef.current = null;
    setRunning(false);
  }, []);

  return { running, start, stop };
}

