from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Optional


class Tier(int, Enum):
    OBSERVE = 0     # read only
    SUGGEST = 1     # needs human approval
    GUARDED = 2     # auto within limits
    AUTONOMOUS = 3  # auto + reversible


class Decision(str, Enum):
    ALLOWED = "allowed"
    BLOCKED = "blocked"
    PENDING_APPROVAL = "pending_approval"


@dataclass
class ActionRequest:
    agent_id: str
    tool: str
    action: str
    params: dict[str, Any] = field(default_factory=dict)
    requested_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class ActionOutcome:
    request: ActionRequest
    decision: Decision
    tier_used: Tier
    reason: str
    ledger_id: Optional[str] = None  # only set if executed + revertible


@dataclass
class LedgerEntry:
    ledger_id: str
    request: ActionRequest
    executed_at: datetime
    revert_fn_name: str
    reverted: bool = False
    reverted_at: Optional[datetime] = None
