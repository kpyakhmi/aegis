# Aegis — Control Plane for Agentic Action (prototype)

Enterprises adopting AI agents have already solved "can the agent do the
task." What's unsolved is **"will the org actually let it act on real
systems, unsupervised."** Every company doing this today hand-rolls the
same governance layer — a hardcoded allowlist, a Slack-bot approval flow —
usually badly. Aegis is that layer, built as infrastructure instead.

This repo is a **working prototype**, not production infra. It exists to
prove out the core mechanics concretely — not just describe them in a doc.
The full product strategy (market analysis, GTM, metrics, roadmap) is in
[`aegis-product-concept.md`](./aegis-product-concept.md).

## What it does

Every action an agent wants to take is routed through an **Action Proxy**,
which checks a declarative **Policy** (`policy.yaml`) and enforces one of
four autonomy tiers:

| Tier | Name | Behavior |
|---|---|---|
| 0 | Observe | Agent can read, cannot act |
| 1 | Suggest | Requires human approval before executing |
| 2 | Guarded | Executes autonomously within bounded limits (e.g. `$` cap) |
| 3 | Autonomous | Executes freely; every action is logged to the **Rollback Ledger** and reversible |

Unknown `(agent, tool, action)` combinations are **default-deny** — they
fall back to Tier 0 automatically. No policy on file means no trust.

A **Trust Score Tracker** watches each agent's real approval/rejection/
rollback history and produces an explainable promotion/demotion
recommendation — autonomy is earned continuously, not granted once.

## Project structure

```
aegis/
  models.py          # core data types (ActionRequest, Tier, Decision, LedgerEntry)
  policy_engine.py    # loads policy.yaml, evaluates rules + limits
  action_proxy.py     # runtime enforcement -- the hot-path component
  rollback_ledger.py  # records executed actions + reverses them
  trust_score.py       # tracks agent track record, recommends tier changes
policy.yaml            # sample declarative policy (what a risk owner would author)
demo.py                # end-to-end simulation of 3 agents across all 4 tiers
tests/test_policy_engine.py
```

## Run it

```bash
pip install -r requirements.txt
python demo.py          # end-to-end walkthrough with printed decisions
python tests/test_policy_engine.py   # or: pytest tests/
```

## What's deliberately NOT here (and why)

This prototype scopes down hard on purpose — matching the MVP scoping
decisions in the product doc:

- **No real integrations.** `mock_issue_refund`, `mock_open_pr`, etc. stand
  in for real Stripe/GitHub calls. The hard, honest engineering work in a
  real build is per-integration compensating-transaction logic for
  rollback — that's flagged as a real cost here, not hand-waved.
- **No automated tier promotion.** `TrustScoreTracker` only *recommends* —
  it doesn't rewrite `policy.yaml`. Automating that responsibly needs real
  production data first.
- **No latency/concurrency handling.** A production Action Proxy sits in
  the hot path and needs to be fast and safe under concurrent requests;
  this prototype is single-threaded and synchronous by design, to keep
  the core policy logic legible.

## Why this exists

Built as a portfolio piece for product leadership interviews in AI
infrastructure — the goal is to show the *reasoning*, not just the pitch:
default-deny as a safety posture, tier escalation on limit breaches,
reversibility as a first-class citizen, and an explainable (not black-box)
trust score. Happy to walk through any design decision here in more depth.
