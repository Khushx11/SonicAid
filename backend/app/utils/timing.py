import time


class Stopwatch:
    def __init__(self) -> None:
        self.t0 = time.time()

    def ms(self) -> float:
        return (time.time() - self.t0) * 1000.0

