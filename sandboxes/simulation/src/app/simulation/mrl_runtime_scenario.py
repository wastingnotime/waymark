"""WNT MRL Runtime adapter for the single Waymark simulation environment."""

from datetime import datetime, timedelta, timezone

from mrl_simulation_runtime.actors import Actor
from mrl_simulation_runtime.invariants import Invariant
from mrl_simulation_runtime.scenario import (
    InitialScheduledAction,
    ObservatoryEdge,
    ObservatoryNode,
    Scenario,
)

from app.simulation.environment import SUMMARY_CALCULATION_VERSION, WaymarkSimulation
from app.simulation.ports import FakePaymentProvider


START = datetime(2026, 9, 1, tzinfo=timezone.utc)

_GRAPH_SOURCE_BY_BOUNDARY = {
    "WaymarkSimulation": "account_bootstrap",
    "Billing": "payment_processing",
    "Access": "entitlement",
    "Recording": "recording",
    "Insights": "insights",
    "Operations": "operations",
}

_GRAPH_SOURCE_BY_OBSERVATION = {
    "subscription_requested": "subscription_lifecycle",
    "cancellation_scheduled": "subscription_lifecycle",
    "duplicate_subscription_request_ignored": "subscription_lifecycle",
    "duplicate_cancellation_ignored": "subscription_lifecycle",
}

_GRAPH_TARGET_BY_OBSERVATION = {
    "account_created": "fact_history",
    "duplicate_account_creation_ignored": "fact_history",
    "subscription_requested": "fact_history",
    "duplicate_subscription_request_ignored": "fact_history",
    "payment_succeeded": "fact_history",
    "payment_failed": "fact_history",
    "payment_recovered": "fact_history",
    "duplicate_payment_success_ignored": "fact_history",
    "duplicate_payment_failure_ignored": "fact_history",
    "entitlement_granted": "entitlement",
    "new_entitlement_granted": "entitlement",
    "entitlement_expired": "entitlement",
    "entitlement_restored": "entitlement",
    "workspace_allowed": "access_control",
    "workspace_restricted": "access_control",
    "workspace_access_checked": "access_control",
    "note_recorded": "fact_history",
    "log_entry_recorded": "fact_history",
    "note_rejected": "access_control",
    "log_entry_rejected": "access_control",
    "daily_entry_summary": "summary",
    "account_inspected": "access_control",
    "cancellation_scheduled": "fact_history",
    "duplicate_cancellation_ignored": "fact_history",
}


class _ObservatoryContext:
    """Decorate runtime observations with declared graph endpoints."""

    def __init__(self, context: object) -> None:
        self._context = context

    def __getattr__(self, name: str) -> object:
        return getattr(self._context, name)

    def emit(
        self,
        event_type: str,
        name: str,
        *,
        source: str | None = None,
        actor: str | None = None,
        correlation_id: str | None = None,
        payload: dict[str, object] | None = None,
    ) -> object:
        graph_source = _GRAPH_SOURCE_BY_OBSERVATION.get(
            name,
            _GRAPH_SOURCE_BY_BOUNDARY.get(source or "", source),
        )
        graph_target = _GRAPH_TARGET_BY_OBSERVATION.get(name)
        graph_payload = dict(payload or {})
        if graph_target is not None:
            graph_payload["use_case_id"] = graph_target
        return self._context.emit(
            event_type,
            name,
            source=graph_source,
            actor=actor,
            correlation_id=correlation_id,
            payload=graph_payload,
        )


