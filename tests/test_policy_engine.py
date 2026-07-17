"""
Minimal tests -- proves the default-deny and limit-checking behavior,
the two properties that actually matter for this to be trustworthy infra.
Run with: pytest tests/
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from aegis import ActionProxy, ActionRequest, Decision, PolicyEngine, RollbackLedger, TrustScoreTracker

POLICY_PATH = Path(__file__).resolve().parents[1] / "policy.yaml"


def make_proxy():
    engine = PolicyEngine.from_yaml(POLICY_PATH)
    ledger = RollbackLedger()
    trust = TrustScoreTracker()
    return ActionProxy(engine, ledger, trust), ledger, trust


def test_default_deny_for_unknown_action():
    proxy, _, _ = make_proxy()
    outcome = proxy.route(ActionRequest(
        agent_id="rogue-agent", tool="payments", action="wire_transfer", params={},
    ))
    assert outcome.decision == Decision.BLOCKED


def test_tier2_within_limit_executes():
    proxy, _, _ = make_proxy()
    outcome = proxy.route(ActionRequest(
        agent_id="support-agent-v1", tool="refunds", action="issue_refund",
        params={"amount_usd": 50, "customer_id": "c1"},
    ))
    assert outcome.decision == Decision.ALLOWED
    assert outcome.ledger_id is not None


def test_tier2_over_limit_escalates():
    proxy, _, _ = make_proxy()
    outcome = proxy.route(ActionRequest(
        agent_id="support-agent-v1", tool="refunds", action="issue_refund",
        params={"amount_usd": 999, "customer_id": "c1"},
    ))
    assert outcome.decision == Decision.PENDING_APPROVAL


def test_tier1_requires_approval():
    proxy, _, _ = make_proxy()
    unapproved = proxy.route(ActionRequest(
        agent_id="devtools-agent-v1", tool="github", action="merge_pr", params={},
    ))
    assert unapproved.decision == Decision.PENDING_APPROVAL

    approved = proxy.route(ActionRequest(
        agent_id="devtools-agent-v1", tool="github", action="merge_pr", params={},
    ), approved_by_human=True)
    assert approved.decision == Decision.ALLOWED


def test_rollback_reverses_action():
    proxy, ledger, _ = make_proxy()

    def open_pr(req):
        return "opened"

    def revert_pr(req):
        return "closed"

    proxy.register_executor("github", "open_pr", open_pr)
    ledger.register_revert_fn("github", "open_pr", revert_pr)

    outcome = proxy.route(ActionRequest(
        agent_id="devtools-agent-v1", tool="github", action="open_pr", params={},
    ))
    assert outcome.decision == Decision.ALLOWED

    result = ledger.revert(outcome.ledger_id)
    assert "closed" in result

    entries = ledger.history()
    assert entries[-1].reverted is True


if __name__ == "__main__":
    test_default_deny_for_unknown_action()
    test_tier2_within_limit_executes()
    test_tier2_over_limit_escalates()
    test_tier1_requires_approval()
    test_rollback_reverses_action()
    print("all tests passed")
