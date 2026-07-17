"""
Aegis prototype demo.

Simulates three agents hitting the Action Proxy under a real policy file,
showing: default-deny, guardrailed autonomy with a limit breach escalating
to human approval, a blocked (Tier 0) action, and a full execute -> rollback
cycle.

Run: python demo.py
"""

from aegis import ActionProxy, ActionRequest, PolicyEngine, RollbackLedger, TrustScoreTracker


def mock_issue_refund(request: ActionRequest) -> str:
    return f"refunded ${request.params.get('amount_usd')} to {request.params.get('customer_id')}"


def mock_revert_refund(request: ActionRequest) -> str:
    return f"reversed refund of ${request.params.get('amount_usd')} to {request.params.get('customer_id')}"


def mock_open_pr(request: ActionRequest) -> str:
    return f"opened PR #{request.params.get('pr_number', 42)} on {request.params.get('repo')}"


def mock_revert_open_pr(request: ActionRequest) -> str:
    return f"closed PR #{request.params.get('pr_number', 42)} on {request.params.get('repo')}"


def print_outcome(label: str, outcome):
    print(f"\n--- {label} ---")
    print(f"  agent:    {outcome.request.agent_id}")
    print(f"  action:   {outcome.request.tool}.{outcome.request.action}({outcome.request.params})")
    print(f"  decision: {outcome.decision.value}  (tier {outcome.tier_used.value})")
    print(f"  reason:   {outcome.reason}")
    if outcome.ledger_id:
        print(f"  ledger:   {outcome.ledger_id}")


def main():
    engine = PolicyEngine.from_yaml("policy.yaml")
    ledger = RollbackLedger()
    trust = TrustScoreTracker()
    proxy = ActionProxy(engine, ledger, trust)

    proxy.register_executor("refunds", "issue_refund", mock_issue_refund)
    ledger.register_revert_fn("refunds", "issue_refund", mock_revert_refund)

    proxy.register_executor("github", "open_pr", mock_open_pr)
    ledger.register_revert_fn("github", "open_pr", mock_revert_open_pr)

    print("=" * 70)
    print("AEGIS DEMO -- routing agent actions through policy + proxy")
    print("=" * 70)

    # 1. Tier 2 (guarded), within limit -> executes automatically
    o1 = proxy.route(ActionRequest(
        agent_id="support-agent-v1", tool="refunds", action="issue_refund",
        params={"amount_usd": 75, "customer_id": "cust_881"},
    ))
    print_outcome("Refund within limit (auto-executes)", o1)

    # 2. Tier 2, OVER limit, escalate_above_limit=True -> pending human approval
    o2 = proxy.route(ActionRequest(
        agent_id="support-agent-v1", tool="refunds", action="issue_refund",
        params={"amount_usd": 500, "customer_id": "cust_902"},
    ))
    print_outcome("Refund over limit (escalates to human)", o2)

    # 3. Tier 0 -- no policy trusts this at all -> blocked by default-deny
    o3 = proxy.route(ActionRequest(
        agent_id="finance-agent-v1", tool="payments", action="wire_transfer",
        params={"amount_usd": 10000},
    ))
    print_outcome("Wire transfer (Tier 0, default-deny)", o3)

    # 4. Tier 1 -- requires approval, not yet approved
    o4 = proxy.route(ActionRequest(
        agent_id="devtools-agent-v1", tool="github", action="merge_pr",
        params={"repo": "core-api", "pr_number": 118},
    ))
    print_outcome("Merge PR without approval (Tier 1, pending)", o4)

    # 5. Same request, now approved by a human -> executes
    o5 = proxy.route(ActionRequest(
        agent_id="devtools-agent-v1", tool="github", action="merge_pr",
        params={"repo": "core-api", "pr_number": 118},
    ), approved_by_human=True)
    print_outcome("Merge PR with approval granted", o5)

    # 6. Tier 3 -- fully autonomous, executes immediately, rollback armed
    o6 = proxy.route(ActionRequest(
        agent_id="devtools-agent-v1", tool="github", action="open_pr",
        params={"repo": "core-api", "pr_number": 119},
    ))
    print_outcome("Open PR (Tier 3, autonomous)", o6)

    # Now demonstrate rollback on that Tier 3 action
    print("\n--- Rolling back the Tier 3 action ---")
    result = ledger.revert(o6.ledger_id)
    print(f"  {result}")

    # Trust score + promotion recommendation after this session
    print("\n--- Trust scores after this session ---")
    for agent_id in ["support-agent-v1", "devtools-agent-v1", "finance-agent-v1"]:
        rec = trust._get(agent_id)
        print(f"  {agent_id}: score={rec.score}  "
              f"(approvals={rec.approvals}, rejections={rec.rejections}, "
              f"autonomous={rec.autonomous_successes}, rollbacks={rec.rollbacks})")

    print("\n--- Ledger history ---")
    for entry in ledger.history():
        status = "REVERTED" if entry.reverted else "active"
        print(f"  [{entry.ledger_id}] {entry.request.tool}.{entry.request.action} -- {status}")


if __name__ == "__main__":
    main()
