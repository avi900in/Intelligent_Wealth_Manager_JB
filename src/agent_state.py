"""
LangGraph Multi-Agent State and Recommendation Contract (§6)
Defines typed dictionaries and models for agent pipeline data exchange.
"""

from typing import TypedDict, List, Dict, Any, Optional
from pydantic import BaseModel, Field

class EvidenceItem(BaseModel):
    source_function: str
    detail: str
    as_of_date: str
    threshold_or_band: Optional[str] = None
    raw_metric_value: Optional[Any] = None

class Recommendation(BaseModel):
    id: str
    client_id: str
    portfolio_id: Optional[str] = None
    portfolio_name: Optional[str] = None
    agent: str  # rebalancing | tax | life_event | liquidity | market | rm_notes | orchestrator
    priority: str  # high | medium | low
    confidence_tier: str  # fact | rule | model
    headline: str
    evidence: List[EvidenceItem]
    recommendation: str
    talking_point: str
    conflicts_with: List[str] = Field(default_factory=list)
    compliance_status: str  # pass | needs_review | blocked
    compliance_reason: Optional[str] = None
    rm_note_influence: Optional[str] = None
    time_horizon: Optional[str] = None  # e.g. "Hold liquid cash till 2026-10-15", "Immediate (48-72h)", "2-4 Weeks"
    rm_status: str = "pending"  # pending | approved | dismissed | modified
    rm_comment: Optional[str] = None

class CrossSpecialistOptimization(BaseModel):
    id: str
    title: str
    optimization_type: str  # tax_alpha_rebalance | liquidity_immunization | duration_macro_overlay | holistic_synergy
    participating_agents: List[str]
    description: str
    strategic_rationale: str
    expected_alpha_or_saving: str
    time_horizon: Optional[str] = None
    implementation_steps: List[str]

class AgentGraphState(TypedDict):
    client_id: str
    snapshot_date: str
    client_context: Dict[str, Any]
    portfolios_data: List[Dict[str, Any]]
    drift_results: Dict[str, Any]
    concentration_results: Dict[str, Any]
    ltv_results: Dict[str, Any]
    liquidity_results: Dict[str, Any]
    tax_results: Dict[str, Any]
    events_results: List[Dict[str, Any]]
    rm_notes_results: Dict[str, Any]
    
    # Generated recommendations per agent
    recommendations: List[Dict[str, Any]]
    conflicts: List[Dict[str, Any]]
    comingling_opportunities: List[Dict[str, Any]]
    cross_specialist_optimizations: List[Dict[str, Any]]
    compliance_flags: List[Dict[str, Any]]
    client_brief: Dict[str, Any]
    urgency_score: float
