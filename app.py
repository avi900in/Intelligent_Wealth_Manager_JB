"""
Bank Julius Baer & Co. Ltd. — Wealth Intelligence Cockpit
Agent-Based RM Decision Support System with Deterministic Analytics & LLM Reasoning
Strictly separates pure deterministic computations from agent narratives.
Relationship Manager retains full autonomy and approval control.
"""

import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import json
import html
from typing import Optional
from datetime import datetime
from src.data_layer import WealthDataRepository
from src.deterministic_analytics import DeterministicAnalytics
from src.orchestrator import ClientOrchestrator, BookPrioritizer
from src.vector_store import WealthVectorStore
from src.julius_baer_theme import get_julius_baer_css, render_jb_header
from src.llm_engine import LLMEngine

# Set Streamlit Page Configuration
st.set_page_config(
    page_title="Julius Baer — Wealth Intelligence Cockpit",
    page_icon="🏦",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Apply Julius Baer Design System CSS
st.markdown(get_julius_baer_css(), unsafe_allow_html=True)

# Initialize Backend Singletons
@st.cache_resource
def get_data_repo():
    return WealthDataRepository.get_instance()

@st.cache_resource
def get_vector_store():
    return WealthVectorStore.get_instance()

repo = get_data_repo()
vector_store = get_vector_store()
analytics = DeterministicAnalytics(repo)
llm_engine = LLMEngine.get_instance()
orchestrator = ClientOrchestrator(analytics)
prioritizer = BookPrioritizer(orchestrator)

# Session State Initialization for Authentication & Actions
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "logged_in_user" not in st.session_state:
    st.session_state.logged_in_user = "Priscilla Ong"
if "logged_in_rm_id" not in st.session_state:
    st.session_state.logged_in_rm_id = "RM-SG-014"
if "logged_in_desk" not in st.session_state:
    st.session_state.logged_in_desk = "Singapore Ultra HNW Desk"
if "selected_client_id" not in st.session_state:
    st.session_state.selected_client_id = "CL-0001"
if "approved_actions" not in st.session_state:
    st.session_state.approved_actions = {}
if "dismissed_actions" not in st.session_state:
    st.session_state.dismissed_actions = {}
if "custom_talking_points" not in st.session_state:
    st.session_state.custom_talking_points = {}
if "groq_api_key" not in st.session_state:
    st.session_state.groq_api_key = ""

# --- LOGIN SCREEN IF NOT AUTHENTICATED ---
if not st.session_state.authenticated:
    login_col1, login_col2, login_col3 = st.columns([1.2, 2.2, 1.2])
    
    with login_col2:
        st.markdown("""
        <div class="jb-login-container">
            <div class="jb-login-brand">
                <svg width="26" height="26" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <rect width="24" height="24" rx="4" fill="#C5A880"/>
                    <path d="M7 6H17V9H13V18H10V9H7V6Z" fill="#081426"/>
                </svg>
                Bank Julius Baer
            </div>
            <div class="jb-login-subtitle">Private Wealth Intelligence RM Portal</div>
            <div class="jb-login-badge">🔐 Relationship Manager Authentication Required</div>
        </div>
        """, unsafe_allow_html=True)

        with st.form("rm_login_form"):
            user_input = st.text_input("User Name", value="Priscilla Ong", placeholder="Enter RM User Name")
            pass_input = st.text_input("Password", type="password", value="••••••••", placeholder="Enter your secure password")
            
            submit_login = st.form_submit_button("🔐 Sign In to Wealth Intelligence Cockpit", use_container_width=True)
            
            if submit_login:
                if user_input.strip():
                    st.session_state.authenticated = True
                    st.session_state.logged_in_user = user_input.strip()
                    st.session_state.logged_in_rm_id = "RM-SG-014" if "priscilla" in user_input.lower() else "RM-AUTH"
                    st.session_state.logged_in_desk = "Singapore Ultra HNW Desk"
                    st.success(f"Welcome, {st.session_state.logged_in_user}!")
                    st.rerun()
                else:
                    st.error("Please enter a valid user name.")

        st.caption("<div style='text-align: center; margin-top: 0.35rem;'>🔒 Bank Julius Baer & Co. Ltd. • Multi-Factor Secured Session • For Authorized RM Personnel Only</div>", unsafe_allow_html=True)
    st.stop()

# --- AUTHENTICATED DASHBOARD VIEW ---

# Sidebar: Controls, Active User Profile & Desk Filters
with st.sidebar:
    st.markdown(f"""
    <div style="background: rgba(197, 168, 128, 0.12); border: 1px solid rgba(197, 168, 128, 0.3); border-radius: 8px; padding: 0.85rem; margin-bottom: 1rem;">
        <div style="font-size: 0.72rem; color: #C5A880; text-transform: uppercase; font-weight: 700; letter-spacing: 0.08em;">Active Relationship Manager</div>
        <div style="font-size: 1.05rem; font-weight: 700; color: #FFFFFF; margin-top: 0.2rem;">👤 {st.session_state.logged_in_user}</div>
        <div style="font-size: 0.78rem; color: #94A3B8;">{st.session_state.logged_in_rm_id} • {st.session_state.logged_in_desk}</div>
    </div>
    """, unsafe_allow_html=True)

    if st.button("🚪 Sign Out", use_container_width=True):
        st.session_state.authenticated = False
        st.rerun()

    st.markdown("---")
    st.markdown("### 🏛️ RM Workspace Controls")
    
    snapshot_dates = repo.get_snapshot_dates()
    selected_snapshot = st.selectbox(
        "📅 Analysis Snapshot Date",
        options=snapshot_dates,
        index=len(snapshot_dates) - 1,
        help="Deterministic calculations will run strictly against this historical valuation snapshot."
    )

    desk_filter = st.selectbox(
        "📍 Desk & Booking Centre Filter",
        options=[
            "All Booking Desks (20)",
            "Singapore Booking Centre (11)",
            "Hong Kong Booking Centre (9)",
            "Singapore Ultra HNW (6)",
            "Singapore HNW (5)",
            "Hong Kong Ultra HNW (5)",
            "Hong Kong HNW (4)"
        ],
        help="Filter the executive cockpit, Morning Call Queue, and KPI cards by Booking Centre and Wealth Tier."
    )

    st.markdown("---")
    st.markdown("### 🤖 Intelligence Architecture")
    st.caption("Multi-Agent LangGraph Framework • Llama-3.3-70B • ChromaDB Vector Memory")
    
    if llm_engine.is_live_llm_active():
        st.markdown('<span class="jb-badge jb-badge-low">🟢 Live Multi-Agent LLM Active</span>', unsafe_allow_html=True)
    else:
        st.markdown('<span class="jb-badge jb-badge-fact">🔵 Deterministic Multi-Agent Active</span>', unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("### 🛡️ Compliance & Governance")
    st.caption("• Deterministic facts isolated from LLM synthesis.")
    st.caption("• RM notes act as active standing overrides.")
    st.caption("• Full 1-click audit trail for every recommendation.")

# Dynamic Desk Name formatting for Executive Header
if "All Booking Desks" in desk_filter:
    active_desk_title = "Asia Desk (Singapore & Hong Kong)"
else:
    base_desk = desk_filter.split("(")[0].strip()
    active_desk_title = f"{base_desk} Desk" if not base_desk.endswith("Desk") and not base_desk.endswith("Centre") else (f"{base_desk} Desk" if not base_desk.endswith("Desk") else base_desk)

# Top Julius Baer Executive Header with Priscilla Ong in the Top Left Corner
st.markdown(render_jb_header(
    rm_name=st.session_state.logged_in_user,
    rm_id=st.session_state.logged_in_rm_id,
    desk=active_desk_title
), unsafe_allow_html=True)

# Run Book Prioritization across all 20 clients
ranked_book = prioritizer.get_ranked_book(snapshot_date=selected_snapshot)

# Filter by Desk & Booking Centre
if "Singapore Booking Centre" in desk_filter:
    filtered_book = [b for b in ranked_book if b.get("booking_centre") == "Singapore"]
elif "Hong Kong Booking Centre" in desk_filter:
    filtered_book = [b for b in ranked_book if b.get("booking_centre") == "Hong Kong"]
elif "Singapore Ultra HNW" in desk_filter:
    filtered_book = [b for b in ranked_book if b.get("booking_centre") == "Singapore" and b.get("wealth_band") == "UHNW"]
elif "Singapore HNW" in desk_filter:
    filtered_book = [b for b in ranked_book if b.get("booking_centre") == "Singapore" and b.get("wealth_band") == "HNW"]
elif "Hong Kong Ultra HNW" in desk_filter:
    filtered_book = [b for b in ranked_book if b.get("booking_centre") == "Hong Kong" and b.get("wealth_band") == "UHNW"]
elif "Hong Kong HNW" in desk_filter:
    filtered_book = [b for b in ranked_book if b.get("booking_centre") == "Hong Kong" and b.get("wealth_band") == "HNW"]
else:
    filtered_book = ranked_book

# Ensure selected client is valid within current filtered scope
filtered_cids = set(b["client_id"] for b in filtered_book)
if st.session_state.selected_client_id not in filtered_cids and filtered_book:
    st.session_state.selected_client_id = filtered_book[0]["client_id"]

client_dropdown_list = filtered_book if filtered_book else ranked_book
client_dropdown_labels = [f"{b['client_id']} — {b['client_name']}" for b in client_dropdown_list]
client_id_list = [b["client_id"] for b in client_dropdown_list]

def render_client_switcher(key_suffix: str):
    current_idx = client_id_list.index(st.session_state.selected_client_id) if st.session_state.selected_client_id in client_id_list else 0
    selected_option = st.selectbox(
        "Switch client",
        options=client_dropdown_labels,
        index=current_idx,
        key=f"switch_client_{key_suffix}"
    )
    new_cid = selected_option.split(" — ")[0]
    if new_cid != st.session_state.selected_client_id:
        st.session_state.selected_client_id = new_cid
        st.rerun()

# Dynamic Book KPIs calculated against active filtered_book
total_book_aum = sum(b["total_aum_usd"] for b in filtered_book)
total_breach_clients = sum(1 for b in filtered_book if b["has_drift_alert"])

# Exact discrete breach line-items and affected portfolios
all_scope_breaches = analytics.get_all_book_breaches(selected_snapshot)
if filtered_cids:
    all_scope_breaches = [b for b in all_scope_breaches if b["client_id"] in filtered_cids]
total_breach_items = len(all_scope_breaches)
total_breach_pfs = len(set(b["portfolio_id"] for b in all_scope_breaches))

total_ltv_alerts = sum(1 for b in filtered_book if b["has_ltv_alert"])
total_liq_crushes = sum(1 for b in filtered_book if b["has_liq_alert"])

# ---------------------------------------------------------
# INTERACTIVE MODAL DIALOGS (CLICKABLE KPI DEEP-DIVES)
# ---------------------------------------------------------
@st.dialog("⚖️ Book-Wide Mandate Breaches & Rebalancing Roster", width="large")
def show_breaches_dialog(snapshot_date: str, scope_cids: Optional[set] = None):
    st.markdown(f"### ⚖️ All Mandate Breaches & Rebalancing Actions ({snapshot_date})")
    st.caption("Consolidated deterministic view of all asset class drift and single-issuer concentration breaches across all client sleeves.")
    
    all_breaches = analytics.get_all_book_breaches(snapshot_date)
    if scope_cids:
        all_breaches = [b for b in all_breaches if b["client_id"] in scope_cids]
    if not all_breaches:
        st.success("✅ No mandate or concentration breaches detected across the entire book.")
        return

    # Metrics summary
    b_col1, b_col2, b_col3 = st.columns(3)
    total_trim_usd = sum(b["impact_usd"] for b in all_breaches if "Trim" in b["action_usd"] or "De-risk" in b["action_usd"])
    total_add_usd = sum(b["impact_usd"] for b in all_breaches if "Add" in b["action_usd"])
    unique_clients = len(set(b["client_id"] for b in all_breaches))
    unique_pfs = len(set(b["portfolio_id"] for b in all_breaches))
    
    with b_col1:
        st.metric("Total Breach Records", f"{len(all_breaches)} ({unique_pfs} Portfolios / {unique_clients} Clients)")
    with b_col2:
        st.metric("Total Required Trimming / De-Risking", f"${total_trim_usd/1e6:,.2f}M USD")
    with b_col3:
        st.metric("Total Deficit Redeployment", f"${total_add_usd/1e6:,.2f}M USD")

    st.markdown("<br>", unsafe_allow_html=True)
    
    # Filter by category or search
    cat_filter = st.radio("Filter Breach Category", options=["All Breaches", "Asset Class Drift", "Concentration Limit"], horizontal=True)
    filtered_b = all_breaches
    if cat_filter != "All Breaches":
        filtered_b = [b for b in filtered_b if b["category"] == cat_filter]

    # Convert to DataFrame
    df_b = pd.DataFrame([
        {
            "client_id": b["client_id"],
            "client_name": b["client_name"],
            "portfolio_id": b["portfolio_id"],
            "portfolio_name": b["portfolio_name"],
            "category": b["category"],
            "item_name": b["item_name"],
            "breach_type": b["breach_type"],
            "actual_pct": f"{b['actual_pct']:.2f}%" if isinstance(b['actual_pct'], (int, float)) else str(b['actual_pct']),
            "band_limit": b["band_limit"],
            "action_usd": b["action_usd"]
        }
        for b in filtered_b
    ])
    breach_selection = st.dataframe(
        df_b[["client_id", "client_name", "portfolio_id", "portfolio_name", "category", "item_name", "breach_type", "actual_pct", "band_limit", "action_usd"]],
        column_config={
            "client_id": "Client ID",
            "client_name": "Client Name",
            "portfolio_id": "Portfolio",
            "portfolio_name": "Sleeve Name",
            "category": "Category",
            "item_name": "Breach Item / Holding",
            "breach_type": "Breach Type",
            "actual_pct": "Actual %",
            "band_limit": "Mandate Limit",
            "action_usd": "Recommended Action"
        },
        hide_index=True,
        use_container_width=True,
        height=380,
        on_select="rerun",
        selection_mode="single-row",
        key="df_breaches_selection_grid"
    )

    if breach_selection and breach_selection.get("selection", {}).get("rows"):
        sel_idx = breach_selection["selection"]["rows"][0]
        if sel_idx < len(df_b):
            target_cid = df_b.iloc[sel_idx]["client_id"]
            st.session_state.selected_client_id = target_cid
            st.session_state.jump_to_tab = 1
            st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)
    b_pick_col1, b_pick_col2 = st.columns([3, 1])
    with b_pick_col1:
        sel_client = st.selectbox(
            "Or pick client directly to open in Client 360 & Action Deck",
            options=sorted(list(set(f"{b['client_id']} — {b['client_name']}" for b in all_breaches))),
            key="sel_client_from_breaches_dialog"
        )
    with b_pick_col2:
        st.markdown("<div style='margin-top: 28px;'>", unsafe_allow_html=True)
        if st.button("🚀 Open Dossier", key="btn_jump_from_breach_dialog", use_container_width=True):
            st.session_state.selected_client_id = sel_client.split(" — ")[0]
            st.session_state.jump_to_tab = 1
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)


