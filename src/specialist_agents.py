"""
Dynamic LLM Specialist Agents Layer (LangGraph & LangChain Ready)
Implements:
4.1 Context Assembler (Prompt & Constraints Pipeline)
4.2 Rebalancing LLM Agent
4.3 Tax-Aware Optimization LLM Agent
4.4 Life-Event Planning LLM Agent
4.5 Liquidity & Credit Risk LLM Agent
4.6 Market & Event-Impact LLM Agent
4.7 RM Notes LLM Agent

Each agent is a dynamic LLM reasoning agent that consumes deterministic tool facts,
applies private banking personas & suitability logic, and emits structured §6 recommendations.
"""

import uuid
import json
import hashlib
from typing import Dict, List, Any, Optional
from src.agent_state import Recommendation, EvidenceItem
from src.deterministic_analytics import DeterministicAnalytics
from src.llm_engine import LLMEngine

def make_rec_id(prefix: str, *keys: Any) -> str:
    """Generates a stable, deterministic recommendation ID based on semantic keys."""
    raw = "_".join(str(k) for k in keys if k is not None)
    h = hashlib.md5(raw.encode("utf-8")).hexdigest()[:6].upper()
    return f"REC-{prefix.upper()}-{h}"

class ContextAssembler:
    """4.1 Assembles comprehensive client context & standing overrides."""
    def __init__(self, analytics: DeterministicAnalytics):
        self.analytics = analytics
        self.repo = analytics.repo

    def assemble(self, client_id: str, snapshot_date: str) -> Dict[str, Any]:
        client = self.repo.get_client(client_id) or {}
        portfolios = self.repo.get_portfolios_for_client(client_id)
        rm_notes_info = self.analytics.get_rm_notes(client_id, as_of_date=snapshot_date)
        
        return {
            "client_id": client_id,
            "client_name": client.get("client_name", "Unknown"),
            "age": client.get("age"),
            "life_stage": client.get("life_stage"),
            "source_of_wealth": client.get("source_of_wealth"),
            "risk_profile": client.get("risk_profile"),
            "risk_tolerance_score": client.get("risk_tolerance_score"),
            "tax_domicile": client.get("tax_domicile"),
            "booking_centre": client.get("booking_centre"),
            "total_aum_usd": client.get("total_aum_usd"),
            "objectives": client.get("objectives"),
            "reporting_language": client.get("reporting_language", "English"),
            "pep_status": client.get("pep_status"),
            "kyc_review_due": client.get("kyc_review_due"),
            "portfolios": portfolios,
            "standing_overrides": rm_notes_info.get("standing_overrides", []),
            "preferences": rm_notes_info.get("preferences", []),
            "last_meeting_date": rm_notes_info.get("last_meeting_date"),
            "last_meeting_channel": rm_notes_info.get("last_meeting_channel"),
            "last_meeting_summary": rm_notes_info.get("last_meeting_summary"),
            "snapshot_date": snapshot_date
        }

class BaseLLMAgent:
    """Base class for Dynamic LLM Specialist Agents."""
    def __init__(self, analytics: DeterministicAnalytics, agent_name: str):
        self.analytics = analytics
        self.repo = analytics.repo
        self.agent_name = agent_name
        self.llm = LLMEngine.get_instance()

    def _parse_llm_recommendations(self, llm_output: Any, client_id: str, default_tier: str = "fact") -> List[Recommendation]:
        """Parses dynamic LLM JSON response into typed Recommendation objects."""
        if not llm_output:
            return []
        
        items = []
        if isinstance(llm_output, dict):
            if "recommendations" in llm_output:
                items = llm_output["recommendations"]
            elif "recommendation" in llm_output:
                items = [llm_output]
            else:
                items = [llm_output]
        elif isinstance(llm_output, list):
            items = llm_output

        recs = []
        for item in items:
            if not isinstance(item, dict):
                continue
            
            # Extract or build evidence
            ev_list = []
            raw_ev = item.get("evidence", [])
            if isinstance(raw_ev, list):
                for e in raw_ev:
                    if isinstance(e, dict):
                        ev_list.append(EvidenceItem(
                            source_function=e.get("source_function", f"compute_{self.agent_name}"),
                            detail=str(e.get("detail", item.get("headline", ""))),
                            as_of_date=str(e.get("as_of_date", "2026-08-26")),
                            threshold_or_band=e.get("threshold_or_band"),
                            raw_metric_value=e.get("raw_metric_value")
                        ))
            if not ev_list:
                ev_list.append(EvidenceItem(
                    source_function=f"compute_{self.agent_name}",
                    detail=item.get("headline", "Specialist evaluation"),
                    as_of_date="2026-08-26"
                ))

            stable_id = item.get("id") or make_rec_id(self.agent_name[:3], client_id, item.get("portfolio_id"), item.get("headline"))

            recs.append(Recommendation(
                id=stable_id,
                client_id=client_id,
                portfolio_id=item.get("portfolio_id"),
                portfolio_name=item.get("portfolio_name"),
                agent=self.agent_name,
                priority=str(item.get("priority", "medium")).lower(),
                confidence_tier=str(item.get("confidence_tier", default_tier)).lower(),
                headline=str(item.get("headline", "")),
                evidence=ev_list,
                recommendation=str(item.get("recommendation", "")),
                talking_point=str(item.get("talking_point", "")),
                conflicts_with=item.get("conflicts_with", []),
                compliance_status=str(item.get("compliance_status", "pass")).lower(),
                compliance_reason=item.get("compliance_reason"),
                rm_note_influence=item.get("rm_note_influence")
            ))
        return recs


