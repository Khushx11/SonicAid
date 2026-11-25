import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";
import { runInNewContext } from "node:vm";

const source = readFileSync(new URL("../public/microphone-processor.js", import.meta.url), "utf8");

for (const inputRate of [16000, 44100, 48000]) {
  test(`encodes four seconds of ${inputRate} Hz mono capture as PCM16`, () => {
    const frames = [];
    let Processor;
    runInNewContext(source, {
      sampleRate: inputRate,
      AudioWorkletProcessor: class {
        port = { postMessage: (buffer) => frames.push(buffer) };
      },
      registerProcessor: (_name, implementation) => { Processor = implementation; },
    });
    const processor = new Processor({ processorOptions: { sampleRate: 16000 } });
    const input = new Float32Array(inputRate * 4).fill(0.5);
    for (let i = 0; i < input.length; i += 128) {
      processor.process([[input.subarray(i, i + 128)]]);
    }
    assert.equal(frames.length * 4096 + processor.length, 64000);
    assert.equal(frames[0].byteLength, 8192);
    assert.equal(new DataView(frames[0]).getInt16(0, true), 16383);
  });
}
