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
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError


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
        existing = next((f for f in self.facts if isinstance(f, AccountCreated)), None)
        if existing:
            if (existing.user_id, existing.payer_id, existing.workspace_id) != (user_id, payer_id, workspace_id):
                raise DomainError("account already exists with different details")
            return existing
        return self._append(AccountCreated(user_id, payer_id, workspace_id, recorded_at))

    def start_subscription(self, subscription_id: UUID, requested_at: datetime) -> SubscriptionRequested:
        self._require_aware(requested_at)
        account = self._account()
        existing = next((f for f in self.facts if isinstance(f, SubscriptionRequested)), None)
        if existing:
            if existing.subscription_id != subscription_id:
                raise DomainError("a current subscription already exists")
            return existing
        return self._append(SubscriptionRequested(subscription_id, account.user_id, requested_at))

    def record_payment_success(
        self,
        period_start: datetime,
        period_end: datetime,
        payment_id: str,
        recorded_at: datetime,
    ) -> PaymentSucceeded:
        self._require_aware(period_start, period_end, recorded_at)
        self._require_payment_id(payment_id)
        subscription = self._subscription()
        if period_end <= period_start:
            raise DomainError("billing period must have a positive duration")
        existing_payment = next(
            (f for f in self.facts if isinstance(f, PaymentSucceeded) and f.payment_id == payment_id),
            None,
        )
        if existing_payment:
            if (existing_payment.period_start, existing_payment.period_end) != (period_start, period_end):
                raise DomainError("payment id already used with different details")
            return existing_payment
        if any(isinstance(f, PaymentFailed) and f.payment_id == payment_id for f in self.facts):
            raise DomainError("payment id already used with a different outcome")
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
        self._require_payment_id(payment_id)
        subscription = self._subscription()
        if any(isinstance(f, PaymentSucceeded) and f.payment_id == payment_id for f in self.facts):
            raise DomainError("payment id already used with a different outcome")
        if any(isinstance(f, PaymentFailed) and f.payment_id == payment_id for f in self.facts):
            return next(f for f in self.facts if isinstance(f, PaymentFailed) and f.payment_id == payment_id)
        failure = self._append(PaymentFailed(subscription.subscription_id, payment_id, recorded_at))
        current = self._current_entitlement(recorded_at)
        if current and not current.suspended and not current.expired:
            self._append(EntitlementSuspended(current.entitlement_id, recorded_at))
        return failure

    def cancel_subscription(self, effective_at: datetime, recorded_at: datetime) -> CancellationScheduled:
        self._require_aware(effective_at, recorded_at)
        if effective_at < recorded_at:
            raise DomainError("effective_at must not precede recorded_at")
        subscription = self._subscription()
        existing = next((f for f in self.facts if isinstance(f, CancellationScheduled)), None)
        if existing:
            if existing.effective_at != effective_at:
                raise DomainError("cancellation already scheduled with different details")
            return existing
        if not any(
            entitlement.effective_from <= effective_at <= entitlement.effective_until
            and not entitlement.expired
            for entitlement in self._entitlements()
        ):
            raise DomainError("cancellation requires an active paid entitlement")
        return self._append(CancellationScheduled(subscription.subscription_id, effective_at, recorded_at))

    def expire_entitlements(self, at: datetime) -> int:
        self._require_aware(at)
        expired_count = 0
        for entitlement in self._entitlements():
            if entitlement.effective_until <= at and not entitlement.expired:
                self._append(EntitlementExpired(entitlement.entitlement_id, at))
                expired_count += 1
        return expired_count

    def access_at(self, at: datetime) -> AccessDecision:
        self._require_aware(at)
        cancellation_at = self._cancellation_at()
        if cancellation_at is not None and cancellation_at <= at:
            return AccessDecision(False, "no_entitlement", at)
        entitlement = self._current_entitlement(at)
        if entitlement is None:
            if any(e.expired and e.effective_until <= at for e in self._entitlements()):
                return AccessDecision(False, "expired", at)
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
        existing_entry = next((f for f in self.facts if getattr(f, "entry_id", None) == entry_id), None)
        if existing_entry:
            if not isinstance(existing_entry, NoteRecorded) or existing_entry.body != body:
                raise DomainError("entry id already used with different details")
            return existing_entry
        return self._append(NoteRecorded(entry_id, self._account().workspace_id, body, recorded_at))

    def record_log(self, body: str, happened_at: datetime, recorded_at: datetime, entry_id: UUID | None = None) -> LogEntryRecorded:
        self._require_aware(happened_at, recorded_at)
        if recorded_at < happened_at:
            raise DomainError("recorded_at must not precede happened_at")
        self._require_access(recorded_at)
        self._require_body(body)
        entry_id = entry_id or uuid4()
        existing_entry = next((f for f in self.facts if getattr(f, "entry_id", None) == entry_id), None)
        if existing_entry:
            if (
                not isinstance(existing_entry, LogEntryRecorded)
                or existing_entry.body != body
                or existing_entry.happened_at != happened_at
            ):
                raise DomainError("entry id already used with different details")
            return existing_entry
        return self._append(LogEntryRecorded(entry_id, self._account().workspace_id, body, happened_at, recorded_at))

    def daily_summary(self, start: datetime, end: datetime, timezone_name: str = "UTC") -> dict[str, int]:
        self._require_aware(start, end)
        if end < start:
            raise DomainError("summary end must not precede start")
        try:
            local_zone = ZoneInfo(timezone_name)
        except ZoneInfoNotFoundError as exc:
            raise DomainError(f"unknown timezone: {timezone_name}") from exc
        counts: Counter[str] = Counter()
        for fact in self.facts:
            instant = getattr(fact, "recorded_at", None)
            if isinstance(fact, (NoteRecorded, LogEntryRecorded)) and start <= instant <= end:
                counts[instant.astimezone(local_zone).date().isoformat()] += 1
        return dict(sorted(counts.items()))

    def _subscription(self) -> SubscriptionRequested:
        try:
            return next(f for f in self.facts if isinstance(f, SubscriptionRequested))
        except StopIteration as exc:
            raise DomainError("subscription does not exist") from exc

    def _cancellation_at(self) -> datetime | None:
        cancellations = [f.effective_at for f in self.facts if isinstance(f, CancellationScheduled)]
        return min(cancellations, default=None)

    def _require_access(self, at: datetime) -> None:
        if not self.access_at(at).allowed:
            raise DomainError("workspace access is restricted")

    @staticmethod
    def _require_body(body: str) -> None:
        if not body.strip():
            raise DomainError("entry body must not be empty")

    @staticmethod
    def _require_payment_id(payment_id: str) -> None:
        if not payment_id.strip():
            raise DomainError("payment id must not be empty")

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