class RebalancingAgent(BaseLLMAgent):
    """4.2 Dynamic Rebalancing LLM Agent — Multi-asset allocation & concentration specialist."""
    def __init__(self, analytics: DeterministicAnalytics):
        super().__init__(analytics, "rebalancing")

    def run(self, context: Dict[str, Any], snapshot_date: str) -> List[Recommendation]:
        client_id = context["client_id"]
        portfolios = context.get("portfolios", [])
        standing_overrides = context.get("standing_overrides", [])

        # Gather deterministic tool facts
        tool_facts = []
        for pf in portfolios:
            pf_id = pf["portfolio_id"]
            drift = self.analytics.compute_drift(pf_id, snapshot_date)
            conc = self.analytics.compute_concentration(pf_id, snapshot_date)
            tool_facts.append({
                "portfolio_id": pf_id,
                "portfolio_name": pf["portfolio_name"],
                "mandate_code": pf["mandate_code"],
                "drift_results": drift,
                "concentration_results": conc
            })

        system_prompt = """You are the Senior Portfolio Rebalancing Strategist at Bank Julius Baer.
Your role: Review deterministic portfolio drift and concentration tool outputs against agreed investment mandates.
Strict rules:
1. NEVER invent or recalculate raw financial figures; cite the provided deterministic numbers.
2. For each breach (upper breach, lower breach, single position concentration limit), produce a structured recommendation conforming to §6.
3. Check standing RM notes for restrictions on legacy holdings or family assets. If an override applies, set compliance_status to 'needs_review'.
4. Write client-ready talking points in an articulate, prestigious Swiss private banking tone.

Respond ONLY with valid JSON in this schema:
{
  "recommendations": [
    {
      "id": "REC-REB-XXXX",
      "client_id": "string",
      "portfolio_id": "string",
      "portfolio_name": "string",
      "agent": "rebalancing",
      "priority": "high | medium | low",
      "confidence_tier": "fact",
      "headline": "One sentence summary of breach",
      "evidence": [
        { "source_function": "compute_drift", "detail": "Fact detail", "as_of_date": "YYYY-MM-DD", "threshold_or_band": "Mandate info" }
      ],
      "recommendation": "Specific rebalancing trade action",
      "talking_point": "Client-ready conversational phrasing for the RM",
      "compliance_status": "pass | needs_review | blocked",
      "compliance_reason": "string or null",
      "rm_note_influence": "string or null"
    }
  ]
}"""

        user_prompt = f"""Client Profile:
ID: {client_id}
Name: {context.get('client_name')}
Risk Profile: {context.get('risk_profile')}
Standing RM Overrides: {json.dumps(standing_overrides)}
Snapshot Date: {snapshot_date}

Deterministic Tool Facts:
{json.dumps(tool_facts, indent=2)}"""

        # Dynamic LLM execution
        llm_response = self.llm.generate_json(user_prompt, system_prompt)
        recs = self._parse_llm_recommendations(llm_response, client_id, default_tier="fact")

        # Dynamic Fallback Synthesis if LLM API is unconfigured
        if not recs:
            for pf_data in tool_facts:
                pf_id = pf_data["portfolio_id"]
                pf_name = pf_data["portfolio_name"]
                drift = pf_data["drift_results"]
                conc = pf_data["concentration_results"]

                for breach in drift.get("breaches", []):
                    ac = breach["asset_class"]
                    b_type = breach["type"]
                    actual_pct = breach["actual_pct"]
                    
                    override_hit = None
                    for ov in standing_overrides:
                        if ac.lower() in ov["summary"].lower() or ("legacy" in ov["summary"].lower() and "equity" in ac.lower()):
                            override_hit = ov["summary"]

                    if b_type == "upper_breach":
                        excess = breach["excess_pct"]
                        max_pct = breach["band_max_pct"]
                        trim_usd = breach["trim_to_target_usd"]
                        headline = f"{ac} overweight at {actual_pct:.1f}% (max band {max_pct:.1f}%) in {pf_name}"
                        rec_text = f"Trim {ac} by approx USD {trim_usd:,.0f} to restore target allocation."
                        talk = f"Your {ac} allocation has appreciated to {actual_pct:.1f}%, exceeding our agreed mandate limit of {max_pct:.1f}%. We recommend locking in gains and rebalancing into core defensive assets."
                    else:
                        deficit = breach["deficit_pct"]
                        min_pct = breach["band_min_pct"]
                        add_usd = breach["add_to_target_usd"]
                        headline = f"{ac} underweight at {actual_pct:.1f}% (min band {min_pct:.1f}%) in {pf_name}"
                        rec_text = f"Add USD {add_usd:,.0f} to {ac} to return within the {min_pct:.1f}% minimum band."
                        talk = f"Your {ac} exposure is currently {actual_pct:.1f}%, below your mandate threshold of {min_pct:.1f}%. We suggest redeploying liquidity to maintain your strategic benchmark."

                    recs.append(Recommendation(
                        id=make_rec_id("REB", client_id, pf_id, ac, b_type),
                        client_id=client_id,
                        portfolio_id=pf_id,
                        portfolio_name=pf_name,
                        agent="rebalancing",
                        priority="high" if abs(breach.get("excess_pct", breach.get("deficit_pct", 0))) > 5.0 else "medium",
                        confidence_tier="fact",
                        headline=headline,
                        evidence=[
                            EvidenceItem(
                                source_function="compute_drift",
                                detail=f"{ac} is {actual_pct:.1f}% vs mandate band ({breach.get('band_min_pct', 0)}% - {breach.get('band_max_pct', 0)}%)",
                                as_of_date=snapshot_date,
                                threshold_or_band=f"Mandate {pf_data['mandate_code']}",
                                raw_metric_value=actual_pct
                            )
                        ],
                        recommendation=rec_text,
                        talking_point=talk,
                        compliance_status="pass" if not override_hit else "needs_review",
                        compliance_reason="RM note constraint detected on legacy/asset class holdings" if override_hit else None,
                        rm_note_influence=f"RM Note Alert: '{override_hit}'" if override_hit else None
                    ))

                for warn in drift.get("warnings", []):
                    ac = warn["asset_class"]
                    actual_pct = warn["actual_pct"]
                    b_min = warn.get("band_min_pct")
                    b_max = warn.get("band_max_pct")
                    limit_val = b_min if b_min is not None else b_max

                    recs.append(Recommendation(
                        id=make_rec_id("WARN", client_id, pf_id, ac, "warning"),
                        client_id=client_id,
                        portfolio_id=pf_id,
                        portfolio_name=pf_name,
                        agent="rebalancing",
                        priority="low",
                        confidence_tier="fact",
                        headline=f"Allocation Warning: {ac} is at the mandate limit ({actual_pct:.1f}%) in {pf_name}",
                        evidence=[
                            EvidenceItem(
                                source_function="compute_drift",
                                detail=f"{ac} is currently {actual_pct:.1f}%, at the mandate limit of {limit_val:.1f}%",
                                as_of_date=snapshot_date,
                                threshold_or_band=f"Mandate {pf_data['mandate_code']}",
                                raw_metric_value=actual_pct
                            )
                        ],
                        recommendation=f"Monitor {ac} allocation. No immediate rebalancing required as position is within tolerance.",
                        talking_point=f"Your {ac} allocation is currently {actual_pct:.1f}%, touching our mandate boundary limit of {limit_val:.1f}%. We are actively monitoring this sleeve.",
                        compliance_status="pass"
                    ))

                for s_breach in conc.get("single_breaches", []):
                    iname = s_breach["instrument_name"]
                    w_pct = s_breach["weight_pct"]
                    limit_pct = s_breach["limit_pct"]
                    excess_usd = s_breach["excess_usd"]

                    recs.append(Recommendation(
                        id=make_rec_id("CONC", client_id, pf_id, iname),
                        client_id=client_id,
                        portfolio_id=pf_id,
                        portfolio_name=pf_name,
                        agent="rebalancing",
                        priority="high",
                        confidence_tier="fact",
                        headline=f"Concentration breach: {iname} represents {w_pct:.1f}% of portfolio (limit {limit_pct:.1f}%)",
                        evidence=[
                            EvidenceItem(
                                source_function="compute_concentration",
                                detail=f"Single security holding is {w_pct:.1f}% (cap is {limit_pct:.1f}%)",
                                as_of_date=snapshot_date,
                                threshold_or_band=f"Max Single Position {limit_pct:.1f}%",
                                raw_metric_value=w_pct
                            )
                        ],
                        recommendation=f"De-risk position by reducing USD {excess_usd:,.0f} to comply with single-issuer concentration guidelines.",
                        talking_point=f"Due to recent market movements, {iname} now accounts for {w_pct:.1f}% of your portfolio, surpassing our risk governance cap of {limit_pct:.1f}%. We recommend prudent partial profit-taking.",
                        compliance_status="needs_review",
                        compliance_reason="Exceeds single issuer mandate concentration threshold."
                    ))

        return recs


