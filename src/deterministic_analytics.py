"""
Deterministic Analytics Layer (Pure Computation)
Strictly computes all financial facts, thresholds, drift, LTV, concentration,
liquidity runways, and tax lots without LLM approximations.
Every function outputs rich evidence metadata for agent citation.
"""

import pandas as pd
import numpy as np
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from src.data_layer import WealthDataRepository, LookThroughDetail

class DeterministicAnalytics:
    def __init__(self, repo: Optional[WealthDataRepository] = None):
        self.repo = repo or WealthDataRepository.get_instance()

    def resolve_look_through(self, instrument_id: str) -> Dict[str, Any]:
        """Resolves structured product look-through underlying details."""
        detail = self.repo.look_through_map.get(instrument_id)
        if not detail:
            return {
                "instrument_id": instrument_id,
                "is_structured": False,
                "underlying_references": [instrument_id],
                "effective_asset_class": "Unknown",
                "effective_sector": "Diversified",
                "effective_region": "Global",
                "notes": ""
            }
        return {
            "instrument_id": detail.instrument_id,
            "instrument_name": detail.instrument_name,
            "is_structured": detail.is_structured,
            "underlying_type": detail.underlying_type,
            "underlying_references": detail.underlying_references,
            "raw_reference": detail.raw_reference,
            "effective_asset_class": detail.effective_asset_class,
            "effective_sector": detail.effective_sector,
            "effective_region": detail.effective_region,
            "notes": detail.leverage_or_barrier_notes
        }

    def compute_drift(self, portfolio_id: str, snapshot_date: str) -> Dict[str, Any]:
        """
        Computes asset class allocation drift against mandate bands.
        Returns actual % vs min/target/max bands, breach severity, and required rebalancing.
        """
        portfolio = self.repo.get_portfolio(portfolio_id)
        if not portfolio:
            return {"error": f"Portfolio {portfolio_id} not found"}

        mandate_code = portfolio["mandate_code"]
        mandate_rows = self.repo.get_mandate_for_code(mandate_code)
        mandate_dict = {m["asset_class"]: m for m in mandate_rows}

        holdings = self.repo.get_holdings(portfolio_id, snapshot_date)
        if not holdings:
            return {"portfolio_id": portfolio_id, "snapshot_date": snapshot_date, "total_value_usd": 0, "allocations": []}

        total_value_usd = sum(h["market_value_usd"] for h in holdings)
        total_value_base = sum(h["market_value_base"] for h in holdings)

        # Aggregate by asset class
        ac_map = {}
        for h in holdings:
            ac = h.get("asset_class", "Other")
            ac_map[ac] = ac_map.get(ac, 0.0) + h["market_value_usd"]

        allocations = []
        breaches = []
        warnings = []

        for ac, m_info in mandate_dict.items():
            actual_usd = ac_map.get(ac, 0.0)
            actual_pct = (actual_usd / total_value_usd * 100.0) if total_value_usd > 0 else 0.0
            min_pct = float(m_info["min_pct"])
            target_pct = float(m_info["target_pct"])
            max_pct = float(m_info["max_pct"])
            
            drift_pct = actual_pct - target_pct
            status = "in_band"
            breach_amount_usd = 0.0
            rounded_actual = round(actual_pct, 2)

            if rounded_actual > max_pct:
                status = "upper_breach"
                breach_amount_usd = (actual_pct - max_pct) / 100.0 * total_value_usd
                breaches.append({
                    "asset_class": ac,
                    "type": "upper_breach",
                    "actual_pct": rounded_actual,
                    "band_max_pct": max_pct,
                    "excess_pct": round(actual_pct - max_pct, 2),
                    "trim_to_target_usd": round((actual_pct - target_pct) / 100.0 * total_value_usd, 2)
                })
            elif rounded_actual == max_pct:
                status = "warning"
                warnings.append({
                    "asset_class": ac,
                    "type": "warning_at_max",
                    "actual_pct": rounded_actual,
                    "band_max_pct": max_pct,
                    "message": f"{ac} is at the mandate maximum limit ({max_pct:.1f}%)."
                })
            elif rounded_actual < min_pct:
                status = "lower_breach"
                breach_amount_usd = (min_pct - actual_pct) / 100.0 * total_value_usd
                breaches.append({
                    "asset_class": ac,
                    "type": "lower_breach",
                    "actual_pct": rounded_actual,
                    "band_min_pct": min_pct,
                    "deficit_pct": round(min_pct - actual_pct, 2),
                    "add_to_target_usd": round((target_pct - actual_pct) / 100.0 * total_value_usd, 2)
                })
            elif rounded_actual == min_pct and min_pct > 0.0:
                status = "warning"
                warnings.append({
                    "asset_class": ac,
                    "type": "warning_at_min",
                    "actual_pct": rounded_actual,
                    "band_min_pct": min_pct,
                    "message": f"{ac} is at the mandate minimum limit ({min_pct:.1f}%)."
                })

            allocations.append({
                "asset_class": ac,
                "actual_usd": round(actual_usd, 2),
                "actual_pct": rounded_actual,
                "min_pct": min_pct,
                "target_pct": target_pct,
                "max_pct": max_pct,
                "drift_pct": round(drift_pct, 2),
                "status": status,
                "breach_amount_usd": round(breach_amount_usd, 2)
            })

        return {
            "portfolio_id": portfolio_id,
            "portfolio_name": portfolio["portfolio_name"],
            "mandate_code": mandate_code,
            "mandate_name": portfolio["mandate_name"],
            "snapshot_date": snapshot_date,
            "total_value_usd": round(total_value_usd, 2),
            "total_value_base": round(total_value_base, 2),
            "currency": portfolio["base_currency"],
            "allocations": allocations,
            "has_breaches": len(breaches) > 0,
            "breaches": breaches,
            "has_warnings": len(warnings) > 0,
            "warnings": warnings,
            "evidence_metadata": {
                "source_function": "compute_drift",
                "as_of_date": snapshot_date,
                "rows_evaluated": len(holdings),
                "mandate_checked": mandate_code
            }
        }

    def compute_concentration(self, portfolio_id: str, snapshot_date: str) -> Dict[str, Any]:
        """
        Computes single-name, sector, and look-through concentration limits.
        Resolves underlying exposures for structured products.
        """
        portfolio = self.repo.get_portfolio(portfolio_id)
        if not portfolio:
            return {"error": f"Portfolio {portfolio_id} not found"}

        mandate_rows = self.repo.get_mandate_for_code(portfolio["mandate_code"])
        max_single_pos_pct = 10.0
        if mandate_rows and "max_single_position_pct" in mandate_rows[0]:
            max_single_pos_pct = float(mandate_rows[0]["max_single_position_pct"])

        holdings = self.repo.get_holdings(portfolio_id, snapshot_date)
        if not holdings:
            return {"portfolio_id": portfolio_id, "snapshot_date": snapshot_date, "positions": [], "look_through_exposures": []}

        total_value_usd = sum(h["market_value_usd"] for h in holdings)

        # Single position concentration
        positions = []
        single_breaches = []
        
        # Look-through aggregation by underlying entity
        look_through_totals: Dict[str, float] = {}

        for h in holdings:
            iid = h["instrument_id"]
            iname = h["instrument_name"]
            val_usd = h["market_value_usd"]
            weight_pct = (val_usd / total_value_usd * 100.0) if total_value_usd > 0 else 0.0
            
            is_breach = weight_pct > max_single_pos_pct
            if is_breach:
                single_breaches.append({
                    "instrument_id": iid,
                    "instrument_name": iname,
                    "weight_pct": round(weight_pct, 2),
                    "limit_pct": max_single_pos_pct,
                    "excess_pct": round(weight_pct - max_single_pos_pct, 2),
                    "excess_usd": round((weight_pct - max_single_pos_pct) / 100.0 * total_value_usd, 2)
                })

            lt_info = self.resolve_look_through(iid)
            positions.append({
                "instrument_id": iid,
                "instrument_name": iname,
                "asset_class": h.get("asset_class"),
                "sector": h.get("sector"),
                "market_value_usd": round(val_usd, 2),
                "weight_pct": round(weight_pct, 2),
                "is_breach": is_breach,
                "is_structured": lt_info["is_structured"],
                "look_through": lt_info
            })

            # Map to underlying references
            for u_ref in lt_info["underlying_references"]:
                look_through_totals[u_ref] = look_through_totals.get(u_ref, 0.0) + (val_usd / len(lt_info["underlying_references"]))

        # Sort positions by weight desc
        positions = sorted(positions, key=lambda x: x["weight_pct"], reverse=True)

        lt_exposures = [
            {
                "underlying": u,
                "value_usd": round(amt, 2),
                "weight_pct": round((amt / total_value_usd * 100.0) if total_value_usd > 0 else 0.0, 2)
            }
            for u, amt in sorted(look_through_totals.items(), key=lambda item: item[1], reverse=True)
        ]

        return {
            "portfolio_id": portfolio_id,
            "snapshot_date": snapshot_date,
            "total_value_usd": round(total_value_usd, 2),
            "max_single_position_pct": max_single_pos_pct,
            "positions": positions,
            "single_breaches": single_breaches,
            "look_through_exposures": lt_exposures[:10],
            "has_breaches": len(single_breaches) > 0,
            "evidence_metadata": {
                "source_function": "compute_concentration",
                "as_of_date": snapshot_date,
                "positions_analyzed": len(positions),
                "max_limit": max_single_pos_pct
            }
        }

    def compute_cross_portfolio_concentration(self, client_id: str, snapshot_date: str, max_single_pos_pct: float = 10.0) -> Dict[str, Any]:
        """
        Computes consolidated whole-client concentration across ALL portfolios and look-through structured entities.
        Identifies invisible concentrations where an underlying issuer is held across multiple sleeves
        and breaches the risk limit when aggregated.
        """
        all_holdings = self.repo.get_all_holdings_for_client(client_id, snapshot_date)
        if not all_holdings:
            return {"client_id": client_id, "snapshot_date": snapshot_date, "aggregated_breaches": [], "underlying_exposures": []}

        total_wealth_usd = sum(h["market_value_usd"] for h in all_holdings)
        underlying_totals: Dict[str, Dict[str, Any]] = {}

        for h in all_holdings:
            iid = h["instrument_id"]
            iname = h["instrument_name"]
            val_usd = h["market_value_usd"]
            pf_id = h["portfolio_id"]

            lt_info = self.resolve_look_through(iid)
            refs = lt_info.get("underlying_references", [iname])
            split_val = val_usd / max(1, len(refs))

            for ref in refs:
                if ref not in underlying_totals:
                    underlying_totals[ref] = {
                        "name": ref,
                        "total_value_usd": 0.0,
                        "portfolios_involved": set(),
                        "is_structured": lt_info.get("is_structured", False),
                        "instruments": set()
                    }
                underlying_totals[ref]["total_value_usd"] += split_val
                underlying_totals[ref]["portfolios_involved"].add(pf_id)
                underlying_totals[ref]["instruments"].add(iname)

        aggregated_breaches = []
        for ref, data in underlying_totals.items():
            tot_usd = data["total_value_usd"]
            weight_pct = (tot_usd / total_wealth_usd * 100.0) if total_wealth_usd > 0 else 0.0

            if weight_pct > max_single_pos_pct:
                pfs = sorted(list(data["portfolios_involved"]))
                aggregated_breaches.append({
                    "underlying_name": ref,
                    "total_value_usd": round(tot_usd, 2),
                    "weight_pct": round(weight_pct, 2),
                    "limit_pct": max_single_pos_pct,
                    "excess_usd": round((weight_pct - max_single_pos_pct) / 100.0 * total_wealth_usd, 2),
                    "portfolios_involved": pfs,
                    "is_multi_portfolio": len(pfs) > 1,
                    "instruments": sorted(list(data["instruments"]))
                })

        all_exposures = []
        for ref, data in underlying_totals.items():
            tot_usd = data["total_value_usd"]
            weight_pct = (tot_usd / total_wealth_usd * 100.0) if total_wealth_usd > 0 else 0.0
            pfs = sorted(list(data["portfolios_involved"]))
            all_exposures.append({
                "underlying_name": ref,
                "total_value_usd": round(tot_usd, 2),
                "weight_pct": round(weight_pct, 2),
                "portfolios_involved": pfs,
                "is_multi_portfolio": len(pfs) > 1,
                "is_structured": data["is_structured"],
                "instruments": sorted(list(data["instruments"]))
            })

        all_exposures = sorted(all_exposures, key=lambda x: x["total_value_usd"], reverse=True)

        return {
            "client_id": client_id,
            "snapshot_date": snapshot_date,
            "total_wealth_usd": round(total_wealth_usd, 2),
            "max_single_position_pct": max_single_pos_pct,
            "aggregated_breaches": aggregated_breaches,
            "has_cross_portfolio_breaches": any(b["is_multi_portfolio"] for b in aggregated_breaches),
            "underlying_exposures": all_exposures
        }

    def compute_ltv(self, client_id: str, snapshot_date: str) -> Dict[str, Any]:
        """
        Computes credit facility LTV, headroom, margin call proximity, and multi-snapshot trend.
        """
        facilities = self.repo.get_credit_facilities_for_client(client_id)
        if not facilities:
            return {
                "client_id": client_id,
                "has_facility": False,
                "facilities": [],
                "aggregate_ltv_pct": 0.0,
                "margin_call_warning": False
            }

        parsed_facilities = []
        margin_call_warnings = []

        for f in facilities:
            fid = f["facility_id"]
            limit = float(f["credit_limit"])
            margin_call_ltv = float(f["margin_call_ltv_pct"])
            
            drawn_col = f"drawn_{snapshot_date}"
            collateral_col = f"collateral_market_value_{snapshot_date}"
            lending_val_col = f"lending_value_{snapshot_date}"
            ltv_col = f"ltv_pct_{snapshot_date}"
            headroom_col = f"headroom_{snapshot_date}"

            drawn = float(f.get(drawn_col, 0.0))
            collateral_mv = float(f.get(collateral_col, 0.0))
            lending_val = float(f.get(lending_val_col, 0.0))
            current_ltv = float(f.get(ltv_col, 0.0))
            headroom = float(f.get(headroom_col, 0.0))

            # Proximity to margin call
            buffer_pct = margin_call_ltv - current_ltv
            is_critical = buffer_pct <= 2.0
            is_warning = buffer_pct <= 5.0

            if is_warning:
                margin_call_warnings.append({
                    "facility_id": fid,
                    "current_ltv_pct": round(current_ltv, 2),
                    "margin_call_threshold_pct": margin_call_ltv,
                    "buffer_pct": round(buffer_pct, 2),
                    "headroom_amount": round(headroom, 2),
                    "is_critical": is_critical
                })

            # Historical LTV progression
            history = []
            for dt in self.repo.get_snapshot_dates():
                history.append({
                    "date": dt,
                    "ltv_pct": float(f.get(f"ltv_pct_{dt}", 0.0)),
                    "drawn": float(f.get(f"drawn_{dt}", 0.0)),
                    "headroom": float(f.get(f"headroom_{dt}", 0.0)),
                    "collateral_value": float(f.get(f"collateral_market_value_{dt}", 0.0))
                })

            parsed_facilities.append({
                "facility_id": fid,
                "facility_type": f["facility_type"],
                "facility_ccy": f["facility_ccy"],
                "credit_limit": limit,
                "margin_call_ltv_pct": margin_call_ltv,
                "interest_rate_pct": float(f.get("interest_rate_pct", 0.0)),
                "drawn": round(drawn, 2),
                "collateral_market_value": round(collateral_mv, 2),
                "lending_value": round(lending_val, 2),
                "current_ltv_pct": round(current_ltv, 2),
                "headroom": round(headroom, 2),
                "buffer_to_margin_call_pct": round(buffer_pct, 2),
                "is_critical": is_critical,
                "is_warning": is_warning,
                "history": history
            })

        return {
            "client_id": client_id,
            "has_facility": True,
            "snapshot_date": snapshot_date,
            "facilities": parsed_facilities,
            "margin_call_warnings": margin_call_warnings,
            "has_critical_warning": any(w["is_critical"] for w in margin_call_warnings),
            "evidence_metadata": {
                "source_function": "compute_ltv",
                "as_of_date": snapshot_date,
                "facilities_count": len(facilities)
            }
        }

    def compute_liquidity_runway(self, client_id: str, snapshot_date: str = "2026-08-26") -> Dict[str, Any]:
        """
        Computes months of cash runway and shortfall risk by reconciling:
        - Available Cash & Money Market holdings
        - Unutilized credit facility headroom
        - Uncalled private equity/debt capital commitments
        - Stated planned cash needs
        """
        client = self.repo.get_client(client_id)
        if not client:
            return {"error": f"Client {client_id} not found"}

        # 1. Total available cash
        holdings = self.repo.get_all_holdings_for_client(client_id, snapshot_date)
        cash_holdings = [h for h in holdings if "cash" in str(h.get("asset_class", "")).lower() or "money market" in str(h.get("sub_asset_class", "")).lower()]
        total_cash_usd = sum(h["market_value_usd"] for h in cash_holdings)

        # 2. Credit facility headroom
        ltv_data = self.compute_ltv(client_id, snapshot_date)
        total_credit_headroom = sum(f["headroom"] for f in ltv_data.get("facilities", []))

        total_liquid_pool = total_cash_usd + total_credit_headroom

        # 3. Uncalled commitments
        commitments = self.repo.get_commitments_for_client(client_id)
        total_uncalled_commitments = sum(float(c.get("uncalled", 0)) for c in commitments)

        # 4. Planned cash needs
        cash_needs = self.repo.get_planned_cash_needs_for_client(client_id)
        total_planned_cash_needs = sum(float(n.get("amount", 0)) for n in cash_needs)

        total_outflows_expected = total_uncalled_commitments + total_planned_cash_needs
        net_surplus_deficit = total_liquid_pool - total_outflows_expected
        
        # Calculate coverage ratio
        coverage_ratio = (total_liquid_pool / total_outflows_expected) if total_outflows_expected > 0 else 999.0
        
        has_shortfall = net_surplus_deficit < 0
        urgency = "LOW"
        if has_shortfall:
            urgency = "CRITICAL"
        elif coverage_ratio < 1.3:
            urgency = "HIGH"
        elif coverage_ratio < 2.0:
            urgency = "MEDIUM"

        return {
            "client_id": client_id,
            "snapshot_date": snapshot_date,
            "cash_holdings_usd": round(total_cash_usd, 2),
            "credit_headroom_usd": round(total_credit_headroom, 2),
            "total_liquid_pool_usd": round(total_liquid_pool, 2),
            "uncalled_commitments_usd": round(total_uncalled_commitments, 2),
            "planned_cash_needs_usd": round(total_planned_cash_needs, 2),
            "total_outflows_expected_usd": round(total_outflows_expected, 2),
            "net_surplus_deficit_usd": round(net_surplus_deficit, 2),
            "coverage_ratio": round(coverage_ratio, 2),
            "has_shortfall": has_shortfall,
            "urgency": urgency,
            "commitments_detail": commitments,
            "cash_needs_detail": cash_needs,
            "evidence_metadata": {
                "source_function": "compute_liquidity_runway",
                "as_of_date": snapshot_date,
                "commitments_count": len(commitments),
                "cash_needs_count": len(cash_needs)
            }
        }

    def compute_tax_lots(self, portfolio_id: str, snapshot_date: str = "2026-08-26") -> Dict[str, Any]:
        """
        Computes tax lot gains/losses, harvestable losses, and holding period flags.
        Takes client tax domicile into account.
        """
        portfolio = self.repo.get_portfolio(portfolio_id)
        if not portfolio:
            return {"error": f"Portfolio {portfolio_id} not found"}

        client = self.repo.get_client(portfolio["client_id"])
        tax_domicile = client.get("tax_domicile", "Unknown") if client else "Unknown"

        holdings = self.repo.get_holdings(portfolio_id, snapshot_date)
        txns = self.repo.get_transactions_for_portfolio(portfolio_id)

        tax_lots = []
        harvestable_losses_usd = 0.0
        embedded_gains_usd = 0.0

        for h in holdings:
            pnl_base = float(h.get("unrealised_pnl_base", 0.0))
            pnl_pct = float(h.get("unrealised_pnl_pct", 0.0))
            mv_base = float(h.get("market_value_base", 0.0))
            cost_base = float(h.get("cost_basis_base", 0.0))
            acq_date = str(h.get("acquired_date", ""))

            # Calculate holding days
            holding_days = 0
            is_long_term = True
            if acq_date:
                try:
                    d_acq = datetime.strptime(acq_date, "%Y-%m-%d")
                    d_snap = datetime.strptime(snapshot_date, "%Y-%m-%d")
                    holding_days = (d_snap - d_acq).days
                    is_long_term = holding_days > 365
                except Exception:
                    pass

            is_harvestable = pnl_base < -10000.0  # substantial loss
            if pnl_base < 0:
                harvestable_losses_usd += abs(pnl_base)
            else:
                embedded_gains_usd += pnl_base

            tax_lots.append({
                "instrument_id": h["instrument_id"],
                "instrument_name": h["instrument_name"],
                "asset_class": h.get("asset_class"),
                "acquired_date": acq_date,
                "holding_days": holding_days,
                "is_long_term": is_long_term,
                "market_value_base": round(mv_base, 2),
                "cost_basis_base": round(cost_base, 2),
                "unrealised_pnl_base": round(pnl_base, 2),
                "unrealised_pnl_pct": round(pnl_pct, 2),
                "is_harvestable_loss": is_harvestable
            })

        # Domicile tax implications
        is_zero_cap_gains = tax_domicile in ["Singapore", "Hong Kong", "UAE", "Switzerland (Private)"]
        tax_notes = ""
        if is_zero_cap_gains:
            tax_notes = f"Client domicile ({tax_domicile}) levies 0% capital gains tax on individual investors. Rebalancing generates zero personal tax drag."
        else:
            tax_notes = f"Client domicile ({tax_domicile}) taxes capital gains. Tax loss harvesting can offset short/long term gains."

        return {
            "portfolio_id": portfolio_id,
            "client_id": portfolio["client_id"],
            "tax_domicile": tax_domicile,
            "is_zero_cap_gains": is_zero_cap_gains,
            "tax_notes": tax_notes,
            "snapshot_date": snapshot_date,
            "total_harvestable_losses_usd": round(harvestable_losses_usd, 2),
            "total_embedded_gains_usd": round(embedded_gains_usd, 2),
            "lots": sorted(tax_lots, key=lambda x: x["unrealised_pnl_base"]),
            "evidence_metadata": {
                "source_function": "compute_tax_lots",
                "as_of_date": snapshot_date,
                "lots_count": len(tax_lots),
                "tax_domicile": tax_domicile
            }
        }

    def compute_trend(self, client_id: str, metric: str = "aum") -> Dict[str, Any]:
        """Computes time series across the 5 snapshots."""
        portfolios = self.repo.get_portfolios_for_client(client_id)
        snapshot_dates = self.repo.get_snapshot_dates()
        
        trend_points = []
        for dt in snapshot_dates:
            dt_aum = sum(float(p.get(f"aum_{dt}", 0.0)) for p in portfolios)
            trend_points.append({"date": dt, "aum_base": round(dt_aum, 2)})

        return {
            "client_id": client_id,
            "metric": metric,
            "snapshot_dates": snapshot_dates,
            "trend_points": trend_points
        }

    def compute_portfolio_returns(
        self, 
        client_id: str, 
        snapshot_date: str, 
        portfolio_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Computes exact point-in-time deterministic portfolio returns from baseline (2025-12-31)
        and period-on-period return specific to the selected snapshot date.
        Supports both consolidated client wealth and individual portfolio sleeve attribution.
        """
        snapshot_dates = self.repo.get_snapshot_dates()
        baseline_date = snapshot_dates[0] if snapshot_dates else "2025-12-31"

        # Determine previous snapshot date
        if snapshot_date in snapshot_dates:
            curr_idx = snapshot_dates.index(snapshot_date)
            prev_date = snapshot_dates[curr_idx - 1] if curr_idx > 0 else None
        else:
            prev_date = None

        # Fetch holdings for client (or single portfolio if specified)
        if portfolio_id:
            h_curr = self.repo.get_holdings(portfolio_id, snapshot_date)
            h_base = self.repo.get_holdings(portfolio_id, baseline_date)
            h_prev = self.repo.get_holdings(portfolio_id, prev_date) if prev_date else h_base
        else:
            h_curr = self.repo.get_all_holdings_for_client(client_id, snapshot_date)
            h_base = self.repo.get_all_holdings_for_client(client_id, baseline_date)
            h_prev = self.repo.get_all_holdings_for_client(client_id, prev_date) if prev_date else h_base

        curr_aum_usd = sum(h["market_value_usd"] for h in h_curr)
        base_aum_usd = sum(h["market_value_usd"] for h in h_base)
        prev_aum_usd = sum(h["market_value_usd"] for h in h_prev) if prev_date else base_aum_usd

        curr_aum_base = sum(h["market_value_base"] for h in h_curr)
        base_aum_base = sum(h["market_value_base"] for h in h_base)
        prev_aum_base = sum(h["market_value_base"] for h in h_prev) if prev_date else base_aum_base

        # Cumulative Return (since 2025-12-31 baseline)
        cum_ret_usd = curr_aum_usd - base_aum_usd
        cum_ret_pct = (cum_ret_usd / base_aum_usd * 100.0) if base_aum_usd > 0 else 0.0

        # Period-on-Period Return (vs previous snapshot)
        if prev_date and prev_date != snapshot_date:
            period_ret_usd = curr_aum_usd - prev_aum_usd
            period_ret_pct = (period_ret_usd / prev_aum_usd * 100.0) if prev_aum_usd > 0 else 0.0
            period_label = f"vs {prev_date}"
        else:
            period_ret_usd = 0.0
            period_ret_pct = 0.0
            period_label = "Baseline Inception"

        # Sleeve breakdowns for multi-portfolio clients
        portfolios = self.repo.get_portfolios_for_client(client_id)
        sleeve_returns = []
        for p in portfolios:
            pid = p["portfolio_id"]
            p_curr_h = self.repo.get_holdings(pid, snapshot_date)
            p_base_h = self.repo.get_holdings(pid, baseline_date)
            p_prev_h = self.repo.get_holdings(pid, prev_date) if prev_date else p_base_h

            p_curr_usd = sum(x["market_value_usd"] for x in p_curr_h)
            p_base_usd = sum(x["market_value_usd"] for x in p_base_h)
            p_prev_usd = sum(x["market_value_usd"] for x in p_prev_h) if prev_date else p_base_usd

            p_cum_pct = ((p_curr_usd - p_base_usd) / p_base_usd * 100.0) if p_base_usd > 0 else 0.0
            p_per_pct = ((p_curr_usd - p_prev_usd) / p_prev_usd * 100.0) if (prev_date and p_prev_usd > 0) else 0.0

            sleeve_returns.append({
                "portfolio_id": pid,
                "portfolio_name": p.get("portfolio_name", pid),
                "mandate_code": p.get("mandate_code", "BAL"),
                "base_currency": p.get("base_currency", "USD"),
                "aum_usd": round(p_curr_usd, 2),
                "cum_return_pct": round(p_cum_pct, 2),
                "cum_return_usd": round(p_curr_usd - p_base_usd, 2),
                "period_return_pct": round(p_per_pct, 2),
                "period_return_usd": round(p_curr_usd - p_prev_usd, 2)
            })

        return {
            "client_id": client_id,
            "portfolio_id": portfolio_id,
            "snapshot_date": snapshot_date,
            "baseline_date": baseline_date,
            "previous_snapshot_date": prev_date,
            "period_label": period_label,
            "current_aum_usd": round(curr_aum_usd, 2),
            "baseline_aum_usd": round(base_aum_usd, 2),
            "cumulative_return_usd": round(cum_ret_usd, 2),
            "cumulative_return_pct": round(cum_ret_pct, 2),
            "period_return_usd": round(period_ret_usd, 2),
            "period_return_pct": round(period_ret_pct, 2),
            "current_aum_base": round(curr_aum_base, 2),
            "baseline_aum_base": round(base_aum_base, 2),
            "sleeve_returns": sleeve_returns,
            "evidence_metadata": {
                "source_function": "compute_portfolio_returns",
                "snapshot_date": snapshot_date,
                "baseline_date": baseline_date,
                "previous_snapshot_date": prev_date
            }
        }

    def match_events_to_holdings(
        self, 
        client_id: str, 
        snapshot_date: str = "2026-08-26",
        since_date: Optional[str] = None,
        **kwargs
    ) -> List[Dict[str, Any]]:
        """
        Correlates world events with the client's holdings by region, sector, and transmission channel.
        If since_date is provided (e.g. date of last RM interaction), prioritizes and highlights
        events occurring strictly AFTER since_date up to snapshot_date so the RM focuses on new market developments.
        """
        events = self.repo.get_events()
        holdings = self.repo.get_all_holdings_for_client(client_id, snapshot_date)
        
        matches = []
        for ev in events:
            ev_date = str(ev.get("event_date", ""))
            
            # Strict point-in-time upper bound: omit events occurring in the future relative to snapshot_date
            if snapshot_date and ev_date and ev_date > snapshot_date:
                continue

            # Check if event occurred strictly after last meeting date
            is_post_meeting = True
            if since_date and ev_date and ev_date <= str(since_date):
                is_post_meeting = False

            ev_desc = str(ev.get("description", ""))
            ev_region = str(ev.get("region", ""))
            ev_trans = str(ev.get("primary_transmission", ""))
            ev_sev = str(ev.get("severity", "Medium"))

            affected_holdings = []
            ev_lower = (ev_desc + " " + ev_trans).lower()
            for h in holdings:
                h_sector = str(h.get("sector", "")).lower()
                h_region = str(h.get("region", "")).lower()
                h_name = str(h.get("instrument_name", "")).lower()
                h_asset = str(h.get("asset_class", "")).lower()
                
                is_hit = False
                channel = ""

                if any(k in ev_lower for k in ["gold", "bullion", "precious metal"]):
                    if "gold" in h_name or "gold" in h_sector or "gold" in h_asset or "commodities" in h_asset:
                        is_hit = True
                        channel = "Gold & Precious Metals Exposure"
                elif any(k in ev_lower for k in ["oil", "brent", "crude", "petroleum", "opec", "energy"]):
                    if any(k in h_sector for k in ["energy", "oil", "gas"]) or any(k in h_name for k in ["energy", "oil", "crude"]):
                        is_hit = True
                        channel = "Energy & Commodity Sector Transmission"
                elif any(k in ev_lower for k in ["chip", "semiconductor", "tech", "ai", "software", "hardware"]):
                    if any(k in h_sector for k in ["technology", "semiconductor", "software"]) or any(k in h_name for k in ["tech", "semiconductor"]):
                        is_hit = True
                        channel = "Technology & Semiconductor Sector Transmission"
                elif any(k in ev_lower for k in ["shipping", "freight", "strait", "red sea", "canal", "logistics"]):
                    if any(k in h_sector for k in ["shipping", "transport", "logistics", "industrials"]):
                        is_hit = True
                        channel = "Supply Chain & Shipping Transmission"
                elif any(k in ev_lower for k in ["rate", "central bank", "ecb", "fed", "yield", "rate hike", "rate cut"]):
                    if any(k in h_asset for k in ["fixed income", "bond"]) or any(k in h_sector for k in ["banking", "financials"]):
                        is_hit = True
                        channel = "Interest Rate & Monetary Transmission"
                elif ev_region and ev_region.lower() not in ["global", "world", "all", ""]:
                    if ev_region.lower() in h_region or h_region in ev_region.lower():
                        is_hit = True
                        channel = f"Regional exposure ({h_region.title()})"

                if is_hit:
                    affected_holdings.append({
                        "instrument_id": h["instrument_id"],
                        "instrument_name": h["instrument_name"],
                        "market_value_usd": h["market_value_usd"],
                        "weight_pct": h["weight_pct"],
                        "channel": channel
                    })

            if affected_holdings:
                matches.append({
                    "event_date": ev_date,
                    "event_type": ev.get("event_type"),
                    "region": ev_region,
                    "description": ev_desc,
                    "severity": ev_sev,
                    "transmission": ev_trans,
                    "is_post_meeting": is_post_meeting,
                    "since_date": since_date,
                    "affected_holdings_count": len(affected_holdings),
                    "affected_holdings": affected_holdings[:5],
                    "total_exposed_usd": round(sum(h["market_value_usd"] for h in affected_holdings), 2)
                })

        # If since_date is provided and there are post-meeting events, prioritize them strictly
        post_meeting_matches = [m for m in matches if m["is_post_meeting"]]
        if post_meeting_matches:
            target_matches = post_meeting_matches
        else:
            target_matches = matches

        # Sort by event_date descending (freshest market events first), then by exposed USD descending
        return sorted(target_matches, key=lambda x: (x.get("event_date", ""), x["total_exposed_usd"]), reverse=True)

    def get_rm_notes(self, client_id: str, as_of_date: Optional[str] = None) -> Dict[str, Any]:
        """
        Extracts structured RM notes, standing overrides, family dynamics, and caveats as of snapshot date.
        Tracks the client's last interaction date and channel prior to the snapshot date.
        """
        raw_notes = self.repo.get_rm_notes_for_client(client_id)
        if not raw_notes:
            return {
                "client_id": client_id,
                "has_notes": False,
                "notes": [],
                "standing_overrides": [],
                "preferences": [],
                "last_meeting_date": None,
                "last_meeting_channel": None,
                "last_meeting_summary": None
            }

        # Point-in-time filter: only include notes on or prior to as_of_date
        if as_of_date:
            notes = [n for n in raw_notes if str(n.get("note_date", "")) <= str(as_of_date)]
        else:
            notes = raw_notes

        # Sort chronologically
        notes = sorted(notes, key=lambda x: str(x.get("note_date", "")))

        if not notes:
            return {
                "client_id": client_id,
                "has_notes": False,
                "notes": [],
                "standing_overrides": [],
                "preferences": [],
                "last_meeting_date": None,
                "last_meeting_channel": None,
                "last_meeting_summary": None,
                "future_notes_count": len(raw_notes)
            }

        last_meeting = notes[-1] if notes else None
        last_meeting_date = last_meeting.get("note_date") if last_meeting else None
        last_meeting_channel = last_meeting.get("channel") if last_meeting else None
        last_meeting_summary = last_meeting.get("note") if last_meeting else None

        overrides = []
        preferences = []
        constraint_keywords = [
            "did not want", "does not want", "do not want", "refused", "not tied to", 
            "do not sell", "not sell", "avoid", "at a loss", "loss", "unwilling to sell", 
            "not make any changes", "must hold", "emotional attachment", "dealing restrictions",
            "cannot sell", "closed period", "won't sell", "will not sell", "waiver on file", 
            "suitability waiver", "preserve capital", "firm on retiring", "exclusive", 
            "legacy shareholding", "sentimental reasons", "gated", "without touching capital"
        ]
        preference_keywords = [
            "interested in", "looking at", "prefers", "preference", "priority", "positive on", 
            "optimistic", "buying opportunity", "more of", "aggressive", "safe and boring", 
            "sustainability", "property purchase", "foundation", "tuition", "deployment", 
            "yield ideas", "redevelopment", "family office", "succession"
        ]

        for n in notes:
            text = n.get("note", "")
            text_lower = text.lower()
            
            # Detect standing constraints & overrides
            if any(kw in text_lower for kw in constraint_keywords):
                overrides.append({
                    "note_id": n.get("note_id"),
                    "date": n.get("note_date"),
                    "rm_name": n.get("rm_name"),
                    "type": "hard_constraint",
                    "summary": text
                })
            elif any(kw in text_lower for kw in preference_keywords):
                preferences.append({
                    "note_id": n.get("note_id"),
                    "date": n.get("note_date"),
                    "rm_name": n.get("rm_name"),
                    "type": "client_preference",
                    "summary": text
                })

        return {
            "client_id": client_id,
            "as_of_date": as_of_date,
            "has_notes": len(notes) > 0,
            "raw_notes_count": len(notes),
            "total_all_time_notes": len(raw_notes),
            "last_meeting_date": last_meeting_date,
            "last_meeting_channel": last_meeting_channel,
            "last_meeting_summary": last_meeting_summary,
            "notes": notes,
            "standing_overrides": overrides,
            "preferences": preferences,
            "evidence_metadata": {
                "source_function": "get_rm_notes",
                "as_of_date": as_of_date or "latest",
                "notes_count": len(notes)
            }
        }

    def get_all_book_breaches(self, snapshot_date: str) -> List[Dict[str, Any]]:
        """Aggregates all mandate drift and single concentration breaches across the entire 20-client book."""
        breaches = []
        clients = self.repo.get_all_clients()
        for c in clients:
            cid = c["client_id"]
            cname = c["client_name"]
            pfs = self.repo.get_portfolios_for_client(cid)
            for p in pfs:
                pid = p["portfolio_id"]
                pname = p["portfolio_name"]
                mcode = p["mandate_code"]
                
                # 1. Mandate SAA Drift Breaches
                drift = self.compute_drift(pid, snapshot_date)
                for b in drift.get("breaches", []):
                    b_type = b["type"]
                    type_label = "Upper Breach (Overweight)" if b_type == "upper_breach" else "Lower Breach (Underweight)"
                    action_txt = f"Trim USD {b['trim_to_target_usd']:,.0f}" if b_type == "upper_breach" else f"Add USD {b['add_to_target_usd']:,.0f}"
                    breaches.append({
                        "client_id": cid,
                        "client_name": cname,
                        "portfolio_id": pid,
                        "portfolio_name": pname,
                        "mandate_code": mcode,
                        "category": "Asset Class Drift",
                        "item_name": b["asset_class"],
                        "breach_type": type_label,
                        "actual_pct": b["actual_pct"],
                        "band_limit": f"Max {b.get('band_max_pct', '-')}%" if b_type == "upper_breach" else f"Min {b.get('band_min_pct', '-')}%",
                        "action_usd": action_txt,
                        "impact_usd": b.get("trim_to_target_usd", b.get("add_to_target_usd", 0.0))
                    })
                
                # 2. Single Position / Concentration Breaches
                conc = self.compute_concentration(pid, snapshot_date)
                for cb in conc.get("single_breaches", []):
                    breaches.append({
                        "client_id": cid,
                        "client_name": cname,
                        "portfolio_id": pid,
                        "portfolio_name": pname,
                        "mandate_code": mcode,
                        "category": "Concentration Limit",
                        "item_name": cb["instrument_name"],
                        "breach_type": f"Single Position > {cb['limit_pct']:.1f}%",
                        "actual_pct": cb["weight_pct"],
                        "band_limit": f"Cap {cb['limit_pct']:.1f}%",
                        "action_usd": f"De-risk USD {cb['excess_usd']:,.0f}",
                        "impact_usd": cb["excess_usd"]
                    })
        return sorted(breaches, key=lambda x: x["impact_usd"], reverse=True)

    def get_all_book_ltv_alerts(self, snapshot_date: str) -> List[Dict[str, Any]]:
        """Aggregates all Lombard credit facility LTV warnings and margin call risks across the book."""
        alerts = []
        clients = self.repo.get_all_clients()
        for c in clients:
            cid = c["client_id"]
            cname = c["client_name"]
            ltv_data = self.compute_ltv(cid, snapshot_date)
            for fac in ltv_data.get("facilities", []):
                if fac.get("is_warning") or fac.get("is_critical"):
                    alerts.append({
                        "client_id": cid,
                        "client_name": cname,
                        "facility_id": fac["facility_id"],
                        "facility_type": fac.get("facility_type", "Lombard Facility"),
                        "currency": fac.get("facility_ccy", "USD"),
                        "drawn_loan_usd": fac.get("drawn", 0.0),
                        "collateral_value_usd": fac.get("collateral_market_value", 0.0),
                        "current_ltv_pct": fac.get("current_ltv_pct", 0.0),
                        "margin_call_pct": fac.get("margin_call_ltv_pct", 0.0),
                        "buffer_pct": fac.get("buffer_to_margin_call_pct", 0.0),
                        "headroom_usd": fac.get("headroom", 0.0),
                        "severity": "🚨 CRITICAL (<2% Buffer)" if fac.get("is_critical") else "⚠️ WARNING (<5% Buffer)"
                    })
        return sorted(alerts, key=lambda x: x["buffer_pct"])

    def get_all_book_liquidity_deficits(self, snapshot_date: str) -> List[Dict[str, Any]]:
        """Aggregates all liquidity deficits, uncalled commitments, and planned cash milestones across the book."""
        records = []
        clients = self.repo.get_all_clients()
        for c in clients:
            cid = c["client_id"]
            cname = c["client_name"]
            liq = self.compute_liquidity_runway(cid, snapshot_date)
            
            # Format primary obligation summary
            obligations = []
            for comm in liq.get("commitments_detail", []):
                fund = comm.get("fund_name", "PE Fund")
                uncalled = float(comm.get("uncalled", 0))
                if uncalled > 0:
                    obligations.append(f"{fund}: ${uncalled/1e6:,.1f}M uncalled")
            for need in liq.get("cash_needs_detail", []):
                purpose = need.get("purpose", "Cash Need")
                amt = float(need.get("amount", 0))
                date_req = need.get("target_date", need.get("required_by", "Upcoming"))
                obligations.append(f"{purpose} ({date_req}): ${amt/1e6:,.1f}M")
            
            obligation_summary = " • ".join(obligations) if obligations else "No immediate milestone obligations"

            # Severity label
            if liq["has_shortfall"]:
                severity = "🚨 SHORTFALL (Deficit)"
            elif liq["coverage_ratio"] < 1.3:
                severity = "⚠️ TIGHT BUFFER (<1.3x)"
            elif liq["coverage_ratio"] < 2.0:
                severity = "🟡 WATCHLIST (<2.0x)"
            else:
                severity = "✅ ADEQUATE (>2.0x)"

            if liq["total_outflows_expected_usd"] > 0 or liq["has_shortfall"]:
                records.append({
                    "client_id": cid,
                    "client_name": cname,
                    "cash_holdings_usd": liq["cash_holdings_usd"],
                    "credit_headroom_usd": liq["credit_headroom_usd"],
                    "total_liquid_pool_usd": liq["total_liquid_pool_usd"],
                    "uncalled_commitments_usd": liq["uncalled_commitments_usd"],
                    "planned_cash_needs_usd": liq["planned_cash_needs_usd"],
                    "total_outflows_expected_usd": liq["total_outflows_expected_usd"],
                    "net_surplus_deficit_usd": liq["net_surplus_deficit_usd"],
                    "coverage_ratio": liq["coverage_ratio"],
                    "has_shortfall": liq["has_shortfall"],
                    "severity": severity,
                    "urgency": liq["urgency"],
                    "obligation_summary": obligation_summary,
                    "commitments_count": len(liq.get("commitments_detail", [])),
                    "cash_needs_count": len(liq.get("cash_needs_detail", []))
                })
        # Sort by deficit ascending (most severe negative deficit first, then lowest coverage ratio)
        return sorted(records, key=lambda x: (0 if x["has_shortfall"] else 1, x["net_surplus_deficit_usd"], x["coverage_ratio"]))
