import streamlit as st
import json
import os
import tomllib
from pathlib import Path
from agents import init_client, run_full_pipeline

# ─── PAGE CONFIG ────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Coverage Review Assistant",
    page_icon="",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ─── CUSTOM CSS ─────────────────────────────────────────────────────────────
st.markdown("""
<style>
    :root {
        --bg: #fff3f2;
        --panel: #ffffff;
        --panel-soft: #ffe3e0;
        --ink: #19110f;
        --muted: #5c403c;
        --accent: #cc2f2f;
        --accent-dark: #8f1c1c;
        --border: #1f1513;
    }

    .stApp {
        background: var(--bg);
        color: var(--ink);
    }
    .main .block-container {
        max-width: 1220px;
        padding-top: 1.2rem;
    }
    h1, h2, h3, h4, h5, h6, p, label {
        color: var(--ink) !important;
    }

    /* Neobrutalist surfaces */
    div[data-testid="stSidebarContent"] {
        background: var(--panel-soft);
        border-right: 3px solid var(--border);
    }
    div[data-testid="stVerticalBlock"] > div:has(> div.stTabs) {
        background: transparent;
    }

    /* Header */
    .app-header {
        background: var(--panel);
        border: 3px solid var(--border);
        padding: 1.3rem 1.6rem;
        border-radius: 0;
        margin-bottom: 1.5rem;
        box-shadow: 8px 8px 0 var(--accent);
    }
    .app-header h1 {
        color: var(--ink);
        margin: 0;
        font-size: 1.65rem;
        letter-spacing: 0.01em;
        text-transform: uppercase;
    }
    .app-header p {
        color: var(--muted);
        margin: 0.35rem 0 0 0;
        font-size: 0.92rem;
        font-weight: 600;
    }
    
    /* Data source badge */
    .data-badge {
        display: inline-block;
        background: #ffd8d4;
        color: var(--ink);
        border: 2px solid var(--border);
        padding: 0.28rem 0.7rem;
        border-radius: 0;
        font-size: 0.72rem;
        font-weight: 700;
        margin-top: 0.65rem;
    }
    
    /* Agent cards */
    .agent-card {
        background: var(--panel);
        border-radius: 0;
        padding: 1.2rem;
        margin-bottom: 1rem;
        border: 3px solid var(--border);
        box-shadow: 6px 6px 0 #3a2220;
    }
    .agent-card.success { background: #effff3; }
    .agent-card.warning { background: #fff5ea; }
    .agent-card.danger  { background: #fff0f0; }
    
    .agent-header {
        display: flex;
        align-items: center;
        gap: 0.5rem;
        font-weight: 700;
        font-size: 0.95rem;
        color: #1e3a5f;
        margin-bottom: 0.75rem;
    }
    
    /* Verdict banner */
    .verdict-approved {
        background: #d8ffe5;
        color: #0f5132;
        border: 1px solid #bbf7d0;
        text-align: center;
        padding: 1rem;
        border-radius: 0;
        font-size: 1.35rem;
        font-weight: 700;
        letter-spacing: 0.03em;
        margin: 1rem 0;
        border: 3px solid var(--border);
        box-shadow: 5px 5px 0 #0f5132;
    }
    .verdict-denied {
        background: #ffdcdc;
        color: #7f1d1d;
        text-align: center;
        padding: 1rem;
        border-radius: 0;
        font-size: 1.35rem;
        font-weight: 700;
        letter-spacing: 0.03em;
        margin: 1rem 0;
        border: 3px solid var(--border);
        box-shadow: 5px 5px 0 #7f1d1d;
    }
    .verdict-pend {
        background: #ffe9cf;
        color: #78350f;
        text-align: center;
        padding: 1rem;
        border-radius: 0;
        font-size: 1.35rem;
        font-weight: 700;
        letter-spacing: 0.03em;
        margin: 1rem 0;
        border: 3px solid var(--border);
        box-shadow: 5px 5px 0 #78350f;
    }
    
    /* Criteria pills */
    .pill-met,
    .pill-notmet,
    .pill-insuff {
        padding: 0.2rem 0.6rem;
        border-radius: 0;
        font-size: 0.78rem;
        font-weight: 700;
        border: 2px solid var(--border);
    }
    .pill-met      { background:#dcfce7; color:#14532d; }
    .pill-notmet   { background:#fee2e2; color:#7f1d1d; }
    .pill-insuff   { background:#fef9c3; color:#78350f; }
    
    /* Case table */
    .case-row {
        background: white;
        border-radius: 8px;
        padding: 0.8rem 1rem;
        margin-bottom: 0.5rem;
        display: flex;
        align-items: center;
        justify-content: space-between;
        box-shadow: 0 1px 2px rgba(0,0,0,0.06);
    }
    
    /* Sidebar */
    .sidebar-section {
        background: white;
        border-radius: 10px;
        padding: 1rem;
        margin-bottom: 1rem;
    }
    
    /* Metric cards */
    .metric-row {
        display: flex;
        gap: 0.75rem;
        margin-bottom: 1rem;
    }
    .metric-card {
        flex: 1;
        background: white;
        border-radius: 8px;
        padding: 0.75rem;
        text-align: center;
        box-shadow: 0 1px 2px rgba(0,0,0,0.06);
    }
    .metric-card .number { font-size: 1.5rem; font-weight: 800; }
    .metric-card .label  { font-size: 0.72rem; color: #64748b; }
    
    /* Confidence bar */
    .conf-bar-bg { background: #e2e8f0; border-radius: 999px; height: 8px; margin: 0.3rem 0; }
    .conf-bar-fill { background: linear-gradient(90deg, #2563eb, #7c3aed); border-radius: 999px; height: 8px; }
    
    button[kind="primary"],
    .stButton > button {
        background: #ffdbd7 !important;
        color: var(--ink) !important;
        border: 3px solid var(--border) !important;
        border-radius: 0 !important;
        font-weight: 800 !important;
        box-shadow: 4px 4px 0 var(--accent-dark) !important;
        transition: transform 0.06s ease, box-shadow 0.06s ease;
    }
    .stButton > button:hover {
        transform: translate(1px, 1px);
        box-shadow: 2px 2px 0 var(--accent-dark) !important;
    }

    /* Inputs and select boxes - fix readability */
    .stTextInput input,
    .stTextArea textarea,
    .stSelectbox [data-baseweb="select"] > div {
        background: #ffffff !important;
        color: var(--ink) !important;
        border: 3px solid var(--border) !important;
        border-radius: 0 !important;
        box-shadow: 3px 3px 0 #3a2220;
    }
    .stTextInput input::placeholder,
    .stTextArea textarea::placeholder {
        color: #7a5a54 !important;
    }
    .stSelectbox svg,
    .stTextInput svg {
        color: var(--ink) !important;
        fill: var(--ink) !important;
    }

    /* Dropdown menu popover options */
    div[data-baseweb="popover"] ul,
    div[data-baseweb="popover"] li,
    div[role="listbox"],
    div[role="option"] {
        background: #fff6f5 !important;
        color: var(--ink) !important;
    }
    div[role="option"][aria-selected="true"] {
        background: #ffd6d0 !important;
        color: var(--ink) !important;
    }

    /* Expanders, alerts, tabs, metrics */
    .streamlit-expanderHeader {
        background: #ffeceb;
        border: 2px solid var(--border);
        border-radius: 0;
    }
    .stAlert {
        border: 2px solid var(--border) !important;
        border-radius: 0 !important;
    }
    .stMetric {
        background: #fff;
        border: 2px solid var(--border);
        padding: 0.5rem;
        box-shadow: 3px 3px 0 #3a2220;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 0.4rem;
    }
    .stTabs [data-baseweb="tab"] {
        background: #ffd8d4;
        border: 2px solid var(--border);
        border-radius: 0;
        color: var(--ink);
        font-weight: 700;
    }
    .stTabs [aria-selected="true"] {
        background: #cc2f2f !important;
        color: #ffffff !important;
    }

    /* Informational note box */
    .note-box {
        background: #fff7f6;
        border: 3px solid var(--border);
        box-shadow: 6px 6px 0 #3a2220;
        padding: 1rem 1.1rem;
        margin-bottom: 1rem;
    }
    .note-box h4 {
        margin: 0 0 0.5rem 0;
        font-size: 1rem;
        text-transform: uppercase;
        letter-spacing: 0.02em;
    }
    .note-box p {
        margin: 0.2rem 0;
        color: var(--muted);
        font-size: 0.9rem;
        line-height: 1.4;
    }
    .mini-note {
        background: #fff;
        border: 2px solid var(--border);
        box-shadow: 4px 4px 0 #3a2220;
        padding: 0.75rem 0.85rem;
        margin-bottom: 0.9rem;
    }
    .mini-note p {
        margin: 0.15rem 0;
        color: var(--muted);
        font-size: 0.86rem;
        line-height: 1.35;
    }
    
    /* Hide streamlit branding */
    #MainMenu { visibility: hidden; }
    footer { visibility: hidden; }
</style>
""", unsafe_allow_html=True)