def create_simulation() -> Scenario:
    simulation = WaymarkSimulation()
    payments = FakePaymentProvider()
    end = START + timedelta(days=7)

    def action(offset: timedelta, name: str, callback):
        def observed(context):
            return callback(_ObservatoryContext(context))

        return InitialScheduledAction(START + offset, observed, name, source="WaymarkScenario")

    def create(context):
        simulation.create_account(context)

    def duplicate_create(context):
        simulation.create_account(context)

    def pre_entitlement_access(context):
        simulation.access_check(context)

    def subscribe(context):
        simulation.request_subscription(context, "subscription-1")

    def activate(context):
        payments.succeed("initial-period")
        simulation.activate_period(context, START, end, "initial-period")

    def duplicate_success(context):
        simulation.activate_period(context, START, end, "initial-period")

    def note(context):
        simulation.record_note(context, "Notice what happened today")

    def retried_note(context):
        simulation.record_note(context, "Retried write", "entry-retry")

    def unauthorized_note(context):
        simulation.record_note(context, "Private attempt", user_id="other-user")

    def fail(context):
        payments.fail("renewal-1")
        simulation.fail_payment(context, "renewal-1")

    def restricted_write(context):
        simulation.record_log(context, "This write should be rejected", context.clock.now())

    def duplicate_fail(context):
        simulation.fail_payment(context, "renewal-1")

    def inspect(context):
        simulation.operator_inspect(context, "support-operator")

    def operator_restore(context):
        simulation.operator_restore(context, "support-operator", "verified payment manually")

    def duplicate_operator_restore(context):
        simulation.operator_restore(context, "support-operator", "verified payment manually")

    def recover(context):
        payments.succeed("renewal-1-recovered")
        simulation.recover_payment(context)

    def cancel(context):
        simulation.cancel(context)

    def duplicate_cancel(context):
        simulation.cancel(context)

    def log(context):
        simulation.record_log(context, "Payment recovered and access returned", START + timedelta(days=1))

    def summary(context):
        simulation.daily_summary(context, START, context.clock.now(), "America/Sao_Paulo")

    def expire(context):
        simulation.expire(context)

    def duplicate_expire(context):
        simulation.expire(context)

    def renew(context):
        simulation.renew_period(context, end, end + timedelta(days=7), "renewal-period-2")

    def post_renewal_log(context):
        simulation.record_log(context, "A new paid period began", context.clock.now())

    def invariant(context):
        if "PaymentFailed" not in simulation.state.facts:
            return True
        return len(simulation.state.entries) >= 1 and simulation.state.facts.count("PaymentFailed") == 1

    def cancellation_boundary(context):
        if not simulation.state.cancelled:
            return True
        if simulation.state.cancellation_at != end:
            return False
        if simulation.state.expired:
            return not simulation.state.access_allowed(context.clock.now())
        return simulation.state.access_allowed(context.clock.now())

    def intervention_audited(context):
        if "OperatorInterventionRecorded" not in simulation.state.facts:
            return True
        return "EntitlementRestored" in simulation.state.facts and not simulation.state.payment_failed

    def operator_restore_is_unique(context):
        duplicate_at = START + timedelta(days=2, minutes=3, seconds=10)
        if context.clock.now() < duplicate_at:
            return True
        return simulation.state.facts.count("OperatorInterventionRecorded") == 1 and any(
            observation.name == "duplicate_operator_restore_ignored"
            for observation in context.observations.observations
        )

    def operator_inspection_is_complete(context):
        inspections = [
            observation
            for observation in context.observations.observations
            if observation.type == "operator_observation" and observation.name == "account_inspected"
        ]
        if not inspections:
            return True
        payload = inspections[-1].payload
        return payload.get("reason") == "payment_failed" and payload.get("payment_failed") is True and payload.get("subscription_status") == "past_due" and all(
            key in payload
            for key in ("payer_id", "period_start", "period_end", "payment_failed", "expired", "cancelled", "event_count", "subscription_status")
        )

    def summary_timezone_recorded(context):
        summaries = [
            observation
            for observation in context.observations.observations
            if observation.type == "projection_result" and observation.name == "daily_entry_summary"
        ]
        if not summaries:
            return True
        return summaries[-1].payload.get("timezone") == "America/Sao_Paulo"

    def summary_version_recorded(context):
        summaries = [
            observation
            for observation in context.observations.observations
            if observation.type == "projection_result" and observation.name == "daily_entry_summary"
        ]
        if not summaries:
            return True
        return summaries[-1].payload.get("calculation_version") == SUMMARY_CALCULATION_VERSION

    def renewal_opens_new_period(context):
        if "EntitlementExpired" not in simulation.state.facts:
            return True
        if simulation.state.expired:
            return True
        return simulation.state.period_start == end and not simulation.state.expired

    def expired_interval_remains_closed(context):
        if "EntitlementExpired" not in simulation.state.facts:
            return True
        if simulation.state.period_start != end:
            return True
        return simulation.state.facts.count("EntitlementGranted") >= 2

    def replay_matches_live_state(context):
        replayed = WaymarkSimulation.replay(simulation.state.events)
        return (
            replayed.state.entries == simulation.state.entries
            and replayed.state.payment_failed == simulation.state.payment_failed
            and replayed.state.expired == simulation.state.expired
            and replayed.state.period_start == simulation.state.period_start
            and replayed.state.period_end == simulation.state.period_end
            and replayed.state.subscription_id == simulation.state.subscription_id
            and replayed.state.payer_id == simulation.state.payer_id
            and replayed.state.cancelled == simulation.state.cancelled
            and replayed.state.cancellation_at == simulation.state.cancellation_at
            and replayed.state.processed_payment_ids == simulation.state.processed_payment_ids
        )

    def log_timestamps_are_distinct(context):
        logs = [entry for entry in simulation.state.entries if entry.kind == "log_entry"]
        if not logs:
            return True
        return any(
            log.happened_at == START + timedelta(days=1) and log.recorded_at > log.happened_at
            for log in logs
        )

    def entry_ids_are_unique(context):
        ids = [entry.entry_id for entry in simulation.state.entries]
        return len(ids) == len(set(ids))

    def private_workspace_is_owner_only(context):
        unauthorized_at = START + timedelta(hours=1, minutes=3)
        if context.clock.now() < unauthorized_at:
            return True
        return any(
            observation.type == "command_rejected"
            and observation.payload.get("reason") == "unauthorized_user"
            for observation in context.observations.observations
        )

    def account_bootstrap_is_unique(context):
        if context.clock.now() < START + timedelta(minutes=1, seconds=30):
            return True
        return simulation.state.facts.count("AccountCreated") == 1 and any(
            observation.name == "duplicate_account_creation_ignored"
            for observation in context.observations.observations
        )

    def payer_identity_is_explicit(context):
        return simulation.state.payer_id == simulation.state.user_id

    def pre_entitlement_is_restricted(context):
        if context.clock.now() < START + timedelta(minutes=1, seconds=5):
            return True
        return any(
            observation.type == "access_decision"
            and observation.payload.get("reason") == "no_entitlement"
            and observation.payload.get("allowed") is False
            for observation in context.observations.observations
        )

    def subscription_request_is_unique(context):
        duplicate_at = START + timedelta(minutes=1, seconds=50)
        if context.clock.now() < duplicate_at:
            return True
        return simulation.state.facts.count("SubscriptionRequested") == 1 and any(
            observation.name == "duplicate_subscription_request_ignored"
            for observation in context.observations.observations
        )

    def subscription_ownership_is_explicit(context):
        requests = [event for event in simulation.state.events if event.name == "SubscriptionRequested"]
        if not requests:
            return True
        payload = requests[0].payload
        return payload.get("user_id") == simulation.state.user_id and payload.get("payer_id") == simulation.state.payer_id

    def cancellation_request_is_unique(context):
        duplicate_at = START + timedelta(days=4, seconds=10)
        if context.clock.now() < duplicate_at:
            return True
        return simulation.state.facts.count("CancellationScheduled") == 1 and any(
            observation.name == "duplicate_cancellation_ignored"
            for observation in context.observations.observations
        )

    def expiry_job_is_unique(context):
        duplicate_at = START + timedelta(days=7, seconds=10)
        if context.clock.now() < duplicate_at:
            return True
        if simulation.state.period_start != START:
            return True
        return not simulation.state.access_allowed(context.clock.now()) and simulation.state.facts.count("EntitlementExpired") == 1 and any(
            observation.name == "duplicate_expiry_ignored"
            for observation in context.observations.observations
        )

    def duplicate_failure_is_observed(context):
        duplicate_at = START + timedelta(days=2, seconds=30)
        if context.clock.now() < duplicate_at:
            return True
        return any(
            observation.name == "duplicate_payment_failure_ignored"
            for observation in context.observations.observations
        )

    def duplicate_success_is_observed(context):
        duplicate_at = START + timedelta(minutes=2, seconds=10)
        if context.clock.now() < duplicate_at:
            return True
        return any(observation.name == "duplicate_payment_success_ignored" for observation in context.observations.observations)

    return Scenario(
        name="waymark.subscription_backed_workspace",
        seed=20260901,
        initial_time=START,
        run_id="waymark-first-slice",
        actors=[Actor("subscriber")],
        scheduled_actions=[
            action(timedelta(minutes=1), "create_account", create),
            action(timedelta(minutes=1, seconds=5), "pre_entitlement_access", pre_entitlement_access),
            action(timedelta(minutes=1, seconds=30), "duplicate_create_account", duplicate_create),
            action(timedelta(minutes=1, seconds=45), "request_subscription", subscribe),
            action(timedelta(minutes=1, seconds=50), "duplicate_subscription", subscribe),
            action(timedelta(minutes=2), "activate_period", activate),
            action(timedelta(minutes=2, seconds=10), "duplicate_payment_success", duplicate_success),
            action(timedelta(hours=1), "record_note", note),
            action(timedelta(hours=1, minutes=1), "record_retried_note", retried_note),
            action(timedelta(hours=1, minutes=2), "repeat_retried_note", retried_note),
            action(timedelta(hours=1, minutes=3), "unauthorized_note", unauthorized_note),
            action(timedelta(days=2), "payment_failure", fail),
            action(timedelta(days=2, seconds=30), "duplicate_payment_failure", duplicate_fail),
            action(timedelta(days=2, minutes=1), "restricted_write", restricted_write),
            action(timedelta(days=2, minutes=2), "operator_inspection", inspect),
            action(timedelta(days=2, minutes=3), "operator_restore", operator_restore),
            action(timedelta(days=2, minutes=3, seconds=10), "duplicate_operator_restore", duplicate_operator_restore),
            action(timedelta(days=3), "payment_recovery", recover),
            action(timedelta(days=3, minutes=1), "record_log", log),
            action(timedelta(days=3, minutes=2), "daily_summary", summary),
            action(timedelta(days=4), "schedule_cancellation", cancel),
            action(timedelta(days=4, seconds=10), "duplicate_cancellation", duplicate_cancel),
            action(timedelta(days=7), "period_expiry", expire),
            action(timedelta(days=7, seconds=10), "duplicate_period_expiry", duplicate_expire),
            action(timedelta(days=8), "renew_after_expiry", renew),
            action(timedelta(days=8, minutes=1), "record_post_renewal_log", post_renewal_log),
        ],
        invariants=[
            Invariant("durable_entries_survive_payment_failure", invariant),
            Invariant("cancellation_respects_paid_boundary", cancellation_boundary),
            Invariant("operator_intervention_is_audited", intervention_audited),
            Invariant("operator_restore_is_unique", operator_restore_is_unique),
            Invariant("operator_inspection_is_complete", operator_inspection_is_complete),
            Invariant("summary_timezone_is_recorded", summary_timezone_recorded),
            Invariant("summary_version_is_recorded", summary_version_recorded),
            Invariant("renewal_opens_new_period", renewal_opens_new_period),
            Invariant("expired_interval_remains_closed", expired_interval_remains_closed),
            Invariant("event_replay_matches_live_state", replay_matches_live_state),
            Invariant("duplicate_failure_is_observed", duplicate_failure_is_observed),
            Invariant("duplicate_success_is_observed", duplicate_success_is_observed),
            Invariant("log_timestamps_are_distinct", log_timestamps_are_distinct),
            Invariant("entry_ids_are_unique", entry_ids_are_unique),
            Invariant("private_workspace_is_owner_only", private_workspace_is_owner_only),
            Invariant("account_bootstrap_is_unique", account_bootstrap_is_unique),
            Invariant("payer_identity_is_explicit", payer_identity_is_explicit),
            Invariant("pre_entitlement_is_restricted", pre_entitlement_is_restricted),
            Invariant("subscription_request_is_unique", subscription_request_is_unique),
            Invariant("subscription_ownership_is_explicit", subscription_ownership_is_explicit),
            Invariant("cancellation_request_is_unique", cancellation_request_is_unique),
            Invariant("expiry_job_is_unique", expiry_job_is_unique),
        ],
        observatory_nodes=[
            ObservatoryNode("subscriber", "Subscriber", "actor", "actors", realm="waymark", domain="Workspace", status="active"),
            ObservatoryNode("payment_provider", "Payment Provider", "external_provider", "external_providers", realm="waymark", domain="Billing"),
            ObservatoryNode("account_bootstrap", "Account Bootstrap", "use_case", "use_cases", realm="waymark", domain="Workspace"),
            ObservatoryNode("subscription_lifecycle", "Subscription Lifecycle", "use_case", "use_cases", realm="waymark", domain="Billing"),
            ObservatoryNode("payment_processing", "Payment Processing", "use_case", "use_cases", realm="waymark", domain="Billing"),
            ObservatoryNode("access_control", "Access Control", "use_case", "use_cases", realm="waymark", domain="Access"),
            ObservatoryNode("recording", "Recording", "use_case", "use_cases", realm="waymark", domain="Recording"),
            ObservatoryNode("insights", "Daily Insights", "use_case", "use_cases", realm="waymark", domain="Insights"),
            ObservatoryNode("operations", "Operator Operations", "use_case", "use_cases", realm="waymark", domain="Operations"),
            ObservatoryNode("fact_history", "Append-only Fact History", "event_store", "domain_model", realm="waymark", domain="Shared"),
            ObservatoryNode("entitlement", "Entitlement Projection", "projection", "projections", realm="waymark", domain="Access"),
            ObservatoryNode("summary", "Summary Projection", "projection", "projections", realm="waymark", domain="Insights"),
        ],
        observatory_edges=[
            ObservatoryEdge("subscriber", "account_bootstrap", "creates account", kind="route"),
            ObservatoryEdge("account_bootstrap", "fact_history", "records account facts", kind="route"),
            ObservatoryEdge("subscriber", "subscription_lifecycle", "requests subscription", kind="route"),
            ObservatoryEdge("subscription_lifecycle", "fact_history", "records subscription facts", kind="route"),
            ObservatoryEdge("payment_provider", "payment_processing", "delivers payment outcome", kind="route"),
            ObservatoryEdge("payment_processing", "entitlement", "grants or suspends access", kind="route"),
            ObservatoryEdge("payment_processing", "fact_history", "records payment facts", kind="route"),
            ObservatoryEdge("entitlement", "access_control", "answers access decision", kind="route"),
            ObservatoryEdge("access_control", "recording", "permits or rejects writes", kind="route"),
            ObservatoryEdge("subscriber", "recording", "records note or log", kind="route"),
            ObservatoryEdge("recording", "fact_history", "records entry fact", kind="route"),
            ObservatoryEdge("fact_history", "summary", "feeds daily projection", kind="route"),
            ObservatoryEdge("subscriber", "insights", "requests summary", kind="route"),
            ObservatoryEdge("insights", "summary", "calculates daily counts", kind="route"),
            ObservatoryEdge("operations", "access_control", "inspects access", kind="route"),
            ObservatoryEdge("operations", "entitlement", "restores entitlement", kind="route"),
            ObservatoryEdge("entitlement", "fact_history", "records lifecycle fact", kind="route"),
        ],
    )
