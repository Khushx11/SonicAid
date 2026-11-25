"""Drive the production dashboard with Chromium's deterministic microphone."""

import argparse
import json
from urllib.request import urlopen

from playwright.sync_api import expect, sync_playwright


def test_microphone(frontend_url, mock_backend):
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
        browser = playwright.chromium.launch(args=[
            "--use-fake-device-for-media-stream",
            "--use-fake-ui-for-media-stream",
        ])
        page = browser.new_page(viewport={"width": 390, "height": 844})
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
        page.get_by_role("button", name="Start", exact=True).click()
        expect(page.get_by_text("Microphone on", exact=True)).to_be_visible()
        row = page.get_by_role("row").filter(has_text="0.0–5.0 s")
        expect(row).to_be_visible(timeout=20_000)
        if mock_backend:
            expect(row).to_contain_text("browser fixture")
            assert received_bytes >= 160_000
        expect(page.get_by_role("button", name="Download CSV")).to_be_enabled()
        page.get_by_role("button", name="Stop", exact=True).click()
        expect(page.get_by_text("Microphone off", exact=True)).to_be_visible()
        assert page.evaluate("window.smokeTrack.readyState") == "ended"

        page.evaluate("""() => {
          navigator.mediaDevices.getUserMedia = async () => {
            throw new DOMException("Permission denied", "NotAllowedError");
          };
        }""")
        page.get_by_role("button", name="Start", exact=True).click()
        expect(page.get_by_role("alert")).to_contain_text("Microphone permission was denied")
        browser.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--frontend", default="http://127.0.0.1:5173")
    parser.add_argument("--mock-backend", action="store_true")
    args = parser.parse_args()
    with urlopen(args.frontend, timeout=10):
        pass
    test_microphone(args.frontend, args.mock_backend)
    print("SonicAid microphone browser checks passed.")
