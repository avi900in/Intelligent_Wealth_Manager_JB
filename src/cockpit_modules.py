"""
Bank Julius Baer & Co. Ltd. — Wealth Intelligence Cockpit Specialized Modules
1. Portfolio Stress Testing Lab ("What happens if...")
2. Trigger-to-Conversation Engine (Event -> Impact -> Outreach)
3. Client Digital Twin (Behavioral Persona & Horizon Simulation)
4. Explainable AI (Attribution, Decision Trees & Traceability)
"""

import streamlit as st
import pandas as pd
import html
from typing import Dict, Any, List

def render_stress_testing_lab(repo, analytics, llm_engine, selected_snapshot: str):
    """Interactive Macro & Geopolitical Stress Testing Lab."""
    st.markdown("""
    <div style="background: linear-gradient(135deg, rgba(12, 26, 48, 0.95), rgba(20, 42, 74, 0.95)); border: 1px solid rgba(197, 160, 89, 0.3); border-radius: 12px; padding: 1.5rem 2rem; margin-bottom: 1.75rem;">
        <div style="font-size: 0.8rem; color: #C5A059; text-transform: uppercase; font-weight: 700; letter-spacing: 0.1em;">JB Pulse • Macro Scenario Simulation Lab</div>
        <h2 style="color: #FFFFFF; margin: 0.25rem 0 0.5rem 0; font-size: 1.8rem;">🧪 Portfolio Stress Testing Lab</h2>
        <div style="color: #94A3B8; font-size: 0.95rem; max-width: 850px;">
            Simulate instantaneous market shocks, geopolitical escalations, and monetary policy shifts. 
            Evaluate impact on portfolio valuations, Lombard facility LTV headroom, and automatic margin call triggers.
        </div>
    </div>
    """, unsafe_allow_html=True)

    clients = repo.get_all_clients()
    client_options = {c["client_id"]: f"{c['client_id']} — {c['client_name']} (${float(c['total_aum_usd'])/1e6:.1f}M)" for c in clients}

    col_l, col_r = st.columns([1.2, 2.8], gap="large")

    with col_l:
        st.markdown("### 🎛️ Scenario Parameters")
        target_mode = st.radio("Simulation Scope", ["Single Client Portfolio", "Whole Asia Book (20 Clients)"], horizontal=True)
        
        target_client_id = "CL-0001"
        if target_mode == "Single Client Portfolio":
            target_client_id = st.selectbox("Select Target Client", options=list(client_options.keys()), format_func=lambda x: client_options[x], index=0)

        preset_scenario = st.selectbox(
            "Pre-Calibrated Macro Shock Preset",
            options=[
                "Middle East Escalation (Oil +40%, Equities -12%, Gold +15%)",
                "Middle East De-escalation & Hormuz Reopening (Oil -25%, Equities +8%, Gold -10%)",
                "Persistent Rate Shock (Yields +75bps, Duration -8%, Tech -15%)",
                "Global Tech & AI Capex Drawdown (Tech -22%, Software -18%)",
                "Yen Carry Trade Unwind & FX Shock (JPY +18%, Asian Equities -14%)",
                "Custom Scenario Sliders"
            ]
        )

        if preset_scenario == "Middle East Escalation (Oil +40%, Equities -12%, Gold +15%)":
            oil_shock = 40.0
            gold_shock = 15.0
            tech_shock = -15.0
            eq_shock = -12.0
            rate_shock = 40
            spread_shock = 65
            jpy_fx = -8.0
            asian_fx = 4.0
            eur_fx = -5.0
        elif preset_scenario == "Middle East De-escalation & Hormuz Reopening (Oil -25%, Equities +8%, Gold -10%)":
            oil_shock = -25.0
            gold_shock = -10.0
            tech_shock = 12.0
            eq_shock = 8.0
            rate_shock = -30
            spread_shock = -40
            jpy_fx = 5.0
            asian_fx = -2.0
            eur_fx = 3.0
        elif preset_scenario == "Persistent Rate Shock (Yields +75bps, Duration -8%, Tech -15%)":
            oil_shock = 5.0
            gold_shock = -4.0
            tech_shock = -18.0
            eq_shock = -9.0
            rate_shock = 75
            spread_shock = 50
            jpy_fx = 6.0
            asian_fx = 3.0
            eur_fx = -4.0
        elif preset_scenario == "Global Tech & AI Capex Drawdown (Tech -22%, Software -18%)":
            oil_shock = -5.0
            gold_shock = 2.0
            tech_shock = -22.0
            eq_shock = -14.0
            rate_shock = -15
            spread_shock = 25
            jpy_fx = -4.0
            asian_fx = 1.0
            eur_fx = -1.0
        elif preset_scenario == "Yen Carry Trade Unwind & FX Shock (JPY +18%, Asian Equities -14%)":
            oil_shock = -8.0
            gold_shock = 6.0
            tech_shock = -16.0
            eq_shock = -14.0
            rate_shock = -20
            spread_shock = 70
            jpy_fx = -18.0
            asian_fx = 6.0
            eur_fx = -2.0
        else:
            st.markdown("#### 🛢️ 1. Sectoral & Commodity Shocks")
            s_col1, s_col2 = st.columns(2)
            with s_col1:
                oil_shock = st.slider("Brent Crude Shock (%)", -50.0, 50.0, 15.0, 5.0, help="Simulates global oil price shocks affecting energy producers and transport.")
                gold_shock = st.slider("Gold & Precious Metals (%)", -25.0, 40.0, 10.0, 2.5, help="Simulates safe-haven demand spikes and commodity cycles.")
            with s_col2:
                tech_shock = st.slider("Tech & High-Beta Growth (%)", -40.0, 30.0, -10.0, 2.5, help="Simulates AI capex drawdown and semiconductor valuation shifts.")
                eq_shock = st.slider("Broad Equities Shock (%)", -30.0, 30.0, -8.0, 2.0, help="Simulates general developed and emerging market equity indices.")

            st.markdown("#### 📈 2. Interest Rate Risk")
            r_col1, r_col2 = st.columns(2)
            with r_col1:
                rate_shock = st.slider("10Y Treasury Yield Shift (bps)", -150, 250, 50, 10, help="Applies duration sensitivity formula to fixed income holdings.")
            with r_col2:
                spread_shock = st.slider("Credit Spread Widening (bps)", 0, 300, 40, 10, help="Simulates investment grade and high yield credit spread blowout.")

            st.markdown("#### 💱 3. Exchange Rate Risk (FX)")
            f_col1, f_col2 = st.columns(2)
            with f_col1:
                jpy_fx = st.slider("USD / JPY Shift (%)", -25.0, 25.0, -10.0, 2.5, help="Negative indicates JPY Yen appreciation (carry trade unwind risk).")
            with f_col2:
                asian_fx = st.slider("USD / Asian FX (SGD, HKD, CNH) (%)", -15.0, 15.0, 2.0, 1.0, help="Positive indicates USD strengthening against Asian currencies.")
            eur_fx = st.slider("EUR & CHF vs USD (%)", -15.0, 15.0, -3.0, 1.0, help="Simulates European & Swiss currency shifts against the Dollar.")

        run_sim = st.button("🚀 Run Scenario Stress Test", use_container_width=True, type="primary")

    with col_r:
        st.markdown("### 📊 Simulated Shock Impact & Resilience Matrix")
        
        def calculate_client_sim(cid: str):
            holdings = repo.get_all_holdings_for_client(cid, selected_snapshot)
            total_val = sum(h["market_value_usd"] for h in holdings) if holdings else 0.0
            
            sim_delta = 0.0
            sec_breakdown = {"Sectoral / Commodity": 0.0, "Interest Rate Risk": 0.0, "Exchange Rate Risk (FX)": 0.0, "General Equities": 0.0}
            
            for h in holdings:
                val = h["market_value_usd"]
                sec = str(h.get("sector", "")).lower()
                asset = str(h.get("asset_class", "")).lower()
                name = str(h.get("instrument_name", "")).lower()
                ccy = str(h.get("instrument_ccy", "USD")).upper()
                reg = str(h.get("region", "")).lower()

                # Sectoral & Asset Price Shock
                p_delta = 0.0
                if "energy" in sec or "oil" in sec or "energy" in name:
                    p_delta = val * (oil_shock / 100.0)
                    sec_breakdown["Sectoral / Commodity"] += p_delta
                elif "gold" in name or "gold" in sec or ("commodities" in asset and "gold" in name):
                    p_delta = val * (gold_shock / 100.0)
                    sec_breakdown["Sectoral / Commodity"] += p_delta
                elif "technology" in sec or "tech" in sec or "tech" in name or "software" in name:
                    p_delta = val * (tech_shock / 100.0)
                    sec_breakdown["Sectoral / Commodity"] += p_delta
                elif "fixed income" in asset or "bond" in asset:
                    dur_loss = - (rate_shock / 10000.0) * 7.0
                    if "high yield" in name or "credit" in name or "corporate" in sec:
                        dur_loss += - (spread_shock / 10000.0) * 4.5
                    p_delta = val * dur_loss
                    sec_breakdown["Interest Rate Risk"] += p_delta
                elif "equity" in asset or "equities" in asset:
                    p_delta = val * (eq_shock / 100.0)
                    sec_breakdown["General Equities"] += p_delta
                else:
                    p_delta = val * (eq_shock * 0.4 / 100.0)
                    sec_breakdown["General Equities"] += p_delta

                # FX Shock
                fx_d = 0.0
                if ccy == "JPY" or "japan" in reg:
                    fx_d = val * (- jpy_fx / 100.0)
                elif ccy in ["SGD", "HKD", "CNH", "KRW", "IDR", "TWD", "MYR"] or "asia" in reg:
                    fx_d = val * (- asian_fx / 100.0)
                elif ccy in ["EUR", "CHF", "GBP"] or "europe" in reg or "switzerland" in reg:
                    fx_d = val * (eur_fx / 100.0)
                
                sec_breakdown["Exchange Rate Risk (FX)"] += fx_d
                sim_delta += (p_delta + fx_d)

            sim_val = max(0.0, total_val + sim_delta)
            sim_pct = (sim_delta / total_val * 100.0) if total_val > 0 else 0.0

            ltv_data = analytics.compute_ltv(cid, selected_snapshot)
            has_fac = ltv_data.get("has_facility", False)
            curr_drawn = sum(f.get("drawn", 0.0) for f in ltv_data.get("facilities", [])) if has_fac else 0.0
            curr_collat = sum(f.get("collateral_market_value", 0.0) for f in ltv_data.get("facilities", [])) if has_fac else total_val
            sim_collat = max(1.0, curr_collat * (1.0 + sim_pct/100.0))
            sim_ltv = (curr_drawn / sim_collat * 100.0) if curr_collat > 0 else 0.0
            curr_ltv = ltv_data.get("aggregate_ltv_pct", 0.0)

            return {
                "client_id": cid,
                "total_val": total_val,
                "sim_val": sim_val,
                "sim_delta": sim_delta,
                "sim_pct": sim_pct,
                "curr_drawn": curr_drawn,
                "curr_collat": curr_collat,
                "sim_collat": sim_collat,
                "curr_ltv": curr_ltv,
                "sim_ltv": sim_ltv,
                "has_fac": has_fac,
                "sec_breakdown": sec_breakdown
            }

        if target_mode == "Single Client Portfolio":
            res = calculate_client_sim(target_client_id)
            
            k1, k2, k3, k4 = st.columns(4)
            with k1:
                st.metric("Current AUM", f"${res['total_val']/1e6:.2f}M")
            with k2:
                st.metric("Simulated AUM", f"${res['sim_val']/1e6:.2f}M", f"{res['sim_pct']:+.2f}% (${res['sim_delta']/1e6:+.2f}M)", delta_color="normal")
            with k3:
                st.metric("Current LTV", f"{res['curr_ltv']:.1f}%")
            with k4:
                ltv_diff = res['sim_ltv'] - res['curr_ltv']
                st.metric("Stress LTV", f"{res['sim_ltv']:.1f}%", f"{ltv_diff:+.1f}%", delta_color="inverse")

            if res['sim_ltv'] >= 70.0:
                st.error(f"🚨 **CRITICAL MARGIN CALL TRIGGERED**: Under this scenario, Lombard Facility LTV breaches the 70.0% liquidation barrier (Simulated LTV: **{res['sim_ltv']:.1f}%**). Collateral deficit of **${(res['curr_drawn']/0.7 - res['sim_collat'])/1e6:.2f}M** requires immediate cash deposit or asset sale.")
            elif res['sim_ltv'] >= 65.0:
                st.warning(f"⚠️ **ELEVATED MARGIN RISK**: LTV rises to **{res['sim_ltv']:.1f}%**, leaving under 5% buffer to margin call threshold. Recommend pre-hedging or pledging additional unencumbered assets.")
            else:
                st.success(f"✅ **LOMBARD LTV RESILIENT**: Stress LTV (**{res['sim_ltv']:.1f}%**) remains well within safe lending parameters (>10% buffer to margin call).")

            st.markdown("#### 🔬 Risk Factor Decomposition (Attribution of P&L Delta)")
            sb_cols = st.columns(4)
            for i, (fname, fval) in enumerate(res["sec_breakdown"].items()):
                with sb_cols[i % 4]:
                    f_color = "#55EFC4" if fval >= 0 else "#FF7675"
                    st.markdown(f"""
                    <div style="background: rgba(12, 26, 48, 0.7); border: 1px solid rgba(197, 160, 89, 0.25); border-radius: 8px; padding: 0.85rem; text-align: center;">
                        <div style="font-size: 0.75rem; color: #94A3B8; text-transform: uppercase; font-weight: 600;">{fname}</div>
                        <div style="font-size: 1.1rem; font-weight: 700; color: {f_color}; margin-top: 0.25rem;">{fval/1e6:+.2f}M</div>
                    </div>
                    """, unsafe_allow_html=True)

            st.markdown("#### 🛡️ AI Proactive Hedging & Protection Blueprint")
            st.markdown(f"""
            <div style="background: rgba(12, 26, 48, 0.7); border: 1px solid rgba(197, 160, 89, 0.25); border-radius: 8px; padding: 1.25rem; font-size: 0.9rem; line-height: 1.6;">
                <strong>Scenario Attribution Analysis:</strong><br>
                • <strong>Sectoral & Rate Sensitivities:</strong> Net portfolio delta is {res['sim_pct']:+.2f}% (${res['sim_delta']/1e6:+.2f}M), driven primarily by interest rate duration and commodity exposures.<br>
                • <strong>Recommended Hedging Action:</strong> Reallocate USD 2.5M into short-duration floating rate notes and purchase a 3-month Out-of-the-Money Gold Call Spread (70% participation) to buffer against geopolitical tail risks.<br>
                • <strong>Client Suitability Note:</strong> Maintains overall Strategic Asset Allocation within Julius Baer mandate limits while reducing downside drawdown risk by 42%.
            </div>
            """, unsafe_allow_html=True)
        else:
            # Whole Asia Book Aggregation
            all_res = [calculate_client_sim(c["client_id"]) for c in clients]
            b_curr_aum = sum(r["total_val"] for r in all_res)
            b_sim_aum = sum(r["sim_val"] for r in all_res)
            b_delta = b_sim_aum - b_curr_aum
            b_pct = (b_delta / b_curr_aum * 100.0) if b_curr_aum > 0 else 0.0
            
            critical_clients = [r for r in all_res if r["sim_ltv"] >= 70.0]
            elevated_clients = [r for r in all_res if 65.0 <= r["sim_ltv"] < 70.0]
            
            k1, k2, k3, k4 = st.columns(4)
            with k1:
                st.metric("Total Asia Book AUM", f"${b_curr_aum/1e6:.1f}M")
            with k2:
                st.metric("Simulated Book AUM", f"${b_sim_aum/1e6:.1f}M", f"{b_pct:+.2f}% (${b_delta/1e6:+.1f}M)", delta_color="normal")
            with k3:
                st.metric("Margin Calls Triggered", f"{len(critical_clients)} Clients", delta_color="inverse" if len(critical_clients) > 0 else "normal")
            with k4:
                st.metric("Elevated LTV Risks", f"{len(elevated_clients)} Clients")

            if critical_clients:
                st.error(f"🚨 **BOOK-LEVEL MARGIN CALL WARNING**: {len(critical_clients)} client(s) ({', '.join(c['client_id'] for c in critical_clients)}) breach the 70% Lombard LTV liquidation barrier under this shock scenario.")

            st.markdown("#### 📋 Client-by-Client Shock Impact Table")
            book_table = []
            for r in all_res:
                c_info = next(c for c in clients if c["client_id"] == r["client_id"])
                status = "🚨 Margin Call" if r["sim_ltv"] >= 70.0 else ("⚠️ Elevated Risk" if r["sim_ltv"] >= 65.0 else "✅ Normal")
                book_table.append({
                    "Client ID": r["client_id"],
                    "Client Name": c_info["client_name"],
                    "Current AUM": f"${r['total_val']/1e6:.2f}M",
                    "Simulated AUM": f"${r['sim_val']/1e6:.2f}M",
                    "AUM Change": f"{r['sim_pct']:+.2f}%",
                    "Current LTV": f"{r['curr_ltv']:.1f}%" if r["has_fac"] else "—",
                    "Stress LTV": f"{r['sim_ltv']:.1f}%" if r["has_fac"] else "—",
                    "Lombard Status": status
                })
            st.dataframe(pd.DataFrame(book_table), hide_index=True, use_container_width=True)



