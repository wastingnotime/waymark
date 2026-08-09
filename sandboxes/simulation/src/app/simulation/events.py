"""Append-only facts produced by the Waymark simulation."""

from dataclasses import dataclass, field
from datetime import datetime


@dataclass(frozen=True)
class SimFact:
    sequence: int
    name: str
    occurred_at: datetime
    payload: dict[str, object] = field(default_factory=dict)