@st.dialog("🚨 Book-Wide Lombard Lending & Credit Risk Alerts", width="large")
def show_ltv_dialog(snapshot_date: str, scope_cids: Optional[set] = None):
    st.markdown(f"### 🚨 Lombard Facility LTV Margin Call Alerts ({snapshot_date})")
    st.caption("Active monitoring of credit facilities approaching covenant margin call triggers or headroom deficits. Click any row to jump to client dossier.")

    all_alerts = analytics.get_all_book_ltv_alerts(snapshot_date)
    if scope_cids:
        all_alerts = [a for a in all_alerts if a["client_id"] in scope_cids]
    if not all_alerts:
        st.success("✅ All credit facilities across the selected dossiers are currently within safe lending buffers.")
        return

    df_ltv = pd.DataFrame([
        {
            "client_id": a["client_id"],
            "client_name": a["client_name"],
            "facility_id": a["facility_id"],
            "drawn_loan_usd": f"${a['drawn_loan_usd']:,.0f}",
            "collateral_value_usd": f"${a['collateral_value_usd']:,.0f}",
            "current_ltv_pct": f"{a['current_ltv_pct']:.2f}%",
            "margin_call_pct": f"{a['margin_call_pct']:.1f}%",
            "buffer_pct": f"{a['buffer_pct']:.2f}%",
            "headroom_usd": f"${a['headroom_usd']:,.0f}",
            "severity": a["severity"]
        }
        for a in all_alerts
    ])
    ltv_selection = st.dataframe(
        df_ltv[["client_id", "client_name", "facility_id", "drawn_loan_usd", "collateral_value_usd", "current_ltv_pct", "margin_call_pct", "buffer_pct", "headroom_usd", "severity"]],
        column_config={
            "client_id": "Client ID",
            "client_name": "Client Name",
            "facility_id": "Facility ID",
            "drawn_loan_usd": "Drawn Loan",
            "collateral_value_usd": "Collateral Value",
            "current_ltv_pct": "Current LTV",
            "margin_call_pct": "Margin Call Trigger",
            "buffer_pct": "Buffer to Trigger",
            "headroom_usd": "Available Headroom",
            "severity": "Severity"
        },
        hide_index=True,
        use_container_width=True,
        on_select="rerun",
        selection_mode="single-row",
        key="df_ltv_selection_grid"
    )

    if ltv_selection and ltv_selection.get("selection", {}).get("rows"):
        sel_idx = ltv_selection["selection"]["rows"][0]
        if sel_idx < len(df_ltv):
            target_cid = df_ltv.iloc[sel_idx]["client_id"]
            st.session_state.selected_client_id = target_cid
            st.session_state.jump_to_tab = 1
            st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)
    l_pick_col1, l_pick_col2 = st.columns([3, 1])
    with l_pick_col1:
        sel_ltv_client = st.selectbox(
            "Or pick client to open dossier",
            options=sorted(list(set(f"{a['client_id']} — {a['client_name']}" for a in all_alerts))),
            key="sel_client_from_ltv_dialog"
        )
    with l_pick_col2:
        st.markdown("<div style='margin-top: 28px;'>", unsafe_allow_html=True)
        if st.button("🚀 Open Dossier", key="btn_jump_from_ltv_dialog", use_container_width=True):
            st.session_state.selected_client_id = sel_ltv_client.split(" — ")[0]
            st.session_state.jump_to_tab = 1
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)


