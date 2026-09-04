"""
Unit tests for deterministic analytics layer
Verifies:
1. Multi-portfolio isolation (CL-0001, CL-0002, CL-0017)
2. Structured product look-through resolution (SYN-SP-0501 to 0506)
3. Mandate drift and concentration calculation
4. Credit facility LTV and headroom
5. Liquidity runway and uncalled commitments
"""

import unittest
from src.data_layer import WealthDataRepository
from src.deterministic_analytics import DeterministicAnalytics

class TestDeterministicAnalytics(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.repo = WealthDataRepository.get_instance()
        cls.analytics = DeterministicAnalytics(cls.repo)

    def test_multi_portfolio_isolation(self):
        """Verify client -> portfolios -> holdings hierarchy is preserved."""
        pfs = self.repo.get_portfolios_for_client("CL-0001")
        self.assertEqual(len(pfs), 2, "CL-0001 must have exactly 2 distinct portfolios")
        
        # Check drift computed separately for PF-0001 and PF-0002
        drift_1 = self.analytics.compute_drift("PF-0001", "2026-08-26")
        drift_2 = self.analytics.compute_drift("PF-0002", "2026-08-26")
        
        self.assertNotEqual(drift_1["total_value_usd"], drift_2["total_value_usd"])
        self.assertEqual(drift_1["portfolio_id"], "PF-0001")
        self.assertEqual(drift_2["portfolio_id"], "PF-0002")

    def test_structured_product_look_through(self):
        """Verify structured products resolve to their underlying components."""
        lt_sp1 = self.analytics.resolve_look_through("SYN-SP-0501")
        self.assertTrue(lt_sp1["is_structured"])
        self.assertEqual(lt_sp1["underlying_type"], "worst_of_basket")
        self.assertGreaterEqual(len(lt_sp1["underlying_references"]), 1)

        lt_sp3 = self.analytics.resolve_look_through("SYN-SP-0503")
        self.assertTrue(lt_sp3["is_structured"])
        self.assertEqual(lt_sp3["underlying_type"], "accumulator")

    def test_credit_facility_ltv_warning(self):
        """Verify credit facility LTV and margin call warning on CL-0002."""
        ltv_cl2 = self.analytics.compute_ltv("CL-0002", "2026-08-26")
        self.assertTrue(ltv_cl2["has_facility"])
        self.assertGreater(len(ltv_cl2["facilities"]), 0)
        
        fac = ltv_cl2["facilities"][0]
        self.assertAlmostEqual(fac["current_ltv_pct"], 73.71, places=1)
        self.assertTrue(fac["is_warning"], "LTV of 73.71% against 75% margin call should trigger warning")

    def test_liquidity_runway(self):
        """Verify liquidity runway computation on commitment client CL-0017."""
        runway = self.analytics.compute_liquidity_runway("CL-0017", "2026-08-26")
        self.assertIn("uncalled_commitments_usd", runway)
        self.assertGreater(runway["uncalled_commitments_usd"], 0)

    def test_all_20_clients_compute(self):
        """Ensure all 20 clients can be processed without runtime errors."""
        clients = self.repo.get_all_clients()
        self.assertEqual(len(clients), 20)
        for c in clients:
            cid = c["client_id"]
            pfs = self.repo.get_portfolios_for_client(cid)
            for p in pfs:
                drift = self.analytics.compute_drift(p["portfolio_id"], "2026-08-26")
                self.assertIn("allocations", drift)
                conc = self.analytics.compute_concentration(p["portfolio_id"], "2026-08-26")
                self.assertIn("positions", conc)
            
            runway = self.analytics.compute_liquidity_runway(cid, "2026-08-26")
            self.assertIn("coverage_ratio", runway)

    def test_boundary_drift_warning(self):
        """Verify that when actual allocation equals the min mandate band (e.g. 2.0% on BALG 2.0%), it triggers a warning instead of a breach alert."""
        drift = self.analytics.compute_drift("PF-0002", "2026-03-31")
        # Cash is at 2.0% and min_pct is 2.0%
        cash_alloc = next((a for a in drift["allocations"] if "Cash" in a["asset_class"]), None)
        self.assertIsNotNone(cash_alloc)
        self.assertEqual(cash_alloc["actual_pct"], 2.0)
        self.assertEqual(cash_alloc["status"], "warning")
        
        # Verify it is in warnings, not in breaches
        cash_breach = next((b for b in drift["breaches"] if "Cash" in b["asset_class"]), None)
        self.assertIsNone(cash_breach, "Cash at 2.0% with min 2.0% should NOT trigger a breach alert")
        
    def test_comingling_opportunity_detection(self):
        """Verify that orchestrator discovers multi-action comingling synergies (Rebalance + Tax + Cash + Milestone) on CL-0001."""
        from src.orchestrator import ClientOrchestrator
        orch = ClientOrchestrator(self.analytics)
        result = orch.run_client("CL-0001", "2026-03-31")
        self.assertIn("comingling_opportunities", result)
        self.assertGreaterEqual(len(result["comingling_opportunities"]), 1)
        
        pkg = result["comingling_opportunities"][0]
        self.assertEqual(pkg["client_id"], "CL-0001")
        self.assertGreaterEqual(len(pkg["clubbed_rec_ids"]), 2)
    def test_book_wide_breaches_and_ltv_alerts(self):
        """Verify that get_all_book_breaches and get_all_book_ltv_alerts return aggregated data across the book."""
        breaches = self.analytics.get_all_book_breaches("2026-03-31")
        self.assertGreater(len(breaches), 0)
        first_b = breaches[0]
        self.assertIn("client_id", first_b)
        self.assertIn("portfolio_id", first_b)
        self.assertIn("breach_type", first_b)
        self.assertIn("action_usd", first_b)

        ltv_alerts = self.analytics.get_all_book_ltv_alerts("2026-03-31")
        self.assertGreaterEqual(len(ltv_alerts), 1)
        first_ltv = ltv_alerts[0]
        self.assertIn("client_id", first_ltv)
        self.assertIn("facility_id", first_ltv)
        self.assertIn("current_ltv_pct", first_ltv)
        self.assertIn("buffer_pct", first_ltv)

        # Verify Book-Wide Liquidity Deficits Drilldown
        liq_deficits = self.analytics.get_all_book_liquidity_deficits("2026-03-31")
        self.assertGreaterEqual(len(liq_deficits), 1)
        first_liq = liq_deficits[0]
        self.assertIn("client_id", first_liq)
        self.assertIn("total_liquid_pool_usd", first_liq)
        self.assertIn("total_outflows_expected_usd", first_liq)
        self.assertIn("net_surplus_deficit_usd", first_liq)
        self.assertIn("coverage_ratio", first_liq)
        self.assertIn("obligation_summary", first_liq)

    def test_temporal_last_meeting_event_filtering(self):
        """Verify that the orchestrator and analytics layer filter market shock events post-last-meeting."""
        from src.orchestrator import ClientOrchestrator

        # 1. Verify RM notes extraction returns last meeting date as of snapshot date
        notes_info = self.analytics.get_rm_notes("CL-0001", as_of_date="2026-08-26")
        self.assertEqual(notes_info["last_meeting_date"], "2026-04-14")
        self.assertEqual(notes_info["last_meeting_channel"], "Call")

        # 2. Verify match_events_to_holdings excludes events on or prior to 2026-04-14
        matches = self.analytics.match_events_to_holdings("CL-0001", snapshot_date="2026-08-26", since_date="2026-04-14")
        self.assertGreater(len(matches), 0)
        for m in matches:
            self.assertGreater(m["event_date"], "2026-04-14", f"Event {m['event_date']} occurred before or on last meeting date 2026-04-14")
            self.assertLessEqual(m["event_date"], "2026-08-26", f"Event {m['event_date']} occurred after snapshot date 2026-08-26")

        # 3. Verify Market recommendations generated by Orchestrator only reference post-meeting events
        orch = ClientOrchestrator(self.analytics)
        client_run = orch.run_client("CL-0001", snapshot_date="2026-08-26")
        market_recs = [r for r in client_run["recommendations"] if r["agent"] == "market"]
        self.assertGreater(len(market_recs), 0)
        for r in market_recs:
            self.assertNotIn("2026-01-26", r["headline"])
            self.assertNotIn("2026-01-28", r["headline"])

if __name__ == "__main__":
    unittest.main()