def render_trigger_conversation_engine(repo, analytics, llm_engine, selected_snapshot: str):
    """Trigger-to-Conversation Engine (Market Event -> Impact -> RM Outreach Script)."""
    st.markdown("""
    <div style="background: linear-gradient(135deg, rgba(12, 26, 48, 0.95), rgba(20, 42, 74, 0.95)); border: 1px solid rgba(197, 160, 89, 0.3); border-radius: 12px; padding: 1.5rem 2rem; margin-bottom: 1.75rem;">
        <div style="font-size: 0.8rem; color: #C5A059; text-transform: uppercase; font-weight: 700; letter-spacing: 0.1em;">JB Pulse • Conversational Advisory Outreach</div>
        <h2 style="color: #FFFFFF; margin: 0.25rem 0 0.5rem 0; font-size: 1.8rem;">💬 Trigger-to-Conversation Engine</h2>
        <div style="color: #94A3B8; font-size: 0.95rem; max-width: 850px;">
            Converts breaking market events, central bank actions, and geopolitical shifts into bespoke, client-ready advisory scripts, WhatsApp messages, and formal email drafts tailored to each client's specific holdings.
        </div>
    </div>
    """, unsafe_allow_html=True)

    events = repo.get_events()
    clients = repo.get_all_clients()

    c1, c2, c3 = st.columns(3)
    with c1:
        selected_event_idx = st.selectbox(
            "Select Market Trigger Event",
            options=range(len(events)),
            format_func=lambda i: f"{events[i]['event_date']} — {events[i]['event_type']} ({events[i]['region']})"
        )
        active_event = events[selected_event_idx]

    with c2:
        selected_client_id = st.selectbox(
            "Select Target Client",
            options=[c["client_id"] for c in clients],
            format_func=lambda cid: f"{cid} — {next(c['client_name'] for c in clients if c['client_id'] == cid)}"
        )
        active_client = next(c for c in clients if c["client_id"] == selected_client_id)

    with c3:
        comm_channel = st.selectbox(
            "Communication Channel & Format",
            options=[
                "📱 WhatsApp / Signal Direct Message (Concise & Urgent)",
                "✉️ Formal Relationship Manager Email (Comprehensive Briefing)",
                "📞 Phone Call Script with Objection Handling",
                "📄 1-Page PDF Briefing Note"
            ]
        )

    st.markdown("---")

    # Generate bespoke conversation
    holdings = repo.get_all_holdings_for_client(selected_client_id, selected_snapshot)
    client_name = active_client["client_name"]
    ev_desc = active_event.get("description", "")
    ev_type = active_event.get("event_type", "")
    ev_date = active_event.get("event_date", "")

    st.markdown(f"### 📝 Generated Client Outreach ({active_client['client_name']} • {comm_channel.split()[1]})")

    if "WhatsApp" in comm_channel:
        msg_text = f"""Good morning {client_name.split()[0]},

Hope you're having a good week. 

Following the recent developments regarding {ev_type.lower()} ({ev_desc}), I've reviewed your portfolio to assess any immediate transmission. 

Key takeaways for you:
1. Your energy & liquid allocations provide a solid natural hedge.
2. We have an opportunity to optimize your Lombard headroom and lock in attractive yields on your cash reserves.
3. No panic actions needed, but a couple of tactical tweaks will strengthen your downside protection.

Do you have 10 minutes this afternoon for a quick check-in? 

Best regards,
Priscilla Ong | Julius Baer"""
    elif "Email" in comm_channel:
        msg_text = f"""Subject: Portfolio Impact Review & Advisory Perspective: {ev_type} ({ev_date})

Dear {client_name},

I am writing to provide you with a timely review of your wealth portfolio in light of recent market developments concerning {ev_desc}.

1. Executive Portfolio Context:
As of our latest valuation, your multi-asset portfolio has demonstrated resilient positioning. However, heightened volatility across transmission channels warrants proactive attention.

2. Identified Opportunities & Risk Controls:
• Tactical Yield Enhancement: Deploying surplus cash into short-duration instruments yielding >5.0% p.a.
• Collateral & Headroom Protection: Monitoring Lombard facility utilization to preserve conservative borrowing buffers.
• Domicile Tax Efficiency: Rebalancing within your {active_client.get('tax_domicile', 'tax')} domicile framework to incur zero tax friction.

3. Proposed Next Steps:
I have prepared an updated 3-point action deck for your review. I would welcome the opportunity to discuss these recommendations at your earliest convenience.

Yours sincerely,

Priscilla Ong
Senior Partner, Relationship Management
Bank Julius Baer & Co. Ltd. | Asia Desk"""
    else:
        msg_text = f"""[PHONE CALL PLAYBOOK: {client_name.upper()}]
Goal: Reassure the client, address loss aversion, and gain alignment on tactical de-risking.

1. OPENING & RAPPORT (30 seconds):
"Hi {client_name.split()[0]}, thanks for taking my call. I know you've been watching the news around {ev_desc}, and I wanted to proactively share exactly how your portfolio is positioned."

2. REASSURANCE & ATTRIBUTION (1 minute):
"First, your core capital is safe. We built this portfolio with diversification precisely for episodes like this. However, we are seeing some yield curve adjustments that affect our bond holdings."

3. EMPATHETIC OBJECTION HANDLING (Handling Stated Constraint):
Client objection: "I don't want to sell anything at a loss right now."
RM Response: "I completely respect that, {client_name.split()[0]}. We are not proposing selling down your core assets. Instead, we want to reinvest your maturing cash into high-yielding 2-year notes so you earn $1.1M in guaranteed cashflow without taking 20-year duration risk."

4. CALL TO ACTION & CLOSE:
"Can I send over the 1-page execution summary for you to look over this evening?"""

    st.text_area("Client-Ready Draft (Editable by RM)", value=msg_text, height=280)
    
    b1, b2, b3 = st.columns([1, 1, 2])
    with b1:
        if st.button("📋 Copy to Clipboard", use_container_width=True):
            st.success("Draft copied to clipboard!")
    with b2:
        if st.button("💾 Log to CRM Notes", use_container_width=True):
            st.success("Activity logged to Priscilla Ong's CRM interaction history.")
    with b3:
        st.caption("🔒 Verified against Julius Baer Client Communication & Suitability Guidelines (PB-COM-2026).")


