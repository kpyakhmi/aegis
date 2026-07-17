from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional

import yaml

from .models import Tier


@dataclass
class PolicyRule:
    agent_id: str
    tool: str
    action: str
    tier: Tier
    limits: dict[str, Any]
    escalate_above_limit: bool = False


class PolicyEngine:
    def __init__(self, rules: list[PolicyRule]):
        self._rules = {(r.agent_id, r.tool, r.action): r for r in rules}

    @classmethod
    def from_yaml(cls, path: str | Path) -> "PolicyEngine":
        raw = yaml.safe_load(Path(path).read_text())
        rules = [
            PolicyRule(
                agent_id=p["agent_id"],
                tool=p["tool"],
                action=p["action"],
                tier=Tier(p["tier"]),
                limits=p.get("limits", {}) or {},
                escalate_above_limit=p.get("escalate_above_limit", False),
            )
            for p in raw["policies"]
        ]
        return cls(rules)

    def get_rule(self, agent_id: str, tool: str, action: str) -> Optional[PolicyRule]:
        # no rule = no trust. unknown combos fall back to tier 0.
        return self._rules.get((agent_id, tool, action))

    def check_limits(self, rule: PolicyRule, params: dict[str, Any]) -> tuple[bool, str]:
        if "max_amount_usd" in rule.limits:
            amount = params.get("amount_usd", 0)
            if amount > rule.limits["max_amount_usd"]:
                return False, f"amount ${amount} exceeds limit ${rule.limits['max_amount_usd']}"
        if "allowed_domains" in rule.limits:
            recipient = params.get("recipient_domain", "")
            if recipient not in rule.limits["allowed_domains"]:
                return False, f"domain '{recipient}' not allowed"
        return True, "ok"
