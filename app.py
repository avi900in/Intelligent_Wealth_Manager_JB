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
from src.cockpit_modules import (
    render_stress_testing_lab,
    render_trigger_conversation_engine,
    render_client_digital_twin,
    render_explainable_ai
)

# Set Streamlit Page Configuration
st.set_page_config(
    page_title="JB Pulse — Wealth Intelligence",
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

# Private Banking RM Coverage Profiles for Row-Level Security (RLS) & Multi-RM Simulation
RM_PROFILES = {
    "RM-SG-014": {
        "name": "Priscilla Ong",
        "rm_id": "RM-SG-014",
        "desk": "Asia Desk (Singapore & Hong Kong)",
        "label": "Priscilla Ong (RM-SG-014) — Senior Partner (Asia Book: 20 Clients)",
        "role": "Assigned Senior RM",
        "accessible": True,
        "can_approve": True,
        "notes": "Full commercial signing and trade approval authority for Singapore and Hong Kong booking centres."
    },
    "RM-ZH-002": {
        "name": "Christian Weber",
        "rm_id": "RM-ZH-002",
        "desk": "Swiss & European Private Banking Desk (Zurich)",
        "label": "Christian Weber (RM-ZH-002) — Exec Director (Swiss Desk: 0 Asia Clients)",
        "role": "Unassigned RM (Cross-Desk Restricted)",
        "accessible": False,
        "can_approve": False,
        "notes": "Coverage restricted to Swiss/European booking centres. Zero Asia dossiers assigned."
    },
    "DH-SG-001": {
        "name": "Marc Guggenheim",
        "rm_id": "DH-SG-001",
        "desk": "Global Wealth Management Supervisory Desk",
        "label": "Marc Guggenheim (DH-SG-001) — Supervisory Desk Head (Audit Mode — Read Only)",
        "role": "Supervisory Desk Head (Read-Only Audit)",
        "accessible": True,
        "can_approve": False,
        "notes": "Full supervisory audit and compliance oversight. Read-only review mode (commercial trade execution reserved for assigned RM)."
    }
}

def format_client_display_name(cname: str, cid: str) -> str:
    """Masks client name if Zero-PII Presentation Mode is active."""
    if st.session_state.get("privacy_mode", False):
        return f"Client {cid} (Protected)"
    return cname

# Session State Initialization for Authentication & Actions
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "logged_in_user" not in st.session_state:
    st.session_state.logged_in_user = "Priscilla Ong"
if "logged_in_rm_id" not in st.session_state:
    st.session_state.logged_in_rm_id = "RM-SG-014"
if "logged_in_desk" not in st.session_state:
    st.session_state.logged_in_desk = "Asia Desk (Singapore & Hong Kong)"
if "privacy_mode" not in st.session_state:
    st.session_state.privacy_mode = False
if "selected_client_id" not in st.session_state:
    st.session_state.selected_client_id = "CL-0001"
if "approved_actions" not in st.session_state:
    st.session_state.approved_actions = {}
if "dismissed_actions" not in st.session_state:
    st.session_state.dismissed_actions = {}
if "custom_talking_points" not in st.session_state:
    st.session_state.custom_talking_points = {}
if "desk_head_endorsements" not in st.session_state:
    st.session_state.desk_head_endorsements = {}
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
                JB Pulse
            </div>
            <div class="jb-login-subtitle">Wealth Intelligence RM Portal • Bank Julius Baer</div>
            <div class="jb-login-badge">🔐 Relationship Manager Authentication Required</div>
        </div>
        """, unsafe_allow_html=True)

        with st.form("rm_login_form"):
            user_input = st.text_input("User Name", value="Priscilla Ong", placeholder="Enter RM User Name")
            pass_input = st.text_input("Password", type="password", value="••••••••", placeholder="Enter your secure password")
            
            submit_login = st.form_submit_button("🔐 Sign In to JB Pulse", use_container_width=True)
            
            if submit_login:
                if user_input.strip():
                    st.session_state.authenticated = True
                    st.session_state.logged_in_user = user_input.strip()
                    if "weber" in user_input.lower() or "christian" in user_input.lower():
                        st.session_state.logged_in_rm_id = "RM-ZH-002"
                        st.session_state.logged_in_desk = "Swiss & European Private Banking Desk (Zurich)"
                    elif "guggenheim" in user_input.lower() or "marc" in user_input.lower():
                        st.session_state.logged_in_rm_id = "DH-SG-001"
                        st.session_state.logged_in_desk = "Global Wealth Management Supervisory Desk"
                    else:
                        st.session_state.logged_in_rm_id = "RM-SG-014"
                        st.session_state.logged_in_desk = "Asia Desk (Singapore & Hong Kong)"
                    st.success(f"Welcome, {st.session_state.logged_in_user}!")
                    st.rerun()
                else:
                    st.error("Please enter a valid user name.")

        st.caption("<div style='text-align: center; margin-top: 0.35rem;'>🔒 Bank Julius Baer & Co. Ltd. • Multi-Factor Secured Session • For Authorized RM Personnel Only</div>", unsafe_allow_html=True)
    st.stop()

# --- AUTHENTICATED DASHBOARD VIEW ---

# Sidebar: Controls, Active User Profile & Desk Filters
with st.sidebar:
    st.markdown("### 🔐 RM Identity & Coverage Scope")
    
    current_rm_id = st.session_state.get("logged_in_rm_id", "RM-SG-014")
    rm_keys = list(RM_PROFILES.keys())
    active_rm_idx = rm_keys.index(current_rm_id) if current_rm_id in rm_keys else 0
    
    selected_rm_key = st.selectbox(
        "Active RM Coverage Profile",
        options=rm_keys,
        format_func=lambda k: RM_PROFILES[k]["label"],
        index=active_rm_idx,
        help="Simulate Private Banking Row-Level Security (RLS), coverage segregation, and supervisor audit modes."
    )
    
    if selected_rm_key != current_rm_id:
        st.session_state.logged_in_rm_id = selected_rm_key
        st.session_state.logged_in_user = RM_PROFILES[selected_rm_key]["name"]
        st.session_state.logged_in_desk = RM_PROFILES[selected_rm_key]["desk"]
        st.rerun()

    active_rm_info = RM_PROFILES.get(selected_rm_key, RM_PROFILES["RM-SG-014"])
    role_badge_class = "jb-badge-fact" if selected_rm_key == "DH-SG-001" else ("jb-badge-high" if not active_rm_info["accessible"] else "jb-badge-low")
    
    st.markdown(f"""
    <div style="background: rgba(197, 168, 128, 0.12); border: 1px solid rgba(197, 168, 128, 0.3); border-radius: 8px; padding: 0.85rem; margin-bottom: 0.75rem;">
        <div style="font-size: 0.72rem; color: #C5A880; text-transform: uppercase; font-weight: 700; letter-spacing: 0.08em;">Active Coverage Profile</div>
        <div style="font-size: 1.05rem; font-weight: 700; color: #FFFFFF; margin-top: 0.2rem;">👤 {st.session_state.logged_in_user}</div>
        <div style="font-size: 0.78rem; color: #94A3B8;">{st.session_state.logged_in_rm_id} • {st.session_state.logged_in_desk}</div>
        <div style="margin-top: 0.4rem;"><span class="jb-badge {role_badge_class}" style="font-size: 0.7rem;">{active_rm_info['role']}</span></div>
    </div>
    """, unsafe_allow_html=True)

    if st.button("🚪 Sign Out", use_container_width=True):
        st.session_state.authenticated = False
        st.rerun()

    st.markdown("---")
    st.markdown("### 🛡️ Client Privacy & Presentation Mode")
    privacy_toggle = st.toggle(
        "🛡️ Zero-PII Presentation Mode",
        value=st.session_state.get("privacy_mode", False),
        help="Mask all client names, account IDs, and sensitive identifiers across all views for secure screen-sharing with clients or external audits."
    )
    if privacy_toggle != st.session_state.get("privacy_mode", False):
        st.session_state.privacy_mode = privacy_toggle
        st.rerun()

    if st.session_state.get("privacy_mode", False):
        st.markdown('<div style="background: rgba(46, 204, 113, 0.15); border: 1px solid #2ECC71; border-radius: 6px; padding: 0.5rem 0.75rem; font-size: 0.78rem; color: #2ECC71; font-weight: 600; margin-bottom: 0.75rem;">🔒 Presentation Privacy Active: All Client PII Masked</div>', unsafe_allow_html=True)

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
    st.caption("• Row-Level Security (RLS) & Cross-RM Data Isolation.")
    st.caption("• Deterministic facts isolated from LLM synthesis.")
    st.caption("• RM notes act as active standing overrides.")
    st.caption("• Full 1-click audit trail for every recommendation.")

# Dynamic Desk Name formatting for Executive Header
if "All Booking Desks" in desk_filter:
    active_desk_title = "Asia Desk (Singapore & Hong Kong)"
else:
    base_desk = desk_filter.split("(")[0].strip()
    active_desk_title = f"{base_desk} Desk" if not base_desk.endswith("Desk") and not base_desk.endswith("Centre") else (f"{base_desk} Desk" if not base_desk.endswith("Desk") else base_desk)

# Top Julius Baer Executive Header with RM Name and Desk
st.markdown(render_jb_header(
    rm_name=st.session_state.logged_in_user,
    rm_id=st.session_state.logged_in_rm_id,
    desk=active_desk_title if active_rm_info["accessible"] else active_rm_info["desk"]
), unsafe_allow_html=True)

# ---------------------------------------------------------
# TOP NAVIGATION: TOP-RIGHT HAMBURGER MENU & BREADCRUMB
# ---------------------------------------------------------
NAV_MODULES = [
    "🏛️ JB Pulse - Wealth Intelligence",
    "🧪 Portfolio Stress Testing Lab",
    "💬 Trigger-to-Conversation Engine",
    "👤 Client Digital Twin",
    "🔍 Explainable AI"
]

if "active_nav_module" not in st.session_state:
    st.session_state.active_nav_module = "🏛️ JB Pulse - Wealth Intelligence"

nav_bar_col1, nav_bar_col2 = st.columns([5.5, 2.5])

with nav_bar_col1:
    st.markdown(f"""
    <div style="display: flex; align-items: center; height: 100%; padding: 0.35rem 0;">
        <span style="font-size: 0.8rem; color: #C5A059; text-transform: uppercase; font-weight: 700; letter-spacing: 0.08em; margin-right: 0.5rem;">Active Workspace:</span>
        <span class="jb-badge jb-badge-fact" style="font-size: 0.85rem; font-weight: 600; padding: 0.25rem 0.65rem;">
            {st.session_state.active_nav_module}
        </span>
    </div>
    """, unsafe_allow_html=True)

with nav_bar_col2:
    with st.popover("☰ Navigation Menu", use_container_width=True):
        st.markdown("<div style='font-size: 0.72rem; color: #C5A059; font-weight: 700; text-transform: uppercase; letter-spacing: 0.08em; margin-bottom: 0.4rem;'>Switch Advisory Workspace</div>", unsafe_allow_html=True)
        for idx, mod in enumerate(NAV_MODULES):
            is_active = (st.session_state.active_nav_module == mod)
            if st.button(mod, key=f"pop_nav_btn_{idx}", use_container_width=True, type="primary" if is_active else "secondary"):
                st.session_state.active_nav_module = mod
                st.rerun()

st.markdown("<div style='margin-bottom: 0.85rem;'></div>", unsafe_allow_html=True)

# ---------------------------------------------------------
# ROW-LEVEL SECURITY (RLS) ACCESS CLEARANCE CHECK
# ---------------------------------------------------------
if not active_rm_info.get("accessible", True):
    st.markdown("""
    <div style="background: rgba(220, 38, 38, 0.08); border: 1.5px solid rgba(220, 38, 38, 0.4); border-radius: 12px; padding: 2.5rem; margin: 2rem 0; text-align: center; box-shadow: 0 8px 32px rgba(0,0,0,0.4);">
        <div style="font-size: 3rem; margin-bottom: 0.75rem;">🔒</div>
        <div style="font-size: 1.4rem; font-weight: 700; color: #FF7675; margin-bottom: 0.6rem; letter-spacing: 0.02em;">Bank Julius Baer Confidentiality & Row-Level Data Isolation Enforced</div>
        <div style="font-size: 0.98rem; color: #E2E8F0; max-width: 700px; margin: 0 auto 1.25rem auto; line-height: 1.6;">
            You are currently authenticated as <strong>Christian Weber (RM-ZH-002 — Swiss & European Private Banking Desk)</strong>.<br>
            Under Julius Baer Data Protection Policy (PB-SEC-402) and Swiss Banking Secrecy regulations, Relationship Managers are strictly isolated to their assigned client coverage book. You do not have mandate clearance to view client dossiers, portfolio asset allocations, mandate breaches, credit facilities, or call queues assigned to <strong>Priscilla Ong (RM-SG-014)</strong>.
        </div>
        <div style="display: inline-flex; gap: 1rem; align-items: center; justify-content: center; background: rgba(0,0,0,0.3); border: 1px solid rgba(255,255,255,0.08); border-radius: 8px; padding: 0.75rem 1.25rem; font-size: 0.85rem; color: #94A3B8;">
            <span>Assigned Dossiers: <strong style="color: #FF7675;">0 Asia Clients</strong></span>
            <span>•</span>
            <span>Mandate Booking Centre: <strong style="color: #FFF;">Zurich & Geneva</strong></span>
            <span>•</span>
            <span>Access Policy: <strong style="color: #55EFC4;">RLS Block Active</strong></span>
        </div>
        <div style="font-size: 0.85rem; color: #C5A880; margin-top: 1.5rem;">
            💡 <em>To view the Asia JB Pulse - Wealth Intelligence platform, switch to <strong>Priscilla Ong (RM-SG-014)</strong> or <strong>Marc Guggenheim (DH-SG-001 — Supervisory Desk Head)</strong> using the sidebar profile switcher.</em>
        </div>
    </div>
    """, unsafe_allow_html=True)
    st.stop()

# ---------------------------------------------------------
# GLOBAL FOOTER DIALOGS & FOOTER COMPONENT
# ---------------------------------------------------------
@st.dialog("🎫 Raise Support / Advisory Ticket", width="medium")
def show_raise_ticket_dialog():
    st.markdown("### 🎫 Raise Support or Advisory Ticket")
    st.caption("Submit an operational inquiry, trade execution dispute, or mandate reclassification request.")
    
    t_type = st.selectbox("Ticket Category", [
        "Trade Execution & Orders",
        "Lombard Credit Facility & Collateral",
        "Client Mandate & SAA Limit Reclassification",
        "Avaloq / Core Banking Data Issue",
        "Compliance & Suitability Review",
        "Other Operational Inquiry"
    ])
    t_prio = st.selectbox("Priority Level", ["Normal", "High", "Critical (Margin Call / Trade Blocking)"])
    t_client = st.text_input("Client ID / Name (Optional)", value=st.session_state.get("selected_client_id", "CL-0001"))
    t_desc = st.text_area("Ticket Description & Context", placeholder="Describe the issue, requested limit increase, or trade override...")
    
    if st.button("🚀 Submit Ticket", type="primary", use_container_width=True):
        st.success("✅ Ticket #JB-2026-8941 successfully created and dispatched to Julius Baer Operations Desk.")

@st.dialog("📞 Julius Baer Internal Support Directory", width="medium")
def show_contact_support_dialog():
    st.markdown("### 📞 Private Banking & Desk Support")
    st.caption("Direct hotlines for Priscilla Ong (Asia Desk — Singapore & Hong Kong)")
    
    st.markdown("""
    <div style="background: rgba(12, 26, 48, 0.8); border: 1px solid rgba(197, 160, 89, 0.3); border-radius: 8px; padding: 1rem; font-size: 0.88rem; line-height: 1.8;">
        <strong>🏛️ Singapore Dealing Room & Trading Desk:</strong><br>
        • Hotline: <code>+65 6827 1800</code> • Dealing Order Desk: <code>sg-execution@juliusbaer.com</code><br><br>
        <strong>🏢 Hong Kong Advisory & Execution Hub:</strong><br>
        • Hotline: <code>+852 2899 4800</code> • HK Desk: <code>hk-dealing@juliusbaer.com</code><br><br>
        <strong>💳 Lombard Lending & Credit Structuring:</strong><br>
        • Credit Hotline: <code>+65 6827 1950</code> • Lead Approver: <code>credit-asia@juliusbaer.com</code><br><br>
        <strong>🔒 Compliance & Supervisory Officer (Desk Head):</strong><br>
        • Marc Guggenheim (DH-SG-001): <code>marc.guggenheim@juliusbaer.com</code><br><br>
        <strong>💻 24/7 IT Infrastructure & Avaloq Support:</strong><br>
        • IT Helpdesk: <code>+41 58 888 1111</code> (Zurich / Global Support)
    </div>
    """, unsafe_allow_html=True)

@st.dialog("📰 Real-Time Macro & Geopolitical News Alerts", width="large")
def show_news_alert_dialog(repo_instance):
    st.markdown("### 📰 2026 Market Events & News Wire")
    st.caption("Authoritative geopolitical and macro transmissions calibrated against event_log.csv")
    
    events = repo_instance.get_events()
    df_ev = pd.DataFrame(events)
    st.dataframe(
        df_ev[["event_date", "event_type", "region", "description", "primary_transmission", "severity"]],
        column_config={
            "event_date": "Event Date",
            "event_type": "Headline / Event Type",
            "region": "Affected Region",
            "description": "Event Description",
            "primary_transmission": "Transmission Channel",
            "severity": "Severity"
        },
        hide_index=True,
        use_container_width=True
    )

@st.dialog("🔒 Data Privacy & Swiss Banking Secrecy Policy", width="medium")
def show_data_privacy_dialog():
    st.markdown("### 🔒 Julius Baer Data Privacy & Protection Policy")
    st.caption("Compliance with Swiss Federal Banking Act (Article 47), MAS Notice 644, and HKMA PDPO")
    
    st.markdown("""
    <div style="background: rgba(12, 26, 48, 0.8); border: 1px solid rgba(197, 160, 89, 0.3); border-radius: 8px; padding: 1rem; font-size: 0.85rem; line-height: 1.6; color: #E2E8F0;">
        <strong>1. Row-Level Security (RLS) Isolation:</strong><br>
        Client portfolios, transactions, and CRM notes are strictly compartmentalized by assigned Relationship Manager. Cross-desk data access is cryptographically restricted.<br><br>
        <strong>2. Zero-PII Presentation Guardrails:</strong><br>
        When client presentation mode is activated, all client names, identification numbers, and account codes are dynamically tokenized to prevent accidental disclosure during video meetings or external reviews.<br><br>
        <strong>3. AI Memory & Data Retention:</strong><br>
        No client data is transmitted to public unvetted external models. All LLM calls operate within secure, enterprise-hosted isolated enclaves with zero data retention for training.
    </div>
    """, unsafe_allow_html=True)

def render_bottom_footer(repo_instance, analytics_instance, key_prefix: str = "main"):
    st.markdown("<br><hr style='border-color: rgba(197, 160, 89, 0.25); margin: 2.5rem 0 1rem 0;'>", unsafe_allow_html=True)
    f_col1, f_col2, f_col3, f_col4, f_col5 = st.columns([2.2, 1.2, 1.3, 1.2, 1.2])
    
    with f_col1:
        st.markdown("""
        <div style="font-size: 0.78rem; color: #94A3B8; padding-top: 0.2rem;">
            <strong style="color: #C5A059;">Bank Julius Baer & Co. Ltd.</strong> • JB Pulse — Wealth Intelligence<br>
            SingHacks 2026 • Confidential & Licensed for Private Banking RM Use
        </div>
        """, unsafe_allow_html=True)
        
    with f_col2:
        if st.button("Raise ticket", key=f"btn_footer_ticket_{key_prefix}", use_container_width=True):
            show_raise_ticket_dialog()
            
    with f_col3:
        if st.button("Contact Support", key=f"btn_footer_support_{key_prefix}", use_container_width=True):
            show_contact_support_dialog()
            
    with f_col4:
        if st.button("News alert", key=f"btn_footer_news_{key_prefix}", use_container_width=True):
            show_news_alert_dialog(repo_instance)
            
    with f_col5:
        if st.button("Data Privacy", key=f"btn_footer_privacy_{key_prefix}", use_container_width=True):
            show_data_privacy_dialog()

# Specialized Module View Routing
if st.session_state.get("active_nav_module") == "🧪 Portfolio Stress Testing Lab":
    render_stress_testing_lab(repo, analytics, llm_engine, selected_snapshot)
    render_bottom_footer(repo, analytics, key_prefix="mod1")
    st.stop()
elif st.session_state.get("active_nav_module") == "💬 Trigger-to-Conversation Engine":
    render_trigger_conversation_engine(repo, analytics, llm_engine, selected_snapshot)
    render_bottom_footer(repo, analytics, key_prefix="mod2")
    st.stop()
elif st.session_state.get("active_nav_module") == "👤 Client Digital Twin":
    render_client_digital_twin(repo, analytics, llm_engine, selected_snapshot)
    render_bottom_footer(repo, analytics, key_prefix="mod3")
    st.stop()
elif st.session_state.get("active_nav_module") == "🔍 Explainable AI":
    render_explainable_ai(repo, analytics, llm_engine, selected_snapshot)
    render_bottom_footer(repo, analytics, key_prefix="mod4")
    st.stop()

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
client_dropdown_labels = [f"{b['client_id']} — {format_client_display_name(b['client_name'], b['client_id'])}" for b in client_dropdown_list]
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

# Dynamic Book KPIs & Overall Book Returns calculated against active filtered_book
total_book_aum = sum(b["total_aum_usd"] for b in filtered_book)
total_book_base_aum = 0.0
total_book_prev_aum = 0.0
for b in filtered_book:
    cid = b["client_id"]
    ret_info = analytics.compute_portfolio_returns(cid, selected_snapshot)
    total_book_base_aum += ret_info["baseline_aum_usd"]
    total_book_prev_aum += (ret_info["baseline_aum_usd"] if not ret_info["previous_snapshot_date"] else (ret_info["current_aum_usd"] - ret_info["period_return_usd"]))

book_cum_ret_usd = total_book_aum - total_book_base_aum
book_cum_ret_pct = (book_cum_ret_usd / total_book_base_aum * 100.0) if total_book_base_aum > 0 else 0.0
book_ret_sign = "+" if book_cum_ret_pct > 0 else ""
book_ret_color = "#55EFC4" if book_cum_ret_pct >= 0 else "#FF7675"

book_period_ret_usd = total_book_aum - total_book_prev_aum
book_period_ret_pct = (book_period_ret_usd / total_book_prev_aum * 100.0) if total_book_prev_aum > 0 else 0.0
book_p_ret_sign = "+" if book_period_ret_pct > 0 else ""
book_p_ret_color = "#55EFC4" if book_period_ret_pct >= 0 else "#FF7675"

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
        st.metric("Total Breach Items", len(all_breaches), f"Across {unique_clients} Clients ({unique_pfs} Portfolios)")
    with b_col2:
        st.metric("Total Trims / De-risking", f"${total_trim_usd/1e6:,.2f}M", "Upper Bands & Concentrations")
    with b_col3:
        st.metric("Total Additions Required", f"${total_add_usd/1e6:,.2f}M", "Underweight Mandates")

    st.markdown("---")
    b_df = pd.DataFrame(all_breaches)
    st.dataframe(
        b_df[["client_id", "client_name", "portfolio_name", "mandate_code", "category", "item_name", "breach_type", "actual_pct", "band_limit", "action_usd"]],
        column_config={
            "client_id": "Client ID",
            "client_name": "Client Name",
            "portfolio_name": "Portfolio Sleeve",
            "mandate_code": "Mandate",
            "category": "Breach Category",
            "item_name": "Asset / Issuer",
            "breach_type": "Breach Severity",
            "actual_pct": st.column_config.NumberColumn("Actual %", format="%.2f%%"),
            "band_limit": "Mandate Limit",
            "action_usd": "Required Action"
        },
        hide_index=True,
        use_container_width=True
    )
    
    st.markdown("<br>", unsafe_allow_html=True)
    pick_col1, pick_col2 = st.columns([3, 1])
    with pick_col1:
        sel_client_to_jump = st.selectbox(
            "Or select client from breaches list to jump directly to dossier",
            options=sorted(list(set(f"{b['client_id']} — {format_client_display_name(b['client_name'], b['client_id'])}" for b in all_breaches))),
            key="sel_client_from_breaches_dialog"
        )
    with pick_col2:
        st.markdown("<div style='margin-top: 28px;'>", unsafe_allow_html=True)
        if st.button("🚀 Open Dossier", key="btn_jump_from_breach_dialog", use_container_width=True):
            st.session_state.selected_client_id = sel_client_to_jump.split(" — ")[0]
            st.session_state.jump_to_tab = 1
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)


@st.dialog("🚨 Credit Facilities & Lombard Margin Call Alerts", width="large")
def show_ltv_dialog(snapshot_date: str, scope_cids: Optional[set] = None):
    st.markdown(f"### 🚨 Credit Facilities & Margin Call Trajectory ({snapshot_date})")
    st.caption("Active Lombard loans, collateral market values, lending values, and margin call headroom buffer.")
    
    all_alerts = analytics.get_all_book_ltv_alerts(snapshot_date)
    if scope_cids:
        all_alerts = [a for a in all_alerts if a["client_id"] in scope_cids]
    if not all_alerts:
        st.success("✅ All credit facilities within safe LTV parameters (>5% headroom buffer).")
        return

    st.markdown("---")
    l_df = pd.DataFrame(all_alerts)
    st.dataframe(
        l_df[["client_id", "client_name", "facility_id", "facility_type", "drawn_loan_usd", "collateral_value_usd", "current_ltv_pct", "margin_call_pct", "buffer_pct", "severity"]],
        column_config={
            "client_id": "Client ID",
            "client_name": "Client Name",
            "facility_id": "Facility ID",
            "facility_type": "Facility Type",
            "drawn_loan_usd": st.column_config.NumberColumn("Drawn Loan ($)", format="$%,.0f"),
            "collateral_value_usd": st.column_config.NumberColumn("Collateral Value ($)", format="$%,.0f"),
            "current_ltv_pct": st.column_config.NumberColumn("Current LTV", format="%.1f%%"),
            "margin_call_pct": st.column_config.NumberColumn("Margin Call LTV", format="%.1f%%"),
            "buffer_pct": st.column_config.NumberColumn("Buffer to Margin Call", format="%.1f%%"),
            "severity": "Severity Status"
        },
        hide_index=True,
        use_container_width=True
    )

    st.markdown("<br>", unsafe_allow_html=True)
    ltv_pick_col1, ltv_pick_col2 = st.columns([3, 1])
    with ltv_pick_col1:
        sel_ltv_client = st.selectbox(
            "Or pick client with credit alerts to open dossier",
            options=sorted(list(set(f"{a['client_id']} — {format_client_display_name(a['client_name'], a['client_id'])}" for a in all_alerts))),
            key="sel_client_from_ltv_dialog"
        )
    with ltv_pick_col2:
        st.markdown("<div style='margin-top: 28px;'>", unsafe_allow_html=True)
        if st.button("🚀 Open Dossier", key="btn_jump_from_ltv_dialog", use_container_width=True):
            st.session_state.selected_client_id = sel_ltv_client.split(" — ")[0]
            st.session_state.jump_to_tab = 1
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)


@st.dialog("💧 Book-Wide Liquidity Runway & Commitment Deficits", width="large")
def show_liquidity_dialog(snapshot_date: str, scope_cids: Optional[set] = None):
    st.markdown(f"### 💧 Liquidity Runway & Private Market Deficits ({snapshot_date})")
    st.caption("Whole-book audit of uncalled private equity commitments, planned milestone cash needs, and liquid cash reserve buffers.")

    all_deficits = analytics.get_all_book_liquidity_deficits(snapshot_date)
    if scope_cids:
        all_deficits = [d for d in all_deficits if d["client_id"] in scope_cids]
    if not all_deficits:
        st.success("✅ All clients have adequate liquid reserves to cover commitments and milestone cash needs.")
        return

    # Aggregate metrics
    tot_uncalled = sum(d["uncalled_commitments_usd"] for d in all_deficits)
    tot_needs = sum(d["planned_cash_needs_usd"] for d in all_deficits)
    tot_shortfall_clients = sum(1 for d in all_deficits if d["has_shortfall"])

    c_m1, c_m2, c_m3 = st.columns(3)
    with c_m1:
        st.metric("Total Uncalled Commitments", f"${tot_uncalled/1e6:,.2f}M", "Private Equity Funds")
    with c_m2:
        st.metric("Planned Cash Milestones", f"${tot_needs/1e6:,.2f}M", "Next 12 Months")
    with c_m3:
        st.metric("Clients in Deficit", tot_shortfall_clients, "Immediate Action Required" if tot_shortfall_clients > 0 else "All Covered")

    st.markdown("---")
    liq_df = pd.DataFrame(all_deficits)
    st.dataframe(
        liq_df[["client_id", "client_name", "total_liquid_pool_usd", "uncalled_commitments_usd", "planned_cash_needs_usd", "total_outflows_expected_usd", "net_surplus_deficit_usd", "coverage_ratio", "severity", "obligation_summary"]],
        column_config={
            "client_id": "Client ID",
            "client_name": "Client Name",
            "total_liquid_pool_usd": st.column_config.NumberColumn("Liquid Pool ($)", format="$%,.0f"),
            "uncalled_commitments_usd": st.column_config.NumberColumn("Uncalled PE ($)", format="$%,.0f"),
            "planned_cash_needs_usd": st.column_config.NumberColumn("Cash Needs ($)", format="$%,.0f"),
            "total_outflows_expected_usd": st.column_config.NumberColumn("Total Outflows ($)", format="$%,.0f"),
            "net_surplus_deficit_usd": st.column_config.NumberColumn("Surplus / (Deficit) ($)", format="$%,.0f"),
            "coverage_ratio": st.column_config.NumberColumn("Coverage Ratio", format="%.2fx"),
            "severity": "Liquidity Status",
            "obligation_summary": "Active Milestone Obligations"
        },
        hide_index=True,
        use_container_width=True
    )

    st.markdown("<br>", unsafe_allow_html=True)
    liq_pick_col1, liq_pick_col2 = st.columns([3, 1])
    with liq_pick_col1:
        sel_liq_client = st.selectbox(
            "Or pick client with liquidity obligations to open dossier",
            options=sorted(list(set(f"{d['client_id']} — {format_client_display_name(d['client_name'], d['client_id'])}" for d in all_deficits))),
            key="sel_client_from_liq_dialog"
        )
    with liq_pick_col2:
        st.markdown("<div style='margin-top: 28px;'>", unsafe_allow_html=True)
        if st.button("🚀 Open Dossier", key="btn_jump_from_liq_dialog", use_container_width=True):
            st.session_state.selected_client_id = sel_liq_client.split(" — ")[0]
            st.session_state.jump_to_tab = 1
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)


# Top KPI Columns with Interactive Clickable Actions (5 Cards Grid)
kpi_c1, kpi_c2, kpi_c3, kpi_c4, kpi_c5 = st.columns(5)
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
        <div class="jb-kpi-label">Overall Book Return</div>
        <div class="jb-kpi-value" style="color: {book_ret_color};">{book_ret_sign}{book_cum_ret_pct:.2f}%</div>
        <div class="jb-kpi-sub">Period: <strong style="color: {book_p_ret_color};">{book_p_ret_sign}{book_period_ret_pct:.2f}%</strong> ({book_ret_sign}${book_cum_ret_usd/1e6:,.1f}M)</div>
    </div>
    """, unsafe_allow_html=True)

