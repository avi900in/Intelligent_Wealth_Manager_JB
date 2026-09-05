"""
Unit Tests for LLM Master Orchestrator & Cross-Specialist Optimization Engine
"""

import pytest
from src.data_layer import WealthDataRepository
from src.deterministic_analytics import DeterministicAnalytics
from src.orchestrator import ClientOrchestrator, BookPrioritizer

@pytest.fixture
def orchestrator():
    repo = WealthDataRepository.get_instance()
    analytics = DeterministicAnalytics(repo)
    return ClientOrchestrator(analytics)

def test_orchestrator_returns_required_structure(orchestrator):
    result = orchestrator.run_client("CL-0001", "2026-08-26")
    
    assert "client_id" in result
    assert result["client_id"] == "CL-0001"
    assert "recommendations" in result
    assert "conflicts" in result
    assert "comingling_opportunities" in result
    assert "cross_specialist_optimizations" in result
    assert "compliance_flags" in result
    assert "client_brief" in result
    assert "urgency_score" in result
    assert "urgency_breakdown" in result
    assert isinstance(result["recommendations"], list)
    assert isinstance(result["cross_specialist_optimizations"], list)

def test_cross_specialist_optimizations_discovery(orchestrator):
    result = orchestrator.run_client("CL-0001", "2026-08-26")
    opts = result["cross_specialist_optimizations"]
    assert len(opts) > 0
    
    for opt in opts:
        assert "id" in opt
        assert "title" in opt
        assert "optimization_type" in opt
        assert "participating_agents" in opt
        assert "description" in opt
        assert "strategic_rationale" in opt
        assert "expected_alpha_or_saving" in opt
        assert "implementation_steps" in opt
        assert isinstance(opt["implementation_steps"], list)

def test_cl0007_orchestrator_deduplication_and_comingling(orchestrator):
    result = orchestrator.run_client("CL-0007", "2026-08-26")
    recs = result["recommendations"]
    comingling = result["comingling_opportunities"]
    
    # Check that comingling package exists and includes concentration + rebalance
    assert len(comingling) > 0
    pkg = comingling[0]
    assert "Commodities" in pkg["title"] or "Global Developed Equity" in pkg["title"]
    
    # Verify no duplicate market recommendation on Brent crude / commodities
    mkt_recs = [r for r in recs if r.get("agent") == "market"]
    for m in mkt_recs:
        assert "brent" not in m["headline"].lower()

def test_all_20_clients_run_orchestrator(orchestrator):
    repo = WealthDataRepository.get_instance()
    clients = repo.get_all_clients()
    assert len(clients) == 20
    
    for c in clients:
        cid = c["client_id"]
        res = orchestrator.run_client(cid, "2026-08-26")
        assert res["client_id"] == cid
        assert res["urgency_score"] >= 0.0
        assert res["urgency_score"] <= 100.0
        assert isinstance(res["cross_specialist_optimizations"], list)