class TaxOptimizationAgent(BaseLLMAgent):
    """4.3 Dynamic Tax Optimization LLM Agent — Domicile rules & harvesting specialist."""
    def __init__(self, analytics: DeterministicAnalytics):
        super().__init__(analytics, "tax")

    def run(self, context: Dict[str, Any], snapshot_date: str) -> List[Recommendation]:
        client_id = context["client_id"]
        tax_domicile = context.get("tax_domicile", "Unknown")
        portfolios = context.get("portfolios", [])

        tool_facts = []
        for pf in portfolios:
            pf_id = pf["portfolio_id"]
            tax_data = self.analytics.compute_tax_lots(pf_id, snapshot_date)
            tool_facts.append({
                "portfolio_id": pf_id,
                "portfolio_name": pf["portfolio_name"],
                "tax_data": tax_data
            })

        system_prompt = """You are the Senior Tax Structuring & Wealth Planning Specialist at Bank Julius Baer.
Evaluate unrealized gains/losses against the client's tax domicile.
Strict rules:
1. In 0% capital gains jurisdictions (Singapore, Hong Kong, UAE, Switzerland private), confirm zero tax drag on rebalancing.
2. In taxable jurisdictions, flag significant harvestable losses (> USD 50,000) to offset realized capital gains.
3. Emit structured JSON matching §6."""

        user_prompt = f"""Client Tax Domicile: {tax_domicile}
Snapshot Date: {snapshot_date}
Tool Tax Facts:
{json.dumps(tool_facts, indent=2)}"""

        llm_response = self.llm.generate_json(user_prompt, system_prompt)
        recs = self._parse_llm_recommendations(llm_response, client_id, default_tier="rule")

        if not recs:
            for item in tool_facts:
                pf_id = item["portfolio_id"]
                tax_data = item["tax_data"]
                harvestable = tax_data.get("total_harvestable_losses_usd", 0.0)
                
                if not tax_data.get("is_zero_cap_gains") and harvestable > 50000.0:
                    recs.append(Recommendation(
                        id=make_rec_id("TAX", client_id, pf_id, tax_domicile),
                        client_id=client_id,
                        portfolio_id=pf_id,
                        portfolio_name=item["portfolio_name"],
                        agent="tax",
                        priority="medium",
                        confidence_tier="rule",
                        headline=f"Tax Loss Harvesting opportunity: USD {harvestable:,.0f} in unrealized losses ({tax_domicile} Domicile)",
                        evidence=[
                            EvidenceItem(
                                source_function="compute_tax_lots",
                                detail=f"Found USD {harvestable:,.0f} in qualifying loss positions in {tax_domicile} tax jurisdiction",
                                as_of_date=snapshot_date,
                                threshold_or_band=f"Tax Domicile: {tax_domicile}",
                                raw_metric_value=harvestable
                            )
                        ],
                        recommendation=f"Harvest eligible loss lots to offset realized capital gains prior to year-end tax assessment.",
                        talking_point=f"Given your tax domicile in {tax_domicile}, we have identified approximately USD {harvestable:,.0f} in harvestable losses that can offset realized capital gains without altering your strategic asset allocation.",
                        compliance_status="pass"
                    ))
        return recs