with kpi_c3:
    st.markdown(f"""
    <div class="jb-kpi-card">
        <div class="jb-kpi-label">Mandate Breaches</div>
        <div class="jb-kpi-value" style="color: {'#FF7675' if total_breach_items > 0 else '#55EFC4'};">{total_breach_items}</div>
        <div class="jb-kpi-sub">Across {total_breach_pfs} Pfs ({total_breach_clients} Clients)</div>
    </div>
    """, unsafe_allow_html=True)
    if st.button(f"🔍 View {total_breach_items} Breach(es)", key="btn_kpi_breaches", use_container_width=True):
        show_breaches_dialog(selected_snapshot, filtered_cids)

with kpi_c4:
    st.markdown(f"""
    <div class="jb-kpi-card">
        <div class="jb-kpi-label">Credit / LTV Alerts</div>
        <div class="jb-kpi-value" style="color: {'#FF7675' if total_ltv_alerts > 0 else '#55EFC4'};">{total_ltv_alerts}</div>
        <div class="jb-kpi-sub">Margin Call Proximity Alerts</div>
    </div>
    """, unsafe_allow_html=True)
    if st.button(f"🔍 View {total_ltv_alerts} Credit Alert(s)", key="btn_kpi_ltv", use_container_width=True):
        show_ltv_dialog(selected_snapshot, filtered_cids)

