"""
Julius Bär (Bank Julius Baer & Co. Ltd.) Design System & Styling
Provides custom CSS, branded SVG headers, color tokens, and styled UI components
tailored for elite Swiss private wealth management interfaces.
"""

def get_julius_baer_css() -> str:
    return """
<style>
/* --- Julius Bär Global Design System --- */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Playfair+Display:ital,wght@0,600;1,400&display=swap');

:root {
    --jb-navy-deep: #081426;
    --jb-navy-dark: #0D1E36;
    --jb-navy-card: #132A4A;
    --jb-navy-surface: #1B385F;
    --jb-gold-primary: #C5A880;
    --jb-gold-light: #E0C7A6;
    --jb-gold-accent: #DFBA73;
    --jb-text-primary: #F8FAFC;
    --jb-text-muted: #94A3B8;
    --jb-text-gold: #D6BD96;
    --jb-red: #E74C3C;
    --jb-amber: #F39C12;
    --jb-green: #2ECC71;
    --jb-blue: #3498DB;
    --jb-purple: #9B59B6;
    --jb-border-gold: rgba(197, 168, 128, 0.25);
    --jb-border-subtle: rgba(255, 255, 255, 0.08);
}

/* App container */
.stApp {
    background-color: var(--jb-navy-deep);
    color: var(--jb-text-primary);
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
}

/* Ensure Streamlit top header is transparent and does not obscure content */
header[data-testid="stHeader"] {
    background: transparent !important;
    color: var(--jb-gold-primary) !important;
}

.block-container {
    padding-top: 4.5rem !important;
    padding-bottom: 2rem !important;
}

/* Headers */
h1, h2, h3, h4, h5, h6 {
    color: var(--jb-text-primary);
    font-family: 'Inter', sans-serif;
    font-weight: 600;
    letter-spacing: -0.01em;
}

/* Julius Bär Brand Header */
.jb-header-container {
    background: linear-gradient(135deg, #0A1B30 0%, #112845 100%);
    border-bottom: 2px solid var(--jb-gold-primary);
    padding: 1.25rem 2rem;
    margin: 0rem -2rem 1.5rem -2rem;
    display: flex;
    justify-content: space-between;
    align-items: center;
    box-shadow: 0 4px 20px rgba(0,0,0,0.4);
    border-radius: 8px;
}

.jb-brand-title {
    font-size: 1.5rem;
    font-weight: 700;
    color: #FFFFFF;
    letter-spacing: 0.05em;
    display: flex;
    align-items: center;
    gap: 0.75rem;
}

.jb-brand-subtitle {
    font-size: 0.8rem;
    text-transform: uppercase;
    color: var(--jb-gold-primary);
    letter-spacing: 0.15em;
    font-weight: 600;
    margin-top: 0.2rem;
}

/* Executive Metric Card */
.jb-kpi-card {
    background: linear-gradient(180deg, rgba(19, 42, 74, 0.9) 0%, rgba(13, 30, 54, 0.9) 100%);
    border: 1px solid var(--jb-border-gold);
    border-radius: 8px;
    padding: 1.1rem 1.25rem;
    position: relative;
    overflow: hidden;
}

.jb-kpi-card::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    width: 4px;
    height: 100%;
    background: var(--jb-gold-primary);
}

.jb-kpi-label {
    font-size: 0.75rem;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    color: var(--jb-text-muted);
    font-weight: 600;
}

.jb-kpi-value {
    font-size: 1.6rem;
    font-weight: 700;
    color: #FFFFFF;
    margin: 0.3rem 0;
    font-family: 'Inter', monospace;
}

.jb-kpi-sub {
    font-size: 0.75rem;
    color: var(--jb-gold-light);
}

/* Priority Client Row / Card */
.jb-client-card {
    background: #112845;
    border: 1px solid var(--jb-border-subtle);
    border-radius: 8px;
    padding: 1.2rem 1.5rem;
    margin-bottom: 1rem;
    transition: all 0.2s ease;
}

.jb-client-card:hover {
    border-color: var(--jb-gold-primary);
    background: #143054;
    transform: translateY(-2px);
    box-shadow: 0 6px 16px rgba(0,0,0,0.3);
}

/* Badge System */
.jb-badge {
    display: inline-block;
    padding: 0.25rem 0.6rem;
    border-radius: 4px;
    font-size: 0.72rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.05em;
}

.jb-badge-high {
    background: rgba(231, 76, 60, 0.2);
    color: #FF7675;
    border: 1px solid rgba(231, 76, 60, 0.5);
}

.jb-badge-medium {
    background: rgba(243, 156, 18, 0.2);
    color: #FDCB6E;
    border: 1px solid rgba(243, 156, 18, 0.5);
}

.jb-badge-low {
    background: rgba(46, 204, 113, 0.2);
    color: #55EFC4;
    border: 1px solid rgba(46, 204, 113, 0.5);
}

.jb-badge-fact {
    background: rgba(52, 152, 219, 0.2);
    color: #74B9FF;
    border: 1px solid rgba(52, 152, 219, 0.5);
}

.jb-badge-rule {
    background: rgba(155, 89, 182, 0.2);
    color: #A29BFE;
    border: 1px solid rgba(155, 89, 182, 0.5);
}

.jb-badge-model {
    background: rgba(197, 168, 128, 0.2);
    color: var(--jb-gold-light);
    border: 1px solid var(--jb-border-gold);
}

/* Recommendation Card */
.jb-rec-card {
    background: #102640;
    border: 1px solid var(--jb-border-gold);
    border-radius: 8px;
    padding: 1.25rem;
    margin-bottom: 1.25rem;
    position: relative;
}

.jb-rec-headline {
    font-size: 1.05rem;
    font-weight: 600;
    color: #FFFFFF;
    margin-bottom: 0.6rem;
}

.jb-talking-point-box {
    background: rgba(8, 20, 38, 0.6);
    border-left: 3px solid var(--jb-gold-primary);
    padding: 0.85rem 1rem;
    margin: 0.75rem 0;
    border-radius: 0 6px 6px 0;
    font-size: 0.88rem;
    color: #E2E8F0;
    font-style: italic;
}

/* Conflict Alert Box */
.jb-conflict-box {
    background: rgba(230, 126, 34, 0.12);
    border: 1px solid rgba(230, 126, 34, 0.4);
    border-radius: 6px;
    padding: 1rem;
    margin-bottom: 1rem;
}

/* Tabs & Sidebar styling */
.stTabs [data-baseweb="tab-list"] {
    gap: 0.5rem;
    display: flex;
    justify-content: space-between;
    border-bottom: 1.5px solid var(--jb-border-subtle);
    padding-bottom: 0.25rem;
    width: 100%;
}

.stTabs [data-baseweb="tab"] {
    font-size: 0.88rem;
    font-weight: 600;
    color: var(--jb-text-muted);
    padding: 0.5rem 0.6rem;
    white-space: nowrap;
    flex: 1;
    text-align: center;
    justify-content: center;
}

.stTabs [aria-selected="true"] {
    color: var(--jb-gold-primary) !important;
    border-bottom: 2.5px solid var(--jb-gold-primary) !important;
    background: rgba(197, 168, 128, 0.06);
    border-radius: 4px 4px 0 0;
}

/* Streamlit buttons */
.stButton > button {
    background-color: var(--jb-navy-surface);
    color: #FFFFFF;
    border: 1px solid var(--jb-border-gold);
    border-radius: 4px;
    font-weight: 600;
    font-size: 0.85rem;
    transition: all 0.2s ease;
}

.stButton > button:hover {
    background-color: var(--jb-gold-primary);
    color: #081426;
    border-color: var(--jb-gold-primary);
}

/* Login Container & Card */
.jb-login-container {
    max-width: 460px;
    margin: 0.5rem auto 0.75rem auto;
    padding: 1.25rem 2rem 1rem 2rem;
    background: linear-gradient(180deg, #102640 0%, #0A1B30 100%);
    border: 1px solid var(--jb-border-gold);
    border-radius: 12px;
    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.5);
    text-align: center;
}

.jb-login-brand {
    font-size: 1.45rem;
    font-weight: 700;
    color: #FFFFFF;
    letter-spacing: 0.04em;
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 0.6rem;
    margin-bottom: 0.15rem;
}

.jb-login-subtitle {
    font-size: 0.75rem;
    text-transform: uppercase;
    color: var(--jb-gold-primary);
    letter-spacing: 0.12em;
    font-weight: 600;
    margin-bottom: 0.6rem;
}

.jb-login-badge {
    background: rgba(197, 168, 128, 0.15);
    border: 1px solid var(--jb-border-gold);
    color: var(--jb-gold-light);
    padding: 0.3rem 0.75rem;
    border-radius: 6px;
    font-size: 0.78rem;
    margin-bottom: 0.75rem;
    display: inline-block;
}
</style>
"""

