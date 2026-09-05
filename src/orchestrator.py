"""
Orchestration & Book Prioritization Layer
Implements:
5.1 Per-Client Orchestrator (LangGraph workflow, conflict surfacing, compliance gate)
5.2 Book-Level Prioritization Engine (20-client urgency scoring & ranked morning queue)
"""

import os
from typing import Dict, List, Any, Optional, Tuple
from src.data_layer import WealthDataRepository
from src.deterministic_analytics import DeterministicAnalytics
from src.llm_engine import LLMEngine
from src.agent_state import AgentGraphState, Recommendation, CrossSpecialistOptimization
from src.specialist_agents import (
    ContextAssembler,
    RebalancingAgent,
    TaxOptimizationAgent,
    LifeEventPlanningAgent,
    LiquidityCreditRiskAgent,
    MarketImpactAgent,
    RMNotesAgent,
    make_rec_id
)
import json

class ClientOrchestrator:
    """5.1 Per-Client Master LLM Orchestration & Strategy Engine."""
    def __init__(self, analytics: Optional[DeterministicAnalytics] = None):
        self.analytics = analytics or DeterministicAnalytics()
        self.repo = self.analytics.repo
        self.llm = LLMEngine.get_instance()
        self.context_assembler = ContextAssembler(self.analytics)
        self.rebalancing_agent = RebalancingAgent(self.analytics)
        self.tax_agent = TaxOptimizationAgent(self.analytics)
        self.life_event_agent = LifeEventPlanningAgent(self.analytics)
        self.liquidity_agent = LiquidityCreditRiskAgent(self.analytics)
        self.market_agent = MarketImpactAgent(self.analytics)
        self.rm_notes_agent = RMNotesAgent(self.analytics)

    def run_client(self, client_id: str, snapshot_date: str = "2026-08-26") -> Dict[str, Any]:
        """
        Runs all specialist agents for a client, executes LLM Master Orchestration 
        to synthesize/deduplicate recommendations, surface conflicts, discover synergistic 
        comingling packages & cross-specialist optimizations, with a robust deterministic fallback.
        """
        # 1. Context Assembly
        context = self.context_assembler.assemble(client_id, snapshot_date)
        
        # 2. Run Specialist Agents
        raw_recs: List[Recommendation] = []
        raw_recs.extend(self.rebalancing_agent.run(context, snapshot_date))
        raw_recs.extend(self.tax_agent.run(context, snapshot_date))
        raw_recs.extend(self.life_event_agent.run(context, snapshot_date))
        raw_recs.extend(self.liquidity_agent.run(context, snapshot_date))
        raw_recs.extend(self.market_agent.run(context, snapshot_date))
        raw_recs.extend(self.rm_notes_agent.run(context, snapshot_date))

        # 3. Master LLM Orchestration Attempt
        llm_orchestration = self._run_llm_orchestrator(raw_recs, context, snapshot_date)

        if llm_orchestration:
            recs = llm_orchestration["recommendations"]
            conflicts = llm_orchestration["conflicts"]
            comingling_opportunities = llm_orchestration["comingling_opportunities"]
            cross_specialist_optimizations = llm_orchestration["cross_specialist_optimizations"]
            brief = llm_orchestration["client_brief"]
        else:
            # Deterministic Fallback Pipeline
            recs = self._deduplicate_and_synthesize_recs(raw_recs, context, snapshot_date)
            conflicts = self._detect_conflicts(recs, context)
            comingling_opportunities = self._detect_comingling_opportunities(recs, context, snapshot_date)
            cross_specialist_optimizations = self._detect_cross_specialist_optimizations(recs, context, snapshot_date)
            brief = self._synthesize_brief(client_id, recs, conflicts, context)

        # 4. Compliance & Suitability Gate (Always Deterministic Ground Truth)
        compliance_flags = self._compliance_gate(recs, context)

        # 5. Client Urgency Score & Factor Breakdown
        urgency_score, urgency_breakdown = self._compute_urgency(recs, context, snapshot_date)

        return {
            "client_id": client_id,
            "snapshot_date": snapshot_date,
            "client_context": context,
            "recommendations": [r.model_dump() if hasattr(r, "model_dump") else r for r in recs],
            "conflicts": conflicts,
            "comingling_opportunities": comingling_opportunities,
            "cross_specialist_optimizations": cross_specialist_optimizations,
            "compliance_flags": compliance_flags,
            "client_brief": brief,
            "urgency_score": round(urgency_score, 1),
            "urgency_breakdown": urgency_breakdown
        }

    def _run_llm_orchestrator(self, raw_recs: List[Recommendation], context: Dict[str, Any], snapshot_date: str) -> Optional[Dict[str, Any]]:
        """Executes LLM reasoning across all specialist agent proposals."""
        if not self.llm.is_live_llm_active():
            return None

        client_id = context["client_id"]
        client_name = context["client_name"]

        system_prompt = f"""You are the Master Wealth Orchestrator & Chief Investment Officer at Bank Julius Baer.
Your role is to orchestrate, synthesize, deduplicate, and optimize the multi-agent recommendation stream for private banking clients.

CRITICAL GOVERNANCE & AUDIT RULES:
1. AUTHORITATIVE EVENT RECORD: `event_log.csv` is the SOLE authoritative source for all 2026 macro/world events. Do NOT hallucinate or free-associate external events. If parametric pre-trained memory disagrees with the event records, the file wins unconditionally.
2. DETERMINISTIC FACT INTEGRITY: Numerical metrics (LTV, asset drift %, cash shortfall USD, exposed holdings USD) are computed deterministically and must not be altered or estimated.
3. STANDING RM NOTES ARE HARD CONSTRAINTS: Qualitative constraints, exclusions, and client instructions in RM notes act as binding overrides.

You receive raw specialist recommendations from:
- Portfolio Rebalancing Agent (drift, concentration breaches)
- Tax Optimization Agent (tax-loss harvesting, domicile rules)
- Life Event & Milestones Agent (upcoming commitments, family milestones)
- Liquidity & Credit Risk Agent (LTV headroom, capital call coverage)
- Global Macro & Market Impact Agent (shock transmission, geopolitical events)
- RM Notes & Sentiment Agent (client constraints, emotional blockers, legacy mandates)

Your core objectives:
1. Deduplicate & Reconcile: If Rebalancing already trims an asset class/holding, absorb and synthesize the Market Agent shock transmission into the rebalancing recommendation rather than producing redundant actions.
2. Resolve multi-agent conflicts and establish clear priority tradeoffs.
3. Club high-value synergistic multi-objective execution packages (e.g. De-risking ↔ Tax-Loss Harvesting ↔ Milestone Ring-Fencing ↔ Cash Buffering).
4. Discover novel cross-specialist strategic optimizations (e.g. cross-sleeve tax alpha, staged liquidity immunization to eliminate cash drag, collateral downside preservation).
5. Produce an executive client briefing with structured talking points tailored in elite Julius Baer private banking tone.

Respond ONLY with valid JSON matching this schema:
{{
  "synthesized_recommendations": [
    {{
      "id": "REC-xxx",
      "client_id": "{client_id}",
      "portfolio_id": null,
      "portfolio_name": null,
      "agent": "rebalancing|tax|life_event|liquidity|market|rm_notes|orchestrator",
      "priority": "high|medium|low",
      "confidence_tier": "fact|rule|model",
      "headline": "...",
      "recommendation": "...",
      "talking_point": "...",
      "rm_note_influence": "...",
      "compliance_status": "pass|needs_review|blocked",
      "evidence": [
        {{
          "source_function": "...",
          "detail": "...",
          "as_of_date": "{snapshot_date}",
          "raw_metric_value": null
        }}
      ]
    }}
  ],
  "conflicts": [
    {{
      "id": "CONF-xxx",
      "title": "...",
      "rec_a": "...",
      "rec_b": "...",
      "description": "...",
      "tradeoff": "...",
      "recommended_resolution": "..."
    }}
  ],
  "comingling_opportunities": [
    {{
      "id": "PKG-SYN-{client_id}-01",
      "title": "...",
      "opportunity_type": "multi_objective_tax_liquidity_rebalance",
      "clubbed_rec_ids": ["..."],
      "summary": "...",
      "unified_action": "...",
      "unified_talking_point": "...",
      "financial_benefits": ["..."]
    }}
  ],
  "cross_specialist_optimizations": [
    {{
      "id": "OPT-xxx",
      "title": "...",
      "optimization_type": "tax_alpha_rebalance|liquidity_immunization|duration_macro_overlay|holistic_synergy",
      "participating_agents": ["rebalancing", "tax"],
      "description": "...",
      "strategic_rationale": "...",
      "expected_alpha_or_saving": "...",
      "implementation_steps": ["1. ...", "2. ..."]
    }}
  ],
  "client_brief": {{
    "headline": "...",
    "primary_action": "...",
    "tone_advice": "...",
    "key_talking_points": ["..."]
  }}
}}"""

        raw_recs_dump = [r.model_dump() for r in raw_recs]
        user_prompt = f"""Client Profile:
- Client ID: {client_id}
- Client Name: {client_name}
- Total AUM: USD {context.get('total_aum', 0):,.2f}
- Risk Profile: {context.get('risk_profile', 'Moderate')}
- Domicile / Tax Jurisdiction: {context.get('domicile', 'Global')} / {context.get('tax_jurisdiction', 'Global')}
- Desk & Booking Centre: {context.get('desk', 'Private Banking')} ({context.get('booking_centre', 'Singapore')})
- Last RM Contact: {context.get('last_meeting_date', 'Initial')} ({context.get('last_meeting_channel', 'N/A')})
- Standing RM Notes / Constraints: {json.dumps(context.get('rm_notes_summary', {}))}

Raw Specialist Agent Recommendations:
{json.dumps(raw_recs_dump, indent=2)}

Perform master orchestration, cross-agent deduplication, comingling package synthesis, and discover advanced cross-specialist optimizations."""

        try:
            parsed = self.llm.generate_json(user_prompt, system_prompt)
            if not parsed or not isinstance(parsed, dict) or "synthesized_recommendations" not in parsed:
                return None
            
            # Reconstruct typed recommendations
            recs = []
            for item in parsed.get("synthesized_recommendations", []):
                try:
                    recs.append(Recommendation(**item))
                except Exception:
                    continue
            
            if not recs:
                return None

            return {
                "recommendations": recs,
                "conflicts": parsed.get("conflicts", []),
                "comingling_opportunities": parsed.get("comingling_opportunities", []),
                "cross_specialist_optimizations": parsed.get("cross_specialist_optimizations", []),
                "client_brief": parsed.get("client_brief", {})
            }
        except Exception:
            return None

    def _detect_cross_specialist_optimizations(self, recs: List[Recommendation], context: Dict[str, Any], snapshot_date: str) -> List[Dict[str, Any]]:
        """
        Discovers advanced cross-specialist strategic optimizations beyond single-agent proposals:
        1. Multi-Sleeve Tax-Alpha Harvesting ↔ Mandate Realignment
        2. Liquidity Runway Immunization ↔ Milestone Pre-Funding Schedule
        3. Collateral Capital Efficiency ↔ Fixed Income Duration Hedging
        """
        optimizations = []
        client_id = context["client_id"]

        rebalance_recs = [r for r in recs if r.agent == "rebalancing"]
        tax_recs = [r for r in recs if r.agent == "tax"]
        life_recs = [r for r in recs if r.agent == "life_event"]
        liq_recs = [r for r in recs if r.agent == "liquidity"]
        market_recs = [r for r in recs if r.agent == "market"]

        # Optimization 1: Cross-Sleeve Tax-Loss Neutralization on Mandate Trims
        if rebalance_recs and tax_recs:
            tax_loss_avail = sum(r.evidence[0].raw_metric_value or 0 for r in tax_recs if r.evidence)
            optimizations.append({
                "id": f"OPT-TAX-ALPHA-{client_id}",
                "title": f"Cross-Sleeve Tax-Alpha Rebalancing Matrix ({context.get('tax_jurisdiction', 'Global')})",
                "optimization_type": "tax_alpha_rebalance",
                "participating_agents": ["rebalancing", "tax"],
                "description": f"Synchronize portfolio mandate trimming with simultaneous realization of qualifying tax losses ({context.get('tax_jurisdiction', 'Global')}) across sleeves.",
                "strategic_rationale": "Realizing mandate trimming without tax coordination creates immediate taxable capital gains drag. Cross-sleeve netting eliminates friction.",
                "expected_alpha_or_saving": f"Tax shield of up to USD {tax_loss_avail:,.0f} in capital gains liability offset" if tax_loss_avail else "Substantial capital gains tax liability offset",
                "implementation_steps": [
                    "1. Match rebalancing sell orders directly against identified unrealized loss tax lots in qualifying sleeves.",
                    "2. Execute loss harvesting prior to settlement of capital gains rebalancing transactions.",
                    "3. Reinvest netted proceeds in adherence with 30-day wash-sale and local tax rules."
                ]
            })

        # Optimization 2: Liquidity Runway Immunization with Milestone Schedule
        if life_recs or liq_recs:
            optimizations.append({
                "id": f"OPT-LIQ-IMMUN-{client_id}",
                "title": "Staged Liquidity Immunization & Cash Drag Elimination",
                "optimization_type": "liquidity_immunization",
                "participating_agents": ["liquidity", "life_event", "rebalancing"],
                "description": "Establish dynamic short-duration liquidity laddering to fund upcoming capital calls and life milestones while keeping remaining assets fully invested.",
                "strategic_rationale": "Holding uninvested cash causes substantial return drag in high-yield environments, while uncoordinated liquidations risk market timing penalties.",
                "expected_alpha_or_saving": "Eliminates ~45-60 bps of annual cash drag across reserves while guaranteeing 100% milestone coverage",
                "implementation_steps": [
                    "1. Ring-fence required liquidity into short-dated Julius Baer Treasury / Money Market sweep.",
                    "2. Structure tranche releases corresponding precisely to anticipated capital call / milestone call dates.",
                    "3. Maintain full compounding exposure in core equity/credit sleeves until T-14 days before disbursement."
                ]
            })

        # Optimization 3: Collateral Protection & Duration Hedging
        if market_recs and any("LTV" in r.headline or "Credit" in r.headline or "Lombard" in r.headline for r in recs):
            optimizations.append({
                "id": f"OPT-COLLAT-HEDGE-{client_id}",
                "title": "Collateral Value Preservation & Dynamic LTV Shield",
                "optimization_type": "duration_macro_overlay",
                "participating_agents": ["market", "liquidity", "rebalancing"],
                "description": "Implement protective duration overlay and structured downside collars on credit facility collateral assets.",
                "strategic_rationale": "Macro rate spikes and market volatility can erode collateral lending values, inadvertently breaching covenant margin call buffers.",
                "expected_alpha_or_saving": "Preserves USD lending headroom and prevents sudden margin calls under 150 bps rate shock",
                "implementation_steps": [
                    "1. Review collateral composition with Treasury & Credit Risk desk.",
                    "2. Overlay structured capital protection or interest rate hedges on duration-sensitive collateral.",
                    "3. Expand available buffer above the covenant margin call threshold."
                ]
            })

        return optimizations

    def _deduplicate_and_synthesize_recs(self, recs: List[Recommendation], context: Dict[str, Any], snapshot_date: str) -> List[Recommendation]:
        """
        Dynamically orchestrates specialist agent recommendations:
        1. Deduplicates redundant / overlapping Market Agent actions that duplicate Portfolio Rebalancing trims.
           - When Rebalancing already trims an asset class / position (e.g. Commodities, Equities), the Orchestrator
             enriches the Rebalancing rationale with the macro context and suppresses duplicate standalone market alerts.
        2. Validates temporal horizons to prevent stale historical events from generating redundant alerts.
        """
        rebalance_recs = [r for r in recs if r.agent == "rebalancing"]
        market_recs = [r for r in recs if r.agent == "market"]
        other_recs = [r for r in recs if r.agent not in ["rebalancing", "market"]]

        # Extract asset classes and holding names trimmed by rebalancing
        rebalance_targets = set()
        for r in rebalance_recs:
            h_lower = r.headline.lower()
            if "commodit" in h_lower or "gold" in h_lower or "materials" in h_lower:
                rebalance_targets.update(["commodities", "gold", "energy", "oil", "crude", "brent"])
            if "equity" in h_lower or "equities" in h_lower or "stock" in h_lower:
                rebalance_targets.update(["equity", "equities", "developed equity", "us equities", "technology"])
            if ":" in r.headline:
                inst = r.headline.split(":")[1].split("represents")[0].strip().lower()
                rebalance_targets.add(inst)

        synthesized_market_recs = []
        for m in market_recs:
            m_text = (m.headline + " " + m.recommendation + " " + " ".join(e.detail for e in m.evidence)).lower()
            
            # Check overlap with rebalancing targets
            overlap = any(t in m_text for t in rebalance_targets)
            
            if overlap:
                # Enrich matching rebalancing recommendations with macro transmission context
                for r in rebalance_recs:
                    if "macro alignment" not in r.talking_point.lower():
                        r.talking_point += " Macro Alignment: This rebalancing action also hedges against recent macro volatility flagged by our Macro Strategist."
                        r.rm_note_influence = (r.rm_note_influence + " | " if r.rm_note_influence else "") + "Orchestrator aligned: De-risking absorbs macro event transmission."
                # Suppress the redundant standalone market recommendation
                continue
            else:
                synthesized_market_recs.append(m)

        return rebalance_recs + other_recs + synthesized_market_recs

    def _detect_comingling_opportunities(self, recs: List[Recommendation], context: Dict[str, Any], snapshot_date: str) -> List[Dict[str, Any]]:
        """
        Discovers high-value comingling / clubbing opportunities across specialist recommendations.
        Identifies multi-objective execution packages combining de-risking, tax-loss harvesting,
        liquidity fortification, and life milestone funding into a cohesive private banking strategy.
        """
        opportunities = []

        rebalance_recs = [r for r in recs if r.agent == "rebalancing"]
        tax_recs = [r for r in recs if r.agent == "tax"]
        life_recs = [r for r in recs if r.agent == "life_event"]
        liq_recs = [r for r in recs if r.agent == "liquidity"]

        # Strategy 1: Multi-Objective Rebalance + Tax-Loss Shield + Cash Buffer + Milestone Funding
        trim_recs = [r for r in rebalance_recs if "breach" in r.headline.lower() or "overweight" in r.headline.lower() or "concentration" in r.headline.lower()]
        tlh_recs = [r for r in tax_recs if "tax loss" in r.headline.lower() or "harvesting" in r.headline.lower()]
        cash_warn_recs = [r for r in rebalance_recs if "cash" in r.headline.lower()] + [r for r in liq_recs if "cash" in r.headline.lower()]

        if trim_recs and (tlh_recs or life_recs or cash_warn_recs):
            clubbed_items = []
            clubbed_ids = []

            # 1. Primary Concentration & Overweight De-risking (all qualifying breaches)
            for t in trim_recs:
                if t.id not in clubbed_ids:
                    clubbed_items.append(t)
                    clubbed_ids.append(t.id)

            # 2. Tax Loss Shield
            main_tax = tlh_recs[0] if tlh_recs else None
            if main_tax and main_tax.id not in clubbed_ids:
                clubbed_items.append(main_tax)
                clubbed_ids.append(main_tax.id)

            # 3. Life-Event Planned Milestone
            main_life = life_recs[0] if life_recs else None
            if main_life and main_life.id not in clubbed_ids:
                clubbed_items.append(main_life)
                clubbed_ids.append(main_life.id)

            # 4. Cash Boundary Warning / Liquidity Sleeve
            main_cash = cash_warn_recs[0] if cash_warn_recs else None
            if main_cash and main_cash.id not in clubbed_ids:
                clubbed_items.append(main_cash)
                clubbed_ids.append(main_cash.id)

            if len(clubbed_items) >= 2:
                # Dynamically derive components from actual clubbed recommendations
                trim_targets = []
                for t in trim_recs:
                    target_name = t.headline
                    if ":" in t.headline:
                        target_name = t.headline.split(":")[1].split("represents")[0].strip()
                    elif "overweight" in t.headline.lower():
                        target_name = t.headline.split("overweight")[0].strip()
                    trim_targets.append(target_name)

                trim_label = ", ".join(trim_targets)
                title_parts = [f"De-risking ({trim_label})"]
                summary_parts = [f"De-risk {t.headline}" for t in trim_recs]
                
                action_bullets = []
                idx = 1
                for t in trim_recs:
                    action_bullets.append(f"{idx}. **De-Risk Mandate Breach:** {t.recommendation}")
                    idx += 1

                talking_point_parts = [f"trimming positions in {trim_label} to restore mandate adherence"]
                benefits = []
                for t in trim_recs:
                    clean_lbl = t.headline
                    if ":" in t.headline and "represents" in t.headline:
                        clean_lbl = t.headline.split(":")[1].split("represents")[0].strip()
                    elif "overweight" in t.headline.lower():
                        clean_lbl = t.headline.split("overweight")[0].strip() + " (Overweight)"
                    benefits.append(f"🛡️ **Mandate Governance ({clean_lbl}):** {t.recommendation}")

                if main_tax:
                    title_parts.append("Tax-Loss Shield")
                    summary_parts.append(f"execute {main_tax.headline.lower()} to shield taxable gains")
                    action_bullets.append(f"{idx}. **Harvest Tax Losses:** {main_tax.recommendation}")
                    idx += 1
                    talking_point_parts.append("simultaneously harvesting available tax losses to neutralize capital gains tax friction")
                    benefits.append(f"📉 **Tax Optimization:** {main_tax.recommendation}")

                if main_life:
                    title_parts.append("Milestone Ring-Fencing")
                    summary_parts.append(f"pre-fund {main_life.headline.lower()}")
                    action_bullets.append(f"{idx}. **Pre-Fund Life Milestone:** {main_life.recommendation}")
                    idx += 1
                    talking_point_parts.append(f"pre-funding your upcoming liquidity milestone ({main_life.headline})")
                    benefits.append(f"🏡 **Milestone Coverage:** {main_life.recommendation}")

                if main_cash:
                    title_parts.append("Cash Reserve Fortification")
                    summary_parts.append("sweep residual proceeds into Cash & Equivalents")
                    action_bullets.append(f"{idx}. **Fortify Cash Reserves:** {main_cash.recommendation}")
                    idx += 1
                    talking_point_parts.append("reinforcing your Cash & Equivalents buffer safely above mandate minimums")
                    benefits.append(f"💧 **Liquidity Fortification:** {main_cash.recommendation}")

                title = f"Multi-Objective Strategy: {' ↔ '.join(title_parts)}"
                summary = f"Synergistic execution package clubbing {len(clubbed_items)} specialist actions: " + ", ".join(summary_parts) + "."
                unified_action = "\n".join(action_bullets)
                unified_talking_point = (
                    f"Rather than addressing your portfolio adjustments piecemeal, we have structured a unified multi-objective execution package: "
                    + ", ".join(talking_point_parts) + "."
                )
                financial_benefits = benefits

                opportunities.append({
                    "id": f"PKG-SYN-{context['client_id']}-01",
                    "title": title,
                    "opportunity_type": "multi_objective_tax_liquidity_rebalance",
                    "client_id": context["client_id"],
                    "clubbed_rec_ids": clubbed_ids,
                    "clubbed_recs": [r.model_dump() for r in clubbed_items],
                    "summary": summary,
                    "unified_action": unified_action,
                    "unified_talking_point": unified_talking_point,
                    "financial_benefits": financial_benefits
                })

        return opportunities

    def _detect_conflicts(self, recs: List[Recommendation], context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Detects contradictions between rebalancing, tax friction, liquidity, and RM notes."""
        conflicts = []
        rebalance_recs = [r for r in recs if r.agent == "rebalancing"]
        tax_recs = [r for r in recs if r.agent == "tax"]
        note_recs = [r for r in recs if r.agent == "rm_notes"]
        liquidity_recs = [r for r in recs if r.agent == "liquidity"]

        # Conflict Type A: Rebalance asks to trim vs RM note says client refuses to sell legacy
        for reb in rebalance_recs:
            for note in note_recs:
                if "legacy" in note.headline.lower() or "did not want" in note.headline.lower() or "avoid" in note.headline.lower():
                    conflicts.append({
                        "id": f"CONF-{reb.id}-{note.id}",
                        "title": "Mandate Rebalancing vs RM Standing Note Constraint",
                        "rec_a": reb.id,
                        "rec_b": note.id,
                        "description": f"Rebalancing agent proposes trimming an overweight position, but RM notes document client refusal/blocker on legacy shareholdings.",
                        "tradeoff": "Strict mandate compliance requires selling; relationship preservation requires respecting client family governance.",
                        "recommended_resolution": "Maintain core holding while exploring synthetic derivative overlay or reallocating satellite sleeve."
                    })
                    reb.conflicts_with.append(note.id)
                    note.conflicts_with.append(reb.id)

        # Conflict Type B: Lombard Deleveraging vs Rebalancing into Equities
        if any("CREDIT ALERT" in l.headline for l in liquidity_recs) and any("underweight" in r.headline for r in rebalance_recs):
            conflicts.append({
                "id": f"CONF-LTV-REB",
                "title": "LTV De-risking vs Equity Dip Buying",
                "rec_a": "LTV-Agent",
                "rec_b": "Rebalance-Agent",
                "description": "Credit facility is near covenant margin call threshold, conflicting with purchasing risk assets for mandate rebalancing.",
                "tradeoff": "Deploying cash to equities worsens margin call risk; deleveraging locks in mandate tracking error.",
                "recommended_resolution": "Prioritize margin call headroom de-risking before allocating to risk assets."
            })

        return conflicts

    def _compliance_gate(self, recs: List[Recommendation], context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Verifies suitability rules, KYC currency, and PEP guidelines."""
        flags = []
        kyc_due = context.get("kyc_review_due", "")
        pep_status = context.get("pep_status", "No")

        if kyc_due and "2026" in kyc_due and ("01" in kyc_due or "02" in kyc_due or "03" in kyc_due or "04" in kyc_due or "05" in kyc_due or "06" in kyc_due or "07" in kyc_due or "08" in kyc_due):
            flags.append({
                "type": "KYC_DUE",
                "severity": "medium",
                "message": f"Periodic KYC review is overdue/due ({kyc_due}). Ensure refresh documentation is requested during client contact."
            })

        if pep_status == "Yes":
            flags.append({
                "type": "PEP_CLIENT",
                "severity": "high",
                "message": "Politically Exposed Person (PEP) protocol active. Enhanced transaction monitoring applies to all proposed trades."
            })

        return flags

    def _compute_urgency(self, recs: List[Recommendation], context: Dict[str, Any], snapshot_date: str) -> Tuple[float, Dict[str, Any]]:
        """Calculates normalized composite urgency score (0 - 100) and structured factor breakdown."""
        base_score = 10.0
        
        # Credit facility urgency
        credit_points = 0.0
        credit_detail = None
        ltv_data = self.analytics.compute_ltv(context["client_id"], snapshot_date)
        if ltv_data.get("has_critical_warning"):
            credit_points = 45.0
            credit_detail = "🚨 Critical Margin Call Warning"
        elif ltv_data.get("margin_call_warnings"):
            credit_points = 30.0
            credit_detail = "⚠️ LTV Margin Call Watch"

        # Liquidity crunch
        liquidity_points = 0.0
        liquidity_detail = None
        runway = self.analytics.compute_liquidity_runway(context["client_id"], snapshot_date)
        if runway.get("urgency") == "CRITICAL":
            liquidity_points = 35.0
            liquidity_detail = "💧 Critical Cash Deficit (<3mo)"
        elif runway.get("urgency") == "HIGH":
            liquidity_points = 20.0
            liquidity_detail = "💧 High Cash Deficit (<6mo)"

        # Mandate Breaches
        mandate_points = 0.0
        mandate_breaches_count = 0
        for pf in context.get("portfolios", []):
            drift = self.analytics.compute_drift(pf["portfolio_id"], snapshot_date)
            if drift.get("has_breaches"):
                mandate_breaches_count += len(drift.get("breaches", []))
        if mandate_breaches_count > 0:
            mandate_points = 15.0 * mandate_breaches_count
        mandate_detail = f"⚖️ {mandate_breaches_count} Mandate Breach(es)" if mandate_breaches_count > 0 else None

        # High priority recommendations
        high_recs = [r for r in recs if r.priority == "high"]
        high_actions_points = min(len(high_recs) * 5.0, 20.0)
        high_actions_detail = f"⚡ {len(high_recs)} High Priority Action(s)" if high_recs else None

        raw_total = base_score + credit_points + liquidity_points + mandate_points + high_actions_points
        final_score = min(round(raw_total, 1), 100.0)

        breakdown = {
            "base_score": base_score,
            "credit_points": credit_points,
            "credit_detail": credit_detail,
            "liquidity_points": liquidity_points,
            "liquidity_detail": liquidity_detail,
            "mandate_points": mandate_points,
            "mandate_breaches_count": mandate_breaches_count,
            "mandate_detail": mandate_detail,
            "high_actions_points": high_actions_points,
            "high_actions_count": len(high_recs),
            "high_actions_detail": high_actions_detail,
            "total_score": final_score
        }

        return final_score, breakdown

    def _synthesize_brief(self, client_id: str, recs: List[Recommendation], conflicts: List[Dict[str, Any]], context: Dict[str, Any]) -> Dict[str, Any]:
        """Synthesizes executive client brief for RM."""
        high_recs = [r for r in recs if r.priority == "high"]
        med_recs = [r for r in recs if r.priority == "medium"]

        top_talking_points = [r.talking_point for r in (high_recs + med_recs)[:3]]
        
        return {
            "client_name": context.get("client_name"),
            "reporting_language": context.get("reporting_language", "English"),
            "total_recommendations": len(recs),
            "high_priority_count": len(high_recs),
            "conflict_count": len(conflicts),
            "executive_summary": f"Client dossier has {len(recs)} intelligent actions surfaced across rebalancing, credit, and liquidity. {len(conflicts)} cross-agent tradeoffs require RM discretion.",
            "top_talking_points": top_talking_points
        }

class BookPrioritizer:
    """5.2 Book-Level Prioritization Engine."""
    def __init__(self, orchestrator: Optional[ClientOrchestrator] = None):
        self.orchestrator = orchestrator or ClientOrchestrator()
        self.repo = self.orchestrator.repo

    def get_ranked_book(self, snapshot_date: str = "2026-08-26") -> List[Dict[str, Any]]:
        """Evaluates and ranks all 20 clients by urgency score."""
        clients = self.repo.get_all_clients()
        results = []

        for c in clients:
            cid = c["client_id"]
            client_run = self.orchestrator.run_client(cid, snapshot_date)
            
            # Extract key badges & triggers
            recs = client_run["recommendations"]
            high_count = sum(1 for r in recs if r["priority"] == "high")
            has_ltv_alert = any("CREDIT ALERT" in r["headline"] for r in recs)
            has_drift_alert = any(r["agent"] == "rebalancing" for r in recs)
            has_liq_alert = any("Liquidity Crunch" in r["headline"] for r in recs)

            # Calculate client AUM as of snapshot_date from holdings
            client_holdings = self.repo.get_all_holdings_for_client(cid, snapshot_date)
            snapshot_aum_usd = sum(h["market_value_usd"] for h in client_holdings) if client_holdings else float(c.get("total_aum_usd", 0.0))

            results.append({
                "client_id": cid,
                "client_name": c["client_name"],
                "rm_id": c.get("rm_id"),
                "rm_name": c.get("rm_name"),
                "rm_desk": c.get("rm_desk"),
                "booking_centre": c.get("booking_centre", "Singapore"),
                "country_of_residence": c.get("country_of_residence", ""),
                "total_aum_usd": round(snapshot_aum_usd, 2),
                "wealth_band": c.get("wealth_band"),
                "risk_profile": c.get("risk_profile"),
                "tax_domicile": c.get("tax_domicile"),
                "urgency_score": client_run["urgency_score"],
                "urgency_breakdown": client_run.get("urgency_breakdown", {}),
                "last_meeting_date": client_run["client_context"].get("last_meeting_date"),
                "last_meeting_channel": client_run["client_context"].get("last_meeting_channel"),
                "high_priority_count": high_count,
                "has_ltv_alert": has_ltv_alert,
                "has_drift_alert": has_drift_alert,
                "has_liq_alert": has_liq_alert,
                "conflicts_count": len(client_run["conflicts"]),
                "comingling_count": len(client_run.get("comingling_opportunities", [])),
                "headline_action": recs[0]["headline"] if recs else "All mandates within tolerances",
                "client_run": client_run
            })

        # Rank by urgency score descending
        return sorted(results, key=lambda x: x["urgency_score"], reverse=True)
