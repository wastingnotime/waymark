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


def test_domain_rejects_naive_command_timestamps():
    domain = WaymarkDomain()
    with pytest.raises(DomainError, match="timezone-aware"):
        domain.create_account(uuid4(), uuid4(), uuid4(), datetime(2026, 9, 1))


def test_reusing_payment_id_with_different_period_is_rejected():
    domain = subscribed()
    with pytest.raises(DomainError, match="payment id already used"):
        domain.record_payment_success(instant(8), instant(15), "pay-1", instant(8))


def test_reusing_entry_id_with_different_body_is_rejected():
    domain = subscribed()
    entry_id = uuid4()
    domain.record_note("original", instant(2), entry_id)
    with pytest.raises(DomainError, match="entry id already used"):
        domain.record_note("changed", instant(2), entry_id)


def test_cancellation_restricts_access_at_its_effective_boundary():
    domain = subscribed()
    domain.cancel_subscription(instant(4), instant(2))
    assert domain.access_at(instant(4)).reason == "no_entitlement"
    assert domain.access_at(instant(3)).allowed


def test_daily_summary_uses_the_requested_timezone_calendar():
    domain = subscribed()
    recorded_at = datetime(2026, 9, 2, 1, 30, tzinfo=UTC)
    domain.record_note("late UTC", recorded_at)
    assert domain.daily_summary(instant(1), instant(3), "America/Sao_Paulo") == {"2026-09-01": 1}


def test_daily_summary_rejects_unknown_timezone():
    domain = subscribed()
    with pytest.raises(DomainError, match="unknown timezone"):
        domain.daily_summary(instant(1), instant(3), "Mars/Olympus")


def test_payment_id_cannot_be_reused_across_success_and_failure():
    domain = subscribed()
    with pytest.raises(DomainError, match="payment id already used"):
        domain.record_payment_failure("pay-1", instant(2))


def test_cancellation_retry_is_idempotent_but_conflicting_retry_is_rejected():
    domain = subscribed()
    first = domain.cancel_subscription(instant(7), instant(2))
    assert domain.cancel_subscription(instant(7), instant(3)) == first
    with pytest.raises(DomainError, match="cancellation already scheduled"):
        domain.cancel_subscription(instant(6), instant(3))


def test_expired_entitlement_reports_expired_access_reason():
    domain = subscribed()
    domain.expire_entitlements(instant(8))
    assert domain.access_at(instant(8)).reason == "expired"


def test_subscription_request_retry_is_idempotent_but_new_id_is_rejected():
    domain = WaymarkDomain()
    domain.create_account(uuid4(), uuid4(), uuid4(), instant(1))
    subscription_id = uuid4()
    first = domain.start_subscription(subscription_id, instant(1))
    assert domain.start_subscription(subscription_id, instant(2)) == first
    with pytest.raises(DomainError, match="current subscription already exists"):
        domain.start_subscription(uuid4(), instant(2))