def render_jb_header(rm_name: str = "Priscilla Ong", rm_id: str = "RM-SG-014", desk: str = "Singapore Ultra HNW Desk"):
    return f"""
<div class="jb-header-container">
    <div>
        <div style="display: flex; align-items: center; gap: 0.75rem;">
            <div style="background: rgba(197, 168, 128, 0.15); border: 1px solid #C5A880; border-radius: 6px; padding: 0.35rem 0.75rem; display: flex; align-items: center; gap: 0.5rem;">
                <span style="font-size: 1rem;">👤</span>
                <div>
                    <div style="font-size: 0.92rem; font-weight: 700; color: #FFFFFF; letter-spacing: 0.02em;">{rm_name}</div>
                    <div style="font-size: 0.7rem; color: #C5A880; text-transform: uppercase; letter-spacing: 0.08em; font-weight: 600;">{rm_id} • Senior Relationship Manager</div>
                </div>
            </div>
            <div>
                <div class="jb-brand-title" style="font-size: 1.25rem;">
                    Bank Julius Baer & Co. Ltd.
                </div>
                <div class="jb-brand-subtitle" style="font-size: 0.72rem;">Private Wealth Intelligence & RM Decision Support Engine</div>
            </div>
        </div>
    </div>
    <div style="text-align: right;">
        <div style="font-size: 0.82rem; font-weight: 600; color: #FFFFFF;">Desk: {desk}</div>
        <div style="font-size: 0.72rem; color: #55EFC4;">● Live Encrypted Session | Confidential</div>
    </div>
</div>
"""
