# Wealth Intelligence Agent App — Build Spec

## 0. What this document is

A build spec for an agent-based wealth management intelligence app. The RM
stays in control at every step — agents surface insight and draft
recommendations; nothing reaches a client without RM review. Feed this file
to an AI coding assistant as project context before starting implementation.

**Core design principle:** separate compute from reasoning.

- **Deterministic layer** (plain code): every number an RM could be held
  accountable for — drift %, LTV, concentration, tax lots, cash runway — is
  computed here, not by an LLM.
- **Reasoning layer** (LLM agents): takes those computed facts as tool
  outputs and turns them into narrative, prioritization, and
  recommendations, always citing the computed fact it used.

Never let an agent compute financial numbers from raw rows in its own
reasoning. Agents call tools; tools return numbers; agents narrate and
prioritize.

---

## 1. Source data

| File | Contents | Grain |
|---|---|---|
| `clients.csv` | 20 clients: age, life stage, source of wealth, risk profile, tax domicile, stated objectives | 1 row / client |
| `portfolios.csv` | 24 portfolios (some clients have >1) | 1 row / portfolio |
| `holdings.csv` | Every position at 5 snapshots, 1,015 rows | 1 row / portfolio / instrument / snapshot date |
| `instruments.csv` | Instrument reference data, price history, structured product look-through references | 1 row / instrument |
| `mandates.csv` | Allocation bands and concentration limits per portfolio | 1 row / portfolio (or per band) |
| `transactions.csv` | Trades, income, fees, capital calls, credit drawdowns | 1 row / transaction |
| `credit_facilities.csv` | Lombard and term loans secured against portfolios, with LTV history | 1 row / facility / snapshot |
| `commitments.csv` | Money committed to private funds, not yet called | 1 row / commitment |
| `planned_cash_needs.csv` | What clients need money for, and when | 1 row / cash need |
| `market_context.csv` | Gold, Brent, yields, FX, equity indices, volatility at the 5 snapshot dates | 1 row / date |
| `event_log.csv` | 2026 world events and the channel through which each reached portfolios | 1 row / event |
| `rm_notes.json` | RM's own notes — informal, subjective, unstructured | free text, keyed by client |

### 1.1 Two traps to solve before anything else

1. **Multi-portfolio clients.** Risk profile and objectives live on the
   client; allocation bands live per-portfolio. A client can be
   conservative on one portfolio and aggressive on a satellite portfolio
   for a specific goal. **Model the entity graph as
   `client → portfolios → holdings`. Never flatten straight to
   `client → holdings`** — that silently merges mandates and produces
   false drift/concentration alerts.

2. **Structured product look-through.** `instruments.csv` records what a
   structured product actually references. A client holding an
   autocallable on an equity index has real look-through exposure to that
   index and its volatility — not just one line item. Concentration and
   mandate checks that only see the wrapper will understate risk.
   **Resolve look-through exposure before computing any concentration or
   band metric.**

---

## 2. Entity model (target shape, not a literal schema)

```
Client
  ├─ id, age, life_stage, source_of_wealth, risk_profile, tax_domicile, objectives[]
  ├─ Portfolios[]
  │    ├─ id, mandate (bands, concentration limits)
  │    ├─ Holdings[] (per snapshot date)
  │    │    └─ instrument_id, quantity, market_value, look_through_exposure[]
  │    ├─ Transactions[]
  │    └─ CreditFacilities[] (LTV history)
  ├─ Commitments[] (uncalled capital)
  ├─ PlannedCashNeeds[] (amount, purpose, due_date)
  └─ RMNotes[] (free text, timestamped)

Instrument
  ├─ id, type, price_history[]
  └─ look_through_references[] (for structured products)

MarketContext (by date)
  └─ gold, brent, yields, fx, equity_indices, volatility

EventLog
  └─ event, date, channel, affected_instruments/sectors
```

Build this as a proper data layer (DuckDB, SQLite, or an in-memory pandas
model behind a repository interface) — not ad hoc joins scattered across
agent code. Every tool function below reads from this layer.

---

## 3. Deterministic analytics layer

Implement as pure functions / tools with fixed, typed signatures. These
are the only things allowed to touch raw rows and produce numbers.

| Function | Inputs | Returns |
|---|---|---|
| `compute_drift(portfolio_id, date)` | holdings, mandate | allocation vs. band per asset class, breach flags |
| `compute_concentration(portfolio_id, date)` | holdings (look-through resolved), instruments | single-name / sector / issuer exposure vs. limits |
| `resolve_look_through(instrument_id)` | instruments | underlying exposure breakdown for structured products |
| `compute_ltv(client_id, date)` | credit_facilities, holdings | current LTV vs. covenant threshold, trend |
| `compute_liquidity_runway(client_id)` | commitments, planned_cash_needs, holdings, credit_facilities | months of covered cash needs, next shortfall date |
| `compute_tax_lots(portfolio_id)` | transactions, holdings, client tax_domicile | unrealized gain/loss by lot, harvestable losses, wash-sale-type conflicts |
| `compute_trend(client_id, metric, date_range)` | holdings across snapshots | direction/magnitude of change over the 5 snapshots |
| `match_events_to_holdings(event_id)` | event_log, holdings, instruments, market_context | affected holdings, channel, estimated impact |
| `get_rm_notes(client_id)` | rm_notes.json | structured extraction: caveats, preferences, concerns |

**Every deterministic function must return values with enough metadata to
cite**: which rows, which date, which threshold — so an agent's narrative
can always say "why" without re-deriving it.

---

## 4. Agent roster

Each agent is an LLM reasoning loop that calls the deterministic tools
above and the client-context tools, then produces a structured
recommendation object (see §6). No agent does its own arithmetic on raw
data.