# ─── LOAD DATA ───────────────────────────────────────────────────────────────
@st.cache_data
def load_data():
    app_dir = Path(__file__).resolve().parent
    candidates = [
        app_dir / "data",
        app_dir / "pa_copilot" / "data",
        Path.cwd() / "data",
        Path.cwd() / "pa_copilot" / "data",
    ]
    data_dir = next((p for p in candidates if p.exists()), app_dir / "data")
    cases_path = data_dir / "cases.json"
    guidelines_path = data_dir / "guidelines.json"
    with open(cases_path) as f:
        cases = json.load(f)
    with open(guidelines_path) as f:
        guidelines = json.load(f)
    return cases, guidelines


cases, guidelines = load_data()


def get_available_api_key() -> str:
    """Resolve API key from session, Streamlit secrets, or environment."""
    if st.session_state.get("api_key"):
        return st.session_state["api_key"]
    secret_key = ""
    # Read secrets.toml directly to avoid Streamlit warnings when file is absent.
    secrets_candidates = [
        Path.home() / ".streamlit" / "secrets.toml",
        Path.cwd() / ".streamlit" / "secrets.toml",
    ]
    for secrets_path in secrets_candidates:
        if secrets_path.exists():
            try:
                with open(secrets_path, "rb") as f:
                    data = tomllib.load(f)
                    secret_key = data.get("ANTHROPIC_API_KEY", "")
            except Exception:
                secret_key = ""
            if secret_key:
                break
    if secret_key:
        return secret_key
    return os.getenv("ANTHROPIC_API_KEY", "")


