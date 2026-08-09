"""Runtime-independent deterministic Waymark simulation environment."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from collections import Counter
from app.simulation.events import SimFact
from app.simulation.ports import DeterministicIds


@dataclass(frozen=True)
class SimEntry:
    kind: str
    body: str
    happened_at: datetime
    recorded_at: datetime


@dataclass
class SimState:
    user_id: str
    workspace_id: str
    period_start: datetime | None = None
    period_end: datetime | None = None
    payment_failed: bool = False
    expired: bool = False
    cancelled: bool = False
    cancellation_at: datetime | None = None
    entries: list[SimEntry] = field(default_factory=list)
    events: list[SimFact] = field(default_factory=list)

    @property
    def facts(self) -> list[str]:
        """Compatibility projection for scenario invariants and inspection."""
        return [event.name for event in self.events]

    def access_allowed(self, at: datetime) -> bool:
        return (
            self.period_start is not None
            and self.period_end is not None
            and self.period_start <= at < self.period_end
            and not self.payment_failed
            and not self.expired
        )


class WaymarkSimulation:
    def __init__(self, ids: DeterministicIds | None = None) -> None:
        self.ids = ids or DeterministicIds()
        self.state = SimState(
            user_id=self.ids.new("user"),
            workspace_id=self.ids.new("workspace"),
        )

    def _fact(self, name: str, occurred_at: datetime, **payload: object) -> None:
        self.state.events.append(SimFact(len(self.state.events), name, occurred_at, payload))

    def create_account(self, context: object) -> None:
        now = context.clock.now()
        self._fact("AccountCreated", now, user_id=str(self.state.user_id))
        self._fact("WorkspaceCreated", now, workspace_id=str(self.state.workspace_id))
        context.emit("domain_fact", "account_created", source="WaymarkSimulation")

    def activate_period(self, context: object, start: datetime, end: datetime) -> None:
        self.state.period_start, self.state.period_end = start, end
        self.state.payment_failed = False
        self.state.expired = False
        self._fact("PaymentSucceeded", context.clock.now(), period_end=end)
        self._fact("EntitlementGranted", context.clock.now(), period_start=start, period_end=end)
        context.emit("domain_fact", "payment_succeeded", source="Billing")
        context.emit("domain_fact", "entitlement_granted", source="Access")

    def record_note(self, context: object, body: str) -> bool:
        return self._record(context, "note", body, context.clock.now())

    def record_log(self, context: object, body: str, happened_at: datetime) -> bool:
        return self._record(context, "log_entry", body, happened_at)

    def fail_payment(self, context: object) -> None:
        self.state.payment_failed = True
        self._fact("PaymentFailed", context.clock.now())
        context.emit("domain_fact", "payment_failed", source="PaymentProvider")
        context.emit("access_changed", "workspace_restricted", source="Access", payload={"reason": "payment_failed"})

    def recover_payment(self, context: object) -> None:
        self.state.payment_failed = False
        self._fact("PaymentSucceeded", context.clock.now())
        self._fact("EntitlementRestored", context.clock.now())
        context.emit("domain_fact", "payment_recovered", source="PaymentProvider")
        context.emit("access_changed", "workspace_allowed", source="Access", payload={"reason": "recovered"})

    def cancel(self, context: object) -> None:
        if self.state.period_end is None:
            raise ValueError("cannot cancel without an active paid period")
        self.state.cancelled = True
        self.state.cancellation_at = self.state.period_end
        self._fact("CancellationScheduled", context.clock.now(), effective_at=self.state.cancellation_at)
        context.emit(
            "domain_fact",
            "cancellation_scheduled",
            source="Billing",
            payload={"effective_at": self.state.cancellation_at.isoformat()},
        )

    def expire(self, context: object) -> None:
        self.state.expired = True
        self._fact("EntitlementExpired", context.clock.now())
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
        if not body.strip():
            context.emit("command_rejected", f"{kind}_rejected", source="Recording", payload={"reason": "empty_body"})
            return False
        if not self.access_check(context):
            context.emit("command_rejected", f"{kind}_rejected", source="Recording", payload={"reason": "restricted"})
            return False
        self.state.entries.append(SimEntry(kind, body, happened_at, context.clock.now()))
        self._fact("NoteRecorded" if kind == "note" else "LogEntryRecorded", context.clock.now(), kind=kind)
        context.emit("domain_fact", f"{kind}_recorded", source="Recording")
        return True

    def _restriction_reason(self) -> str:
        if self.state.expired:
            return "expired"
        if self.state.payment_failed:
            return "payment_failed"
        return "no_entitlement"
