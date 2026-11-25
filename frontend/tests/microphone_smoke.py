"""Drive the production dashboard with Chromium's deterministic microphone."""

import argparse
import json
import re
from urllib.request import urlopen

from playwright.sync_api import expect, sync_playwright


def test_microphone(frontend_url, mock_backend, physical_mic=False):
    received_bytes = 0

    def route_stream(socket):
        socket.send(json.dumps({"type": "status", "status": "ready", "model": "ESC-10"}))

        def receive(chunk):
            nonlocal received_bytes
            assert isinstance(chunk, bytes)
            assert len(chunk) == 8192
            received_bytes += len(chunk)
            if received_bytes - len(chunk) < 160_000 <= received_bytes:
                socket.send(json.dumps({
                    "session_id": "browser-smoke",
                    "window_start": 0,
                    "window_end": 5,
                    "primary_class": "browser fixture",
                    "primary_confidence": 0.5,
                    "latency_ms": 1,
                }))

        socket.on_message(receive)

    with sync_playwright() as playwright:
        browser_args = [] if physical_mic else [
            "--use-fake-device-for-media-stream",
            "--use-fake-ui-for-media-stream",
        ]
        browser = playwright.chromium.launch(args=browser_args, headless=not physical_mic)
        page = browser.new_page(
            viewport={"width": 390, "height": 844},
            permissions=["microphone"],
            device_scale_factor=2,
        )
        if mock_backend:
            page.route_web_socket("**/ws/stream", route_stream)
        page.goto(frontend_url)
        expect(page.get_by_role("heading", name="Environmental sound monitor")).to_be_visible()
        assert page.evaluate("document.documentElement.scrollWidth <= window.innerWidth")
        expect(page.get_by_text("Model ready", exact=True)).to_be_visible(timeout=20_000)
        page.evaluate("""() => {
          const media = navigator.mediaDevices;
          const getUserMedia = media.getUserMedia.bind(media);
          media.getUserMedia = async (constraints) => {
            const stream = await getUserMedia(constraints);
            window.smokeTrack = stream.getAudioTracks()[0];
            return stream;
          };
        }""")
        page.get_by_role("button", name="Start microphone capture", exact=True).click()
        expect(page.get_by_text("Microphone on", exact=True)).to_be_visible()
        window = page.get_by_role("cell", name=re.compile(r"^\d+\.\d–\d+\.\d s$")).first
        expect(window).to_be_visible(timeout=20_000)
        start, end = map(float, window.inner_text().removesuffix(" s").split("–"))
        assert abs(end - start - 5) < 0.11

        if mock_backend:
            expect(page.get_by_role("cell", name="browser fixture")).to_be_visible()
            assert received_bytes >= 160_000
        export = page.get_by_role("button", name=re.compile(r"^Download session CSV"))
        expect(export).to_be_enabled()
        with page.expect_download() as download:
            export.click()
        assert download.value.path().read_text().startswith("session_id,window_start,window_end,")
        assert page.evaluate("""() => {
            const canvas = document.querySelector('[aria-label="Live audio spectrogram"]');
            return canvas.getContext('2d').getImageData(canvas.width - 1, canvas.height - 1, 1, 1).data[3] === 255;
        }""")
        page.get_by_role("button", name="Stop microphone capture and reset session", exact=True).click()
        expect(page.get_by_text("Microphone off", exact=True)).to_be_visible()
        assert page.evaluate("window.smokeTrack.readyState") == "ended"

        page.evaluate("""() => {
          navigator.mediaDevices.getUserMedia = async () => {
            throw new DOMException("Permission denied", "NotAllowedError");
          };
        }""")
        expect(page.get_by_text("Model ready", exact=True)).to_be_visible(timeout=20_000)
        page.get_by_role("button", name="Start microphone capture", exact=True).click()
        expect(page.get_by_role("alert")).to_contain_text("Microphone permission was denied")
        browser.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--frontend", default="http://127.0.0.1:5173")
    parser.add_argument("--mock-backend", action="store_true")
    parser.add_argument("--physical-mic", action="store_true", help="Use the host input device")
    args = parser.parse_args()
    with urlopen(args.frontend, timeout=10):
        pass
    test_microphone(args.frontend, args.mock_backend, args.physical_mic)
    print("SonicAid microphone browser checks passed.")