class LifeEventPlanningAgent(BaseLLMAgent):
    """4.4 Dynamic Life-Event Planning LLM Agent — Milestones, cash needs & succession specialist."""
    def __init__(self, analytics: DeterministicAnalytics):
        super().__init__(analytics, "life_event")

    def run(self, context: Dict[str, Any], snapshot_date: str) -> List[Recommendation]:
        client_id = context["client_id"]
        cash_needs = self.analytics.repo.get_planned_cash_needs_for_client(client_id)
        
        system_prompt = """You are the Family Office & Life-Event Advisory Director at Bank Julius Baer.
Evaluate planned cash needs, liquidity milestones, and generational succession goals.
Generate structured recommendations that ring-fence required liquidity in advance of due dates."""

        user_prompt = f"""Client Life Stage: {context.get('life_stage')}, Stated Objectives: {context.get('objectives')}
Planned Cash Needs:
{json.dumps(cash_needs, indent=2)}"""

        llm_response = self.llm.generate_json(user_prompt, system_prompt)
        recs = self._parse_llm_recommendations(llm_response, client_id, default_tier="fact")

        if not recs:
            for cn in cash_needs:
                amt = float(cn.get("amount", 0))
                desc = cn.get("description", "Cash Need")
                due_from = cn.get("due_from", "")
                certainty = cn.get("certainty", "Likely")
                ccy = cn.get("currency", "USD")

                if amt > 500000.0:
                    recs.append(Recommendation(
                        id=make_rec_id("LIFE", client_id, desc, due_from),
                        client_id=client_id,
                        portfolio_id=None,
                        agent="life_event",
                        priority="high" if "2026" in due_from else "medium",
                        confidence_tier="fact",
                        headline=f"Upcoming liquidity milestone: {desc} ({ccy} {amt:,.0f}) due {due_from}",
                        evidence=[
                            EvidenceItem(
                                source_function="get_planned_cash_needs",
                                detail=f"Planned cash need of {ccy} {amt:,.0f} ({certainty}) scheduled for {due_from}",
                                as_of_date=snapshot_date,
                                threshold_or_band=f"Certainty: {certainty}",
                                raw_metric_value=amt
                            )
                        ],
                        recommendation=f"Structure liquidity sleeve and ring-fence capital to meet upcoming {desc} without forced position liquidations.",
                        talking_point=f"With the upcoming requirement of {ccy} {amt:,.0f} for {desc.lower()} in {due_from}, we should ensure that appropriate liquidity is pre-funded to avoid market timing pressure.",
                        compliance_status="pass"
                    ))
        return recs


