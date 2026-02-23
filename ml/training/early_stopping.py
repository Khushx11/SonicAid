from __future__ import annotations


class EarlyStopping:
    def __init__(self, patience: int = 3, min_delta: float = 1e-4) -> None:
        self.patience = patience
        self.min_delta = min_delta
        self.best = None
        self.bad_epochs = 0

    def step(self, metric: float) -> bool:
        """
        Returns True if training should stop.
        Metric is assumed to be minimized (e.g. loss).
        """
        if self.best is None:
            self.best = metric
            return False

        if metric < self.best - self.min_delta:
            self.best = metric
            self.bad_epochs = 0
            return False

        self.bad_epochs += 1
        return self.bad_epochs >= self.patience

