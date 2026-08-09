from datetime import datetime, timedelta, timezone

import pytest

from app.simulation.environment import WaymarkSimulation
from app.simulation.ports import DeterministicIds, FakePaymentProvider


class Context:
    def __init__(self, now):
        self.clock = type("Clock", (), {"now": lambda _: now})()
        self.events = []

    def emit(self, *args, **kwargs):
        self.events.append((args, kwargs))


def test_first_slice_preserves_facts_through_failure_and_recovery():
    start = datetime(2026, 9, 1, tzinfo=timezone.utc)
    context = Context(start)
    simulation = WaymarkSimulation()
    simulation.create_account(context)
    simulation.activate_period(context, start, start + timedelta(days=7))
    assert simulation.record_note(context, "one")
    simulation.fail_payment(context)
    assert not simulation.record_log(context, "rejected", start)
    simulation.recover_payment(context)
    assert simulation.record_log(context, "two", start)
    assert len(simulation.state.entries) == 2
    assert simulation.state.facts.count("PaymentFailed") == 1


def test_first_slice_restricts_at_exclusive_period_boundary():
    start = datetime(2026, 9, 1, tzinfo=timezone.utc)
    end = start + timedelta(days=7)
    context = Context(start)
    simulation = WaymarkSimulation()
    simulation.create_account(context)
    simulation.activate_period(context, start, end)
    context.clock = type("Clock", (), {"now": lambda _: end})()
    simulation.expire(context)
    assert not simulation.access_check(context)


def test_daily_summary_is_recomputed_from_entries():
    start = datetime(2026, 9, 1, tzinfo=timezone.utc)
    context = Context(start)
    simulation = WaymarkSimulation()
    simulation.create_account(context)
    simulation.activate_period(context, start, start + timedelta(days=7))
    simulation.record_note(context, "one")
    first = simulation.daily_summary(context, start, start + timedelta(days=7))
    second = simulation.daily_summary(context, start, start + timedelta(days=7))
    assert first == second == {"2026-09-01": 1}


def test_cancellation_keeps_access_until_period_end():
    start = datetime(2026, 9, 1, tzinfo=timezone.utc)
    end = start + timedelta(days=7)
    context = Context(start)
    simulation = WaymarkSimulation()
    simulation.create_account(context)
    simulation.activate_period(context, start, end)
    simulation.cancel(context)
    assert simulation.access_check(context)
    assert simulation.state.cancellation_at == end


def test_entries_require_non_empty_bodies():
    start = datetime(2026, 9, 1, tzinfo=timezone.utc)
    context = Context(start)
    simulation = WaymarkSimulation()
    simulation.create_account(context)
    simulation.activate_period(context, start, start + timedelta(days=7))
    assert not simulation.record_note(context, "  ")
    assert simulation.state.entries == []


def test_event_history_and_provider_outcomes_are_deterministic():
    start = datetime(2026, 9, 1, tzinfo=timezone.utc)
    context = Context(start)
    simulation = WaymarkSimulation(DeterministicIds())
    provider = FakePaymentProvider()
    provider.succeed("initial")
    simulation.create_account(context)
    simulation.activate_period(context, start, start + timedelta(days=7))
    assert simulation.state.user_id == "waymark-user-0001"
    assert [event.name for event in simulation.state.events] == [
        "AccountCreated",
        "WorkspaceCreated",
        "PaymentSucceeded",
        "EntitlementGranted",
    ]
    assert provider.outcomes == {"initial": "succeeded"}


def test_operator_can_inspect_and_restore_a_suspended_entitlement():
    start = datetime(2026, 9, 1, tzinfo=timezone.utc)
    context = Context(start)
    simulation = WaymarkSimulation()
    simulation.create_account(context)
    simulation.activate_period(context, start, start + timedelta(days=7))
    simulation.fail_payment(context)
    inspection = simulation.operator_inspect(context, "support-operator")
    assert inspection["reason"] == "payment_failed"
    assert simulation.operator_restore(context, "support-operator", "verified payment manually")
    assert simulation.access_check(context)
    assert simulation.state.facts.count("OperatorInterventionRecorded") == 1


def test_recovery_after_operator_restore_is_idempotent():
    start = datetime(2026, 9, 1, tzinfo=timezone.utc)
    context = Context(start)
    simulation = WaymarkSimulation()
    simulation.create_account(context)
    simulation.activate_period(context, start, start + timedelta(days=7))
    simulation.fail_payment(context)
    assert simulation.operator_restore(context, "support-operator", "verified payment manually")
    simulation.recover_payment(context)
    assert simulation.state.facts.count("EntitlementRestored") == 1


