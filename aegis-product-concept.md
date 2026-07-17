# Aegis — The Control Plane for Agentic Action
### A 0→1 AI Infra product concept, built for Director-level PM interviews

---

## 0. The One-Line Pitch

**Aegis is the permissions, policy, and rollback layer that sits between AI agents and the real systems they act on — so enterprises can let agents *do* things, not just *say* things.**

Think: IAM (Okta) + a circuit breaker + git revert, purpose-built for autonomous agents instead of humans.

---

## 1. The Insight (why this, why now, why you)

Every "agentic AI" pitch in 2025–2026 has converged on the same story: agents are now good enough to *plan* and *use tools*. The bottleneck has quietly moved. It's no longer "can the agent figure out what to do" — it's **"will any serious organization let an agent do it unsupervised."**

Three things are true simultaneously right now:

1. **Capability has outpaced trust.** Agents can already write and merge code, issue refunds, rewrite pricing, modify infra configs, and email customers. Capability is not the blocker anymore.
2. **Existing infra solves the wrong layer.** Observability/eval tools (LangSmith, Braintrust, Arize, Langfuse) tell you *what the agent did after the fact*. They don't constrain *what it's allowed to do in the moment*, and they don't give you an undo button.
3. **Every enterprise is independently rebuilding the same governance layer badly.** Ask any AI infra lead at a bank, a healthcare company, or a mid-size SaaS company how they let agents touch production, and you get a duct-taped combination of: hardcoded allowlists, a human-in-the-loop Slack approval bot, and hope.

This is a **MECE gap**: the market has observability (past), eval (quality), and orchestration (how agents chain tools) well covered. Nobody owns **runtime governance** (present-tense control) as a standalone infra category. That's the wedge.

This is a Director-level pitch, not a feature pitch, because the insight isn't "add a permission check to an agent framework" — it's **"agent adoption in the enterprise is bottlenecked by an organizational trust problem, and trust problems get solved with infrastructure, not better models."** That's the kind of reframe that signals product leadership in an interview.

---

## 2. Market Landscape (MECE breakdown of the agentic AI infra stack)

| Layer | What it does | Who owns it today | Gap |
|---|---|---|---|
| **Model layer** | Reasoning, generation | Anthropic, OpenAI, Google | — |
| **Orchestration layer** | Chaining tool calls, multi-agent coordination | LangGraph, CrewAI, AutoGen, Anthropic's Agent SDK | Mature, commoditizing fast |
| **Observability layer** | Logging, tracing, debugging agent runs | LangSmith, Langfuse, Arize | Mature, converging on "eval" |
| **Evaluation layer** | Scoring output quality, regression testing | Braintrust, Weights & Biases | Mature |
| **Data/RAG layer** | Retrieval, memory, context management | Pinecone, Weaviate, Mem0 | Mature |
| **🔲 Governance/Action layer** | Real-time permissioning, blast-radius limits, rollback, audit for *actions* an agent takes on live systems | **Nobody at infra-grade.** Homegrown Slack-bots and hardcoded allowlists. | **This is Aegis.** |

The pattern: every existing category answers "did the agent do a good job?" Aegis answers **"was the agent allowed to do that, and can we undo it if not?"** — a categorically different question, asked at a different moment (before/during the action, not after).

---

## 3. Who Buys, Who Uses (customer segmentation — MECE)

**Buyer:** VP/Head of Engineering, CISO, or Head of AI Platform at a mid-to-large enterprise (500+ eng org) that has moved at least one agent past the pilot stage into a workflow touching production systems (code, money, customer data, infra).

**Three user personas, cleanly separated by job:**

1. **The Platform/Infra Engineer** — installs Aegis as a proxy layer in front of the agent's tool calls. Wants: low-latency policy enforcement, SDK that doesn't fight their existing orchestration framework (LangGraph, Anthropic SDK, custom).
2. **The Risk/Compliance Owner** (CISO, Head of Risk, sometimes legal) — defines policy: what an agent can touch, at what autonomy tier, with what approval requirements. Wants: an auditable, human-readable policy language and a paper trail regulators/auditors will accept.
3. **The Agent Builder (PM/Eng building the actual agent product)** — wants a "staged autonomy" ladder so they can ship an agent at low trust (suggest-only) and *earn* higher autonomy (auto-execute) over time without re-architecting, based on the agent's track record.