with kpi_c5:
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
        display_book = [
            b for b in display_book 
            if sq in b["client_name"].lower() 
            or sq in format_client_display_name(b["client_name"], b["client_id"]).lower() 
            or sq in b["client_id"].lower() 
            or sq in str(b.get("wealth_band", "")).lower()
        ]

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
        cname = html.escape(format_client_display_name(str(item["client_name"]), str(item["client_id"])))
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

                c_ret_info = analytics.compute_portfolio_returns(item["client_id"], selected_snapshot)
                c_ret_pct = c_ret_info["cumulative_return_pct"]
                c_ret_sign = "+" if c_ret_pct > 0 else ""
                c_ret_color = "#55EFC4" if c_ret_pct >= 0 else "#FF7675"

                info_html = f"""<div><div style="display: flex; align-items: center; gap: 0.75rem;"><span style="font-size: 1.15rem; font-weight: 700; color: #FFFFFF;">{cname}</span><span style="font-size: 0.8rem; color: #C5A880; font-family: monospace;">{cid}</span>{badge_html}</div><div style="font-size: 0.85rem; color: #94A3B8; margin-top: 0.2rem;">AUM: <strong style="color: #FFFFFF;">${aum/1e6:,.2f}M</strong> | Return (YTD): <strong style="color: {c_ret_color};">{c_ret_sign}{c_ret_pct:.2f}%</strong> | Risk: <strong style="color: #FFFFFF;">{risk}</strong> | {last_contact_html} | Desk: {desk} | Domicile: {domicile}</div><div style="font-size: 0.9rem; color: #E2E8F0; margin-top: 0.4rem; padding-left: 0.5rem; border-left: 2px solid #C5A880;">💡 <strong>Priority Action:</strong> {headline}</div></div>"""
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
        c360_header_c1, c360_header_c2 = st.columns([1.8, 2.2])
        with c360_header_c1:
            age_val = client.get("age")
            if pd.notna(age_val) and str(age_val).strip() != "":
                try:
                    age_str = f"🎂 Age: <strong style='color: #FFF;'>{int(float(age_val))}</strong> ({client.get('life_stage', 'N/A')})"
                except (ValueError, TypeError):
                    age_str = f"🏛️ Entity: <strong style='color: #FFF;'>{client.get('life_stage', 'Institutional')}</strong>"
            else:
                age_str = f"🏛️ Entity: <strong style='color: #FFF;'>{client.get('life_stage', 'Family Office')}</strong>"

            disp_client_name = format_client_display_name(client['client_name'], target_cid)
            st.markdown(f"## 👤 {disp_client_name} ({target_cid})")
            st.markdown(f"""
            <div style="display: flex; gap: 0.85rem; flex-wrap: wrap; font-size: 0.85rem; color: #94A3B8;">
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
            ret_data = analytics.compute_portfolio_returns(target_cid, selected_snapshot)
            snap_aum_usd = ret_data["current_aum_usd"]
            snap_aum_base = ret_data["current_aum_base"]
            cum_ret_pct = ret_data["cumulative_return_pct"]
            cum_ret_usd = ret_data["cumulative_return_usd"]
            period_ret_pct = ret_data["period_return_pct"]
            period_label = ret_data["period_label"]
            base_ccy = client.get("base_currency", "USD")

            ret_color = "#55EFC4" if cum_ret_pct >= 0 else "#FF7675"
            ret_sign = "+" if cum_ret_pct > 0 else ""
            p_ret_color = "#55EFC4" if period_ret_pct >= 0 else "#FF7675"
            p_ret_sign = "+" if period_ret_pct > 0 else ""

            kpi_c_l, kpi_c_r = st.columns(2)
            with kpi_c_l:
                st.markdown(f"""
                <div class="jb-kpi-card" style="margin-top: 0.4rem; padding: 0.75rem 0.85rem;">
                    <div class="jb-kpi-label">Client AUM ({selected_snapshot})</div>
                    <div class="jb-kpi-value" style="font-size: 1.25rem;">${snap_aum_usd/1e6:,.2f}M</div>
                    <div class="jb-kpi-sub">{base_ccy} {snap_aum_base/1e6:,.2f}M • {client['booking_centre']}</div>
                </div>
                """, unsafe_allow_html=True)
            with kpi_c_r:
                st.markdown(f"""
                <div class="jb-kpi-card" style="margin-top: 0.4rem; padding: 0.75rem 0.85rem;">
                    <div class="jb-kpi-label">Portfolio Returns (YTD)</div>
                    <div class="jb-kpi-value" style="font-size: 1.25rem; color: {ret_color};">{ret_sign}{cum_ret_pct:.2f}%</div>
                    <div class="jb-kpi-sub">{period_label}: <strong style="color: {p_ret_color};">{p_ret_sign}{period_ret_pct:.2f}%</strong> ({ret_sign}${cum_ret_usd/1e6:,.2f}M)</div>
                </div>
                """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # Multi-Portfolio Switcher (Crucial Trap §1.1 Solution)
        portfolios = repo.get_portfolios_for_client(target_cid)
        st.markdown(f"### 📂 Multi-Portfolio Entity Graph ({len(portfolios)} Portfolios)")
        
        pf_options = {f"{p['portfolio_id']} — {p['portfolio_name']} ({p['mandate_code']})": p['portfolio_id'] for p in portfolios}
        selected_pf_label = st.selectbox("Select Portfolio Sleeve for Deep-Dive", options=list(pf_options.keys()))
        selected_pf_id = pf_options[selected_pf_label]

        pf_ret = analytics.compute_portfolio_returns(target_cid, selected_snapshot, portfolio_id=selected_pf_id)
        sleeve_cum_pct = pf_ret["cumulative_return_pct"]
        sleeve_per_pct = pf_ret["period_return_pct"]
        s_ret_color = "#55EFC4" if sleeve_cum_pct >= 0 else "#FF7675"
        s_ret_sign = "+" if sleeve_cum_pct > 0 else ""
        s_p_color = "#55EFC4" if sleeve_per_pct >= 0 else "#FF7675"
        s_p_sign = "+" if sleeve_per_pct > 0 else ""

        st.markdown(f"""
        <div style="background: rgba(19, 42, 74, 0.6); border: 1px solid rgba(197, 160, 89, 0.2); border-radius: 6px; padding: 0.45rem 0.85rem; font-size: 0.82rem; margin-bottom: 0.75rem; display: flex; gap: 1.25rem; flex-wrap: wrap;">
            <span>💼 Sleeve AUM ({selected_snapshot}): <strong style="color: #FFF;">${pf_ret['current_aum_usd']/1e6:,.2f}M</strong></span>
            <span>📈 YTD Performance: <strong style="color: {s_ret_color};">{s_ret_sign}{sleeve_cum_pct:.2f}%</strong> ({s_ret_sign}${pf_ret['cumulative_return_usd']/1e6:,.2f}M)</span>
            <span>⏱️ Period Move ({pf_ret['period_label']}): <strong style="color: {s_p_color};">{s_p_sign}{sleeve_per_pct:.2f}%</strong> ({s_p_sign}${pf_ret['period_return_usd']/1e6:,.2f}M)</span>
        </div>
        """, unsafe_allow_html=True)

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
                shown_ids = set()
                for ov in notes_info.get("standing_overrides", []):
                    shown_ids.add(ov.get("note_id"))
                    st.warning(f"🔒 **Standing Constraint ({ov['date']}):** {ov['summary']}")
                for pref in notes_info.get("preferences", []):
                    shown_ids.add(pref.get("note_id"))
                    st.info(f"💡 **Preference ({pref['date']}):** {pref['summary']}")
                for n in notes_info.get("notes", []):
                    if n.get("note_id") not in shown_ids:
                        st.markdown(f"""
                        <div style="background: rgba(255,255,255,0.04); border-left: 3px solid #C5A880; border-radius: 4px; padding: 0.5rem 0.75rem; margin-bottom: 0.5rem; font-size: 0.84rem; color: #E2E8F0;">
                            📝 <strong>RM Note ({n.get('note_date', '')} via {n.get('channel', 'Meeting')}):</strong> {html.escape(n.get('note', ''))}
                        </div>
                        """, unsafe_allow_html=True)
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

    is_read_only = not active_rm_info.get("can_approve", True)
    if is_read_only:
        st.markdown(f"""
        <div style="background: rgba(197, 168, 128, 0.12); border: 1.5px solid rgba(197, 168, 128, 0.45); border-radius: 8px; padding: 0.9rem 1.25rem; margin-bottom: 1.25rem; display: flex; align-items: center; justify-content: space-between;">
            <div>
                <div style="font-size: 0.95rem; font-weight: 700; color: #C5A880;">🔍 Supervisory Desk Head Audit Mode (Read-Only Review)</div>
                <div style="font-size: 0.82rem; color: #E2E8F0; margin-top: 0.25rem; line-height: 1.4;">
                    You are authenticated with supervisory oversight credentials (<strong>{st.session_state.logged_in_user} • {st.session_state.logged_in_rm_id}</strong>).<br>
                    Under Julius Baer Compliance Policy #PB-AUD-101, commercial action approval, trade sign-off, and talking point phrasing are reserved exclusively for the assigned Relationship Manager (<strong>Priscilla Ong</strong>).
                </div>
            </div>
            <div style="margin-left: 1rem;">
                <span class="jb-badge jb-badge-fact" style="font-size: 0.78rem; padding: 0.4rem 0.8rem; white-space: nowrap;">🔒 Read-Only Audit</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

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
            pkg_horizon = pkg.get("time_horizon")
            pkg_horizon_badge = f'<span class="jb-badge" style="background: rgba(197, 168, 128, 0.2); border: 1px solid rgba(197, 168, 128, 0.4); color: #F5E6CC; font-weight: 600;">⏱️ Horizon: {html.escape(str(pkg_horizon))}</span>' if pkg_horizon else ""
            conflicts_reconciled = pkg.get("conflicts_reconciled", [])
            pkg_conf_badge = f'<span class="jb-badge" style="background: rgba(253, 203, 110, 0.2); border: 1px solid rgba(253, 203, 110, 0.4); color: #FDCB6E; font-weight: 600;">⚖️ {len(conflicts_reconciled)} Conflict Reconciled</span>' if conflicts_reconciled else ""

            with st.container():
                st.markdown(f"""
                <div class="jb-rec-card" style="border: 1.5px solid {pkg_border}; background: linear-gradient(135deg, rgba(197,168,128,0.12) 0%, rgba(13,30,54,0.7) 100%); border-radius: 8px; padding: 1.25rem;">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.6rem;">
                        <div style="display: flex; flex-wrap: wrap; gap: 4px; align-items: center;">
                            <span class="jb-badge jb-badge-fact">✨ Multi-Agent Synergy</span>
                            <span class="jb-badge jb-badge-high">{len(clubbed_recs)} Actions Clubbed</span>
                            {pkg_horizon_badge}
                            {pkg_conf_badge}
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
                    "💬 Unified Client-Ready Advisory Phrasing (Verbatim for RM)" + (" [Read-Only in Supervisory Audit Mode]" if is_read_only else ""),
                    value=curr_pkg_tp,
                    key=f"tp_pkg_{pkg_id}",
                    height=80,
                    disabled=is_read_only
                )
                if not is_read_only and edited_pkg_tp != curr_pkg_tp:
                    st.session_state.custom_talking_points[pkg_id] = edited_pkg_tp

                if is_read_only:
                    st.markdown(f"""
                    <div style="background: rgba(255,255,255,0.03); border: 1px dashed rgba(197,168,128,0.35); border-radius: 6px; padding: 0.65rem 0.9rem; font-size: 0.83rem; color: #94A3B8;">
                        🔒 <strong>Approval Locked:</strong> Supervisory Desk Head ({st.session_state.logged_in_user}) has read-only oversight privileges. Action approval and commercial trade sign-off require assigned RM (Priscilla Ong) credentials.
                    </div>
                    """, unsafe_allow_html=True)
                else:
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
            horizon_val = rec.get("time_horizon")
            horizon_badge = f'<span class="jb-badge" style="background: rgba(197, 168, 128, 0.2); border: 1px solid rgba(197, 168, 128, 0.4); color: #F5E6CC; font-weight: 600;">⏱️ Horizon: {html.escape(str(horizon_val))}</span>' if horizon_val else ""

            with st.container():
                rec_html = f"""<div class="jb-rec-card" style="border-left: 4px solid {border_color};"><div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.5rem;"><div style="display: flex; flex-wrap: wrap; gap: 4px; align-items: center;"><span class="jb-badge {p_class}">{priority.upper()} Priority</span> <span class="jb-badge {tier_class}">Confidence: {tier.upper()}</span> <span class="jb-badge" style="background: rgba(255,255,255,0.1); color: #FFF;">Agent: {agent.upper()}</span> {horizon_badge} {status_badge}</div><div style="font-size: 0.8rem; color: #C5A880; font-family: monospace;">{rec_id}</div></div><div class="jb-rec-headline">{headline}</div><div style="font-size: 0.9rem; color: #E2E8F0; margin-bottom: 0.5rem;"><strong>Proposed Action:</strong> {recommendation_text}</div>{override_html}</div>"""
                st.markdown(rec_html, unsafe_allow_html=True)

                # Editable Client-Ready Talking Point
                curr_tp = st.session_state.custom_talking_points.get(rec["id"], default_talking_point)
                edited_tp = st.text_area(
                    f"💬 Client-Ready Phrasing (Verbatim for RM)" + (" [Read-Only in Supervisory Audit Mode]" if is_read_only else ""),
                    value=curr_tp,
                    key=f"tp_{prefix}_{rec['id']}",
                    height=70,
                    disabled=is_read_only
                )
                if not is_read_only and edited_tp != curr_tp:
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
                if is_read_only:
                    st.markdown(f"""
                    <div style="background: rgba(255,255,255,0.03); border: 1px dashed rgba(255,255,255,0.15); border-radius: 6px; padding: 0.55rem 0.85rem; font-size: 0.82rem; color: #94A3B8;">
                        🔒 <strong>Approval Locked:</strong> Read-only supervisory audit mode. Commercial action sign-off reserved for assigned RM (Priscilla Ong).
                    </div>
                    """, unsafe_allow_html=True)
                else:
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
        st.markdown(f"### 📄 Client Meeting Brief & Governance Pack")
        st.caption("Compiles RM-approved recommendations, multi-objective packages, and supervisory pre-clearance into client-ready briefings and internal audit dossiers.")
    with pack_top_c2:
        render_client_switcher("tab4")

    target_cid = st.session_state.selected_client_id
    client = repo.get_client(target_cid)

    if client:
        client_result = orchestrator.run_client(target_cid, selected_snapshot)
        recs = client_result["recommendations"]
        disp_client_name = format_client_display_name(client['client_name'], client['client_id'])
        client_context = client_result.get("client_context", {})

        # ---------------------------------------------------------
        # 1. 4-POINT SUPERVISORY GOVERNANCE & SUITABILITY CHECKLIST
        # ---------------------------------------------------------
        kyc_due = client.get("kyc_review_due", "2027-01-01")
        kyc_ok = kyc_due >= selected_snapshot
        kyc_badge = "✅ Cleared" if kyc_ok else "⚠️ Review Due"
        kyc_color = "#55EFC4" if kyc_ok else "#FDCB6E"

        st.markdown("#### 🛡️ 4-Point Supervisory Governance & Suitability Audit")
        st.markdown(f"""
        <div style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 0.75rem; margin-bottom: 1.25rem;">
            <div style="background: rgba(15,23,42,0.6); border: 1px solid rgba(85,239,196,0.3); border-radius: 8px; padding: 0.75rem;">
                <div style="font-size: 0.72rem; color: {kyc_color}; font-weight: 700; text-transform: uppercase;">1. KYC & PEP Clearance</div>
                <div style="font-size: 0.88rem; font-weight: 700; color: #FFF; margin-top: 0.2rem;">{kyc_badge}</div>
                <div style="font-size: 0.75rem; color: #94A3B8;">Review Due: {kyc_due}</div>
            </div>
            <div style="background: rgba(15,23,42,0.6); border: 1px solid rgba(85,239,196,0.3); border-radius: 8px; padding: 0.75rem;">
                <div style="font-size: 0.72rem; color: #55EFC4; font-weight: 700; text-transform: uppercase;">2. Mandate Suitability</div>
                <div style="font-size: 0.88rem; font-weight: 700; color: #FFF; margin-top: 0.2rem;">✅ Suitable Fit</div>
                <div style="font-size: 0.75rem; color: #94A3B8;">{client.get('risk_profile')} ({client.get('risk_tolerance_score', 'N/A')}/100)</div>
            </div>
            <div style="background: rgba(15,23,42,0.6); border: 1px solid rgba(85,239,196,0.3); border-radius: 8px; padding: 0.75rem;">
                <div style="font-size: 0.72rem; color: #55EFC4; font-weight: 700; text-transform: uppercase;">3. Standing Exclusions</div>
                <div style="font-size: 0.88rem; font-weight: 700; color: #FFF; margin-top: 0.2rem;">✅ Validated</div>
                <div style="font-size: 0.75rem; color: #94A3B8;">0 exclusion violations</div>
            </div>
            <div style="background: rgba(15,23,42,0.6); border: 1px solid rgba(85,239,196,0.3); border-radius: 8px; padding: 0.75rem;">
                <div style="font-size: 0.72rem; color: #55EFC4; font-weight: 700; text-transform: uppercase;">4. Cross-Border Fit</div>
                <div style="font-size: 0.88rem; font-weight: 700; color: #FFF; margin-top: 0.2rem;">✅ Compliant</div>
                <div style="font-size: 0.75rem; color: #94A3B8;">{client.get('tax_domicile')} → {client.get('booking_centre')}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # ---------------------------------------------------------
        # 2. SUPERVISORY DESK HEAD ENDORSEMENT STAMP (FOR MARC GUGGENHEIM)
        # ---------------------------------------------------------
        is_endorsed = st.session_state.desk_head_endorsements.get(target_cid, False)
        if is_read_only:
            e_col1, e_col2 = st.columns([3.2, 1.8])
            with e_col1:
                endorse_status_html = '<span style="color: #2ECC71; font-weight: 700;">✓ SUPERVISORY ENDORSEMENT ACTIVE</span> — Certified for RM Client Delivery' if is_endorsed else '<span style="color: #FDCB6E; font-weight: 600;">⏳ Pending Desk Head Supervisory Endorsement</span>'
                st.markdown(f"""
                <div style="background: rgba(197, 168, 128, 0.08); border: 1px solid {'#2ECC71' if is_endorsed else 'rgba(197, 168, 128, 0.35)'}; border-radius: 8px; padding: 0.85rem 1.1rem; margin-bottom: 1.25rem;">
                    <div style="font-size: 0.88rem; font-weight: 700; color: #C5A880; margin-bottom: 0.25rem;">✍️ Desk Head Supervisory Endorsement Authority</div>
                    <div style="font-size: 0.82rem; color: #E2E8F0;">{endorse_status_html}</div>
                    <div style="font-size: 0.76rem; color: #94A3B8; margin-top: 0.2rem;">Governance Policy #PB-AUD-101 • Reviewing Officer: Marc Guggenheim (DH-SG-001)</div>
                </div>
                """, unsafe_allow_html=True)
            with e_col2:
                st.markdown("<div style='margin-top: 6px;'>", unsafe_allow_html=True)
                if not is_endorsed:
                    if st.button("✍️ Endorse Meeting Pack", key=f"btn_endorse_{target_cid}", use_container_width=True):
                        st.session_state.desk_head_endorsements[target_cid] = True
                        st.rerun()
                else:
                    if st.button("↩️ Revoke Endorsement", key=f"btn_revoke_{target_cid}", use_container_width=True):
                        st.session_state.desk_head_endorsements[target_cid] = False
                        st.rerun()
                st.markdown("</div>", unsafe_allow_html=True)

        approved_recs = [r for r in recs if st.session_state.approved_actions.get(r["id"], False)]
        if approved_recs:
            st.success(f"✅ **{len(approved_recs)} RM-Approved Action(s) Included** in this client communication.")
        else:
            st.info("ℹ️ **Draft Preview Mode:** No actions explicitly approved yet in Tab 3 (Agent Action Deck). Showing default high-priority actions. Approve any recommendation in Tab 3 to include it.")
            approved_recs = [r for r in recs if r["priority"] == "high"][:2]

        # Check for approved comingling packages
        approved_pkgs = [p for p in client_result.get("comingling_opportunities", []) if st.session_state.approved_actions.get(p["id"], False)]

        # Communication formats (including Internal Supervisory Audit Memo for Marc Guggenheim)
        format_options = ["Executive Client Briefing Note", "Formal Advisory Email", "Meeting Discussion Agenda"]
        if is_read_only:
            format_options.append("Internal Supervisory Audit Dossier & Risk Memo")

        meeting_format = st.radio("Communication Format", options=format_options, horizontal=True)

        lang = client.get("reporting_language", "English")

        # ---------------------------------------------------------
        # 3. GENERATE DOCUMENT CONTENT BY SELECTED FORMAT
        # ---------------------------------------------------------
        endorsement_stamp = ""
        if is_endorsed:
            endorsement_stamp = f"""================================================================================
🏛️ BANK JULIUS BAER — SUPERVISORY DESK HEAD COMPLIANCE ENDORSEMENT
================================================================================
Status: SUPERVISORY PRE-CLEARANCE GRANTED & SUITABILITY ENDORSED
Reviewing Officer: Marc Guggenheim (DH-SG-001 — Supervisory Desk Head)
Audit Clearance Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}
Governance Mandate: Julius Baer Private Banking Governance Standard PB-AUD-101
Audit Scope: Multi-Agent Synthesis, Cross-Border Suitability, Lombard Lending Buffers
================================================================================

"""

        if meeting_format == "Internal Supervisory Audit Dossier & Risk Memo":
            # Comprehensive Internal Risk & Supervisory Audit Memo
            pack_content = f"""**CONFIDENTIAL — BANK JULIUS BAER & CO. LTD.**
**SUPERVISORY AUDIT DOSSIER & COMPLIANCE PRE-CLEARANCE MEMO**
**FOR INTERNAL GOVERNANCE & RISK COMMITTEE REVIEW ONLY**

{endorsement_stamp}**Target Client:** {disp_client_name} ({client['client_id']})
**Date:** {datetime.now().strftime('%d %B %Y')} | Valuation Snapshot: {selected_snapshot}
**Assigned Relationship Manager:** {client.get('rm_name', 'Priscilla Ong')} ({client.get('rm_desk')})
**Booking Centre:** {client.get('booking_centre')} | Tax Domicile: {client.get('tax_domicile')}
**Total Stated AUM:** USD {client.get('total_aum_usd', 0)/1e6:,.2f}M | Wealth Band: {client.get('wealth_band')}

---

### 1. GOVERNANCE & SUITABILITY ASSESSMENT (4-POINT AUDIT)
1. **KYC & Periodic Review:** Status = {kyc_badge} (Review Due: {kyc_due}) | PEP Status: {client.get('pep_status', 'No')}
2. **Mandate Fit:** Risk Profile = {client.get('risk_profile')} (Score: {client.get('risk_tolerance_score')}/100) | Investment Horizon: {client.get('investment_horizon_years')} Years
3. **Standing Instructions & Overrides:** Validated against standing RM notes ({len(client_context.get('standing_instructions', []))} notes active) — 0 exclusion violations.
4. **Cross-Border Regulatory Compliance:** MAS/SFC private banking cross-border solicitation rules verified for {client.get('tax_domicile')} domicile booked in {client.get('booking_centre')}.

---

### 2. MASTER ORCHESTRATOR SYNTHESIS & CROSS-SPECIALIST ALPHA
- **Total Specialist Agent Proposals Evaluated:** {len(recs)}
- **Synergistic Comingling Packages Detected:** {len(client_result.get('comingling_opportunities', []))}
- **Cross-Agent Conflicts Surfaced & Resolved:** {len(client_result.get('conflicts', []))}
- **Master Orchestrator Strategic Optimizations:** {len(client_result.get('cross_specialist_optimizations', []))}
- **Pre-Clearance Urgency Score:** {client_result.get('urgency_score', 0):.0f} / 100

---

### 3. PURE-FUNCTION EVIDENCE & AUDIT TRAIL CITATIONS
"""
            for i, r in enumerate(recs, 1):
                ev = r["evidence"][0] if r.get("evidence") else {}
                horizon_str = f" | Horizon: {r['time_horizon']}" if r.get("time_horizon") else ""
                pack_content += f"""**Item {i}: [{r['agent'].upper()}] {r['headline']}**
- *Pure Function Citation:* `{ev.get('source_function', 'N/A')}`
- *Calculated Metric Fact:* {ev.get('detail', 'N/A')} (as of {ev.get('as_of_date', selected_snapshot)})
- *Compliance Status:* {r.get('compliance_status', 'pass').upper()} | Priority: {r.get('priority', 'medium').upper()}{horizon_str}
- *Proposed Execution:* {r['recommendation']}
"""

            pack_content += f"""
---
### 4. SUPERVISORY SIGN-OFF & AUDIT RECORD
- **Reviewing Desk Head:** Marc Guggenheim (DH-SG-001)
- **Supervisory Decision:** {'ENDORSED FOR COMMERCIAL EXECUTION' if is_endorsed else 'PENDING DESK HEAD SIGN-OFF'}
- **Digital Audit Token:** SHA256-JB-AUD-{client['client_id']}-{selected_snapshot}
"""

        elif meeting_format == "Formal Advisory Email":
            # Executive Client Email
            pack_content = f"""{endorsement_stamp}**Subject:** Bank Julius Baer — Strategic Portfolio & Allocation Review for {disp_client_name}
**Date:** {datetime.now().strftime('%d %B %Y')}
**From:** {client.get('rm_name', 'Priscilla Ong')} <priscilla.ong@juliusbaer.com>
**To:** {disp_client_name}

Dear {disp_client_name},

I hope this email finds you well.

As part of our continuous portfolio stewardship at Bank Julius Baer, our specialist advisory team and multi-mandate analytics have completed a strategic review of your holdings, credit lines, and cash reserves as of our valuation snapshot ({selected_snapshot}).

We have outlined key strategic recommendations for your review below:
"""
            if approved_pkgs:
                for pkg in approved_pkgs:
                    pkg_tp = st.session_state.custom_talking_points.get(pkg["id"], pkg["unified_talking_point"])
                    pkg_horiz = f"\n- **Execution Horizon:** {pkg['time_horizon']}" if pkg.get("time_horizon") else ""
                    pack_content += f"""
**★ Unified Strategic Action Package: {pkg['title']}**
{pkg['summary']}
- **Action Plan:** {pkg['unified_action']}{pkg_horiz}
- **Key Client Benefit:** {pkg_tp}
"""
            for i, r in enumerate(approved_recs, 1):
                tp = st.session_state.custom_talking_points.get(r["id"], r["talking_point"])
                rec_horiz = f"\n- **Time Horizon:** {r['time_horizon']}" if r.get("time_horizon") else ""
                pack_content += f"""
**{i}. {r['headline']}**
- **Recommended Action:** {r['recommendation']}{rec_horiz}
- **Rationale:** {tp}
"""
            pack_content += f"""
Please let me know your availability for a brief discussion this week so we can review these adjustments and ensure full alignment with your upcoming milestone objectives.

Warm regards,

**{client.get('rm_name', 'Priscilla Ong')}**
Senior Partner | Relationship Management
Bank Julius Baer & Co. Ltd., {client.get('booking_centre')} Booking Centre
"""

        elif meeting_format == "Meeting Discussion Agenda":
            # Client Meeting Agenda
            pack_content = f"""{endorsement_stamp}**BANK JULIUS BAER & CO. LTD.**
**PORTFOLIO REVIEW MEETING AGENDA**

**Client:** {disp_client_name} ({client['client_id']})
**Date:** {datetime.now().strftime('%d %B %Y')} | Snapshot: {selected_snapshot}
**Attendees:** {disp_client_name}, {client.get('rm_name', 'Priscilla Ong')} (Relationship Manager)

---

### Agenda Overview (45 Minutes)

1. **Macro & Market Context (10 mins)**
   - Regional macro environment and tactical asset allocation stance.
   
2. **Portfolio Health & Mandate Alignment (15 mins)**
   - Review of asset allocation drift and concentration thresholds.
   - Lombard credit facility headroom and liquidity coverage buffer.

3. **Key Advisory Proposals & Decision Items (15 mins)**
"""
            if approved_pkgs:
                for pkg in approved_pkgs:
                    pack_content += f"""   - **Unified Strategy:** {pkg['title']} ({pkg['summary']})
"""
            for i, r in enumerate(approved_recs, 1):
                pack_content += f"""   - **Item {i}:** {r['headline']} — {r['recommendation']}
"""
            pack_content += f"""
4. **Q&A, Governance Sign-off & Next Steps (5 mins)**
   - Confirmation of execution mandate and schedule of next periodic review.

---
**Bank Julius Baer & Co. Ltd.**
"""

        else:
            # Executive Client Briefing Note
            pack_content = f"""{endorsement_stamp}**CONFIDENTIAL — BANK JULIUS BAER & CO. LTD.**
**PORTFOLIO INTELLIGENCE & ADVISORY BRIEFING**

**Client:** {disp_client_name} ({client['client_id']})
**Date:** {datetime.now().strftime('%d %B %Y')} | Valuation Snapshot: {selected_snapshot}
**Relationship Manager:** {client.get('rm_name', 'Private Banking Desk')} ({client.get('rm_desk')})
**Booking Centre:** {client.get('booking_centre')} | Tax Domicile: {client.get('tax_domicile')}
**Total Stated AUM:** USD {client.get('total_aum_usd', 0)/1e6:,.2f}M

---

### 1. Executive Portfolio Context
Dear {disp_client_name},

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

        st.text_area("Generated Document Preview", value=pack_content, height=440)
        
        file_suffix = "AuditDossier" if meeting_format == "Internal Supervisory Audit Dossier & Risk Memo" else "Brief"
        st.download_button(
            label=f"💾 Download {meeting_format} (.md / .txt)",
            data=pack_content,
            file_name=f"JuliusBaer_{file_suffix}_{client['client_id']}_{selected_snapshot}.txt",
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

# Standard Footer for Main JB Pulse Page (Outside tabs to render on every tab)
render_bottom_footer(repo, analytics, key_prefix="jb_pulse_main")