def test_daily_summary_uses_the_requested_timezone_calendar():
    start = datetime(2026, 9, 1, tzinfo=timezone.utc)
    context = Context(start)
    simulation = WaymarkSimulation()
    simulation.create_account(context)
    simulation.activate_period(context, start, start + timedelta(days=7))
    context.clock = type("Clock", (), {"now": lambda _: datetime(2026, 9, 2, 1, 30, tzinfo=timezone.utc)})()
    simulation.record_note(context, "late in UTC")
    summary = simulation.daily_summary(
        context,
        start,
        start + timedelta(days=7),
        "America/Sao_Paulo",
    )
    assert summary == {"2026-09-01": 1}


def test_daily_summary_rejects_unknown_timezone():
    start = datetime(2026, 9, 1, tzinfo=timezone.utc)
    context = Context(start)
    simulation = WaymarkSimulation()
    with pytest.raises(ValueError, match="unknown timezone"):
        simulation.daily_summary(context, start, start, "Mars/Olympus")


def test_summary_observation_records_timezone_without_mutating_events():
    start = datetime(2026, 9, 1, tzinfo=timezone.utc)
    context = Context(start)
    simulation = WaymarkSimulation()
    simulation.create_account(context)
    simulation.activate_period(context, start, start + timedelta(days=7))
    simulation.record_note(context, "one")
    event_count = len(simulation.state.events)
    simulation.daily_summary(context, start, start + timedelta(days=7), "America/Sao_Paulo")
    assert len(simulation.state.events) == event_count
    assert context.events[-1][1]["payload"]["timezone"] == "America/Sao_Paulo"


def test_renewal_after_expiry_opens_a_new_period():
    start = datetime(2026, 9, 1, tzinfo=timezone.utc)
    end = start + timedelta(days=7)
    context = Context(end)
    simulation = WaymarkSimulation()
    simulation.create_account(context)
    simulation.activate_period(context, start, end)
    simulation.expire(context)
    assert not simulation.access_check(context)
    new_end = end + timedelta(days=7)
    simulation.renew_period(context, end, new_end)
    assert simulation.state.period_start == end
    assert simulation.access_check(context)
    assert simulation.state.facts.count("EntitlementGranted") == 2


def test_renewal_requires_expiry():
    start = datetime(2026, 9, 1, tzinfo=timezone.utc)
    context = Context(start)
    simulation = WaymarkSimulation()
    simulation.create_account(context)
    simulation.activate_period(context, start, start + timedelta(days=7))
    with pytest.raises(ValueError, match="expired entitlement"):
        simulation.renew_period(context, start + timedelta(days=7), start + timedelta(days=14))


def test_renewal_requires_a_positive_period():
    start = datetime(2026, 9, 1, tzinfo=timezone.utc)
    context = Context(start)
    simulation = WaymarkSimulation()
    simulation.create_account(context)
    simulation.activate_period(context, start, start + timedelta(days=7))
    simulation.expire(context)
    with pytest.raises(ValueError, match="positive duration"):
        simulation.renew_period(context, start + timedelta(days=7), start + timedelta(days=7))


def test_event_history_replays_to_the_same_state():
    start = datetime(2026, 9, 1, tzinfo=timezone.utc)
    end = start + timedelta(days=7)
    context = Context(start)
    simulation = WaymarkSimulation()
    simulation.create_account(context)
    simulation.activate_period(context, start, end)
    simulation.record_note(context, "one")
    simulation.fail_payment(context)
    replayed = WaymarkSimulation.replay(simulation.state.events)
    assert replayed.state.entries == simulation.state.entries
    assert replayed.state.payment_failed == simulation.state.payment_failed
    assert replayed.state.period_end == simulation.state.period_end


def test_duplicate_payment_failure_delivery_does_not_duplicate_facts():
    start = datetime(2026, 9, 1, tzinfo=timezone.utc)
    context = Context(start)
    simulation = WaymarkSimulation()
    simulation.create_account(context)
    simulation.activate_period(context, start, start + timedelta(days=7))
    simulation.fail_payment(context, "renewal-1")
    simulation.fail_payment(context, "renewal-1")
    assert simulation.state.facts.count("PaymentFailed") == 1
    assert any(event[0][1] == "duplicate_payment_failure_ignored" for event in context.events)


def test_replay_clears_old_cancellation_when_a_new_period_is_granted():
    start = datetime(2026, 9, 1, tzinfo=timezone.utc)
    end = start + timedelta(days=7)
    context = Context(start)
    simulation = WaymarkSimulation()
    simulation.create_account(context)
    simulation.activate_period(context, start, end)
    simulation.cancel(context)
    simulation.expire(context)
    simulation.renew_period(context, end, end + timedelta(days=7))
    replayed = WaymarkSimulation.replay(simulation.state.events)
    assert not replayed.state.cancelled
    assert replayed.state.cancellation_at is None