### 4.1 Context Assembler (not client-facing — used by every other agent)
Pulls `clients.csv` fields + mandate + `get_rm_notes` for a given client.
Every specialist agent queries this first to get constraints before
proposing anything. RM notes act as a **standing override layer** — if a
note says a client is uncomfortable with leverage even though their stated
risk profile is "aggressive," downstream recommendations must reflect the
note, not just the numeric profile.

### 4.2 Rebalancing Agent
Inputs: `compute_drift`, `compute_concentration`, mandate, context.
Output: proposed trades to bring the portfolio back within bands, with
reasoning that cites the specific breach (e.g. "EM equity is 34% vs. a
20–28% band — trim to 25%"). Never invents a number.

### 4.3 Tax-Aware Optimisation Agent
Inputs: `compute_tax_lots`, client tax_domicile, transaction history.
Output: harvestable losses, conflicts with any pending rebalancing trade
(wash-sale-type issues), domicile-specific treatment notes.

### 4.4 Life-Event Planning Agent
Inputs: client life_stage + objectives, `planned_cash_needs`,
`commitments`, `credit_facilities`.
Covers: retirement, business sale, philanthropy, education, succession.
Output: is the portfolio positioned for the stated objective; if not, what
changes. Philanthropy/succession lean more heavily on RM notes since
intent is rarely fully captured in structured fields — flag when notes are
the primary evidence for a recommendation.

### 4.5 Liquidity & Credit Risk Agent
Inputs: `compute_ltv` trend, `market_context`, `compute_liquidity_runway`.
Output: margin-call early warning (LTV approaching covenant), and
reconciliation of uncalled commitments against available cash — flags
where multiple capital calls could land alongside a planned cash need.

### 4.6 Market & Event-Impact Agent
Inputs: `match_events_to_holdings`, `market_context`.
Output: system-wide "why did this portfolio move" narratives, traceable to
a specific event + channel, not speculative commentary.

### 4.7 RM Notes Agent
Inputs: `rm_notes.json`.
Output: structured caveats/preferences per client, tagged with the client
id and a confidence/recency note. Feeds the Context Assembler. Treat as a
modifier other agents must check — never let it be silently overridden by
the numbers.

---

## 5. Orchestration

### 5.1 Per-client orchestrator
- Calls the relevant specialist agents for one client.
- **Surfaces conflicts explicitly** rather than silently picking a winner
  — e.g. tax agent says "hold to avoid short-term gains," rebalancing
  agent says "trim now, mandate breach." The RM sees both with the
  tradeoff stated.
- Passes every recommendation through a **compliance/suitability gate**
  before it reaches the RM view (check against mandate + any documented
  suitability rule before display).
- Emits one structured client brief (see §6).

### 5.2 Book-level prioritization agent
- Runs the per-client orchestrator across all clients.
- Scores each client by urgency: mandate breach severity, LTV proximity
  to covenant, days to next cash shortfall, unaddressed life event, etc.
- Produces the ranked "who to call first" queue for the RM.

---

## 6. Recommendation output contract

Every agent and the orchestrator must emit this shape (adapt field names
to your language/framework, but keep the concept intact):

```json
{
  "client_id": "string",
  "portfolio_id": "string | null",
  "agent": "rebalancing | tax | life_event | liquidity | market | orchestrator",
  "priority": "high | medium | low",
  "confidence_tier": "fact | rule | model",
  "headline": "one sentence, plain language",
  "evidence": [
    { "source_function": "compute_drift", "detail": "EM equity 34% vs 20-28% band", "as_of_date": "YYYY-MM-DD" }
  ],
  "recommendation": "what to do",
  "talking_point": "client-ready phrasing the RM can use verbatim",
  "conflicts_with": ["other recommendation ids, if any"],
  "compliance_status": "pass | needs_review | blocked",
  "rm_note_influence": "string | null"
}
```

`confidence_tier` matters: a `fact` came straight from a deterministic
function, a `rule` came from a documented business rule, a `model` came
from LLM inference over ambiguous inputs (e.g. inferring intent from RM
notes). Surface this in the UI so RMs learn how much to lean on each type.

---

## 7. Build order (phases)

**Phase 1 — Data layer + deterministic analytics (no LLM)**
- Load all 12 files into the entity model described in §2.
- Implement every function in §3. Unit test each against the real data —
  drift, LTV, concentration, tax lots, and liquidity runway must be
  correct for all clients across all 5 snapshots before moving on.
- Explicitly test the two traps in §1.1: a multi-portfolio client and a
  client holding a structured product.

**Phase 2 — One agent, end to end**
- Build the Rebalancing Agent only, wired to real tool outputs, for one
  client. Get the evidence-citing output format (§6) right before
  replicating the pattern.

**Phase 3 — Remaining specialist agents**
- Tax, Life-Event, Liquidity & Credit, Market & Event-Impact, RM Notes.
- Each follows the same tool-calling → structured-output pattern from
  Phase 2.

**Phase 4 — Per-client orchestrator**
- Conflict surfacing + compliance gate + single client brief output.

**Phase 5 — Book-level prioritization**
- Run across all 20 clients, produce the ranked queue.

**Phase 6 — RM-facing UI**
- Narrative brief → why (evidence) → suggested action → talking point,
  per client, plus the prioritized book view.
- Every insight must be one click away from its evidence trail (§6).

---

## 8. Non-negotiables

- No agent performs financial arithmetic itself — always via the
  deterministic tools in §3.
- No recommendation ships without at least one `evidence` entry.
- No client-facing output bypasses the compliance gate.
- RM notes (`rm_notes.json`) can soften or block a numeric recommendation;
  a numeric recommendation cannot silently override a documented RM note.
- Every recommendation is traceable to source rows and a date — no
  black-box outputs.
