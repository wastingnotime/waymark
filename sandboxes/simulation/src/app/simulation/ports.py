"""Small deterministic ports used by the simulation environment."""

from dataclasses import dataclass


@dataclass
class DeterministicIds:
    prefix: str = "waymark"
    _next: int = 0

    def new(self, kind: str) -> str:
        self._next += 1
        return f"{self.prefix}-{kind}-{self._next:04d}"


class FakePaymentProvider:
    """Provider boundary with replay-safe, explicit outcomes."""

    def __init__(self) -> None:
        self.outcomes: dict[str, str] = {}

    def succeed(self, payment_id: str) -> str:
        self.outcomes[payment_id] = "succeeded"
        return self.outcomes[payment_id]

    def fail(self, payment_id: str) -> str:
        self.outcomes[payment_id] = "failed"
        return self.outcomes[payment_id]
