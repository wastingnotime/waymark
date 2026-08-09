"""Runtime-independent deterministic Waymark simulation environment."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from collections import Counter
from uuid import UUID, uuid4


@dataclass(frozen=True)
class SimEntry:
    kind: str
    body: str
    happened_at: datetime
    recorded_at: datetime


@dataclass
class SimState:
    user_id: UUID = field(default_factory=uuid4)
    workspace_id: UUID = field(default_factory=uuid4)
    period_start: datetime | None = None
    period_end: datetime | None = None
    payment_failed: bool = False
    expired: bool = False
    cancelled: bool = False
    entries: list[SimEntry] = field(default_factory=list)
    facts: list[str] = field(default_factory=list)

    def access_allowed(self, at: datetime) -> bool:
        return (
            self.period_start is not None
            and self.period_end is not None
            and self.period_start <= at < self.period_end
            and not self.payment_failed
            and not self.expired
        )


class WaymarkSimulation:
    def __init__(self) -> None:
        self.state = SimState()

    def create_account(self, context: object) -> None:
        self.state.facts.extend(("AccountCreated", "WorkspaceCreated"))
        context.emit("domain_fact", "account_created", source="WaymarkSimulation")

    def activate_period(self, context: object, start: datetime, end: datetime) -> None:
        self.state.period_start, self.state.period_end = start, end
        self.state.payment_failed = False
        self.state.expired = False
        self.state.facts.extend(("PaymentSucceeded", "EntitlementGranted"))
        context.emit("domain_fact", "payment_succeeded", source="Billing")
        context.emit("domain_fact", "entitlement_granted", source="Access")

    def record_note(self, context: object, body: str) -> bool:
        return self._record(context, "note", body, context.clock.now())

    def record_log(self, context: object, body: str, happened_at: datetime) -> bool:
        return self._record(context, "log_entry", body, happened_at)

    def fail_payment(self, context: object) -> None:
        self.state.payment_failed = True
        self.state.facts.append("PaymentFailed")
        context.emit("domain_fact", "payment_failed", source="PaymentProvider")
        context.emit("access_changed", "workspace_restricted", source="Access", payload={"reason": "payment_failed"})

    def recover_payment(self, context: object) -> None:
        self.state.payment_failed = False
        self.state.facts.extend(("PaymentSucceeded", "EntitlementRestored"))
        context.emit("domain_fact", "payment_recovered", source="PaymentProvider")
        context.emit("access_changed", "workspace_allowed", source="Access", payload={"reason": "recovered"})

    def cancel(self, context: object) -> None:
        self.state.cancelled = True
        self.state.facts.append("CancellationScheduled")
        context.emit("domain_fact", "cancellation_scheduled", source="Billing")

    def expire(self, context: object) -> None:
        self.state.expired = True
        self.state.facts.append("EntitlementExpired")
        context.emit("domain_fact", "entitlement_expired", source="Access")
        context.emit("access_changed", "workspace_restricted", source="Access", payload={"reason": "expired"})

    def access_check(self, context: object) -> bool:
        allowed = self.state.access_allowed(context.clock.now())
        context.emit(
            "access_decision",
            "workspace_access_checked",
            source="Access",
            payload={"allowed": allowed, "reason": "entitled" if allowed else self._restriction_reason()},
        )
        return allowed

    def daily_summary(self, context: object, start: datetime, end: datetime) -> dict[str, int]:
        """Project recorded facts without mutating the append-only history."""
        counts: Counter[str] = Counter(
            entry.recorded_at.date().isoformat()
            for entry in self.state.entries
            if start <= entry.recorded_at <= end
        )
        summary = dict(sorted(counts.items()))
        context.emit(
            "projection_result",
            "daily_entry_summary",
            source="Insights",
            payload={"start": start.isoformat(), "end": end.isoformat(), "counts": summary},
        )
        return summary

    def _record(self, context: object, kind: str, body: str, happened_at: datetime) -> bool:
        if not self.access_check(context):
            context.emit("command_rejected", f"{kind}_rejected", source="Recording", payload={"reason": "restricted"})
            return False
        self.state.entries.append(SimEntry(kind, body, happened_at, context.clock.now()))
        self.state.facts.append("NoteRecorded" if kind == "note" else "LogEntryRecorded")
        context.emit("domain_fact", f"{kind}_recorded", source="Recording")
        return True

    def _restriction_reason(self) -> str:
        if self.state.expired:
            return "expired"
        if self.state.payment_failed:
            return "payment_failed"
        return "no_entitlement"