def build_demo_outputs(selected_case: dict, guideline: dict):
    """Provide deterministic demo outputs when API key is not available."""
    likely_positive_ids = {
        "CASE-001", "CASE-003", "CASE-005", "CASE-007", "CASE-009",
        "CASE-011", "CASE-012", "CASE-013", "CASE-014", "CASE-015",
        "CASE-016", "CASE-017", "CASE-018", "CASE-019", "CASE-020",
    }
    decision = "APPROVED" if selected_case["id"] in likely_positive_ids else "DENIED"
    confidence = 86 if decision == "APPROVED" else 79

    chart_data = {
        "diagnosis": selected_case["chief_complaint"],
        "procedure_requested": selected_case["procedure_requested"],
        "imaging_results": "Findings documented in transcription",
        "conservative_treatments": ["Conservative care documented in note"],
        "duration_of_symptoms": "Duration documented in transcription",
        "functional_impairment": "Functional impact present in clinical narrative",
        "contraindications_noted": "None documented",
        "red_flags": [],
        "missing_information": ["Detailed contraindication checklist", "Prior treatment response timeline"]
    }

    criteria_results = []
    for idx, criterion in enumerate(guideline["criteria"]):
        if decision == "APPROVED":
            status = "MET" if idx < max(3, len(guideline["criteria"]) - 1) else "INSUFFICIENT INFO"
        else:
            status = "NOT MET" if idx < 2 else "INSUFFICIENT INFO"
        criteria_results.append(
            {
                "criterion": criterion,
                "status": status,
                "evidence": "Demo mode summary generated from selected case data.",
                "notes": "Enable live mode with API key for full chart-grounded reasoning.",
            }
        )

    met_count = sum(1 for c in criteria_results if c["status"] == "MET")
    not_met_count = sum(1 for c in criteria_results if c["status"] == "NOT MET")
    insufficient_count = sum(1 for c in criteria_results if c["status"] == "INSUFFICIENT INFO")

    decision_result = {
        "decision": decision,
        "confidence": confidence,
        "primary_reason": "Demo mode estimate based on case profile and matched guideline.",
        "supporting_reasons": [
            "Selected case characteristics were mapped to the requested policy criteria.",
            "Coverage decision in demo mode is illustrative, not payer-adjudicated.",
            "Use live mode for chart-level evidence extraction and stronger justification.",
        ],
        "denial_codes": ["CO-50: Not medically necessary"] if decision == "DENIED" else [],
        "clinical_basis": guideline["source"],
    }

    advice_result = {
        "immediate_actions": [
            "Confirm documentation of symptom duration and failed conservative care.",
            "Add objective exam or imaging evidence tied directly to policy criteria.",
        ],
        "documentation_gaps": [
            "Explicit contraindication review",
            "Procedure-specific risk and benefit discussion",
        ],
        "appeal_likelihood": "MODERATE",
        "appeal_strategy": "If denied, submit a focused addendum that maps each unmet criterion to explicit chart evidence and request peer review when medically appropriate.",
        "peer_to_peer_recommended": decision == "DENIED",
        "peer_to_peer_talking_points": [
            "Clinical severity and impact on function",
            "Objective findings supporting necessity",
            "Why alternatives are not adequate for this patient",
        ],
        "alternative_options": [
            "Continue optimized conservative management",
            "Re-evaluate with specialist follow-up and updated diagnostics",
        ],
    }

    return chart_data, {
        "criteria_results": criteria_results,
        "met_count": met_count,
        "not_met_count": not_met_count,
        "insufficient_count": insufficient_count,
    }, decision_result, advice_result

