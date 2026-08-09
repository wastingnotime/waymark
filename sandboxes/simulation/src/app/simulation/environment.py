"""Runtime-independent deterministic Waymark simulation environment."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from collections import Counter
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError
from app.simulation.events import SimFact
from app.simulation.ports import DeterministicIds


SUMMARY_CALCULATION_VERSION = "daily-entry-counts-v1"


@dataclass(frozen=True)
class SimEntry:
    entry_id: str
    kind: str
    body: str
    happened_at: datetime
    recorded_at: datetime


@dataclass
class SimState:
    user_id: str
    workspace_id: str
    subscription_id: str | None = None
    period_start: datetime | None = None
    period_end: datetime | None = None
    payment_failed: bool = False
    expired: bool = False
    cancelled: bool = False
    cancellation_at: datetime | None = None
    entries: list[SimEntry] = field(default_factory=list)
    events: list[SimFact] = field(default_factory=list)
    processed_payment_ids: set[str] = field(default_factory=set)

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

    @classmethod
    def replay(cls, events: list[SimFact]) -> "WaymarkSimulation":
        """Rehydrate a fresh environment from append-only simulation facts."""
        simulation = cls()
        simulation.state.events = list(events)
        for event in events:
            if event.name == "AccountCreated":
                simulation.state.user_id = str(event.payload["user_id"])
                simulation.ids.reserve(simulation.state.user_id)
            elif event.name == "WorkspaceCreated":
                simulation.state.workspace_id = str(event.payload["workspace_id"])
                simulation.ids.reserve(simulation.state.workspace_id)
            elif event.name == "SubscriptionRequested":
                simulation.state.subscription_id = str(event.payload["subscription_id"])
            elif event.name == "EntitlementGranted":
                simulation.state.period_start = event.payload["period_start"]
                simulation.state.period_end = event.payload["period_end"]
                simulation.state.expired = False
                simulation.state.payment_failed = False
                simulation.state.cancelled = False
                simulation.state.cancellation_at = None
            elif event.name == "PaymentFailed":
                simulation.state.payment_failed = True
                payment_id = event.payload.get("payment_id")
                if payment_id:
                    simulation.state.processed_payment_ids.add(str(payment_id))
            elif event.name == "PaymentSucceeded":
                payment_id = event.payload.get("payment_id")
                if payment_id:
                    simulation.state.processed_payment_ids.add(str(payment_id))
            elif event.name in {"EntitlementRestored", "OperatorInterventionRecorded"}:
                simulation.state.payment_failed = False
            elif event.name == "CancellationScheduled":
                simulation.state.cancelled = True
                simulation.state.cancellation_at = event.payload["effective_at"]
            elif event.name == "EntitlementExpired":
                simulation.state.expired = True
            elif event.name in {"NoteRecorded", "LogEntryRecorded"}:
                simulation.state.entries.append(
                    SimEntry(
                        str(event.payload["entry_id"]),
                        str(event.payload["kind"]),
                        str(event.payload["body"]),
                        event.payload["happened_at"],
                        event.payload["recorded_at"],
                    )
                )
                simulation.ids.reserve(str(event.payload["entry_id"]))
        return simulation

    def create_account(self, context: object) -> None:
        if "AccountCreated" in self.state.facts:
            context.emit("account_notice", "duplicate_account_creation_ignored", source="WaymarkSimulation")
            return
        now = context.clock.now()
        self._fact("AccountCreated", now, user_id=str(self.state.user_id))
        self._fact("WorkspaceCreated", now, workspace_id=str(self.state.workspace_id))
        context.emit("domain_fact", "account_created", source="WaymarkSimulation")

    def request_subscription(self, context: object, subscription_id: str) -> None:
        if self.state.subscription_id is not None:
            if self.state.subscription_id == subscription_id:
                context.emit("subscription_notice", "duplicate_subscription_request_ignored", source="Billing")
                return
            raise ValueError("a current subscription already exists")
        self.state.subscription_id = subscription_id
        self._fact("SubscriptionRequested", context.clock.now(), subscription_id=subscription_id)
        context.emit("domain_fact", "subscription_requested", source="Billing")

    def activate_period(self, context: object, start: datetime, end: datetime, payment_id: str | None = None) -> None:
        if payment_id and payment_id in self.state.processed_payment_ids:
            context.emit("payment_notice", "duplicate_payment_success_ignored", source="PaymentProvider", payload={"payment_id": payment_id})
            return
        if self.state.subscription_id is None:
            self.request_subscription(context, "subscription-implicit")
        self.state.period_start, self.state.period_end = start, end
        self.state.payment_failed = False
        self.state.expired = False
        if payment_id:
            self.state.processed_payment_ids.add(payment_id)
        self._fact("PaymentSucceeded", context.clock.now(), period_end=end, payment_id=payment_id)
        self._fact("EntitlementGranted", context.clock.now(), period_start=start, period_end=end)
        context.emit("domain_fact", "payment_succeeded", source="Billing")
        context.emit("domain_fact", "entitlement_granted", source="Access")

    def renew_period(self, context: object, start: datetime, end: datetime, payment_id: str | None = None) -> None:
        """Open a new paid period after expiry; never reopen the old interval."""
        if payment_id and payment_id in self.state.processed_payment_ids:
            context.emit("payment_notice", "duplicate_payment_success_ignored", source="PaymentProvider", payload={"payment_id": payment_id})
            return
        if not self.state.expired:
            raise ValueError("renewal period requires an expired entitlement")
        if end <= start:
            raise ValueError("renewal period must have a positive duration")
        self.state.period_start, self.state.period_end = start, end
        self.state.payment_failed = False
        self.state.expired = False
        self.state.cancelled = False
        self.state.cancellation_at = None
        if payment_id:
            self.state.processed_payment_ids.add(payment_id)
        self._fact("PaymentSucceeded", context.clock.now(), period_start=start, period_end=end, payment_id=payment_id)
        self._fact("EntitlementGranted", context.clock.now(), period_start=start, period_end=end)
        context.emit("domain_fact", "payment_succeeded", source="Billing")
        context.emit("domain_fact", "new_entitlement_granted", source="Access")

    def record_note(self, context: object, body: str, entry_id: str | None = None, user_id: str | None = None) -> bool:
        return self._record(context, "note", body, context.clock.now(), entry_id, user_id)

    def record_log(self, context: object, body: str, happened_at: datetime, entry_id: str | None = None, user_id: str | None = None) -> bool:
        return self._record(context, "log_entry", body, happened_at, entry_id, user_id)

    def fail_payment(self, context: object, payment_id: str | None = None) -> None:
        if payment_id and payment_id in self.state.processed_payment_ids:
            context.emit("payment_notice", "duplicate_payment_failure_ignored", source="PaymentProvider", payload={"payment_id": payment_id})
            return
        self.state.payment_failed = True
        if payment_id:
            self.state.processed_payment_ids.add(payment_id)
        self._fact("PaymentFailed", context.clock.now(), payment_id=payment_id)
        context.emit("domain_fact", "payment_failed", source="PaymentProvider")
        context.emit("access_changed", "workspace_restricted", source="Access", payload={"reason": "payment_failed"})

    def recover_payment(self, context: object) -> None:
        if not self.state.payment_failed:
            context.emit(
                "payment_notice",
                "payment_recovery_already_resolved",
                source="PaymentProvider",
                payload={"reason": "entitlement_already_restored"},
            )
            return
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

    def access_check(self, context: object, user_id: str | None = None) -> bool:
        if user_id is not None and user_id != self.state.user_id:
            context.emit("access_decision", "workspace_access_checked", source="Access", payload={"allowed": False, "reason": "unauthorized_user"})
            return False
        allowed = self.state.access_allowed(context.clock.now())
        context.emit(
            "access_decision",
            "workspace_access_checked",
            source="Access",
            payload={"allowed": allowed, "reason": "entitled" if allowed else self._restriction_reason()},
        )
        return allowed

    def operator_inspect(self, context: object, actor: str) -> dict[str, object]:
        if not actor.strip():
            raise ValueError("operator actor is required")
        decision = self.state.access_allowed(context.clock.now())
        inspection = {
            "actor": actor,
            "user_id": self.state.user_id,
            "workspace_id": self.state.workspace_id,
            "access_allowed": decision,
            "reason": "entitled" if decision else self._restriction_reason(),
            "entry_count": len(self.state.entries),
            "period_start": self.state.period_start.isoformat() if self.state.period_start else None,
            "period_end": self.state.period_end.isoformat() if self.state.period_end else None,
            "payment_failed": self.state.payment_failed,
            "expired": self.state.expired,
            "cancelled": self.state.cancelled,
            "cancellation_at": self.state.cancellation_at.isoformat() if self.state.cancellation_at else None,
            "event_count": len(self.state.events),
        }
        context.emit("operator_observation", "account_inspected", source="Operations", payload=inspection)
        return inspection

    def operator_restore(self, context: object, actor: str, reason: str) -> bool:
        if not actor.strip() or not reason.strip():
            raise ValueError("operator actor and reason are required")
        if not self.state.payment_failed:
            return False
        self.state.payment_failed = False
        self._fact("OperatorInterventionRecorded", context.clock.now(), actor=actor, reason=reason)
        self._fact("EntitlementRestored", context.clock.now(), source="operator")
        context.emit("operator_action", "entitlement_restored", source="Operations", payload={"actor": actor, "reason": reason})
        return True

    def daily_summary(
        self,
        context: object,
        start: datetime,
        end: datetime,
        timezone_name: str = "UTC",
    ) -> dict[str, int]:
        """Project recorded facts without mutating the append-only history."""
        try:
            local_zone = ZoneInfo(timezone_name)
        except ZoneInfoNotFoundError as exc:
            raise ValueError(f"unknown timezone: {timezone_name}") from exc
        counts: Counter[str] = Counter(
            entry.recorded_at.astimezone(local_zone).date().isoformat()
            for entry in self.state.entries
            if start <= entry.recorded_at <= end
        )
        summary = dict(sorted(counts.items()))
        context.emit(
            "projection_result",
            "daily_entry_summary",
            source="Insights",
            payload={
                "start": start.isoformat(),
                "end": end.isoformat(),
                "timezone": timezone_name,
                "calculation_version": SUMMARY_CALCULATION_VERSION,
                "counts": summary,
            },
        )
        return summary

    def _record(self, context: object, kind: str, body: str, happened_at: datetime, entry_id: str | None, user_id: str | None) -> bool:
        if not body.strip():
            context.emit("command_rejected", f"{kind}_rejected", source="Recording", payload={"reason": "empty_body"})
            return False
        if not self.access_check(context, user_id):
            reason = "unauthorized_user" if user_id is not None and user_id != self.state.user_id else "restricted"
            context.emit("command_rejected", f"{kind}_rejected", source="Recording", payload={"reason": reason})
            return False
        if entry_id:
            existing = next((entry for entry in self.state.entries if entry.entry_id == entry_id), None)
            if existing:
                if existing.kind == kind and existing.body == body:
                    return True
                context.emit(
                    "command_rejected",
                    f"{kind}_rejected",
                    source="Recording",
                    payload={"reason": "conflicting_entry_retry", "entry_id": entry_id},
                )
                return False
        entry_id = entry_id or self.ids.new("entry")
        recorded_at = context.clock.now()
        self.state.entries.append(SimEntry(entry_id, kind, body, happened_at, recorded_at))
        self._fact(
            "NoteRecorded" if kind == "note" else "LogEntryRecorded",
            context.clock.now(),
            kind=kind,
            entry_id=entry_id,
            body=body,
            happened_at=happened_at,
            recorded_at=recorded_at,
        )
        context.emit("domain_fact", f"{kind}_recorded", source="Recording")
        return True

    def _restriction_reason(self) -> str:
        if self.state.expired:
            return "expired"
        if self.state.payment_failed:
            return "payment_failed"
        return "no_entitlement"
