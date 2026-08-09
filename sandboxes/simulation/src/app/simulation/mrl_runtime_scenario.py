"""WNT MRL Runtime adapter for the single Waymark simulation environment."""

from datetime import datetime, timedelta, timezone

from mrl_simulation_runtime.actors import Actor
from mrl_simulation_runtime.invariants import Invariant
from mrl_simulation_runtime.scenario import InitialScheduledAction, Scenario

from app.simulation.environment import WaymarkSimulation


START = datetime(2026, 9, 1, tzinfo=timezone.utc)


def create_simulation() -> Scenario:
    simulation = WaymarkSimulation()
    end = START + timedelta(days=7)

    def action(offset: timedelta, name: str, callback):
        return InitialScheduledAction(START + offset, callback, name, source="WaymarkScenario")

    def create(context):
        simulation.create_account(context)

    def activate(context):
        simulation.activate_period(context, START, end)

    def note(context):
        simulation.record_note(context, "Notice what happened today")

    def fail(context):
        simulation.fail_payment(context)

    def restricted_write(context):
        simulation.record_log(context, "This write should be rejected", context.clock.now())

    def recover(context):
        simulation.recover_payment(context)

    def cancel(context):
        simulation.cancel(context)

    def log(context):
        simulation.record_log(context, "Payment recovered and access returned", context.clock.now())

    def expire(context):
        simulation.expire(context)

    def invariant(context):
        if "PaymentFailed" not in simulation.state.facts:
            return True
        return 1 <= len(simulation.state.entries) <= 2 and simulation.state.facts.count("PaymentFailed") == 1

    return Scenario(
        name="waymark.subscription_backed_workspace",
        seed=20260901,
        initial_time=START,
        run_id="waymark-first-slice",
        actors=[Actor("subscriber")],
        scheduled_actions=[
            action(timedelta(minutes=1), "create_account", create),
            action(timedelta(minutes=2), "activate_period", activate),
            action(timedelta(hours=1), "record_note", note),
            action(timedelta(days=2), "payment_failure", fail),
            action(timedelta(days=2, minutes=1), "restricted_write", restricted_write),
            action(timedelta(days=3), "payment_recovery", recover),
            action(timedelta(days=3, minutes=1), "record_log", log),
            action(timedelta(days=4), "schedule_cancellation", cancel),
            action(timedelta(days=7), "period_expiry", expire),
        ],
        invariants=[Invariant("durable_entries_survive_payment_failure", invariant)],
    )
