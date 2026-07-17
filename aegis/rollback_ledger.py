from __future__ import annotations

import uuid
from datetime import datetime
from typing import Callable

from .models import ActionRequest, LedgerEntry


class RollbackLedger:
    def __init__(self):
        self._entries: dict[str, LedgerEntry] = {}
        self._revert_fns: dict[tuple[str, str], Callable[[ActionRequest], str]] = {}

    def register_revert_fn(self, tool: str, action: str, fn: Callable[[ActionRequest], str]):
        self._revert_fns[(tool, action)] = fn

    def record(self, request: ActionRequest) -> str:
        ledger_id = str(uuid.uuid4())[:8]
        revert_fn = self._revert_fns.get((request.tool, request.action))
        entry = LedgerEntry(
            ledger_id=ledger_id,
            request=request,
            executed_at=datetime.utcnow(),
            revert_fn_name=revert_fn.__name__ if revert_fn else "NO_REVERT_REGISTERED",
        )
        self._entries[ledger_id] = entry
        return ledger_id

    def revert(self, ledger_id: str) -> str:
        entry = self._entries.get(ledger_id)
        if entry is None:
            return f"error: no ledger entry {ledger_id}"
        if entry.reverted:
            return f"error: {ledger_id} already reverted"

        fn = self._revert_fns.get((entry.request.tool, entry.request.action))
        if fn is None:
            return f"error: no revert fn for {entry.request.tool}.{entry.request.action}"

        result = fn(entry.request)
        entry.reverted = True
        entry.reverted_at = datetime.utcnow()
        return result

    def history(self) -> list[LedgerEntry]:
        return sorted(self._entries.values(), key=lambda e: e.executed_at)
