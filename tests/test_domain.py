from datetime import datetime, timezone
from uuid import uuid4

import pytest

from waymark import DomainError, WaymarkDomain


UTC = timezone.utc


def instant(day: int, hour: int = 0) -> datetime:
    return datetime(2026, 9, day, hour, tzinfo=UTC)


def subscribed() -> WaymarkDomain:
    domain = WaymarkDomain()
    domain.create_account(uuid4(), uuid4(), uuid4(), instant(1))
    domain.start_subscription(uuid4(), instant(1))
    domain.record_payment_success(instant(1), instant(8), "pay-1", instant(1))
    return domain


def test_successful_payment_grants_access_and_entries_are_durable():
    domain = subscribed()
    note = domain.record_note("A useful observation", instant(2))
    assert domain.access_at(instant(2)).allowed
    assert note.body == "A useful observation"


def test_failed_payment_restricts_access_but_keeps_existing_entries():
    domain = subscribed()
    note = domain.record_note("Keep this fact", instant(2))
    domain.record_payment_failure("renewal-1", instant(3))
    assert domain.access_at(instant(3)).reason == "payment_failed"
    assert note in domain.facts
    with pytest.raises(DomainError):
        domain.record_log("Cannot write while restricted", instant(3), instant(3))


def test_recovery_restores_access_within_the_paid_period():
    domain = subscribed()
    domain.record_payment_failure("renewal-1", instant(3))
    domain.record_payment_success(instant(1), instant(8), "recovery-1", instant(4))
    assert domain.access_at(instant(4)).allowed


def test_expiry_removes_access_at_the_exclusive_boundary():
    domain = subscribed()
    domain.expire_entitlements(instant(8))
    assert not domain.access_at(instant(8)).allowed


def test_daily_summary_is_derived_and_reproducible():
    domain = subscribed()
    domain.record_note("one", instant(2, 9))
    domain.record_log("two", instant(2, 10), instant(2, 10))
    assert domain.daily_summary(instant(2), instant(3)) == {"2026-09-02": 2}
    assert domain.daily_summary(instant(2), instant(3)) == {"2026-09-02": 2}


def test_retries_do_not_duplicate_payment_or_entry_facts():
    domain = subscribed()
    payment = domain.record_payment_success(instant(1), instant(8), "pay-1", instant(1))
    assert domain.record_payment_success(instant(1), instant(8), "pay-1", instant(2)) == payment
    entry_id = uuid4()
    first = domain.record_note("same", instant(2), entry_id)
    assert domain.record_note("same", instant(2), entry_id) == first
