from __future__ import annotations

from typing import Callable

from .models import ActionOutcome, ActionRequest, Decision, Tier
from .policy_engine import PolicyEngine
from .rollback_ledger import RollbackLedger
from .trust_score import TrustScoreTracker


class ActionProxy:
    def __init__(self, policy_engine: PolicyEngine, ledger: RollbackLedger, trust: TrustScoreTracker):
        self.policy_engine = policy_engine
        self.ledger = ledger
        self.trust = trust
        self._executors: dict[tuple[str, str], Callable[[ActionRequest], str]] = {}

    def register_executor(self, tool: str, action: str, fn: Callable[[ActionRequest], str]):
        self._executors[(tool, action)] = fn

    def route(self, request: ActionRequest, approved_by_human: bool = False) -> ActionOutcome:
        rule = self.policy_engine.get_rule(request.agent_id, request.tool, request.action)

        if rule is None:
            self.trust.record_decision(request.agent_id, Decision.BLOCKED)
            return ActionOutcome(
                request=request, decision=Decision.BLOCKED, tier_used=Tier.OBSERVE,
                reason="no policy on file, default-deny",
            )

        if rule.tier == Tier.OBSERVE:
            self.trust.record_decision(request.agent_id, Decision.BLOCKED)
            return ActionOutcome(
                request=request, decision=Decision.BLOCKED, tier_used=Tier.OBSERVE,
                reason="tier 0, observe only",
            )

        if rule.tier == Tier.SUGGEST and not approved_by_human:
            self.trust.record_decision(request.agent_id, Decision.PENDING_APPROVAL)
            return ActionOutcome(
                request=request, decision=Decision.PENDING_APPROVAL, tier_used=Tier.SUGGEST,
                reason="needs human approval first",
            )

        if rule.tier == Tier.GUARDED:
            ok, reason = self.policy_engine.check_limits(rule, request.params)
            if not ok:
                if rule.escalate_above_limit:
                    self.trust.record_decision(request.agent_id, Decision.PENDING_APPROVAL)
                    return ActionOutcome(
                        request=request, decision=Decision.PENDING_APPROVAL, tier_used=Tier.SUGGEST,
                        reason=f"over limit ({reason}), escalated",
                    )
                self.trust.record_decision(request.agent_id, Decision.BLOCKED)
                return ActionOutcome(
                    request=request, decision=Decision.BLOCKED, tier_used=Tier.GUARDED,
                    reason=f"blocked: {reason}",
                )

        return self._execute(request, rule.tier)

    def _execute(self, request: ActionRequest, tier: Tier) -> ActionOutcome:
        executor = self._executors.get((request.tool, request.action))
        result = executor(request) if executor else "(no executor registered, simulated)"

        ledger_id = self.ledger.record(request)
        self.trust.record_decision(request.agent_id, Decision.ALLOWED)

        return ActionOutcome(
            request=request, decision=Decision.ALLOWED, tier_used=tier,
            reason=f"executed: {result}", ledger_id=ledger_id,
        )