@st.dialog("💧 Book-Wide Liquidity Runway & Capital Call Deficits", width="large")
def show_liquidity_dialog(snapshot_date: str, scope_cids: Optional[set] = None):
    st.markdown(f"### 💧 Book-Wide Liquidity Runway & Milestone Obligations ({snapshot_date})")
    st.caption("Consolidated deterministic reconciliation of cash holdings, credit headroom, uncalled PE capital commitments, and planned cash needs across the book. Click any row to jump to client dossier.")

    all_deficits = analytics.get_all_book_liquidity_deficits(snapshot_date)
    if scope_cids:
        all_deficits = [d for d in all_deficits if d["client_id"] in scope_cids]
    if not all_deficits:
        st.success("✅ All clients currently maintain strong liquidity surpluses and comfortable capital call coverage.")
        return

    # Metrics summary
    shortfall_clients = [d for d in all_deficits if d["has_shortfall"]]
    total_shortfall_usd = sum(abs(d["net_surplus_deficit_usd"]) for d in shortfall_clients)
    total_uncalled_book = sum(d["uncalled_commitments_usd"] for d in all_deficits)
    total_planned_needs_book = sum(d["planned_cash_needs_usd"] for d in all_deficits)

    l_col1, l_col2, l_col3, l_col4 = st.columns(4)
    with l_col1:
        st.metric("Clients in Deficit", f"{len(shortfall_clients)} Clients", delta=f"{len(all_deficits)} with Obligations", delta_color="inverse")
    with l_col2:
        st.metric("Net Cumulative Shortfall", f"${total_shortfall_usd/1e6:,.2f}M USD")
    with l_col3:
        st.metric("Total Uncalled Commitments", f"${total_uncalled_book/1e6:,.2f}M USD")
    with l_col4:
        st.metric("Planned Life Milestones", f"${total_planned_needs_book/1e6:,.2f}M USD")

    st.markdown("<br>", unsafe_allow_html=True)

    # Filter by urgency
    liq_filter = st.radio("Filter Liquidity Health", options=["All Clients with Obligations", "Deficits / Shortfalls Only (🚨)", "Tight Buffers (<1.3x)"], horizontal=True)
    filtered_l = all_deficits
    if liq_filter == "Deficits / Shortfalls Only (🚨)":
        filtered_l = [d for d in filtered_l if d["has_shortfall"]]
    elif liq_filter == "Tight Buffers (<1.3x)":
        filtered_l = [d for d in filtered_l if d["coverage_ratio"] < 1.3]

    df_liq = pd.DataFrame([
        {
            "client_id": d["client_id"],
            "client_name": d["client_name"],
            "total_liquid_pool_usd": f"${d['total_liquid_pool_usd']:,.0f}",
            "total_outflows_expected_usd": f"${d['total_outflows_expected_usd']:,.0f}",
            "net_surplus_deficit_usd": f"-${abs(d['net_surplus_deficit_usd']):,.0f}" if d["net_surplus_deficit_usd"] < 0 else f"${d['net_surplus_deficit_usd']:,.0f}",
            "coverage_ratio": f"{d['coverage_ratio']:.2f}x" if d["coverage_ratio"] < 900 else "N/A",
            "severity": d["severity"],
            "obligation_summary": d["obligation_summary"]
        }
        for d in filtered_l
    ])
    liq_selection = st.dataframe(
        df_liq[["client_id", "client_name", "total_liquid_pool_usd", "total_outflows_expected_usd", "net_surplus_deficit_usd", "coverage_ratio", "severity", "obligation_summary"]],
        column_config={
            "client_id": "Client ID",
            "client_name": "Client Name",
            "total_liquid_pool_usd": "Liquid Pool",
            "total_outflows_expected_usd": "Total Obligations",
            "net_surplus_deficit_usd": "Net Surplus / (Deficit)",
            "coverage_ratio": "Coverage Ratio",
            "severity": "Status & Urgency",
            "obligation_summary": "Key Commitments & Planned Cash Needs"
        },
        hide_index=True,
        use_container_width=True,
        height=360,
        on_select="rerun",
        selection_mode="single-row",
        key="df_liq_selection_grid"
    )

    if liq_selection and liq_selection.get("selection", {}).get("rows"):
        sel_idx = liq_selection["selection"]["rows"][0]
        if sel_idx < len(df_liq):
            target_cid = df_liq.iloc[sel_idx]["client_id"]
            st.session_state.selected_client_id = target_cid
            st.session_state.jump_to_tab = 1
            st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)
    liq_pick_col1, liq_pick_col2 = st.columns([3, 1])
    with liq_pick_col1:
        sel_liq_client = st.selectbox(
            "Or pick client with liquidity obligations to open dossier",
            options=sorted(list(set(f"{d['client_id']} — {d['client_name']}" for d in all_deficits))),
            key="sel_client_from_liq_dialog"
        )
    with liq_pick_col2:
        st.markdown("<div style='margin-top: 28px;'>", unsafe_allow_html=True)
        if st.button("🚀 Open Dossier", key="btn_jump_from_liq_dialog", use_container_width=True):
            st.session_state.selected_client_id = sel_liq_client.split(" — ")[0]
            st.session_state.jump_to_tab = 1
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)


# Top KPI Columns with Interactive Clickable Actions
kpi_c1, kpi_c2, kpi_c3, kpi_c4 = st.columns(4)
scope_count = len(filtered_book)
scope_label = "Book" if scope_count == 20 else f"{scope_count} Dossiers"

with kpi_c1:
    st.markdown(f"""
    <div class="jb-kpi-card">
        <div class="jb-kpi-label">Active Book AUM</div>
        <div class="jb-kpi-value">${total_book_aum/1e6:,.1f}M</div>
        <div class="jb-kpi-sub">Across {scope_count} Wealth Dossiers</div>
    </div>
    """, unsafe_allow_html=True)

with kpi_c2:
    st.markdown(f"""
    <div class="jb-kpi-card">
        <div class="jb-kpi-label">Mandate Breaches</div>
        <div class="jb-kpi-value" style="color: {'#FF7675' if total_breach_items > 0 else '#55EFC4'};">{total_breach_items}</div>
        <div class="jb-kpi-sub">Across {total_breach_pfs} Portfolios ({total_breach_clients} Clients)</div>
    </div>
    """, unsafe_allow_html=True)
    if st.button(f"🔍 View {total_breach_items} Breach Records ({scope_label})", key="btn_kpi_breaches", use_container_width=True):
        show_breaches_dialog(selected_snapshot, filtered_cids)

with kpi_c3:
    st.markdown(f"""
    <div class="jb-kpi-card">
        <div class="jb-kpi-label">Credit / LTV Alerts</div>
        <div class="jb-kpi-value" style="color: {'#FF7675' if total_ltv_alerts > 0 else '#55EFC4'};">{total_ltv_alerts}</div>
        <div class="jb-kpi-sub">Margin Call Proximity Alerts</div>
    </div>
    """, unsafe_allow_html=True)
    if st.button(f"🔍 View {total_ltv_alerts} Credit Alert(s) ({scope_label})", key="btn_kpi_ltv", use_container_width=True):
        show_ltv_dialog(selected_snapshot, filtered_cids)

with kpi_c4:
    st.markdown(f"""
    <div class="jb-kpi-card">
        <div class="jb-kpi-label">Liquidity Deficits</div>
        <div class="jb-kpi-value" style="color: {'#FF7675' if total_liq_crushes > 0 else '#55EFC4'};">{total_liq_crushes}</div>
        <div class="jb-kpi-sub">Capital Call & Cash Milestones</div>
    </div>
    """, unsafe_allow_html=True)
    if st.button(f"🔍 View {total_liq_crushes} Liquidity Alert(s) ({scope_label})", key="btn_kpi_liq", use_container_width=True):
        show_liquidity_dialog(selected_snapshot, filtered_cids)


st.markdown("<br>", unsafe_allow_html=True)

# Main Application Tabs
tab_queue, tab_client360, tab_actions, tab_pack, tab_vector = st.tabs([
    "📋 Morning Call Queue",
    "👤 Client 360",
    "⚡ Agent Action Deck",
    "📄 Client Meeting Pack",
    "🧠 Semantic Navigator"
])

tab_target_index = st.session_state.pop("jump_to_tab", None)
if tab_target_index is not None:
    components.html(
        f"""
        <script>
            function activateTab() {{
                try {{
                    const mainTabContainer = window.parent.document.querySelector('[data-testid="stTabs"]');
                    if (mainTabContainer) {{
                        const tabs = mainTabContainer.querySelectorAll('button[role="tab"], button[data-baseweb="tab"]');
                        if (tabs && tabs.length > {tab_target_index}) {{
                            tabs[{tab_target_index}].click();
                        }}
                    }}
                }} catch (e) {{
                    console.error("Tab switch error:", e);
                }}
            }}
            activateTab();
            setTimeout(activateTab, 60);
            setTimeout(activateTab, 180);
            setTimeout(activateTab, 350);
        </script>
        """,
        height=0,
        width=0,
    )

