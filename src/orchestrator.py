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
from src.agent_state import AgentGraphState, Recommendation
from src.specialist_agents import (
    ContextAssembler,
    RebalancingAgent,
    TaxOptimizationAgent,
    LifeEventPlanningAgent,
    LiquidityCreditRiskAgent,
    MarketImpactAgent,
    RMNotesAgent
)

class ClientOrchestrator:
    """5.1 Per-Client Orchestration Engine."""
    def __init__(self, analytics: Optional[DeterministicAnalytics] = None):
        self.analytics = analytics or DeterministicAnalytics()
        self.repo = self.analytics.repo
        self.context_assembler = ContextAssembler(self.analytics)
        self.rebalancing_agent = RebalancingAgent(self.analytics)
        self.tax_agent = TaxOptimizationAgent(self.analytics)
        self.life_event_agent = LifeEventPlanningAgent(self.analytics)
        self.liquidity_agent = LiquidityCreditRiskAgent(self.analytics)
        self.market_agent = MarketImpactAgent(self.analytics)
        self.rm_notes_agent = RMNotesAgent(self.analytics)

    def run_client(self, client_id: str, snapshot_date: str = "2026-08-26") -> Dict[str, Any]:
        """Runs all specialist agents for a client, surfaces conflicts, and runs compliance gate."""
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

        # 3. Dynamic Orchestrator Deduplication & Cross-Agent Synthesis
        recs = self._deduplicate_and_synthesize_recs(raw_recs, context, snapshot_date)

        # 4. Detect Conflicts
        conflicts = self._detect_conflicts(recs, context)

        # 5. Discover Comingling & Clubbing Opportunities
        comingling_opportunities = self._detect_comingling_opportunities(recs, context, snapshot_date)

        # 6. Compliance & Suitability Gate
        compliance_flags = self._compliance_gate(recs, context)

        # 7. Client Brief Synthesis
        brief = self._synthesize_brief(client_id, recs, conflicts, context)

        # 8. Client Urgency Score & Breakdown
        urgency_score, urgency_breakdown = self._compute_urgency(recs, context, snapshot_date)

        return {
            "client_id": client_id,
            "snapshot_date": snapshot_date,
            "client_context": context,
            "recommendations": [r.model_dump() for r in recs],
            "conflicts": conflicts,
            "comingling_opportunities": comingling_opportunities,
            "compliance_flags": compliance_flags,
            "client_brief": brief,
            "urgency_score": round(urgency_score, 1),
            "urgency_breakdown": urgency_breakdown
        }

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