**Why this segmentation matters:** most agent-infra pitches conflate "the person who builds the agent" with "the person who has to sign off on the agent touching production." They are almost never the same person past ~200 employees. Aegis is designed around that org reality — which is itself the Director-level differentiator over an engineer-level pitch.

---

## 4. Product: What Aegis Actually Is

### Core mental model: **Autonomy Tiers**
Every agent action is classified into one of four tiers before it executes:

- **Tier 0 — Observe only.** Agent can read, cannot act. (Default for any new agent/tool combo.)
- **Tier 1 — Suggest.** Agent proposes an action; a human approves via an inline approval (Slack, email, dashboard) before it runs.
- **Tier 2 — Act with guardrails.** Agent executes autonomously within a bounded policy (e.g., "issue refunds up to $200," "merge PRs to non-prod branches," "send emails only to internal domains").
- **Tier 3 — Full autonomy with rollback armed.** Agent acts freely within scope, but every action is versioned and reversible within a defined window; anomalous patterns auto-downgrade the agent back to Tier 1.

### Four core components (this is the architecture, MECE against the problem):

1. **Policy Engine** — a declarative policy language (think: "Terraform for agent permissions") where risk/compliance owners define scope, spend limits, blast radius, and required approvals per tool/agent/environment. Versioned, diffable, auditable like code.
2. **Action Proxy (runtime enforcement)** — every tool call the agent makes is intercepted here before it hits the real API. Enforces the policy in real time, sub-50ms overhead target. This is the technical moat: it has to be a transparent proxy that works with *any* orchestration framework, not a rebuild of one.
3. **Rollback & Undo Ledger** — every state-changing action is captured with enough metadata to reverse it (compensating transaction, git revert, API-level undo where the underlying system supports it; otherwise a documented manual-remediation path). This is what makes Tier 3 autonomy something a CISO will actually sign off on.
4. **Trust Score & Autonomy Promotion** — tracks an agent's real-world track record (approval rate, rollback frequency, anomaly rate) and automates *promotion* up the autonomy ladder (Tier 1 → 2 → 3) or automatic *demotion* the moment behavior drifts. This turns "granting an agent more autonomy" from a one-time leap-of-faith decision into a continuous, evidence-based process — which is the actual unlock for enterprise adoption.

