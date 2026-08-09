"""Small deterministic ports used by the simulation environment."""

from dataclasses import dataclass


@dataclass
class DeterministicIds:
    prefix: str = "waymark"
    _next: int = 0

    def new(self, kind: str) -> str:
        self._next += 1
        return f"{self.prefix}-{kind}-{self._next:04d}"

    def reserve(self, identifier: str) -> None:
        prefix, _, suffix = identifier.rpartition("-")
        if prefix.startswith(f"{self.prefix}-") and suffix.isdigit():
            self._next = max(self._next, int(suffix))


class FakePaymentProvider:
    """Provider boundary with replay-safe, explicit outcomes."""

    def __init__(self) -> None:
        self.outcomes: dict[str, str] = {}

    def succeed(self, payment_id: str) -> str:
        self._set_outcome(payment_id, "succeeded")
        return self.outcomes[payment_id]

    def fail(self, payment_id: str) -> str:
        self._set_outcome(payment_id, "failed")
        return self.outcomes[payment_id]

    def _set_outcome(self, payment_id: str, outcome: str) -> None:
        existing = self.outcomes.get(payment_id)
        if existing is not None and existing != outcome:
            raise ValueError(f"conflicting outcome for payment: {payment_id}")
        self.outcomes[payment_id] = outcome