# ─── SESSION STATE ───────────────────────────────────────────────────────────
if "results" not in st.session_state:
    st.session_state.results = {}
if "history" not in st.session_state:
    st.session_state.history = []
if "api_key" not in st.session_state:
    st.session_state.api_key = ""
if "demo_mode" not in st.session_state:
    st.session_state.demo_mode = False

# ─── SIDEBAR ─────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### Configuration")
    
    resolved_key = get_available_api_key()
    if resolved_key and not st.session_state.api_key:
        st.session_state.api_key = resolved_key
        init_client(resolved_key)

    st.caption("Choose how you want to run this tool.")
    st.session_state.demo_mode = st.checkbox(
        "Use demo mode (no API key)",
        value=st.session_state.demo_mode,
    )

    api_key = st.text_input(
        "Anthropic API Key",
        type="password",
        value=st.session_state.api_key,
        placeholder="sk-ant-...",
        help="Only needed for live AI analysis."
    )
    if api_key:
        st.session_state.api_key = api_key
        init_client(api_key)
        st.success("Live mode is ready")
    elif st.session_state.demo_mode:
        st.info("Demo mode is on")
    
    st.markdown("---")
    st.markdown("### Session Summary")
    
    total = len(st.session_state.history)
    approved = sum(1 for h in st.session_state.history if h.get("decision") == "APPROVED")
    denied = sum(1 for h in st.session_state.history if h.get("decision") == "DENIED")
    pended = total - approved - denied
    
    col1, col2 = st.columns(2)
    col1.metric("Total Cases", total)
    col2.metric("Approved", approved)
    col1.metric("Denied", denied)
    col2.metric("Pending", pended)
    
    st.markdown("---")
    st.markdown("### Recent Cases")
    if st.session_state.history:
        for h in st.session_state.history[-5:][::-1]:
            status = "Approved" if h["decision"] == "APPROVED" else ("Denied" if h["decision"] == "DENIED" else "Pending")
            st.markdown(f"**{h['case_id']}** ({status}) — {h['procedure'][:25]}...")
    else:
        st.caption("No cases run yet")
    
    st.markdown("---")
    st.markdown("""
    <div style='font-size:0.72rem; color:#64748b;'>
    <b>Data Used</b><br>
    Clinical note samples<br>
    CMS coverage criteria<br>
    Claude Sonnet (live mode)
    </div>
    """, unsafe_allow_html=True)