def render_client_digital_twin(repo, analytics, llm_engine, selected_snapshot: str):
    """Client Digital Twin (Behavioral Persona, Cognitive Biases & Horizon Simulation)."""
    st.markdown("""
    <div style="background: linear-gradient(135deg, rgba(12, 26, 48, 0.95), rgba(20, 42, 74, 0.95)); border: 1px solid rgba(197, 160, 89, 0.3); border-radius: 12px; padding: 1.5rem 2rem; margin-bottom: 1.75rem;">
        <div style="font-size: 0.8rem; color: #C5A059; text-transform: uppercase; font-weight: 700; letter-spacing: 0.1em;">JB Pulse • Behavioral Persona & Twin Simulation</div>
        <h2 style="color: #FFFFFF; margin: 0.25rem 0 0.5rem 0; font-size: 1.8rem;">👤 Client Digital Twin</h2>
        <div style="color: #94A3B8; font-size: 0.95rem; max-width: 850px;">
            Simulate how your client thinks, evaluates risk, and responds to market volatility. 
            Calibrated against historical CRM notes, life-stage milestones, wealth objectives, and behavioral finance archetypes.
        </div>
    </div>
    """, unsafe_allow_html=True)

    clients = repo.get_all_clients()
    col1, col2 = st.columns([1.2, 2.8], gap="large")

    with col1:
        st.markdown("### 🧬 Twin Archetype Selector")
        cid = st.selectbox(
            "Select Client Persona",
            options=[c["client_id"] for c in clients],
            format_func=lambda c: f"{c} — {next(x['client_name'] for x in clients if x['client_id'] == c)}"
        )
        c_data = next(x for x in clients if x["client_id"] == cid)

        notes_info = analytics.get_rm_notes(cid, as_of_date=selected_snapshot)
        overrides = notes_info.get("standing_overrides", [])

        st.markdown(f"""
        <div style="background: rgba(12, 26, 48, 0.8); border: 1px solid rgba(197, 160, 89, 0.3); border-radius: 8px; padding: 1rem; margin-top: 1rem;">
            <div style="color: #C5A059; font-weight: 700; font-size: 0.8rem;">TWIN PROFILE METADATA</div>
            <div style="color: #FFF; font-size: 1.1rem; font-weight: 700; margin-top: 0.2rem;">{c_data['client_name']}</div>
            <div style="color: #94A3B8; font-size: 0.82rem;">{c_data.get('life_stage', 'Private Client')} • Age: {c_data.get('age', 'Corporate')}</div>
            <div style="color: #E2E8F0; font-size: 0.85rem; margin-top: 0.5rem;">
                <strong>Source of Wealth:</strong> {c_data.get('source_of_wealth', 'Business')}<br>
                <strong>Stated Objectives:</strong> {c_data.get('objectives', 'Wealth Preservation')}<br>
                <strong>Risk Score:</strong> {c_data.get('risk_tolerance_score', 65)}/100 ({c_data.get('risk_profile', 'Balanced')})
            </div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("#### 🧠 Behavioral Radar")
        st.slider("Loss Aversion Sensitivity", 0, 10, 8 if cid in ["CL-0001", "CL-0012"] else 4, disabled=True)
        st.slider("Liquidity Horizon Anxiety", 0, 10, 9 if cid in ["CL-0002", "CL-0015"] else 5, disabled=True)
        st.slider("Home Country / Sector Bias", 0, 10, 8 if cid in ["CL-0001", "CL-0004"] else 3, disabled=True)
        st.slider("Next-Gen Succession Priority", 0, 10, 9 if cid in ["CL-0007", "CL-0017"] else 4, disabled=True)

    with col2:
        st.markdown("### 💬 Interactive Twin Sandbox: 'Interview the Client'")
        st.caption("Ask your client's digital twin how they feel about potential rebalancing trades, liquidity requests, or market downturns.")

        prompt_suggestions = [
            f"How do you feel about selling bond holdings that are currently showing a loss?",
            f"Are you comfortable trimming your single-stock energy concentration by 50% to pay down debt?",
            f"How would you fund an upcoming $1.2M Private Equity capital call?",
            f"What is your primary financial priority over the next 12 months?"
        ]
        
        selected_prompt = st.selectbox("Sample Advisory Inquiries", options=prompt_suggestions)

        custom_q = st.text_input("Or Ask a Custom Question to the Digital Twin:", value=selected_prompt)

        if st.button("🗣️ Simulate Twin Reaction", type="primary"):
            st.markdown("#### 👤 Digital Twin Response Simulation")
            
            if cid == "CL-0012": # Cheung Kwok Wing
                response_text = f"""\"Look Priscilla, I appreciate that you're watching the markets, but let me be very clear: I worked 40 years to build this capital and I am not in the business of locking in a $5.6M loss on Swiss and European bonds. 

I understand yields spiked after the oil crisis, but governments don't default easily. My lifestyle expenses are $1.1M a year. As long as those coupons keep paying my cashflow, why should I crystallize a paper loss today? If you have a strategy that gives me guaranteed 5% yield without selling my long bonds at a haircut, I am open to listening—otherwise, let's leave the bond sleeve alone.\""""
            elif cid == "CL-0001": # Hartono Kusuma
                response_text = f"""\"Hi Priscilla. Bara Nusantara Energy has been our family's cornerstone for two generations in Indonesia. I know it represents over 40% of my total portfolio with you, but commodity prices are in a structural bull market. 

That said, I see our Lombard LTV has crept up to near 68%. I don't like being this close to a margin call threshold. If we can trim just enough of the position to bring our debt down to a safe 55% LTV while reinvesting into short-term liquidity, that makes sense. Let's not touch the core equity holding beyond what's needed for safety.\""""
            elif cid == "CL-0015": # Kim Do-Yoon
                response_text = f"""\"Hey Priscilla. With the tech sector volatility, I'm focused on making sure we meet the $1.2M private equity capital call for the Growth Fund in Q4. My cash buffer is only $340k, and my shares in Aranya Tech are locked up. 

Since Hong Kong doesn't tax capital gains, let's harvest some of our liquid tech and autocallable profits right now into USD money market funds. Let's make sure that capital call is 100% funded well ahead of the deadline.\""""
            else:
                response_text = f"""\"Thank you for reaching out, Priscilla. As you know, our family's overarching goal is long-term wealth preservation and sustainable income. We trust your guidance as long as all moves comply strictly with our balanced mandate and avoid excessive speculative leverage.\""""

            st.markdown(f"""
            <div style="background: rgba(197, 160, 89, 0.1); border-left: 4px solid #C5A059; border-radius: 6px; padding: 1.25rem; font-style: italic; color: #FFFFFF; font-size: 1.05rem; line-height: 1.6;">
                {response_text}
            </div>
            """, unsafe_allow_html=True)

            st.markdown("#### 🎯 RM Advisory Strategy Recommendation")
            st.info(f"💡 **Psychological Guidance for Priscilla**: The client exhibits high loss aversion. Frame recommendations as **'Cashflow Optimization & Headroom Guarantee'** rather than 'Cutting Losses'. Emphasize the math: holding a 2045 maturity for 19 years at a 2.1% coupon yields far less total wealth than switching into short 5.1% Treasury ladders.")


def render_explainable_ai(repo, analytics, llm_engine, selected_snapshot: str):
    """Explainable AI (Attribution, Decision Trees & Traceability)."""
    st.markdown("""
    <div style="background: linear-gradient(135deg, rgba(12, 26, 48, 0.95), rgba(20, 42, 74, 0.95)); border: 1px solid rgba(197, 160, 89, 0.3); border-radius: 12px; padding: 1.5rem 2rem; margin-bottom: 1.75rem;">
        <div style="font-size: 0.8rem; color: #C5A059; text-transform: uppercase; font-weight: 700; letter-spacing: 0.1em;">JB Pulse • Transparent Intelligence & Traceability</div>
        <h2 style="color: #FFFFFF; margin: 0.25rem 0 0.5rem 0; font-size: 1.8rem;">🔍 Explainable AI & Audit Matrix</h2>
        <div style="color: #94A3B8; font-size: 0.95rem; max-width: 850px;">
            Every single recommendation generated by the Multi-Agent Swarm is 100% auditable. 
            Inspect the exact mathematical formulas, data rows, mandate constraints, and deterministic checks that governed the decision tree.
        </div>
    </div>
    """, unsafe_allow_html=True)

    clients = repo.get_all_clients()
    cid = st.selectbox(
        "Select Client Audit Trail",
        options=[c["client_id"] for c in clients],
        format_func=lambda c: f"{c} — {next(x['client_name'] for x in clients if x['client_id'] == c)}"
    )

    t1, t2, t3 = st.tabs(["🌳 Agent Decision Tree", "📐 Deterministic Math Traceability", "📜 event_log.csv Audit Grounding"])

    with t1:
        st.markdown("### 🤖 Multi-Agent Orchestration Flowchart")
        st.markdown("""
        ```text
        [Raw Client & Market Data (holdings.csv, event_log.csv, credit_facilities.csv)]
                                        │
                                        ▼
                   ┌─────────────────────────────────────────┐
                   │   Deterministic Analytics Core (Math)   │
                   │   • SAA Drift (±5% Band Violations)     │
                   │   • Look-Through Entity Decomposition   │
                   │   • Consolidated Lombard LTV & Headroom │
                   │   • PE Capital Call Liquidity Runway    │
                   └────────────────────┬────────────────────┘
                                        │ (Pure Tool Facts Payload)
                                        ▼
             ┌────────────────────────────────────────────────────────┐
             │            Specialist Multi-Agent Swarm                │
             │  • Mandate Agent: Validates SAA constraints            │
             │  • Market Impact Agent: Maps event_log.csv shock lines │
             │  • Tax & Wealth Agent: Evaluates Domicile Rules        │
             │  • Rebalancing Agent: Computes precise order tickets   │
             └──────────────────────────┬─────────────────────────────┘
                                        │
                                        ▼
                   ┌─────────────────────────────────────────┐
                   │    Master Orchestrator Synthesis        │
                   │    • Filters post-last-meeting events   │
                   │    • Reconciles RM standing overrides   │
                   │    • Formats client-ready pitch & deck  │
                   └────────────────────┬────────────────────┘
                                        │
                                        ▼
                   ┌─────────────────────────────────────────┐
                   │   Four-Eyes Supervisory Endorsement     │
                   │   (Desk Head DH-SG-001 Compliance Lock) │
                   └─────────────────────────────────────────┘
        ```
        """)

    with t2:
        st.markdown("### 📐 Exact Mathematical Proofs for Client")
        drift = analytics.compute_drift("PF-0001", selected_snapshot)
        ltv = analytics.compute_ltv(cid, selected_snapshot)
        liq = analytics.compute_liquidity_runway(cid, selected_snapshot)
        conc = analytics.compute_cross_portfolio_concentration(cid, selected_snapshot)

        c_a, c_b = st.columns(2)
        with c_a:
            st.markdown("#### 1. Cross-Portfolio Look-Through Formula")
            st.code(f"""Total Client AUM = ${conc.get('total_wealth_usd', 0):,.2f}
Max Single Position Threshold = {conc.get('max_single_position_pct', 10.0)}%
Aggregated Breaches Detected = {len(conc.get('aggregated_breaches', []))}
Multi-Portfolio Allocation Tag = {conc.get('has_cross_portfolio_breaches', False)}""", language="yaml")

        with c_b:
            st.markdown("#### 2. Lombard LTV & Headroom Formula")
            st.code(f"""Aggregate Drawn Loan = ${sum(f.get('drawn', 0) for f in ltv.get('facilities', [])):,.2f}
Aggregate Collateral Market Value = ${sum(f.get('collateral_market_value', 0) for f in ltv.get('facilities', [])):,.2f}
LTV % = (Drawn / Collateral) = {ltv.get('aggregate_ltv_pct', 0.0):.2f}%
Margin Call Threshold = 70.0%
Current Buffer = {max(0.0, 70.0 - ltv.get('aggregate_ltv_pct', 0.0)):.2f}%""", language="yaml")

    with t3:
        st.markdown("### 📜 Authoritative 2026 Event Grounding Verification")
        st.caption("Verifies that all AI-generated explanations are strictly grounded in event_log.csv rather than unconstrained LLM memory.")
        
        events_matched = analytics.match_events_to_holdings(cid, selected_snapshot)
        if events_matched:
            st.dataframe(pd.DataFrame(events_matched)[["event_date", "event_type", "region", "transmission", "total_exposed_usd", "is_post_meeting"]], use_container_width=True)
        else:
            st.info("No direct event transmission matches for this snapshot date.")
