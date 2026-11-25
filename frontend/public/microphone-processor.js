class MicrophoneProcessor extends AudioWorkletProcessor {
  constructor({ processorOptions }) {
    super();
    this.targetRate = processorOptions.sampleRate;
    this.phase = 0;
    this.previous = 0;
    this.hasPrevious = false;
    this.buffer = new ArrayBuffer(8192);
    this.pcm = new DataView(this.buffer);
    this.length = 0;
  }

  write(sample) {
    const clipped = Math.max(-1, Math.min(1, sample));
    this.pcm.setInt16(this.length * 2, clipped < 0 ? clipped * 32768 : clipped * 32767, true);
    this.length++;
    if (this.length === 4096) {
      this.port.postMessage(this.buffer, [this.buffer]);
      this.buffer = new ArrayBuffer(8192);
      this.pcm = new DataView(this.buffer);
      this.length = 0;
    }
  }

  process(inputs) {
    const channel = inputs[0]?.[0];
    if (!channel) return true;
    for (const sample of channel) {
      if (!this.hasPrevious) {
        this.previous = sample;
        this.hasPrevious = true;
        this.write(sample);
        continue;
      }
      // Carry the fractional sampling position across audio callback blocks.
      let offset = sampleRate - this.phase;
      while (offset <= this.targetRate) {
        const fraction = offset / this.targetRate;
        this.write(this.previous + (sample - this.previous) * fraction);
        offset += sampleRate;
      }
      this.phase = (this.phase + this.targetRate) % sampleRate;
      this.previous = sample;
    }
    return true;
  }
}

registerProcessor("sonicaid-microphone", MicrophoneProcessor);