# ---------------------------------------------------------
# TAB 1: MORNING CALL QUEUE (BOOK PRIORITIZATION)
# ---------------------------------------------------------
with tab_queue:
    st.markdown("### 📋 Prioritized Morning Action Queue — Who to Call First")
    st.caption("Ranked autonomously by composite risk urgency (Mandate breaches, Lombard margin call proximity, uncalled commitment coverage, and life milestones).")

    # Search & Quick Filters
    q_col1, q_col2 = st.columns([3, 2])
    with q_col1:
        search_query = st.text_input("🔍 Filter by Client Name, ID, or Wealth Band", placeholder="e.g. Hartono, CL-0002, Ultra HNW")
    with q_col2:
        urgency_filter = st.selectbox(
            "Filter Queue by Status",
            options=[
                "All Clients (20)",
                "Portfolios with Mandate Breaches",
                "Clients with Credit / LTV Alerts",
                "Clients with Synergistic Packages",
                "High Urgency (Score >= 50)",
                "Medium Urgency (30 <= Score < 50)",
                "Low Urgency (Score < 30)"
            ]
        )

    display_book = filtered_book
    if search_query:
        sq = search_query.lower()
        display_book = [b for b in display_book if sq in b["client_name"].lower() or sq in b["client_id"].lower() or sq in str(b.get("wealth_band", "")).lower()]

    if urgency_filter == "Portfolios with Mandate Breaches":
        display_book = [b for b in display_book if b["has_drift_alert"]]
    elif urgency_filter == "Clients with Credit / LTV Alerts":
        display_book = [b for b in display_book if b["has_ltv_alert"]]
    elif urgency_filter == "Clients with Synergistic Packages":
        display_book = [b for b in display_book if b.get("comingling_count", 0) > 0]
    elif urgency_filter == "High Urgency (Score >= 50)":
        display_book = [b for b in display_book if b["urgency_score"] >= 50.0]
    elif urgency_filter == "Medium Urgency (30 <= Score < 50)":
        display_book = [b for b in display_book if 30.0 <= b["urgency_score"] < 50.0]
    elif urgency_filter == "Low Urgency (Score < 30)":
        display_book = [b for b in display_book if b["urgency_score"] < 30.0]

    for item in display_book:
        cid = html.escape(str(item["client_id"]))
        cname = html.escape(str(item["client_name"]))
        score = item["urgency_score"]
        aum = item["total_aum_usd"]
        risk = html.escape(str(item["risk_profile"]))
        desk = html.escape(str(item["rm_desk"]))
        headline = html.escape(str(item["headline_action"]))
        conflicts = item["conflicts_count"]
        domicile = html.escape(str(item.get("tax_domicile", "")))
        last_contact_date = item.get("last_meeting_date")
        last_contact_channel = item.get("last_meeting_channel")
        last_contact_html = f"📅 Last Contact: <strong style='color: #C5A880;'>{last_contact_date} ({last_contact_channel})</strong>" if last_contact_date else "📅 Last Contact: <span style='color: #94A3B8;'>Initial Onboarding</span>"

        # Card container
        with st.container():
            col_rank, col_info, col_action = st.columns([1, 6, 2])
            
            with col_rank:
                urgency_class = "jb-badge-high" if score >= 60 else ("jb-badge-medium" if score >= 35 else "jb-badge-low")
                urgency_label = "HIGH" if score >= 60 else ("MED" if score >= 35 else "LOW")
                rank_html = f"""<div style="text-align: center; padding: 0.5rem;"><div style="font-size: 0.75rem; color: #94A3B8; text-transform: uppercase;">Score</div><div style="font-size: 1.8rem; font-weight: 700; color: #FFFFFF; font-family: monospace;">{score:.0f}</div><span class="jb-badge {urgency_class}">{urgency_label}</span></div>"""
                st.markdown(rank_html, unsafe_allow_html=True)

            with col_info:
                badge_html = ""
                if item["has_ltv_alert"]:
                    badge_html += '<span class="jb-badge jb-badge-high" style="margin-right: 4px;">🚨 LTV Margin Risk</span>'
                if item["has_drift_alert"]:
                    badge_html += '<span class="jb-badge jb-badge-medium" style="margin-right: 4px;">⚖️ Mandate Drift</span>'
                if item["has_liq_alert"]:
                    badge_html += '<span class="jb-badge jb-badge-medium" style="margin-right: 4px;">💧 Liquidity Crunch</span>'
                if item.get("comingling_count", 0) > 0:
                    badge_html += f'<span class="jb-badge jb-badge-fact" style="margin-right: 4px;">✨ {item["comingling_count"]} Synergistic Package</span>'
                if conflicts > 0:
                    badge_html += f'<span class="jb-badge jb-badge-rule" style="margin-right: 4px;">⚡ {conflicts} Conflict Tradeoff</span>'

                info_html = f"""<div><div style="display: flex; align-items: center; gap: 0.75rem;"><span style="font-size: 1.15rem; font-weight: 700; color: #FFFFFF;">{cname}</span><span style="font-size: 0.8rem; color: #C5A880; font-family: monospace;">{cid}</span>{badge_html}</div><div style="font-size: 0.85rem; color: #94A3B8; margin-top: 0.2rem;">AUM: <strong style="color: #FFFFFF;">${aum/1e6:,.2f}M</strong> | Risk: <strong style="color: #FFFFFF;">{risk}</strong> | {last_contact_html} | Desk: {desk} | Domicile: {domicile}</div><div style="font-size: 0.9rem; color: #E2E8F0; margin-top: 0.4rem; padding-left: 0.5rem; border-left: 2px solid #C5A880;">💡 <strong>Priority Action:</strong> {headline}</div></div>"""
                st.markdown(info_html, unsafe_allow_html=True)

            with col_action:
                st.markdown("<br>", unsafe_allow_html=True)
                if st.button(f"🔍 Open Dossier", key=f"btn_open_{cid}", use_container_width=True):
                    st.session_state.selected_client_id = item["client_id"]
                    st.session_state.jump_to_tab = 1
                    st.rerun()

            st.markdown("<hr style='border-color: rgba(255,255,255,0.06); margin: 0.75rem 0;'>", unsafe_allow_html=True)

