"""The first executable Waymark domain slice.

The store is intentionally small and in-memory. Facts are append-only; all
operational state is rebuilt from them, making this a useful seam for a real
adapter later.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Union
from uuid import UUID, uuid4


class DomainError(ValueError):
    """A command violates a Waymark domain invariant."""


@dataclass(frozen=True)
class AccountCreated:
    user_id: UUID
    payer_id: UUID
    workspace_id: UUID
    recorded_at: datetime


@dataclass(frozen=True)
class NoteRecorded:
    entry_id: UUID
    workspace_id: UUID
    body: str
    recorded_at: datetime


@dataclass(frozen=True)
class LogEntryRecorded:
    entry_id: UUID
    workspace_id: UUID
    body: str
    happened_at: datetime
    recorded_at: datetime


@dataclass(frozen=True)
class SubscriptionRequested:
    subscription_id: UUID
    user_id: UUID
    requested_at: datetime


@dataclass(frozen=True)
class PaymentSucceeded:
    subscription_id: UUID
    period_start: datetime
    period_end: datetime
    payment_id: str
    recorded_at: datetime


@dataclass(frozen=True)
class PaymentFailed:
    subscription_id: UUID
    payment_id: str
    recorded_at: datetime


@dataclass(frozen=True)
class CancellationScheduled:
    subscription_id: UUID
    effective_at: datetime
    recorded_at: datetime


@dataclass(frozen=True)
class EntitlementGranted:
    entitlement_id: UUID
    user_id: UUID
    effective_from: datetime
    effective_until: datetime
    recorded_at: datetime


@dataclass(frozen=True)
class EntitlementSuspended:
    entitlement_id: UUID
    recorded_at: datetime


@dataclass(frozen=True)
class EntitlementRestored:
    entitlement_id: UUID
    recorded_at: datetime


@dataclass(frozen=True)
class EntitlementExpired:
    entitlement_id: UUID
    recorded_at: datetime


Fact = Union[
    AccountCreated,
    NoteRecorded,
    LogEntryRecorded,
    SubscriptionRequested,
    PaymentSucceeded,
    PaymentFailed,
    CancellationScheduled,
    EntitlementGranted,
    EntitlementSuspended,
    EntitlementRestored,
    EntitlementExpired,
]


@dataclass(frozen=True)
class AccessDecision:
    allowed: bool
    reason: str
    evaluated_at: datetime


class WaymarkDomain:
    """Command handler and projection for one Waymark user's workspace."""

    def __init__(self) -> None:
        self.facts: list[Fact] = []

    def _append(self, fact: Fact) -> Fact:
        self.facts.append(fact)
        return fact

    def _account(self) -> AccountCreated:
        try:
            return next(f for f in self.facts if isinstance(f, AccountCreated))
        except StopIteration as exc:
            raise DomainError("account does not exist") from exc

    def create_account(
        self, user_id: UUID, payer_id: UUID, workspace_id: UUID, recorded_at: datetime
    ) -> AccountCreated:
        self._require_aware(recorded_at)
        if any(isinstance(f, AccountCreated) for f in self.facts):
            raise DomainError("only one account is supported")
        return self._append(AccountCreated(user_id, payer_id, workspace_id, recorded_at))

    def start_subscription(self, subscription_id: UUID, requested_at: datetime) -> SubscriptionRequested:
        self._require_aware(requested_at)
        account = self._account()
        if any(isinstance(f, SubscriptionRequested) for f in self.facts):
            raise DomainError("a current subscription already exists")
        return self._append(SubscriptionRequested(subscription_id, account.user_id, requested_at))

    def record_payment_success(
        self,
        period_start: datetime,
        period_end: datetime,
        payment_id: str,
        recorded_at: datetime,
    ) -> PaymentSucceeded:
        self._require_aware(period_start, period_end, recorded_at)
        subscription = self._subscription()
        if period_end <= period_start:
            raise DomainError("billing period must have a positive duration")
        if any(isinstance(f, PaymentSucceeded) and f.payment_id == payment_id for f in self.facts):
            return next(f for f in self.facts if isinstance(f, PaymentSucceeded) and f.payment_id == payment_id)
        if any(
            period_start < entitlement.effective_until
            and entitlement.effective_from < period_end
            for entitlement in self._entitlements()
        ):
            current = self._current_entitlement(period_start)
            if not current or not current.suspended:
                raise DomainError("billing period overlaps an existing entitlement")
        payment = self._append(PaymentSucceeded(subscription.subscription_id, period_start, period_end, payment_id, recorded_at))
        current = self._current_entitlement(period_start)
        if current and current.suspended and period_start < current.effective_until:
            self._append(EntitlementRestored(current.entitlement_id, recorded_at))
        else:
            self._append(EntitlementGranted(uuid4(), self._account().user_id, period_start, period_end, recorded_at))
        return payment

    def record_payment_failure(self, payment_id: str, recorded_at: datetime) -> PaymentFailed:
        self._require_aware(recorded_at)
        subscription = self._subscription()
        if any(isinstance(f, PaymentFailed) and f.payment_id == payment_id for f in self.facts):
            return next(f for f in self.facts if isinstance(f, PaymentFailed) and f.payment_id == payment_id)
        failure = self._append(PaymentFailed(subscription.subscription_id, payment_id, recorded_at))
        current = self._current_entitlement(recorded_at)
        if current and not current.suspended and not current.expired:
            self._append(EntitlementSuspended(current.entitlement_id, recorded_at))
        return failure

    def cancel_subscription(self, effective_at: datetime, recorded_at: datetime) -> CancellationScheduled:
        self._require_aware(effective_at, recorded_at)
        subscription = self._subscription()
        if any(isinstance(f, CancellationScheduled) for f in self.facts):
            raise DomainError("subscription is already scheduled for cancellation")
        return self._append(CancellationScheduled(subscription.subscription_id, effective_at, recorded_at))

    def expire_entitlements(self, at: datetime) -> None:
        self._require_aware(at)
        for entitlement in self._entitlements():
            if entitlement.effective_until <= at and not entitlement.expired:
                self._append(EntitlementExpired(entitlement.entitlement_id, at))

    def access_at(self, at: datetime) -> AccessDecision:
        self._require_aware(at)
        entitlement = self._current_entitlement(at)
        if entitlement is None:
            return AccessDecision(False, "no_entitlement", at)
        if entitlement.suspended:
            return AccessDecision(False, "payment_failed", at)
        if entitlement.expired:
            return AccessDecision(False, "expired", at)
        return AccessDecision(True, "entitled", at)

    def record_note(self, body: str, recorded_at: datetime, entry_id: UUID | None = None) -> NoteRecorded:
        self._require_aware(recorded_at)
        self._require_access(recorded_at)
        self._require_body(body)
        entry_id = entry_id or uuid4()
        if any(getattr(f, "entry_id", None) == entry_id for f in self.facts):
            return next(f for f in self.facts if getattr(f, "entry_id", None) == entry_id)
        return self._append(NoteRecorded(entry_id, self._account().workspace_id, body, recorded_at))

    def record_log(self, body: str, happened_at: datetime, recorded_at: datetime, entry_id: UUID | None = None) -> LogEntryRecorded:
        self._require_aware(happened_at, recorded_at)
        self._require_access(recorded_at)
        self._require_body(body)
        entry_id = entry_id or uuid4()
        if any(getattr(f, "entry_id", None) == entry_id for f in self.facts):
            return next(f for f in self.facts if getattr(f, "entry_id", None) == entry_id)
        return self._append(LogEntryRecorded(entry_id, self._account().workspace_id, body, happened_at, recorded_at))

    def daily_summary(self, start: datetime, end: datetime, timezone_name: str = "UTC") -> dict[str, int]:
        self._require_aware(start, end)
        if end < start:
            raise DomainError("summary end must not precede start")
        # The first slice accepts UTC; named timezone conversion belongs in the adapter.
        if timezone_name != "UTC":
            raise DomainError("only UTC summaries are supported in the first slice")
        counts: Counter[str] = Counter()
        for fact in self.facts:
            instant = getattr(fact, "recorded_at", None)
            if isinstance(fact, (NoteRecorded, LogEntryRecorded)) and start <= instant <= end:
                counts[instant.date().isoformat()] += 1
        return dict(sorted(counts.items()))

    def _subscription(self) -> SubscriptionRequested:
        try:
            return next(f for f in self.facts if isinstance(f, SubscriptionRequested))
        except StopIteration as exc:
            raise DomainError("subscription does not exist") from exc

    def _require_access(self, at: datetime) -> None:
        if not self.access_at(at).allowed:
            raise DomainError("workspace access is restricted")

    @staticmethod
    def _require_body(body: str) -> None:
        if not body.strip():
            raise DomainError("entry body must not be empty")

    @staticmethod
    def _require_aware(*timestamps: datetime) -> None:
        if any(timestamp.tzinfo is None or timestamp.utcoffset() is None for timestamp in timestamps):
            raise DomainError("timestamps must be timezone-aware")

    def _entitlements(self) -> list["_EntitlementState"]:
        states: dict[UUID, _EntitlementState] = {}
        for fact in self.facts:
            if isinstance(fact, EntitlementGranted):
                states[fact.entitlement_id] = _EntitlementState(fact)
            elif isinstance(fact, EntitlementSuspended) and fact.entitlement_id in states:
                states[fact.entitlement_id].suspended = True
            elif isinstance(fact, EntitlementRestored) and fact.entitlement_id in states:
                states[fact.entitlement_id].suspended = False
            elif isinstance(fact, EntitlementExpired) and fact.entitlement_id in states:
                states[fact.entitlement_id].expired = True
        return list(states.values())

    def _current_entitlement(self, at: datetime) -> "_EntitlementState | None":
        candidates = [e for e in self._entitlements() if e.effective_from <= at < e.effective_until]
        return max(candidates, key=lambda e: e.effective_from, default=None)


@dataclass
class _EntitlementState:
    fact: EntitlementGranted
    suspended: bool = False
    expired: bool = False

    @property
    def entitlement_id(self) -> UUID:
        return self.fact.entitlement_id

    @property
    def effective_from(self) -> datetime:
        return self.fact.effective_from

    @property
    def effective_until(self) -> datetime:
        return self.fact.effective_until