class LiquidityCreditRiskAgent(BaseLLMAgent):
    """4.5 Dynamic Liquidity & Credit Risk LLM Agent — Lombard covenants & capital calls specialist."""
    def __init__(self, analytics: DeterministicAnalytics):
        super().__init__(analytics, "liquidity")

    def run(self, context: Dict[str, Any], snapshot_date: str) -> List[Recommendation]:
        client_id = context["client_id"]
        ltv_info = self.analytics.compute_ltv(client_id, snapshot_date)
        runway = self.analytics.compute_liquidity_runway(client_id, snapshot_date)

        system_prompt = """You are the Chief Credit & Liquidity Risk Officer at Bank Julius Baer.
Evaluate Lombard loan LTV proximity to margin call thresholds, headroom trends, and private market uncalled capital call coverage.
Highlight critical margin call risks immediately and propose actionable de-leveraging or liquidity re-allocation steps."""

        user_prompt = f"""Credit LTV Tool Output:
{json.dumps(ltv_info, indent=2)}

Liquidity Runway Tool Output:
{json.dumps(runway, indent=2)}"""

        llm_response = self.llm.generate_json(user_prompt, system_prompt)
        recs = self._parse_llm_recommendations(llm_response, client_id, default_tier="fact")

        if not recs:
            for warn in ltv_info.get("margin_call_warnings", []):
                fid = warn["facility_id"]
                cur_ltv = warn["current_ltv_pct"]
                call_ltv = warn["margin_call_threshold_pct"]
                buf = warn["buffer_pct"]
                is_crit = warn["is_critical"]

                recs.append(Recommendation(
                    id=make_rec_id("LTV", client_id, fid),
                    client_id=client_id,
                    portfolio_id=None,
                    agent="liquidity",
                    priority="high",
                    confidence_tier="fact",
                    headline=f"CREDIT ALERT: Lombard facility {fid} LTV is {cur_ltv:.1f}% — buffer to margin call is only {buf:.1f}%",
                    evidence=[
                        EvidenceItem(
                            source_function="compute_ltv",
                            detail=f"Facility {fid}: Current LTV {cur_ltv:.1f}% vs covenant margin call trigger {call_ltv:.1f}%",
                            as_of_date=snapshot_date,
                            threshold_or_band=f"Margin Call at {call_ltv:.1f}%",
                            raw_metric_value=cur_ltv
                        )
                    ],
                    recommendation="Inject unencumbered collateral or pay down loan balance immediately to restore LTV safety buffer.",
                    talking_point=f"Your credit facility utilization is currently at {cur_ltv:.1f}%, leaving only a {buf:.1f}% buffer before the covenant margin call threshold of {call_ltv:.1f}%. We recommend a proactive top-up of collateral.",
                    compliance_status="blocked" if is_crit else "needs_review",
                    compliance_reason="High risk of covenant breach on Lombard facility."
                ))

            if runway.get("urgency") in ["CRITICAL", "HIGH"]:
                uncalled = runway.get("uncalled_commitments_usd", 0)
                cov = runway.get("coverage_ratio", 0)

                recs.append(Recommendation(
                    id=make_rec_id("LIQ", client_id, "runway"),
                    client_id=client_id,
                    portfolio_id=None,
                    agent="liquidity",
                    priority="high",
                    confidence_tier="fact",
                    headline=f"Liquidity Crunch Warning: Coverage ratio is {cov:.2f}x against USD {uncalled:,.0f} uncalled commitments",
                    evidence=[
                        EvidenceItem(
                            source_function="compute_liquidity_runway",
                            detail=f"Liquid pool USD {runway.get('total_liquid_pool_usd'):,.0f} vs planned obligations USD {runway.get('total_outflows_expected_usd'):,.0f}",
                            as_of_date=snapshot_date,
                            threshold_or_band="Minimum Coverage 1.5x",
                            raw_metric_value=cov
                        )
                    ],
                    recommendation=f"Reposition short-term liquidity buffers to ensure private fund capital calls can be honored seamlessly.",
                    talking_point=f"We have reviewed your private market commitments (USD {uncalled:,.0f} uncalled). Your current liquidity coverage is {cov:.2f}x. We recommend fortifying liquid reserves ahead of Q4 capital call windows.",
                    compliance_status="needs_review",
                    compliance_reason="Liquidity buffer below target reserve threshold."
                ))
        return recs


