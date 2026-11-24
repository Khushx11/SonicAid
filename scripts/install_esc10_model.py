"""Install and SHA-256 verify the repository's published ESC-10 checkpoint.

Only use the GitHub release owned by this project. Joblib is pickle-based
and executing an untrusted checkpoint is unsafe.
"""
import argparse
import hashlib
import re
from pathlib import Path
from urllib.request import urlopen

BASE = "https://github.com/Khushx11/SonicAid/releases/download/esc10-baseline"
MAX_CHECKPOINT_BYTES = 10 * 1024 * 1024


def download(url, limit):
    with urlopen(url, timeout=120) as response:
        body = response.read(limit + 1)
    if len(body) > limit:
        raise ValueError("download exceeds expected maximum size")
    return body


def install(output: Path, force=False):
    checksum = download(BASE + "/esc10.sha256", 4096).decode("utf-8")
    match = re.match(r"^([0-9a-f]{64})\s+", checksum.strip())
    if match is None:
        raise ValueError("invalid publisher checksum format")
    expected = match.group(1)
    if output.is_file():
        current = hashlib.sha256(output.read_bytes()).hexdigest()
        if current == expected:
            print(f"Already verified: {output}")
            return output
        if not force:
            raise FileExistsError("Local checkpoint differs; pass --force to replace it")
    data = download(BASE + "/esc10.joblib", MAX_CHECKPOINT_BYTES)
    actual = hashlib.sha256(data).hexdigest()
    if actual != expected:
        raise ValueError("ESC-10 checkpoint SHA-256 mismatch")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(data)
    print(f"Verified ESC-10 checkpoint: {output}")
    return output


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path("ml/artifacts/esc10.joblib"))
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()
    install(args.output, force=args.force)


if __name__ == "__main__":
    main()