# ---------------------------------------------------------
# TAB 2: CLIENT 360 & MULTI-PORTFOLIO INTELLIGENCE
# ---------------------------------------------------------
with tab_client360:
    target_cid = st.session_state.selected_client_id
    client = repo.get_client(target_cid)
    
    if client:
        c360_header_c1, c360_header_c2 = st.columns([3, 1.5])
        with c360_header_c1:
            age_val = client.get("age")
            if pd.notna(age_val) and str(age_val).strip() != "":
                try:
                    age_str = f"🎂 Age: <strong style='color: #FFF;'>{int(float(age_val))}</strong> ({client.get('life_stage', 'N/A')})"
                except (ValueError, TypeError):
                    age_str = f"🏛️ Entity: <strong style='color: #FFF;'>{client.get('life_stage', 'Institutional')}</strong>"
            else:
                age_str = f"🏛️ Entity: <strong style='color: #FFF;'>{client.get('life_stage', 'Family Office')}</strong>"

            st.markdown(f"## 👤 {client['client_name']} ({target_cid})")
            st.markdown(f"""
            <div style="display: flex; gap: 1rem; flex-wrap: wrap; font-size: 0.88rem; color: #94A3B8;">
                <div>{age_str}</div>
                <div>📍 Domicile: <strong style="color: #FFF;">{client.get('tax_domicile', 'N/A')}</strong></div>
                <div>⚖️ Risk: <strong style="color: #FFF;">{client.get('risk_profile', 'N/A')} ({client.get('risk_tolerance_score', 'N/A')}/100)</strong></div>
                <div>💼 Wealth Band: <strong style="color: #C5A880;">{client.get('wealth_band', 'N/A')}</strong></div>
                <div>🗣️ Language: <strong style="color: #FFF;">{client.get('reporting_language', 'English')}</strong></div>
                <div>🏷️ KYC Status: <strong style="color: #FFF;">{client.get('kyc_review_due', 'N/A')}</strong></div>
            </div>
            """, unsafe_allow_html=True)
        with c360_header_c2:
            render_client_switcher("tab2")
            client_snap_holdings = repo.get_all_holdings_for_client(target_cid, selected_snapshot)
            snap_aum_usd = sum(h["market_value_usd"] for h in client_snap_holdings) if client_snap_holdings else float(client.get("total_aum_usd", 0.0))
            snap_aum_base = sum(h["market_value_base"] for h in client_snap_holdings) if client_snap_holdings else 0.0
            base_ccy = client_snap_holdings[0]["portfolio_ccy"] if client_snap_holdings else client.get("base_currency", "USD")
            
            st.markdown(f"""
            <div class="jb-kpi-card" style="margin-top: 0.5rem; padding: 0.75rem 1rem;">
                <div class="jb-kpi-label">Client AUM ({selected_snapshot})</div>
                <div class="jb-kpi-value" style="font-size: 1.35rem;">${snap_aum_usd/1e6:,.2f}M</div>
                <div class="jb-kpi-sub">{base_ccy} {snap_aum_base/1e6:,.2f}M • {client['booking_centre']}</div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # Multi-Portfolio Switcher (Crucial Trap §1.1 Solution)
        portfolios = repo.get_portfolios_for_client(target_cid)
        st.markdown(f"### 📂 Multi-Portfolio Entity Graph ({len(portfolios)} Portfolios)")
        
        pf_options = {f"{p['portfolio_id']} — {p['portfolio_name']} ({p['mandate_code']})": p['portfolio_id'] for p in portfolios}
        selected_pf_label = st.selectbox("Select Portfolio Sleeve for Deep-Dive", options=list(pf_options.keys()))
        selected_pf_id = pf_options[selected_pf_label]

        col_left, col_right = st.columns([1, 1])

        with col_left:
            st.markdown("#### ⚖️ Asset Allocation vs Mandate Bands (Deterministic)")
            drift_data = analytics.compute_drift(selected_pf_id, selected_snapshot)
            
            if "allocations" in drift_data and drift_data["allocations"]:
                alloc_df = pd.DataFrame(drift_data["allocations"])
                
                # Visual table
                st.dataframe(
                    alloc_df[["asset_class", "actual_pct", "min_pct", "target_pct", "max_pct", "drift_pct", "status"]],
                    column_config={
                        "asset_class": "Asset Class",
                        "actual_pct": st.column_config.NumberColumn("Actual %", format="%.2f%%"),
                        "min_pct": st.column_config.NumberColumn("Min %", format="%.1f%%"),
                        "target_pct": st.column_config.NumberColumn("Target %", format="%.1f%%"),
                        "max_pct": st.column_config.NumberColumn("Max %", format="%.1f%%"),
                        "drift_pct": st.column_config.NumberColumn("Drift %", format="%+.2f%%"),
                        "status": "Band Status"
                    },
                    hide_index=True,
                    use_container_width=True
                )
                
                if drift_data.get("has_breaches"):
                    for b in drift_data["breaches"]:
                        st.error(f"🚨 **Breach Alert:** {b['asset_class']} is {b['actual_pct']:.2f}% (Limit {b.get('band_max_pct', b.get('band_min_pct'))}%).")

                if drift_data.get("has_warnings"):
                    for w in drift_data["warnings"]:
                        st.warning(f"⚠️ **Warning:** {w['asset_class']} is {w['actual_pct']:.2f}% (At Mandate Limit {w.get('band_min_pct', w.get('band_max_pct'))}%).")

        with col_right:
            st.markdown("#### 🔬 Structured Product Look-Through Exposure")
            st.caption("Deconstructs derivatives/accumulators into underlying asset exposures.")
            conc_data = analytics.compute_concentration(selected_pf_id, selected_snapshot)
            
            if "look_through_exposures" in conc_data and conc_data["look_through_exposures"]:
                lt_df = pd.DataFrame(conc_data["look_through_exposures"])
                st.dataframe(
                    lt_df[["underlying", "value_usd", "weight_pct"]],
                    column_config={
                        "underlying": "Underlying Asset Look-Through",
                        "value_usd": st.column_config.NumberColumn("Look-Through USD", format="$ %.2f"),
                        "weight_pct": st.column_config.NumberColumn("Effective Weight", format="%.2f%%")
                    },
                    hide_index=True,
                    use_container_width=True
                )
            else:
                st.info("No structured product wrappers in this sleeve.")

        st.markdown("---")
        
        # Credit, Liquidity, & Tax Overview
        c_sub1, c_sub2, c_sub3 = st.columns(3)
        
        with c_sub1:
            st.markdown("#### 💳 Credit Facility & LTV")
            ltv_data = analytics.compute_ltv(target_cid, selected_snapshot)
            if ltv_data["has_facility"]:
                for fac in ltv_data["facilities"]:
                    cur_ltv = fac["current_ltv_pct"]
                    margin_call = fac["margin_call_ltv_pct"]
                    headroom = fac["headroom"]
                    is_warn = fac["is_warning"]
                    
                    st.metric(
                        label=f"Facility {fac['facility_id']} LTV",
                        value=f"{cur_ltv:.2f}%",
                        delta=f"{cur_ltv - margin_call:+.2f}% to Margin Call ({margin_call}%)",
                        delta_color="inverse"
                    )
                    st.caption(f"Available Headroom: **${headroom:,.0f} {fac['facility_ccy']}**")
                    if is_warn:
                        st.warning("⚠️ Approaching covenant trigger threshold.")
            else:
                st.info("No active credit facilities for this client.")

        with c_sub2:
            st.markdown("#### 💧 Liquidity Runway & Commitments")
            runway = analytics.compute_liquidity_runway(target_cid, selected_snapshot)
            st.metric(
                label="Liquidity Coverage Ratio",
                value=f"{runway['coverage_ratio']:.2f}x",
                delta=f"${runway['net_surplus_deficit_usd']/1e3:+,.0f}k Net Surplus",
                delta_color="normal" if runway['net_surplus_deficit_usd'] >= 0 else "inverse"
            )
            st.caption(f"Uncalled Capital Commitments: **${runway['uncalled_commitments_usd']:,.0f}**")
            st.caption(f"Planned Cash Needs: **${runway['planned_cash_needs_usd']:,.0f}**")

        with c_sub3:
            st.markdown(f"#### 📜 Standing RM Notes (As of {selected_snapshot})")
            notes_info = analytics.get_rm_notes(target_cid, as_of_date=selected_snapshot)
            if notes_info["has_notes"]:
                for ov in notes_info.get("standing_overrides", []):
                    st.warning(f"🔒 **Standing Constraint ({ov['date']}):** {ov['summary']}")
                for pref in notes_info.get("preferences", []):
                    st.info(f"💡 **Preference ({pref['date']}):** {pref['summary']}")
            else:
                st.info(f"No qualitative overrides on record as of {selected_snapshot}.")
                if notes_info.get("future_notes_count"):
                    st.caption(f"ℹ️ {notes_info['future_notes_count']} subsequent note(s) recorded after {selected_snapshot}.")

# ---------------------------------------------------------
# TAB 3: AGENT ACTION DECK (RM IN CONTROL)
# ---------------------------------------------------------
with tab_actions:
    act_top_c1, act_top_c2 = st.columns([3, 1.5])
    with act_top_c1:
        st.markdown(f"### ⚡ Intelligent Action Deck — Relationship Manager in Control")
        st.caption("Specialist agents analyze deterministic facts to draft client-ready actions. Nothing reaches the client without your approval.")
    with act_top_c2:
        render_client_switcher("tab3")

    target_cid = st.session_state.selected_client_id

    # Run client orchestrator
    client_result = orchestrator.run_client(target_cid, selected_snapshot)
    recs = client_result["recommendations"]
    conflicts = client_result["conflicts"]
    comingling_opportunities = client_result.get("comingling_opportunities", [])
    compliance_flags = client_result["compliance_flags"]

    # Compliance suitability banners
    if compliance_flags:
        for flag in compliance_flags:
            if flag["severity"] == "high":
                st.error(f"🛡️ **Compliance Alert ({flag['type']}):** {flag['message']}")
            else:
                st.warning(f"🛡️ **Suitability Notice ({flag['type']}):** {flag['message']}")

    # ---------------------------------------------------------
    # SCORE PROVENANCE (OPTION A) & PROJECTED SCORE (OPTION C)
    # ---------------------------------------------------------
    urgency_breakdown = client_result.get("urgency_breakdown", {})
    raw_urgency_score = client_result.get("urgency_score", 10.0)
    
    # Identify active queue rank
    rank_in_book = next((i + 1 for i, b in enumerate(filtered_book) if b["client_id"] == target_cid), 1)
    total_in_book = len(filtered_book)
    
    # Calculate Post-Approval Projected Score (Option C)
    base_pts = urgency_breakdown.get("base_score", 10.0)
    cred_pts = urgency_breakdown.get("credit_points", 0.0)
    liq_pts = urgency_breakdown.get("liquidity_points", 0.0)
    mand_pts = urgency_breakdown.get("mandate_points", 0.0)
    high_pts = urgency_breakdown.get("high_actions_points", 0.0)
    
    # Track resolved components from approved recommendations
    approved_rec_ids = {rid for rid, approved in st.session_state.approved_actions.items() if approved}
    
    # Check if credit risk is resolved
    credit_recs = [r for r in recs if r.get("agent") == "liquidity" and ("CREDIT ALERT" in r.get("headline", "") or "LTV" in r.get("headline", ""))]
    is_credit_resolved = any(r["id"] in approved_rec_ids for r in credit_recs) if credit_recs else True
    proj_credit = 0.0 if is_credit_resolved else cred_pts
    
    # Check if liquidity deficit is resolved
    liq_recs = [r for r in recs if "liquidity" in r.get("agent", "").lower() and ("Crunch" in r.get("headline", "") or "Runway" in r.get("headline", ""))]
    is_liq_resolved = any(r["id"] in approved_rec_ids for r in liq_recs) if liq_recs else True
    proj_liq = 0.0 if is_liq_resolved else liq_pts
    
    # Check if mandate drift is resolved
    drift_recs = [r for r in recs if r.get("agent") == "rebalancing"]
    approved_drift_count = sum(1 for r in drift_recs if r["id"] in approved_rec_ids)
    drift_ratio = (1.0 - (approved_drift_count / len(drift_recs))) if drift_recs else 0.0
    proj_mandate = mand_pts * drift_ratio
    
    # Check if high actions are resolved
    high_priority_recs = [r for r in recs if r.get("priority") == "high"]
    unapproved_high_count = sum(1 for r in high_priority_recs if r["id"] not in approved_rec_ids)
    proj_high = min(unapproved_high_count * 5.0, 20.0)
    
    # Projected Score
    projected_score = round(min(100.0, base_pts + proj_credit + proj_liq + proj_mandate + proj_high), 1)
    score_delta = round(raw_urgency_score - projected_score, 1)
    
    # Factor Badges HTML (Option A)
    factor_badges = [f'<span class="jb-badge" style="background: rgba(255,255,255,0.08); color: #E2E8F0; margin-right: 4px; margin-bottom: 4px;">🏛️ Base: +{base_pts:.0f}</span>']
    if cred_pts > 0:
        factor_badges.append(f'<span class="jb-badge jb-badge-high" style="margin-right: 4px; margin-bottom: 4px;">🚨 Credit LTV Alert: +{cred_pts:.0f}</span>')
    if liq_pts > 0:
        factor_badges.append(f'<span class="jb-badge jb-badge-medium" style="margin-right: 4px; margin-bottom: 4px;">💧 Liquidity Deficit: +{liq_pts:.0f}</span>')
    if mand_pts > 0:
        breaches_n = urgency_breakdown.get("mandate_breaches_count", 1)
        factor_badges.append(f'<span class="jb-badge jb-badge-rule" style="margin-right: 4px; margin-bottom: 4px;">⚖️ Mandate Drift: +{mand_pts:.0f} ({breaches_n} breach{"es" if breaches_n > 1 else ""})</span>')
    if high_pts > 0:
        high_n = urgency_breakdown.get("high_actions_count", 1)
        factor_badges.append(f'<span class="jb-badge jb-badge-fact" style="margin-right: 4px; margin-bottom: 4px;">⚡ High Actions: +{high_pts:.0f} ({high_n} rec{"s" if high_n > 1 else ""})</span>')
    factor_badges_html = "".join(factor_badges)
    
    # Urgency labels & badge styling
    curr_class = "jb-badge-high" if raw_urgency_score >= 60 else ("jb-badge-medium" if raw_urgency_score >= 35 else "jb-badge-low")
    curr_label = "HIGH RISK" if raw_urgency_score >= 60 else ("MEDIUM" if raw_urgency_score >= 35 else "LOW")
    
    proj_class = "jb-badge-high" if projected_score >= 60 else ("jb-badge-medium" if projected_score >= 35 else "jb-badge-low")
    proj_label = "HIGH RISK" if projected_score >= 60 else ("MEDIUM" if projected_score >= 35 else "OPTIMAL / PASS")
    proj_border = "#2ECC71" if score_delta > 0 else "rgba(255,255,255,0.12)"
    
    if score_delta > 0:
        risk_reduction_pct = (score_delta / max(1.0, raw_urgency_score - base_pts)) * 100.0 if (raw_urgency_score - base_pts) > 0 else 100.0
        proj_status_html = f'<div style="font-size: 1.15rem; font-weight: 700; color: #2ECC71;">↓ {score_delta:.0f} pts Risk Mitigated ({risk_reduction_pct:.0f}% Resolved)</div>'
        proj_explanation = '<div style="font-size: 0.82rem; color: #55EFC4; margin-top: 0.3rem;">✓ Approved actions will de-risk margin call headroom, eliminate mandate drift, and restore cash runway upon RM sign-off.</div>'
    else:
        proj_status_html = '<div style="font-size: 0.95rem; font-weight: 600; color: #FDCB6E;">⏳ 0 Actions Approved (Pending RM Sign-Off)</div>'
        proj_explanation = '<div style="font-size: 0.82rem; color: #94A3B8; margin-top: 0.3rem;">Approve recommended specialist actions below to simulate post-execution risk resolution and track projected score drop.</div>'

    last_meeting_date = client_result["client_context"].get("last_meeting_date")
    last_meeting_channel = client_result["client_context"].get("last_meeting_channel")
    temporal_str = f"📅 Last Contact: {last_meeting_date} ({last_meeting_channel}) • ⏱️ Horizon: Post-{last_meeting_date} to {selected_snapshot}" if last_meeting_date else f"📅 Initial Onboarding • ⏱️ Snapshot {selected_snapshot}"

    st.markdown(f"""
    <div style="background: linear-gradient(135deg, rgba(8,20,38,0.95) 0%, rgba(13,30,54,0.95) 100%); border: 1.5px solid rgba(197,168,128,0.35); border-radius: 10px; padding: 1.25rem; margin-bottom: 1.5rem; box-shadow: 0 4px 20px rgba(0,0,0,0.3);">
        <div style="border-bottom: 1px solid rgba(255,255,255,0.08); padding-bottom: 0.65rem; margin-bottom: 1rem;">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.45rem;">
                <div style="font-size: 1.06rem; font-weight: 700; color: #FFFFFF; display: flex; align-items: center; gap: 0.5rem;">
                    <span>🎯 Morning Call Urgency Provenance & Risk Mitigation Simulator</span>
                </div>
                <div>
                    <span class="jb-badge jb-badge-rule" style="font-size: 0.85rem; padding: 0.35rem 0.9rem; border: 1.5px solid #C5A880; font-weight: 700; background: rgba(197,168,128,0.15); color: #FFF;">🏆 Rank #{rank_in_book} of {total_in_book} in Queue</span>
                </div>
            </div>
            <div style="display: flex; justify-content: space-between; align-items: center; font-size: 0.8rem; color: #C5A880; font-family: monospace;">
                <span style="font-weight: 600; color: #E2E8F0;">Client: <span style="color: #C5A880;">{target_cid}</span></span>
                <span>{temporal_str}</span>
            </div>
        </div>
        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 1.25rem;">
            <div style="background: rgba(15,23,42,0.6); border: 1px solid rgba(255,255,255,0.06); border-radius: 8px; padding: 1rem;">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.5rem;">
                    <span style="font-size: 0.82rem; text-transform: uppercase; color: #94A3B8; font-weight: 600;">Queue Urgency Score</span>
                    <span class="jb-badge {curr_class}">{raw_urgency_score:.0f} / 100 ({curr_label})</span>
                </div>
                <div style="font-size: 0.82rem; color: #C5A880; margin-bottom: 0.5rem;">Factor Breakdown (Why client is ranked #{rank_in_book}):</div>
                <div style="display: flex; flex-wrap: wrap; gap: 0.2rem;">
                    {factor_badges_html}
                </div>
            </div>
            <div style="background: rgba(15,23,42,0.6); border: 1px solid {proj_border}; border-radius: 8px; padding: 1rem;">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.5rem;">
                    <span style="font-size: 0.82rem; text-transform: uppercase; color: #94A3B8; font-weight: 600;">Post-Approval Projected Risk</span>
                    <span class="jb-badge {proj_class}">{projected_score:.0f} / 100 ({proj_label})</span>
                </div>
                <div style="margin-bottom: 0.4rem;">
                    {proj_status_html}
                </div>
                {proj_explanation}
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Comingling Opportunities (Synergistic Multi-Action Clubbing)
    if comingling_opportunities:
        st.markdown("#### ✨ Synergistic Comingling Opportunity (Clubbed Multi-Agent Strategy)")
        for pkg in comingling_opportunities:
            pkg_id = pkg["id"]
            pkg_title = html.escape(str(pkg["title"]))
            pkg_summary = html.escape(str(pkg["summary"]))
            pkg_unified_action = pkg["unified_action"]
            pkg_unified_tp = pkg["unified_talking_point"]
            clubbed_rec_ids = pkg["clubbed_rec_ids"]
            clubbed_recs = pkg["clubbed_recs"]
            benefits = pkg.get("financial_benefits", [])

            is_pkg_approved = all(st.session_state.approved_actions.get(rid, False) for rid in clubbed_rec_ids) or st.session_state.approved_actions.get(pkg_id, False)
            pkg_border = "#2ECC71" if is_pkg_approved else "#C5A880"

            with st.container():
                st.markdown(f"""
                <div class="jb-rec-card" style="border: 1.5px solid {pkg_border}; background: linear-gradient(135deg, rgba(197,168,128,0.12) 0%, rgba(13,30,54,0.7) 100%); border-radius: 8px; padding: 1.25rem;">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.6rem;">
                        <div>
                            <span class="jb-badge jb-badge-fact">✨ Multi-Agent Synergy</span>
                            <span class="jb-badge jb-badge-high">{len(clubbed_recs)} Actions Clubbed</span>
                            <span class="jb-badge" style="background: rgba(255,255,255,0.1); color: #FFF;">Comingling Opportunity</span>
                        </div>
                        <div style="font-size: 0.8rem; color: #C5A880; font-family: monospace;">{pkg_id}</div>
                    </div>
                    <div style="font-size: 1.15rem; font-weight: 700; color: #FFFFFF; margin-bottom: 0.4rem;">{pkg_title}</div>
                    <div style="font-size: 0.92rem; color: #E2E8F0; margin-bottom: 0.8rem;">{pkg_summary}</div>
                    <div style="background: rgba(8,20,38,0.6); padding: 0.8rem; border-radius: 6px; margin-bottom: 0.8rem;">
                        <div style="font-size: 0.85rem; font-weight: 600; color: #C5A880; margin-bottom: 0.3rem;">🎯 Unified Multi-Objective Execution Plan:</div>
                        <div style="font-size: 0.85rem; color: #FFFFFF; white-space: pre-line;">{pkg_unified_action}</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

                with st.expander(f"📦 View {len(clubbed_recs)} Clubbed Specialist Components & Strategic Benefits"):
                    for cr in clubbed_recs:
                        st.markdown(f"- **[{cr['agent'].upper()}]** {cr['headline']}")
                    st.markdown("<br><strong>Financial Benefits:</strong>", unsafe_allow_html=True)
                    for ben in benefits:
                        st.markdown(f"- {ben}")

                curr_pkg_tp = st.session_state.custom_talking_points.get(pkg_id, pkg_unified_tp)
                edited_pkg_tp = st.text_area(
                    "💬 Unified Client-Ready Advisory Phrasing (Verbatim for RM)",
                    value=curr_pkg_tp,
                    key=f"tp_pkg_{pkg_id}",
                    height=80
                )
                if edited_pkg_tp != curr_pkg_tp:
                    st.session_state.custom_talking_points[pkg_id] = edited_pkg_tp

                col_pkg1, col_pkg2, col_pkg3 = st.columns([3, 2, 4])
                with col_pkg1:
                    if st.button("⚡ Approve Unified Package (1-Click)", key=f"btn_app_pkg_{pkg_id}", use_container_width=True):
                        for rid in clubbed_rec_ids:
                            st.session_state.approved_actions[rid] = True
                            st.session_state.dismissed_actions[rid] = False
                        st.session_state.approved_actions[pkg_id] = True
                        st.rerun()
                with col_pkg2:
                    if st.button("❌ Dismiss Package", key=f"btn_dism_pkg_{pkg_id}", use_container_width=True):
                        for rid in clubbed_rec_ids:
                            st.session_state.approved_actions[rid] = False
                            st.session_state.dismissed_actions[rid] = True
                        st.session_state.approved_actions[pkg_id] = False
                        st.rerun()
                with col_pkg3:
                    if is_pkg_approved:
                        st.markdown("<span style='color: #2ECC71; font-weight: 600;'>✓ Unified Package Approved (All 4 Actions Synchronized)</span>", unsafe_allow_html=True)
                    else:
                        st.markdown("<span style='color: #94A3B8; font-size: 0.85rem;'>Approve unified package to queue synchronized multi-trade briefing to Tab 4.</span>", unsafe_allow_html=True)

                st.markdown("<hr style='border-color: rgba(255,255,255,0.12); margin: 1.5rem 0;'>", unsafe_allow_html=True)

    # Cross-Specialist Strategic Optimizations (Master LLM Orchestrator)
    cross_specialist_optimizations = client_result.get("cross_specialist_optimizations", [])
    if cross_specialist_optimizations:
        st.markdown("#### 🧠 Master Orchestrator Strategic Optimizations (Cross-Specialist Alpha)")
        for opt in cross_specialist_optimizations:
            opt_id = opt.get("id", "")
            opt_title = html.escape(str(opt.get("title", "")))
            opt_desc = html.escape(str(opt.get("description", "")))
            opt_saving = html.escape(str(opt.get("expected_alpha_or_saving", "")))
            opt_rat = html.escape(str(opt.get("strategic_rationale", "")))
            agents = opt.get("participating_agents", [])
            steps = opt.get("implementation_steps", [])

            agent_badges = "".join([f'<span class="jb-badge jb-badge-fact" style="margin-right: 4px;">{a.upper()}</span>' for a in agents])

            st.markdown(f"""
            <div class="jb-rec-card" style="border: 1.5px solid rgba(85,239,196,0.5); background: linear-gradient(135deg, rgba(85,239,196,0.08) 0%, rgba(13,30,54,0.8) 100%); border-radius: 8px; padding: 1.15rem; margin-bottom: 1rem;">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.5rem;">
                    <div>
                        <span class="jb-badge" style="background: #00B894; color: #FFF; font-weight: 700;">🧠 Strategic Alpha</span>
                        {agent_badges}
                    </div>
                    <div style="font-size: 0.8rem; color: #55EFC4; font-family: monospace;">{opt_id}</div>
                </div>
                <div style="font-size: 1.05rem; font-weight: 700; color: #FFFFFF; margin-bottom: 0.3rem;">{opt_title}</div>
                <div style="font-size: 0.88rem; color: #E2E8F0; margin-bottom: 0.6rem;">{opt_desc}</div>
                <div style="display: flex; flex-direction: column; gap: 0.4rem; background: rgba(8,20,38,0.6); padding: 0.75rem; border-radius: 6px; font-size: 0.84rem;">
                    <div><span style="color: #55EFC4; font-weight: 600;">💡 Expected Benefit:</span> <span style="color: #FFF;">{opt_saving}</span></div>
                    <div><span style="color: #94A3B8; font-weight: 600;">🎯 Strategic Rationale:</span> <span style="color: #CBD5E1;">{opt_rat}</span></div>
                </div>
            </div>
            """, unsafe_allow_html=True)
            if steps:
                with st.expander(f"📋 View Execution Roadmap for {opt_title}"):
                    for s in steps:
                        st.markdown(f"- {s}")

    # Cross-Agent Conflicts Surfacing
    if conflicts:
        st.markdown("#### ⚡ Cross-Agent Tradeoffs & Conflict Resolution")
        for conf in conflicts:
            conf_title = html.escape(str(conf.get("title", "")))
            conf_desc = html.escape(str(conf.get("description", "")))
            conf_tradeoff = html.escape(str(conf.get("tradeoff", "")))
            conf_res = html.escape(str(conf.get("recommended_resolution", "")))
            conf_html = f"""<div class="jb-conflict-box"><div style="font-weight: 700; color: #FDCB6E; font-size: 0.95rem;">⚠️ Conflict Detected: {conf_title}</div><div style="font-size: 0.85rem; color: #E2E8F0; margin: 0.3rem 0;">{conf_desc}</div><div style="font-size: 0.82rem; color: #94A3B8;"><strong>Tradeoff:</strong> {conf_tradeoff}</div><div style="font-size: 0.82rem; color: #55EFC4; margin-top: 0.2rem;"><strong>Suggested RM Policy:</strong> {conf_res}</div></div>"""
            st.markdown(conf_html, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("#### 🤖 Specialist Agent Recommendations")

    if not recs:
        st.success("All portfolio parameters, credit lines, and cash runways are currently optimal.")
    else:
        # Separate by priority
        high_recs = [r for r in recs if str(r.get("priority", "")).lower() == "high"]
        med_recs = [r for r in recs if str(r.get("priority", "")).lower() == "medium"]
        low_recs = [r for r in recs if str(r.get("priority", "")).lower() == "low"]

        def render_rec_item(rec, prefix: str = "all"):
            rec_id = html.escape(str(rec["id"]))
            agent = html.escape(str(rec["agent"]))
            priority = str(rec["priority"]).lower()
            tier = str(rec["confidence_tier"]).lower()
            headline = html.escape(str(rec["headline"]))
            recommendation_text = html.escape(str(rec["recommendation"]))
            default_talking_point = rec["talking_point"]
            evidence_items = rec["evidence"]
            override_note = html.escape(str(rec.get("rm_note_influence", ""))) if rec.get("rm_note_influence") else None
            
            # Check session state approval/dismissal
            is_approved = st.session_state.approved_actions.get(rec["id"], False)
            is_dismissed = st.session_state.dismissed_actions.get(rec["id"], False)

            # Styling cards
            p_class = "jb-badge-high" if priority == "high" else ("jb-badge-medium" if priority == "medium" else "jb-badge-low")
            tier_class = "jb-badge-fact" if tier == "fact" else ("jb-badge-rule" if tier == "rule" else "jb-badge-model")
            border_color = "#2ECC71" if is_approved else ("#E74C3C" if is_dismissed else "#C5A880")
            status_badge = f'<span class="jb-badge jb-badge-high">Status: {html.escape(rec["compliance_status"].upper())}</span>' if rec["compliance_status"] != "pass" else ""
            override_html = f'<div style="font-size: 0.82rem; color: #FDCB6E; margin-bottom: 0.4rem;">🔒 <em>{override_note}</em></div>' if override_note else ""

            with st.container():
                rec_html = f"""<div class="jb-rec-card" style="border-left: 4px solid {border_color};"><div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.5rem;"><div><span class="jb-badge {p_class}">{priority.upper()} Priority</span> <span class="jb-badge {tier_class}">Confidence: {tier.upper()}</span> <span class="jb-badge" style="background: rgba(255,255,255,0.1); color: #FFF;">Agent: {agent.upper()}</span> {status_badge}</div><div style="font-size: 0.8rem; color: #C5A880; font-family: monospace;">{rec_id}</div></div><div class="jb-rec-headline">{headline}</div><div style="font-size: 0.9rem; color: #E2E8F0; margin-bottom: 0.5rem;"><strong>Proposed Action:</strong> {recommendation_text}</div>{override_html}</div>"""
                st.markdown(rec_html, unsafe_allow_html=True)

                # Editable Client-Ready Talking Point
                curr_tp = st.session_state.custom_talking_points.get(rec["id"], default_talking_point)
                edited_tp = st.text_area(
                    f"💬 Client-Ready Phrasing (Verbatim for RM)",
                    value=curr_tp,
                    key=f"tp_{prefix}_{rec['id']}",
                    height=70
                )
                if edited_tp != curr_tp:
                    st.session_state.custom_talking_points[rec["id"]] = edited_tp

                # 1-Click Evidence Audit Trail Drawer
                with st.expander(f"🔍 1-Click Evidence Audit Trail ({len(evidence_items)} Facts Cited)"):
                    for idx, ev in enumerate(evidence_items):
                        st.markdown(f"""
                        - **Source Pure Function:** `{ev.get('source_function')}`
                        - **Calculated Metric Fact:** `{ev.get('detail')}`
                        - **Valuation Date:** `{ev.get('as_of_date')}`
                        - **Threshold / Band Reference:** `{ev.get('threshold_or_band', 'Standard mandate constraint')}`
                        """)

                # RM Control Decision Bar
                col_act1, col_act2, col_act3 = st.columns([2, 2, 4])
                with col_act1:
                    if st.button(f"✅ Approve Action", key=f"app_{prefix}_{rec['id']}", use_container_width=True):
                        st.session_state.approved_actions[rec["id"]] = True
                        st.session_state.dismissed_actions[rec["id"]] = False
                        st.rerun()
                with col_act2:
                    if st.button(f"❌ Dismiss Action", key=f"dism_{prefix}_{rec['id']}", use_container_width=True):
                        st.session_state.dismissed_actions[rec["id"]] = True
                        st.session_state.approved_actions[rec["id"]] = False
                        st.rerun()
                with col_act3:
                    if is_approved:
                        st.markdown("<span style='color: #2ECC71; font-weight: 600;'>✓ Action Approved & Queued for Client Meeting Pack</span>", unsafe_allow_html=True)
                    elif is_dismissed:
                        st.markdown("<span style='color: #E74C3C; font-weight: 600;'>✗ Action Dismissed by RM</span>", unsafe_allow_html=True)

                st.markdown("<hr style='border-color: rgba(255,255,255,0.08); margin: 1.25rem 0;'>", unsafe_allow_html=True)

        # Priority Sub-tabs
        p_tab_all, p_tab_high, p_tab_med, p_tab_low = st.tabs([
            f"📑 All Actions ({len(recs)})",
            f"🚨 High Priority ({len(high_recs)})",
            f"⚖️ Medium Priority ({len(med_recs)})",
            f"🌱 Low Priority ({len(low_recs)})"
        ])

        with p_tab_all:
            for r in recs:
                render_rec_item(r, prefix="all")

        with p_tab_high:
            if high_recs:
                for r in high_recs:
                    render_rec_item(r, prefix="high")
            else:
                st.info("No High Priority breaches or critical alerts for this client.")

        with p_tab_med:
            if med_recs:
                for r in med_recs:
                    render_rec_item(r, prefix="med")
            else:
                st.info("No Medium Priority actions active for this client.")

        with p_tab_low:
            if low_recs:
                for r in low_recs:
                    render_rec_item(r, prefix="low")
            else:
                st.info("No Low Priority hygiene items.")

# ---------------------------------------------------------
# TAB 4: CLIENT MEETING PACK & EMAIL GENERATOR
# ---------------------------------------------------------
with tab_pack:
    pack_top_c1, pack_top_c2 = st.columns([3, 1.5])
    with pack_top_c1:
        st.markdown(f"### 📄 Client Meeting Brief & Email Generator")
        st.caption("Compiles all RM-approved recommendations and talking points into a private banking client brief.")
    with pack_top_c2:
        render_client_switcher("tab4")

    target_cid = st.session_state.selected_client_id
    client = repo.get_client(target_cid)

    if client:
        client_result = orchestrator.run_client(target_cid, selected_snapshot)
        recs = client_result["recommendations"]
        
        approved_recs = [r for r in recs if st.session_state.approved_actions.get(r["id"], False)]
        if approved_recs:
            st.success(f"✅ **{len(approved_recs)} RM-Approved Action(s) Included** in this client communication.")
        else:
            st.info("ℹ️ **Draft Preview Mode:** No actions explicitly approved yet in Tab 3 (Agent Action Deck). Showing default high-priority actions. Approve any recommendation in Tab 3 to include it.")
            approved_recs = [r for r in recs if r["priority"] == "high"][:2]

        # Check for approved comingling packages
        approved_pkgs = [p for p in client_result.get("comingling_opportunities", []) if st.session_state.approved_actions.get(p["id"], False)]

        meeting_format = st.radio("Communication Format", options=["Executive Client Briefing Note", "Formal Advisory Email", "Meeting Discussion Agenda"], horizontal=True)

        lang = client.get("reporting_language", "English")

        # Generate Formal Document Content
        pack_content = f"""**CONFIDENTIAL — BANK JULIUS BAER & CO. LTD.**
**PORTFOLIO INTELLIGENCE & ADVISORY BRIEFING**

**Client:** {client['client_name']} ({client['client_id']})
**Date:** {datetime.now().strftime('%d %B %Y')} | Valuation Snapshot: {selected_snapshot}
**Relationship Manager:** {client.get('rm_name', 'Private Banking Desk')} ({client.get('rm_desk')})
**Booking Centre:** {client.get('booking_centre')} | Tax Domicile: {client.get('tax_domicile')}
**Total Stated AUM:** USD {client.get('total_aum_usd', 0)/1e6:,.2f}M

---

### 1. Executive Portfolio Context
Dear {client['client_name']},

As part of Bank Julius Baer's continuous portfolio stewardship, we have reviewed your asset allocations, credit facilities, and liquidity provisions across your mandates.
"""
        if approved_pkgs:
            for pkg in approved_pkgs:
                pkg_tp = st.session_state.custom_talking_points.get(pkg["id"], pkg["unified_talking_point"])
                pack_content += f"""
### 2. Unified Strategic Execution Package (Multi-Objective Synergy)
**Strategy:** {pkg['title']}
- **Summary:** {pkg['summary']}
- **Unified Action Plan:**
{pkg['unified_action']}
- **Advisory Phrasing:** {pkg_tp}
"""
            pack_content += """
### 3. Detailed Component Recommendations & Governance Audit
"""
        else:
            pack_content += """
### 2. Strategic Insights & Recommended Actions
"""

        for i, r in enumerate(approved_recs, 1):
            tp = st.session_state.custom_talking_points.get(r["id"], r["talking_point"])
            pack_content += f"""
**{i}. {r['headline']}**
- **Action:** {r['recommendation']}
- **Advisory Rationale:** {tp}
- **Governance Audit Citation:** {r['evidence'][0]['detail']} (as of {r['evidence'][0]['as_of_date']})
"""

        step_num = 4 if approved_pkgs else 3
        pack_content += f"""
---
### {step_num}. Next Steps & Governance
We look forward to reviewing these adjustments during our upcoming conversation. Please let us know if any personal circumstances or liquidity horizons have evolved.

Sincerely,

**{client.get('rm_name', 'Your Relationship Manager')}**  
Bank Julius Baer & Co. Ltd.
"""

        st.text_area("Generated Formal Document Preview", value=pack_content, height=420)
        
        st.download_button(
            label="💾 Download Client Briefing (.md / .txt)",
            data=pack_content,
            file_name=f"JuliusBaer_Brief_{client['client_id']}_{selected_snapshot}.txt",
            mime="text/plain"
        )

# ---------------------------------------------------------
# TAB 5: SEMANTIC KNOWLEDGE NAVIGATOR
# ---------------------------------------------------------
with tab_vector:
    st.markdown("### 🧠 Semantic Knowledge Navigator")
    st.caption("Vector similarity search across unstructured RM meeting logs, world market shock events, and mandate compliance clauses.")

    v_col1, v_col2 = st.columns([3, 1])
    with v_col1:
        v_query = st.text_input("Semantic Query", placeholder="e.g. 'client refused leverage', 'gold upside participation', 'shipping crisis', 'Bukit Timah property deposit'")
    with v_col2:
        v_target = st.selectbox("Search Target Collection", options=["RM Meeting Notes", "Market Shock Events"])

    if v_query:
        if v_target == "RM Meeting Notes":
            results = vector_store.search_rm_notes(v_query, n_results=4)
            st.markdown(f"#### 🔍 RM Notes Semantic Matches ({len(results)} found)")
            for r in results:
                st.markdown(f"""
                <div class="jb-client-card">
                    <div style="display: flex; justify-content: space-between;">
                        <strong style="color: #C5A880;">Client {r['client_id']} — {r['channel']} ({r['note_date']})</strong>
                        <span style="font-size: 0.8rem; color: #94A3B8;">RM: {r['rm_name']}</span>
                    </div>
                    <div style="font-size: 0.9rem; color: #FFF; margin-top: 0.4rem;">{r['text']}</div>
                </div>
                """, unsafe_allow_html=True)
        else:
            results = vector_store.search_events(v_query, n_results=4)
            st.markdown(f"#### 🔍 Market Shock Events Matches ({len(results)} found)")
            for r in results:
                st.markdown(f"""
                <div class="jb-client-card">
                    <div style="display: flex; justify-content: space-between;">
                        <strong style="color: #FF7675;">{r['date']} — Severity: {r['severity']}</strong>
                        <span style="font-size: 0.8rem; color: #94A3B8;">Region: {r['region']}</span>
                    </div>
                    <div style="font-size: 0.9rem; color: #FFF; margin-top: 0.4rem;">{r['text']}</div>
                </div>
                """, unsafe_allow_html=True)