class MarketImpactAgent(BaseLLMAgent):
    """4.6 Dynamic Market & Event-Impact LLM Agent — Macro shock transmission specialist."""
    def __init__(self, analytics: DeterministicAnalytics):
        super().__init__(analytics, "market")

    def run(self, context: Dict[str, Any], snapshot_date: str) -> List[Recommendation]:
        client_id = context["client_id"]
        last_meeting_date = context.get("last_meeting_date")
        try:
            matches = self.analytics.match_events_to_holdings(client_id, snapshot_date, since_date=last_meeting_date)
        except TypeError:
            matches = self.analytics.match_events_to_holdings(client_id, snapshot_date)

        system_prompt = f"""You are the Global Macro & Event Risk Strategist at Bank Julius Baer.
Correlate world market events occurring since the client's last RM interaction ({last_meeting_date or 'recent baseline'}) with specific client holdings and transmission channels.
Provide defensive hedging and tactical overlay insights focusing on fresh market developments."""

        user_prompt = f"""Client Last RM Contact Date: {last_meeting_date or 'None on record'}
Evaluation Snapshot Date: {snapshot_date}
Correlated New Market Events & Affected Holdings (Occurring Post-Last-Meeting):
{json.dumps(matches[:3], indent=2)}"""

        llm_response = self.llm.generate_json(user_prompt, system_prompt)
        recs = self._parse_llm_recommendations(llm_response, client_id, default_tier="model")

        if not recs:
            for match in matches[:2]:
                ev_desc = match["description"]
                ev_date = match["event_date"]
                trans = match["transmission"]
                exposed_usd = match["total_exposed_usd"]
                
                since_prefix = f"Post-{last_meeting_date} " if last_meeting_date else ""

                recs.append(Recommendation(
                    id=make_rec_id("MKT", client_id, f"{ev_date}_{ev_desc[:20]}"),
                    client_id=client_id,
                    portfolio_id=None,
                    agent="market",
                    priority="medium",
                    confidence_tier="model",
                    headline=f"Macro Event Transmission ({since_prefix}Event on {ev_date}): '{ev_desc}' impacts USD {exposed_usd:,.0f} in exposed holdings",
                    evidence=[
                        EvidenceItem(
                            source_function="match_events_to_holdings",
                            detail=f"New event post last meeting ({last_meeting_date or 'baseline'}): '{ev_desc}' ({ev_date}) via {trans}. Correlated holdings total USD {exposed_usd:,.0f}",
                            as_of_date=snapshot_date,
                            threshold_or_band=f"Event Date: {ev_date} | Last RM Interaction: {last_meeting_date or 'N/A'}",
                            raw_metric_value=exposed_usd
                        )
                    ],
                    recommendation=f"Review defensive hedges or structured downside protection for positions sensitive to {trans.lower()}.",
                    talking_point=(
                        f"Since our last meeting on {last_meeting_date}, several key market developments have emerged — notably: {ev_desc.lower()} ({ev_date}). "
                        f"We have evaluated the transmission channels across your portfolios (USD {exposed_usd:,.0f} exposed) and prepared defensive positioning options."
                        if last_meeting_date else
                        f"In light of recent market developments regarding {ev_desc.lower()} ({ev_date}), we have evaluated the transmission channels across your portfolio and prepared defensive positioning options."
                    ),
                    compliance_status="pass"
                ))
        return recs


