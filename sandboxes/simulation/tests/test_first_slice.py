from datetime import datetime, timedelta, timezone

from app.simulation.environment import WaymarkSimulation


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
