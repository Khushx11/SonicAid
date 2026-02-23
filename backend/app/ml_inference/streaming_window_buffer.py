from __future__ import annotations

from collections import deque
from typing import Deque, List, Tuple


class StreamingWindowBuffer:
    """
    Maintains a sliding buffer of PCM samples and yields fixed-size windows
    with a given hop size for near real-time processing.
    """

    def __init__(self, sample_rate: int, window_seconds: float, hop_seconds: float):
        self.sample_rate = sample_rate
        self.window_size = int(window_seconds * sample_rate)
        self.hop_size = int(hop_seconds * sample_rate)
        self.buffer: Deque[float] = deque()
        self.total_samples = 0

    def append_samples(self, samples: List[float]) -> None:
        self.buffer.extend(samples)
        self.total_samples += len(samples)

    def available_windows(self) -> List[Tuple[int, int, List[float]]]:
        """
        Returns all complete windows currently available in the buffer.

        Each window is a tuple of (start_sample_index, end_sample_index, samples_list).
        """
        windows: List[Tuple[int, int, List[float]]] = []
        offset = 0

        while len(self.buffer) - offset >= self.window_size:
            start_idx = self.total_samples - len(self.buffer) + offset
            end_idx = start_idx + self.window_size

            # Extract window samples
            window = list(
                list(self.buffer)[offset : offset + self.window_size]  # noqa: E203
            )
            windows.append((start_idx, end_idx, window))
            offset += self.hop_size

        # Drop consumed samples
        for _ in range(offset):
            if self.buffer:
                self.buffer.popleft()

        return windows