### What Aegis deliberately does NOT do (scope discipline — important to state explicitly in an interview):
- Does not evaluate output *quality* (that's Braintrust/eval's job — Aegis integrates with eval scores as an input to the Trust Score, doesn't replace evals).
- Does not orchestrate the agent's reasoning/tool-chaining (that's LangGraph/Agent SDK's job — Aegis sits *underneath* as the enforcement layer, agnostic to orchestration framework).
- Does not build agents. Aegis is infra other people's agents run on top of.

Stating what you *won't* build is one of the highest-signal things a Director-level candidate can do in a product interview — it shows discipline over scope-creep and a real point of view on the stack.

---

## 5. MVP (0→1 scope)

**Design partner profile:** a company with 1–3 agents already in production touching a *reversible, bounded-blast-radius* system — e.g., an internal dev-tools agent that opens/merges PRs, or a support agent that issues refunds/credits. Avoid anything irreversible (don't launch in a domain like "agent that sends legally binding contracts") — you want a design partner where mistakes are cheap to prove the model before tackling higher-stakes domains.

**MVP feature set (deliberately narrow):**
- Policy Engine: YAML/declarative policy definition for a single tool integration (start with GitHub or a generic REST API webhook).
- Action Proxy: enforce Tier 0–2 only (skip full autonomous rollback complexity in v1).
- Basic audit log + Slack-based Tier 1 approval flow.
- Manual (not automated) trust scoring — a dashboard showing approval/override rates, without the auto-promotion logic yet.

**Explicitly deferred to post-MVP:** Tier 3 autonomous rollback (hardest engineering problem — compensating transactions per integration), auto-promotion logic (needs real trust-score data to build responsibly), multi-agent policy conflicts.

**Why this scope:** it proves the wedge (policy + real-time enforcement) without betting the MVP on the hardest, most integration-heavy piece (universal rollback), and it's honest about sequencing — a Director-level answer defends *why* something is cut, not just what's cut.

---

## 6. Metrics

**North Star:** % of agent actions executed at Tier 2+ (autonomous, guardrailed) without human review, *held at a stable or improving override/rollback rate.* This single metric captures the actual value prop — moving enterprises from "agent needs a human to babysit every action" to "agent acts autonomously and safely" — without rewarding autonomy at the expense of safety.

**Guardrail metrics (things that must NOT degrade as North Star improves):**
- Rollback rate (actions that had to be reversed) — should trend down as trust scoring matures, not up.
- Time-to-detect anomalous agent behavior (target: seconds, not the next day's log review).
- False-positive block rate (policy engine wrongly blocking a legitimate action) — high friction here kills adoption fast.

**Business metrics:** design partners → paid pilots → land-and-expand (tools integrated per customer, agents onboarded per customer) → net revenue retention as the expansion signal (this is a classic infra land-and-expand motion, similar to how Okta expanded from SSO to full identity governance).

---

## 7. GTM & Business Model

**Wedge:** land with platform/infra teams who already feel the pain acutely (they're the ones building the janky Slack-bot approval flow today) — sell the "stop hand-rolling this" pitch, not an abstract "AI safety" pitch.

**Pricing model:** usage-based on agent actions governed (like a WAF/API gateway pricing model — pay per request processed through the proxy), with an enterprise tier for advanced policy/compliance features (SSO, SOC2 audit exports, custom rollback integrations). This aligns price with value (more autonomous agent activity = more value delivered = more revenue) rather than seat-based pricing, which doesn't fit an agent-first buyer.

**Category creation risk:** the biggest GTM risk is that "agent governance" isn't a budget line yet at most companies — it gets bundled into either security budget or platform-eng budget. Mitigation: position early enterprise deals as extensions of existing security/API-gateway spend (competing conceptually with a Kong/Okta-adjacent budget line) rather than pitching a brand-new category that has no home in anyone's budget.

---

## 8. Competitive Positioning & Moat

**Nearest adjacent competitors and why they don't already own this:**
- **LangSmith/Langfuse/Arize** — built observability-first; adding real-time enforcement is a different latency/reliability bar (has to be in the hot path, not just logging) and a different buyer (risk/compliance, not just ML eng).
- **Okta/identity platforms** — understand permissions deeply but model *humans*, not agent trust scores that evolve based on behavior; would need to rebuild the runtime proxy and rollback ledger from scratch.
- **API gateways (Kong, Apigee)** — have the proxy/enforcement pattern already, but no concept of agent-specific policy (autonomy tiers, trust scoring) or rollback semantics.

**The moat, honestly assessed:** in year one, there isn't a deep moat — this is a reasonable build for a well-resourced competitor or even an in-house team at a big AI lab. The real moat is **data network effects on the Trust Score**: the more agent-action outcomes Aegis observes across customers (anonymized/aggregated), the better its anomaly detection and default policy templates get for *every* customer — a classic "gets better with usage" flywheel, similar to how fraud-detection infra compounds. This should be stated as a *thesis to validate*, not a guaranteed moat — that intellectual honesty is itself a signal of seniority in an interview.

---

## 9. Risks (MECE: technical, market, safety/ethical)

**Technical risks:**
- Rollback is genuinely hard for irreversible actions (sent emails, executed trades) — mitigation is scoping v1 to reversible domains and being explicit that full rollback coverage is a multi-year integration effort, not a v1 promise.
- Latency in the hot path — every agent action now has a network hop through Aegis; needs aggressive caching of policy decisions and a documented latency SLA.

**Market risks:**
- Budget-line ambiguity (see GTM section above).
- Orchestration frameworks (LangGraph, Anthropic's own Agent SDK) could absorb basic policy/permissioning as a built-in feature, commoditizing the simplest version of this. Mitigation/response: compete on the compliance-grade audit trail, cross-framework neutrality, and trust-score intelligence — the parts a framework vendor is less incentivized to build deeply (frameworks want you locked into their ecosystem; Aegis's value is being framework-agnostic).

**Safety/ethical risks:**
- A governance product that's too permissive gives false confidence ("we have Aegis, we're covered") while an agent still causes harm — the product's actual credibility depends on conservative defaults (new agent/tool pairs start at Tier 0) and honest false-negative reporting, not on making customers feel safe.
- Aggregated trust-score data across customers raises its own data-sharing/privacy question that needs an explicit opt-in model, not implicit pooling.

---

## 10. Roadmap Shape (0→1→10→100)

- **0→1:** Single-tool policy + Tier 0–2 enforcement + manual trust dashboard. Prove the wedge with 3–5 design partners in a reversible-action domain (dev tools, support ops).
- **1→10:** Multi-tool/multi-agent policy support, Tier 3 rollback for the top 3–5 most common integrations (GitHub, Salesforce, Stripe/payments, internal REST APIs, Slack/email), automated trust-score-based promotion.
- **10→100:** Become the default compliance layer — SOC2/HIPAA/SOX-ready audit exports, industry-specific policy templates (financial services, healthcare), and the trust-score data flywheel maturing into predictive risk scoring (flagging an agent as likely to misbehave *before* it does, based on cross-customer patterns).

---

## 11. How to Tell This Story in the Interview

**Opening framing (use almost verbatim as your hook):**
"Every agentic AI product I've seen recently answers 'can the agent do the task.' Almost none of them answer 'will the org actually let it.' I think that gap — not model capability — is the real bottleneck to enterprise agent adoption right now, and nobody's building infrastructure for it at the category level. That's the product I'd build."

**Likely interviewer follow-ups, and how to handle them:**

- *"Isn't this just an eval platform?"* — No: eval asks "was the output good," this asks "was the agent allowed to do this, and can we undo it." Different question, different moment (before/during the action vs. after), different buyer (risk/compliance vs. ML eng).
- *"Why wouldn't [LangSmith/Anthropic/OpenAI] just build this?"* — They might build a basic version. Answer honestly (see moat section) — the durable differentiation is framework-neutrality and the compliance/audit posture a model vendor is structurally less credible selling (a model vendor grading its own agent's trustworthiness is a weaker pitch to a CISO than a neutral third party).
- *"What's your MVP, and what would you cut?"* — Walk through Section 5 exactly, and lead with what you *cut* (Tier 3 rollback, auto-promotion) and why — sequencing discipline is what separates a Director answer from an IC answer.
- *"How do you know this is a real problem and not something you're inventing?"* — Point to the pattern: any platform/infra engineer who's touched an internal agent-approval-Slack-bot has lived this. Frame it as "I'd validate this with 10 design partner conversations before writing a line of code" — shows you're not skipping discovery even though you have conviction.
- *"What metric would tell you this is failing?"* — Rollback rate climbing while Tier 2/3 usage grows — that means you're granting autonomy faster than trust is actually earned. Naming a metric that indicates *failure*, not just success, is a strong signal.

**If asked to defend why this over a "friendlier" consumer AI idea:** be direct that you chose AI Infra deliberately because Director-level infra bets require reasoning about organizational trust, budget ownership, and multi-stakeholder buying — not just user delight — and that's the muscle you want to demonstrate.

---

## 12. One paragraph you could say cold, no notes

"I'd build the control plane that lets enterprises actually trust agents to act, not just talk. Right now every company adopting agentic AI is hand-rolling the same governance layer — permissions, blast-radius limits, an undo button — usually badly, usually with a Slack bot. I'd build that as infrastructure: a policy engine risk teams can define like Terraform, a real-time proxy that enforces it on every agent action regardless of what orchestration framework built the agent, and a rollback ledger so autonomy isn't a one-way door. The MVP is narrow on purpose — one tool, three autonomy tiers, manual trust tracking — because the hardest part, universal rollback, deserves real integration work, not a v1 promise. The bet is that the bottleneck to agent adoption stopped being capability a while ago and became trust, and trust gets solved with infrastructure."
