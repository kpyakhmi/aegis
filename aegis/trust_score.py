from __future__ import annotations

from dataclasses import dataclass

from .models import Decision, Tier


@dataclass
class AgentTrustRecord:
    agent_id: str
    approvals: int = 0
    rejections: int = 0
    rollbacks: int = 0
    autonomous_successes: int = 0

    @property
    def total_actions(self) -> int:
        return self.approvals + self.rejections + self.autonomous_successes

    @property
    def score(self) -> float:
        if self.total_actions == 0:
            return 0.0
        good = self.approvals + self.autonomous_successes
        raw = good / self.total_actions
        rollback_penalty = min(0.5, self.rollbacks * 0.1)
        return max(0.0, round(raw - rollback_penalty, 3))


class TrustScoreTracker:
    # NOTE: only recommends promotion/demotion, doesn't auto-apply it.
    # wiring that up needs real prod data first, not comfortable automating
    # it off a handful of toy examples.

    def __init__(self):
        self._records: dict[str, AgentTrustRecord] = {}

    def _get(self, agent_id: str) -> AgentTrustRecord:
        return self._records.setdefault(agent_id, AgentTrustRecord(agent_id))

    def record_decision(self, agent_id: str, decision: Decision):
        rec = self._get(agent_id)
        if decision == Decision.ALLOWED:
            rec.autonomous_successes += 1
        elif decision == Decision.BLOCKED:
            rec.rejections += 1
        elif decision == Decision.PENDING_APPROVAL:
            rec.approvals += 1

    def record_rollback(self, agent_id: str):
        self._get(agent_id).rollbacks += 1

    def promotion_recommendation(self, agent_id: str, current_tier: Tier) -> str:
        rec = self._get(agent_id)
        if rec.total_actions < 10:
            return f"not enough data ({rec.total_actions} actions), hold at tier {current_tier.value}"
        if rec.score >= 0.9 and current_tier.value < Tier.AUTONOMOUS.value:
            return f"promote to tier {current_tier.value + 1} (score={rec.score})"
        if rec.score < 0.6 and current_tier.value > Tier.OBSERVE.value:
            return f"demote to tier {current_tier.value - 1} (score={rec.score})"
        return f"hold at tier {current_tier.value} (score={rec.score})"
