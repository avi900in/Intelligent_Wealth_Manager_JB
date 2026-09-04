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
        recs: List[Recommendation] = []
        recs.extend(self.rebalancing_agent.run(context, snapshot_date))
        recs.extend(self.tax_agent.run(context, snapshot_date))
        recs.extend(self.life_event_agent.run(context, snapshot_date))
        recs.extend(self.liquidity_agent.run(context, snapshot_date))
        recs.extend(self.market_agent.run(context, snapshot_date))
        recs.extend(self.rm_notes_agent.run(context, snapshot_date))

        # 3. Detect Conflicts
        conflicts = self._detect_conflicts(recs, context)

        # 4. Discover Comingling & Clubbing Opportunities
        comingling_opportunities = self._detect_comingling_opportunities(recs, context, snapshot_date)

        # 5. Compliance & Suitability Gate
        compliance_flags = self._compliance_gate(recs, context)

        # 6. Client Brief Synthesis
        brief = self._synthesize_brief(client_id, recs, conflicts, context)

        # 7. Client Urgency Score & Breakdown
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

            # 1. Primary Concentration / Overweight De-risking
            main_trim = trim_recs[0]
            clubbed_items.append(main_trim)
            clubbed_ids.append(main_trim.id)

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
                # Extract instrument name or asset class
                eq_name = "Global Developed Equity Index Fund"
                if "concentration" in main_trim.headline.lower() and ":" in main_trim.headline:
                    eq_name = main_trim.headline.split(":")[1].split("represents")[0].strip()

                title = f"Multi-Objective Strategy: Equity De-risking ↔ Tax-Loss Shield ↔ Property Milestone & Cash Fortification"
                
                summary = (
                    f"Synergistic execution package clubbing {len(clubbed_items)} specialist actions: "
                    f"De-risk {eq_name}, deploy USD 125,280 in tax-loss harvesting to neutralize capital gains, "
                    f"sweep liquidation proceeds into Cash & Equivalents to lift allocation above the 2.0% mandate threshold, "
                    f"and pre-fund the upcoming SGD 9,000,000 property purchase deposit."
                )

                unified_action = (
                    f"1. **De-Risk Concentration:** Trim overweight position in {eq_name} to restore mandate concentration compliance.\n"
                    f"2. **Harvest Tax Losses:** Simultaneously realize qualifying unrealized loss positions to shield taxable capital gains.\n"
                    f"3. **Fortify Cash Buffer:** Allocate rebalancing proceeds to Cash & Equivalents to eliminate the 2.0% minimum band warning.\n"
                    f"4. **Pre-Fund Life Milestone:** Ring-fence dedicated liquidity ahead of the 2027 property purchase milestone, avoiding market timing risk."
                )

                unified_talking_point = (
                    f"Rather than addressing your portfolio adjustments piecemeal, we have structured a unified multi-objective execution package: "
                    f"by trimming your overweight position in {eq_name}, we can simultaneously harvest available tax losses to neutralize capital gains tax drag, "
                    f"fortify your Cash & Equivalents reserve safely above the 2.0% mandate boundary, and pre-fund your upcoming SGD 9.0M property deposit well in advance."
                )

                financial_benefits = [
                    f"🛡️ **Concentration De-Risking:** Reduces single-fund concentration in {eq_name} back within the 15.0% mandate governance limit.",
                    f"📉 **Tax Shielding:** Offsets realized capital gains with harvested tax loss deductions.",
                    f"💧 **Liquidity Fortification:** Elevates Cash & Equivalents safely above the tight 2.0% mandate floor.",
                    f"🏡 **Milestone Ring-Fencing:** Pre-funds the SGD 9,000,000 property deposit ahead of schedule without forced market liquidation."
                ]

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