# ─── MAIN HEADER ─────────────────────────────────────────────────────────────
st.markdown("""
<div class="app-header">
    <h1>Coverage Review Assistant</h1>
    <p>Clinical Coverage Review Workspace</p>
    <span class="data-badge">MTSamples Dataset</span>
    <span class="data-badge" style="margin-left:0.5rem;">CMS Coverage Guidelines</span>
</div>
""", unsafe_allow_html=True)

# ─── TABS ────────────────────────────────────────────────────────────────────
tab1, tab2 = st.tabs(["Run Analysis", "Browse Cases"])

# ══════════════════════════════════════════════════════════════════
# TAB 1: PA ANALYSIS
# ══════════════════════════════════════════════════════════════════
with tab1:
    col_left, col_right = st.columns([1.05, 1.2], gap="medium")
    
    with col_left:
        st.markdown("### Step 1: Select a Case")
        
        # Case selector
        case_options = {
            f"{c['id']} — {c['specialty']} — {c['chief_complaint'][:50]}": c
            for c in cases
        }
        selected_label = st.selectbox(
            "Choose a real clinical case:",
            options=list(case_options.keys()),
            label_visibility="collapsed"
        )
        selected_case = case_options[selected_label]
        
        # Case preview
        with st.expander("View Full Clinical Note", expanded=False):
            st.markdown(f"**Case:** {selected_case['id']}")
            st.markdown(f"**Specialty:** {selected_case['specialty']}")
            st.markdown(f"**Procedure Requested:** {selected_case['procedure_requested']}")
            st.markdown("---")
            st.text_area(
                "Transcription",
                value=selected_case['transcription'],
                height=250,
                disabled=True,
                label_visibility="collapsed"
            )
        
        st.markdown("### Step 2: Review Guideline")
        guideline_key = selected_case['guideline_key']
        guideline = guidelines[guideline_key]
        
        st.info(f"**Auto-matched:** {guideline['name']}\n\n*Source: {guideline['source']}*")
        
        with st.expander("View Coverage Criteria", expanded=False):
            for i, criterion in enumerate(guideline['criteria'], 1):
                st.markdown(f"**{i}.** {criterion}")
        
        st.markdown("---")
        
        # Run button
        live_api_key = get_available_api_key()
        run_disabled = not (st.session_state.demo_mode or live_api_key)
        if run_disabled:
            st.warning("To continue, either enter an API key or enable demo mode in the sidebar.")
        
        run_btn = st.button(
            "Step 3: Run Analysis",
            type="primary",
            disabled=run_disabled,
            use_container_width=True
        )
    
    # ── RIGHT PANEL: RESULTS ──────────────────────────────────────
    with col_right:
        st.markdown("### Results")

        st.markdown(
            """
            <div class="note-box">
                <h4>How This Tool Helps</h4>
                <p><b>Purpose:</b> This tool helps you check whether a coverage request is well-supported before submission.</p>
                <p><b>What happens:</b> It reads the note, compares it with coverage rules, then shows a coverage recommendation and next steps.</p>
                <p><b>How to use:</b> Pick a case, review the guideline, and click <b>Step 3: Run Analysis</b>.</p>
            </div>
            """,
            unsafe_allow_html=True
        )

        st.markdown(
            """
            <div class="mini-note">
                <p><b>Quick Start:</b> Pick a case, confirm the guideline, and click <b>Step 3: Run Analysis</b>.</p>
                <p><b>You will get:</b> Criteria check, coverage recommendation, confidence score, and simple next actions.</p>
            </div>
            """,
            unsafe_allow_html=True
        )
        
        results_container = st.container()
        
        if run_btn:
            st.session_state.results = {}
            if live_api_key:
                init_client(live_api_key)
            demo_mode_active = st.session_state.demo_mode and not live_api_key
            demo_agent1 = demo_agent2 = demo_agent3 = demo_agent4 = None
            if demo_mode_active:
                demo_agent1, demo_agent2, demo_agent3, demo_agent4 = build_demo_outputs(selected_case, guideline)
            
            with results_container:
                # ── AGENT 1 ──────────────────────────────────────
                with st.status("Step 1 of 4: Reading clinical details...", expanded=True) as status1:
                    agent1_result = None
                    try:
                        if demo_mode_active:
                            agent1_result = demo_agent1
                            st.session_state.results['agent_1'] = agent1_result
                            status1.update(label="Step 1 complete (demo mode)", state="complete")
                        else:
                            for agent_id, result in run_full_pipeline(
                                transcription=selected_case['transcription'],
                                procedure=selected_case['procedure_requested'],
                                guidelines=guideline['criteria'],
                                guideline_name=guideline['name']
                            ):
                                if agent_id == "agent_1":
                                    agent1_result = result
                                    st.session_state.results['agent_1'] = result
                                    status1.update(label="Step 1 complete", state="complete")
                                    break
                    except Exception as e:
                        status1.update(label=f"Agent 1 failed: {str(e)}", state="error")
                
                # Show Agent 1 results
                if agent1_result:
                    st.markdown('<div class="agent-card success">', unsafe_allow_html=True)
                    st.markdown("**Step 1: Clinical Summary**")
                    
                    a1_cols = st.columns(2)
                    with a1_cols[0]:
                        st.markdown(f"**Diagnosis:** {agent1_result.get('diagnosis', 'N/A')}")
                        st.markdown(f"**Duration:** {agent1_result.get('duration_of_symptoms', 'N/A')}")
                        st.markdown(f"**Imaging:** {agent1_result.get('imaging_results', 'N/A')}")
                    with a1_cols[1]:
                        st.markdown(f"**Functional Impairment:**\n{agent1_result.get('functional_impairment', 'N/A')}")
                        txts = agent1_result.get('conservative_treatments', [])
                        st.markdown("**Treatment Tried:** " + (", ".join(txts) if txts else "None documented"))
                    
                    missing = agent1_result.get('missing_information', [])
                    if missing:
                        st.warning("Missing information: " + " | ".join(missing))
                    st.markdown('</div>', unsafe_allow_html=True)
                
                # ── AGENT 2 ──────────────────────────────────────
                agent2_result = None
                if agent1_result:
                    with st.status("Step 2 of 4: Checking coverage criteria...", expanded=True) as status2:
                        try:
                            if demo_mode_active:
                                agent2_result = demo_agent2
                                st.session_state.results['agent_2'] = agent2_result
                                status2.update(label="Step 2 complete (demo mode)", state="complete")
                            else:
                                # Re-run remaining agents
                                for agent_id, result in run_full_pipeline(
                                    transcription=selected_case['transcription'],
                                    procedure=selected_case['procedure_requested'],
                                    guidelines=guideline['criteria'],
                                    guideline_name=guideline['name']
                                ):
                                    if agent_id == "agent_2":
                                        agent2_result = result
                                        st.session_state.results['agent_2'] = result
                                        status2.update(label="Step 2 complete", state="complete")
                                        break
                        except Exception as e:
                            status2.update(label=f"Agent 2 failed: {str(e)}", state="error")
                
                if agent2_result:
                    st.markdown('<div class="agent-card">', unsafe_allow_html=True)
                    st.markdown("**Step 2: Criteria Check**")
                    
                    met = agent2_result.get('met_count', 0)
                    not_met = agent2_result.get('not_met_count', 0)
                    insuff = agent2_result.get('insufficient_count', 0)
                    total_c = met + not_met + insuff
                    
                    m1, m2, m3 = st.columns(3)
                    m1.metric("Met", met)
                    m2.metric("Not Met", not_met)
                    m3.metric("Insufficient", insuff)
                    
                    progress_ratio = (met / total_c) if total_c > 0 else 0
                    if progress_ratio > 0:
                        st.progress(progress_ratio, text=f"{met}/{total_c} criteria met")
                    else:
                        st.caption(f"Criteria matched: {met}/{total_c} (no criteria met yet)")
                    
                    for cr in agent2_result.get('criteria_results', []):
                        pill_class = (
                            "pill-met" if cr['status'] == "MET" else
                            "pill-notmet" if cr['status'] == "NOT MET" else
                            "pill-insuff"
                        )
                        st.markdown(
                            f"<span class='{pill_class}'>{cr['status']}</span> **{cr['criterion'][:80]}...**<br>"
                            f"<small style='color:#475569'>Evidence: {cr.get('evidence', '')[:120]}</small>",
                            unsafe_allow_html=True
                        )
                    st.markdown('</div>', unsafe_allow_html=True)
                
                # ── AGENT 3 ──────────────────────────────────────
                agent3_result = None
                if agent2_result:
                    with st.status("Step 3 of 4: Generating coverage recommendation...", expanded=True) as status3:
                        try:
                            if demo_mode_active:
                                agent3_result = demo_agent3
                                st.session_state.results['agent_3'] = agent3_result
                                status3.update(label="Step 3 complete (demo mode)", state="complete")
                            else:
                                for agent_id, result in run_full_pipeline(
                                    transcription=selected_case['transcription'],
                                    procedure=selected_case['procedure_requested'],
                                    guidelines=guideline['criteria'],
                                    guideline_name=guideline['name']
                                ):
                                    if agent_id == "agent_3":
                                        agent3_result = result
                                        st.session_state.results['agent_3'] = result
                                        status3.update(label="Step 3 complete", state="complete")
                                        break
                        except Exception as e:
                            status3.update(label=f"Agent 3 failed: {str(e)}", state="error")
                
                if agent3_result:
                    decision = agent3_result.get('decision', 'UNKNOWN')
                    verdict_class = (
                        "verdict-approved" if "APPROVED" in decision else
                        "verdict-denied" if "DENIED" in decision else
                        "verdict-pend"
                    )
                    st.markdown(
                        f'<div class="{verdict_class}">{decision}</div>',
                        unsafe_allow_html=True
                    )
                    
                    conf = agent3_result.get('confidence', 0)
                    st.markdown(
                        f'<div class="conf-bar-bg"><div class="conf-bar-fill" style="width:{conf}%"></div></div>'
                        f'<small style="color:#64748b">Confidence: {conf}%</small>',
                        unsafe_allow_html=True
                    )
                    
                    st.markdown(f"**Rationale:** {agent3_result.get('primary_reason', '')}")
                    for reason in agent3_result.get('supporting_reasons', []):
                        st.markdown(f"• {reason}")
                    
                    if agent3_result.get('denial_codes'):
                        st.error("Denial Codes: " + " · ".join(agent3_result['denial_codes']))
                    
                    # ── AGENT 4 ──────────────────────────────────────
                    with st.status("Step 4 of 4: Recommending next actions...", expanded=True) as status4:
                        agent4_result = None
                        try:
                            if demo_mode_active:
                                agent4_result = demo_agent4
                                st.session_state.results['agent_4'] = agent4_result
                                status4.update(label="Step 4 complete (demo mode)", state="complete")
                            else:
                                for agent_id, result in run_full_pipeline(
                                    transcription=selected_case['transcription'],
                                    procedure=selected_case['procedure_requested'],
                                    guidelines=guideline['criteria'],
                                    guideline_name=guideline['name']
                                ):
                                    if agent_id == "agent_4":
                                        agent4_result = result
                                        st.session_state.results['agent_4'] = result
                                        status4.update(label="Step 4 complete", state="complete")
                                        break
                        except Exception as e:
                            status4.update(label=f"Agent 4 failed: {str(e)}", state="error")
                    
                    if agent4_result:
                        st.markdown('<div class="agent-card warning">', unsafe_allow_html=True)
                        st.markdown("**Step 4: Next Actions**")
                        
                        appeal_likelihood = agent4_result.get('appeal_likelihood', 'UNKNOWN')
                        p2p = agent4_result.get('peer_to_peer_recommended', False)
                        
                        al_col, p2p_col = st.columns(2)
                        al_col.metric("Appeal Likelihood", appeal_likelihood)
                        p2p_col.metric("Peer-to-Peer Call", "Recommended" if p2p else "Not Required")
                        
                        if agent4_result.get('immediate_actions'):
                            st.markdown("**Immediate Actions:**")
                            for action in agent4_result['immediate_actions']:
                                st.markdown(f"- {action}")
                        
                        if agent4_result.get('documentation_gaps'):
                            st.markdown("**Documentation Gaps:**")
                            for gap in agent4_result['documentation_gaps']:
                                st.markdown(f"• {gap}")
                        
                        if p2p and agent4_result.get('peer_to_peer_talking_points'):
                            with st.expander("Peer-to-Peer Talking Points"):
                                for tp in agent4_result['peer_to_peer_talking_points']:
                                    st.markdown(f"• {tp}")
                        
                        if agent4_result.get('alternative_options'):
                            with st.expander("Alternative Options"):
                                for alt in agent4_result['alternative_options']:
                                    st.markdown(f"• {alt}")
                        
                        st.markdown('</div>', unsafe_allow_html=True)
                    
                    # Save to history
                    st.session_state.history.append({
                        "case_id": selected_case['id'],
                        "procedure": selected_case['procedure_requested'],
                        "decision": decision,
                        "confidence": conf
                    })
        
        elif st.session_state.results:
            st.info("Last results are shown above. Select a case and click Step 3: Run Analysis.")
        else:
            st.markdown("""
            <div style='text-align:left; padding: 1rem 0.2rem; color:#64748b; border:2px dashed #3a2220; background:#fff;'>
                <div style='font-size:0.98rem; margin-top:0.1rem; padding:0.6rem 0.8rem;'>
                    Select a case and click <b>Step 3: Run Analysis</b> to start.
                </div>
                <div style='font-size:0.84rem; margin-top:0.2rem; padding:0 0.8rem 0.6rem 0.8rem;'>
                    You will see 4 simple sections: clinical summary, criteria check, coverage recommendation, and next actions.
                </div>
            </div>
            """, unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════
# TAB 2: CASE BROWSER
# ══════════════════════════════════════════════════════════════════
with tab2:
    st.markdown("### Browse Cases")
    st.caption(f"Showing {len(cases)} real clinical cases from MTSamples dataset")
    
    # Filter row
    f1, f2, f3 = st.columns([2, 2, 1])
    with f1:
        specialty_filter = st.selectbox(
            "Filter by Specialty",
            ["All"] + sorted(set(c['specialty'] for c in cases))
        )
    with f2:
        procedure_filter = st.selectbox(
            "Filter by Procedure",
            ["All"] + sorted(set(c['procedure_requested'] for c in cases))
        )
    with f3:
        st.markdown("<br>", unsafe_allow_html=True)
        clear = st.button("Clear Filters", use_container_width=True)
    
    filtered_cases = cases
    if specialty_filter != "All":
        filtered_cases = [c for c in filtered_cases if c['specialty'] == specialty_filter]
    if procedure_filter != "All":
        filtered_cases = [c for c in filtered_cases if c['procedure_requested'] == procedure_filter]
    
    st.markdown(f"**{len(filtered_cases)} cases** matching filters")
    st.markdown("---")
    
    # Case table header
    h1, h2, h3, h4, h5 = st.columns([1, 1.5, 2, 2.5, 1])
    h1.markdown("**Case ID**")
    h2.markdown("**Specialty**")
    h3.markdown("**Procedure**")
    h4.markdown("**Chief Complaint**")
    h5.markdown("**Action**")
    st.markdown("---")
    
    for case in filtered_cases:
        c1, c2, c3, c4, c5 = st.columns([1, 1.5, 2, 2.5, 1])
        c1.markdown(f"`{case['id']}`")
        c2.markdown(case['specialty'])
        c3.markdown(case['procedure_requested'])
        c4.markdown(case['chief_complaint'])
        if c5.button("Run", key=f"run_{case['id']}", use_container_width=True):
            st.session_state['selected_case_from_browser'] = case['id']
            st.info(f"Case {case['id']} selected. Switch to **PA Analysis** and click Run.")