class RMNotesAgent(BaseLLMAgent):
    """4.7 Dynamic RM Notes LLM Agent — Sentiment, relationship nuance & standing constraint extractor."""
    def __init__(self, analytics: DeterministicAnalytics):
        super().__init__(analytics, "rm_notes")

    def run(self, context: Dict[str, Any], snapshot_date: str) -> List[Recommendation]:
        client_id = context["client_id"]
        notes_info = self.analytics.get_rm_notes(client_id, as_of_date=snapshot_date)

        system_prompt = """You are the Relationship Intelligence & Client Sentiment Specialist at Bank Julius Baer.
Extract qualitative constraints, emotional blockers, family dynamics, and standing mandates from free-text RM meeting notes.
Ensure documented client preferences act as active standing overrides across all algorithmic suggestions."""

        user_prompt = f"""Unstructured RM Notes & Extracted Overrides:
{json.dumps(notes_info, indent=2)}"""

        llm_response = self.llm.generate_json(user_prompt, system_prompt)
        recs = self._parse_llm_recommendations(llm_response, client_id, default_tier="model")

        if not recs:
            for ov in notes_info.get("standing_overrides", []):
                summary = ov["summary"]
                date_str = ov.get("date", "")
                rm_author = ov.get("rm_name", "RM")

                recs.append(Recommendation(
                    id=make_rec_id("NOTE", client_id, summary[:25]),
                    client_id=client_id,
                    portfolio_id=None,
                    agent="rm_notes",
                    priority="high",
                    confidence_tier="model",
                    headline=f"Standing Client Constraint: {summary[:90]}...",
                    evidence=[
                        EvidenceItem(
                            source_function="get_rm_notes",
                            detail=f"RM Note recorded by {rm_author} on {date_str}: '{summary}'",
                            as_of_date=date_str,
                            threshold_or_band="Standing RM Override",
                            raw_metric_value=1.0
                        )
                    ],
                    recommendation="Enforce documented RM constraint across all algorithmic rebalancing and leverage suggestions.",
                    talking_point="We remain strictly attentive to your preference to preserve this strategic position while optimizing surrounding asset sleeves.",
                    compliance_status="pass",
                    rm_note_influence="Active standing constraint that overrides raw quantitative optimization."
                ))
        return recs
