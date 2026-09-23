import os
import streamlit as st
from datetime import datetime
from langchain_core.messages import HumanMessage
from main import app

st.set_page_config(
    page_title="Boarding Pass — AI Travel Planner",
    page_icon="🎫",
    layout="wide",
)

# ═══════════════════════════════════════════════════════════════════════════
# STYLE
# ═══════════════════════════════════════════════════════════════════════════

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,400;9..144,500;9..144,600;9..144,700&family=IBM+Plex+Mono:wght@400;500;600&family=Work+Sans:wght@400;500;600&display=swap');

:root {
    --ink:      #0E1F1B;
    --ink-2:    #132923;
    --paper:    #F5EFDD;
    --paper-2:  #ECE3C8;
    --teal:     #16453D;
    --teal-2:   #1E5A50;
    --rust:     #B4472A;
    --brass:    #C6A15B;
    --muted:    #5C6B62;
    --muted-on-paper: #6B6350;
}

html, body, .stApp {
    background: var(--ink) !important;
    font-family: 'Work Sans', sans-serif;
    color: var(--paper);
}

#MainMenu, footer, header { visibility: hidden; }
.block-container { max-width: 980px !important; padding-top: 2.2rem !important; padding-bottom: 5rem !important; }

/* ── faint runway-line texture on the page ── */
.stApp {
    background-image:
        repeating-linear-gradient(180deg, transparent, transparent 79px, rgba(198,161,91,0.05) 80px);
}

/* ── masthead ── */
.masthead {
    display: flex;
    align-items: baseline;
    justify-content: space-between;
    margin-bottom: 1.6rem;
    padding-bottom: 0.9rem;
    border-bottom: 1px solid rgba(198,161,91,0.28);
}
.masthead-mark {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.72rem;
    letter-spacing: 0.14em;
    color: var(--brass);
    text-transform: uppercase;
}
.masthead-mark b { color: var(--paper); }
.masthead-tag {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.68rem;
    color: var(--muted);
    letter-spacing: 0.04em;
}

/* ══════════════════════════════════════════════
   THE BOARDING PASS (hero + input)
   ══════════════════════════════════════════════ */

.pass {
    background: var(--paper);
    color: var(--ink);
    border-radius: 4px;
    position: relative;
    box-shadow: 0 24px 60px rgba(0,0,0,0.45);
    margin-bottom: 2.4rem;
}
.pass-top {
    padding: 1.9rem 2.2rem 1.5rem 2.2rem;
}
.pass-eyebrow {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.66rem;
    letter-spacing: 0.16em;
    color: var(--rust);
    text-transform: uppercase;
    margin-bottom: 0.6rem;
}
.pass-route {
    display: flex;
    align-items: center;
    gap: 1.1rem;
}
.pass-city {
    font-family: 'Fraunces', serif;
    font-weight: 600;
    font-size: 2.1rem;
    line-height: 1;
    color: var(--ink);
}
.pass-city-sub {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.72rem;
    color: var(--muted-on-paper);
    margin-top: 0.35rem;
    letter-spacing: 0.05em;
}
.pass-arrow {
    flex: 1;
    height: 1px;
    background:
        repeating-linear-gradient(90deg, var(--rust), var(--rust) 6px, transparent 6px, transparent 12px);
    position: relative;
    top: -4px;
}
.pass-arrow::after {
    content: "✈";
    position: absolute;
    right: -2px;
    top: -11px;
    color: var(--rust);
    font-size: 0.95rem;
}
.pass-dest-placeholder {
    color: #9C8F6E;
}

/* perforation strip between pass halves */
.perf {
    position: relative;
    height: 1px;
    border-top: 1.5px dashed #C9BC98;
    margin: 0 0;
}
.perf::before, .perf::after {
    content: "";
    position: absolute;
    top: -10px;
    width: 20px;
    height: 20px;
    background: var(--ink);
    border-radius: 50%;
}
.perf::before { left: -32px; }
.perf::after  { right: -32px; }

.pass-bottom {
    padding: 1.5rem 2.2rem 2rem 2.2rem;
}
.pass-field-label {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.66rem;
    letter-spacing: 0.13em;
    color: var(--muted-on-paper);
    text-transform: uppercase;
    margin-bottom: 0.5rem;
}

/* textarea styled as passenger-notes field */
.pass-bottom .stTextArea textarea {
    background: var(--paper-2) !important;
    border: 1px solid #D9CC9F !important;
    border-radius: 3px !important;
    color: var(--ink) !important;
    font-family: 'Work Sans', sans-serif !important;
    font-size: 0.97rem !important;
    line-height: 1.55 !important;
    resize: none !important;
}
.pass-bottom .stTextArea textarea:focus {
    border-color: var(--rust) !important;
    box-shadow: 0 0 0 1px var(--rust) !important;
}
.pass-bottom .stTextArea textarea::placeholder { color: #A69A79 !important; }
.pass-bottom .stTextArea label { display: none !important; }

/* destination stub chips */
.stub-row-label {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.64rem;
    letter-spacing: 0.12em;
    color: var(--muted-on-paper);
    text-transform: uppercase;
    margin: 1.1rem 0 0.55rem 0;
}
.pass-bottom div[data-testid="stButton"] > button {
    background: transparent !important;
    color: var(--teal) !important;
    border: 1px dashed #B7A876 !important;
    border-radius: 3px !important;
    font-family: 'IBM Plex Mono', monospace !important;
    font-size: 0.76rem !important;
    font-weight: 500 !important;
    padding: 0.4rem 0.6rem !important;
    box-shadow: none !important;
    transition: all 0.15s ease !important;
}
.pass-bottom div[data-testid="stButton"] > button:hover {
    border-color: var(--rust) !important;
    color: var(--rust) !important;
    background: rgba(180,71,42,0.06) !important;
}

/* the stamp / submit button */
.stamp-wrap { margin-top: 1.5rem; display: flex; justify-content: flex-start; }
.stamp-wrap div[data-testid="stButton"] > button {
    background: transparent !important;
    color: var(--rust) !important;
    border: 2.5px solid var(--rust) !important;
    border-radius: 999px !important;
    font-family: 'IBM Plex Mono', monospace !important;
    font-size: 0.82rem !important;
    font-weight: 600 !important;
    letter-spacing: 0.08em !important;
    text-transform: uppercase !important;
    padding: 0.7rem 1.8rem !important;
    transform: rotate(-2deg);
    transition: all 0.15s ease !important;
    box-shadow: none !important;
    width: auto !important;
}
.stamp-wrap div[data-testid="stButton"] > button:hover {
    background: rgba(180,71,42,0.08) !important;
    transform: rotate(-2deg) scale(1.02);
}
.stamp-wrap div[data-testid="stButton"] > button:active {
    transform: rotate(-2deg) scale(0.98);
}

/* ══════════════════════════════════════════════
   SECTION LABEL (mono, ticket-coupon style)
   ══════════════════════════════════════════════ */
.coupon-head {
    display: flex;
    align-items: center;
    gap: 0.7rem;
    margin: 2.1rem 0 0.9rem 0;
}
.coupon-head-num {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.72rem;
    color: var(--ink);
    background: var(--brass);
    padding: 0.15rem 0.5rem;
    border-radius: 2px;
    font-weight: 600;
}
.coupon-head-text {
    font-family: 'Fraunces', serif;
    font-size: 1.25rem;
    font-weight: 600;
    color: var(--paper);
}
.coupon-head-line { flex: 1; height: 1px; background: rgba(198,161,91,0.25); }

/* ══════════════════════════════════════════════
   AGENT COUPON STUBS
   ══════════════════════════════════════════════ */
[data-testid="stStatusWidget"] {
    background: var(--paper) !important;
    border: none !important;
    border-radius: 3px !important;
    border-left: 4px solid var(--teal) !important;
    margin-bottom: 0.55rem;
}
[data-testid="stStatusWidget"] > div:first-child {
    background: var(--paper) !important;
    border-radius: 0 !important;
}
[data-testid="stStatusWidget"] p,
[data-testid="stStatusWidget"] span,
[data-testid="stStatusWidget"] label {
    font-family: 'IBM Plex Mono', monospace !important;
    color: var(--ink) !important;
    font-size: 0.86rem !important;
}
[data-testid="stStatusWidget"] details,
[data-testid="stStatusWidget"] details > div,
[data-testid="stStatusWidget"] [data-testid="stVerticalBlock"] {
    background: var(--paper-2) !important;
    padding: 0.3rem 0.6rem !important;
}
[data-testid="stStatusWidget"] .stMarkdown p,
[data-testid="stStatusWidget"] .stMarkdown li {
    font-family: 'Work Sans', sans-serif !important;
    color: var(--ink) !important;
    font-size: 0.92rem !important;
}
[data-testid="stStatusWidget"] svg { color: var(--teal) !important; }
[data-testid="stStatusWidget"] a { color: var(--teal-2) !important; }

/* ══════════════════════════════════════════════
   MANIFEST (metrics row) — styled like a ticket summary strip
   ══════════════════════════════════════════════ */
.manifest {
    display: flex;
    font-family: 'IBM Plex Mono', monospace;
    border: 1px solid rgba(198,161,91,0.3);
    border-radius: 3px;
    overflow: hidden;
    margin: 1.6rem 0;
}
.manifest-cell {
    flex: 1;
    padding: 0.85rem 1rem;
    border-right: 1px dashed rgba(198,161,91,0.3);
}
.manifest-cell:last-child { border-right: none; }
.manifest-val { font-size: 1.35rem; font-weight: 600; color: var(--brass); }
.manifest-lbl { font-size: 0.62rem; letter-spacing: 0.1em; text-transform: uppercase; color: var(--muted); margin-top: 0.15rem; }

/* ══════════════════════════════════════════════
   FINAL ITINERARY TICKET
   ══════════════════════════════════════════════ */
.itinerary-ticket {
    background: var(--paper);
    color: var(--ink);
    border-radius: 4px;
    padding: 2rem 2.2rem 1.4rem 2.2rem;
    margin-top: 0.3rem;
    box-shadow: 0 20px 50px rgba(0,0,0,0.4);
    position: relative;
}
.itinerary-ticket::before {
    content: "";
    position: absolute;
    top: -1px; left: 0; right: 0; height: 6px;
    background: repeating-linear-gradient(90deg, var(--rust), var(--rust) 10px, transparent 10px, transparent 20px);
    border-radius: 4px 4px 0 0;
}
.itinerary-ticket .stMarkdown p,
.itinerary-ticket .stMarkdown li { color: var(--ink) !important; font-size: 0.98rem; line-height: 1.75; }
.itinerary-ticket .stMarkdown h1,
.itinerary-ticket .stMarkdown h2,
.itinerary-ticket .stMarkdown h3 {
    font-family: 'Fraunces', serif !important;
    color: var(--teal) !important;
}
.itinerary-ticket .stMarkdown strong { color: var(--rust) !important; }
.itinerary-ticket .stMarkdown code {
    background: var(--paper-2) !important;
    color: var(--teal-2) !important;
    font-family: 'IBM Plex Mono', monospace !important;
}

/* ── save strip ── */
.save-strip {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.8rem;
    color: var(--muted);
    border-top: 1px dashed rgba(198,161,91,0.3);
    padding-top: 0.7rem;
    margin-top: 1rem;
}
.save-strip code { color: var(--brass); background: none; }

div[data-testid="stDownloadButton"] > button {
    background: transparent !important;
    color: var(--paper) !important;
    border: 1px solid rgba(198,161,91,0.4) !important;
    border-radius: 3px !important;
    font-family: 'IBM Plex Mono', monospace !important;
    font-size: 0.78rem !important;
    letter-spacing: 0.04em;
}
div[data-testid="stDownloadButton"] > button:hover {
    border-color: var(--brass) !important;
    color: var(--brass) !important;
}

/* ── alerts ── */
.stAlert {
    background: var(--paper) !important;
    border-radius: 3px !important;
    border-left: 4px solid var(--rust) !important;
}
.stAlert p, .stAlert div { color: var(--ink) !important; font-family: 'Work Sans', sans-serif !important; }

/* ── sidebar: passport page ── */
section[data-testid="stSidebar"] {
    background: var(--ink-2) !important;
    border-right: 1px solid rgba(198,161,91,0.18) !important;
}
.pp-title {
    font-family: 'Fraunces', serif;
    font-size: 1.15rem;
    font-weight: 600;
    color: var(--paper);
    margin-bottom: 0.15rem;
}
.pp-sub {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.65rem;
    letter-spacing: 0.1em;
    color: var(--brass);
    text-transform: uppercase;
    margin-bottom: 1.1rem;
}
.pp-section {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.65rem;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    color: var(--muted);
    margin: 1.3rem 0 0.6rem 0;
}
.pp-stamp {
    display: inline-block;
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.72rem;
    color: var(--brass);
    border: 1px dashed rgba(198,161,91,0.45);
    border-radius: 999px;
    padding: 0.3rem 0.7rem;
    margin: 0 0.35rem 0.4rem 0;
}
.pp-chain { display: flex; flex-direction: column; gap: 0.4rem; }
.pp-chain-item {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.78rem;
    color: #C8D6CE;
    padding: 0.4rem 0.6rem;
    background: rgba(198,161,91,0.06);
    border-left: 2px solid var(--teal-2);
}

section[data-testid="stSidebar"] .stTextInput input {
    background: rgba(245,239,221,0.06) !important;
    border: 1px solid rgba(198,161,91,0.3) !important;
    border-radius: 3px !important;
    color: var(--paper) !important;
    font-family: 'IBM Plex Mono', monospace !important;
}
section[data-testid="stSidebar"] .stTextInput input:focus {
    border-color: var(--rust) !important;
    box-shadow: 0 0 0 1px var(--rust) !important;
}
section[data-testid="stSidebar"] label {
    font-family: 'IBM Plex Mono', monospace !important;
    color: var(--brass) !important;
    font-size: 0.68rem !important;
    letter-spacing: 0.08em !important;
}
section[data-testid="stSidebar"] hr { border-color: rgba(198,161,91,0.18) !important; }

/* keyboard focus visibility */
button:focus-visible, input:focus-visible, textarea:focus-visible {
    outline: 2px solid var(--rust) !important;
    outline-offset: 2px;
}

@media (prefers-reduced-motion: reduce) {
    * { transition: none !important; animation: none !important; }
}

@media (max-width: 640px) {
    .pass-city { font-size: 1.5rem; }
    .pass-top, .pass-bottom { padding-left: 1.2rem !important; padding-right: 1.2rem !important; }
    .manifest { flex-direction: column; }
    .manifest-cell { border-right: none; border-bottom: 1px dashed rgba(198,161,91,0.3); }
}
</style>
""", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════
# STATE
# ═══════════════════════════════════════════════════════════════════════════

if "quick_fill" not in st.session_state:
    st.session_state.quick_fill = ""

# ═══════════════════════════════════════════════════════════════════════════
# SIDEBAR — passport page
# ═══════════════════════════════════════════════════════════════════════════

with st.sidebar:
    st.markdown("<div class='pp-title'>🎫 Boarding Pass</div>", unsafe_allow_html=True)
    st.markdown("<div class='pp-sub'>AI Travel Planner · Multi-Agent</div>", unsafe_allow_html=True)
    st.markdown("---")

    thread_id = st.text_input("Passenger ID", value="aarohi_user",
                               help="Keeps your trip history linked across visits").strip()

    st.markdown("<div class='pp-section'>Crew on board</div>", unsafe_allow_html=True)
    st.markdown(
        "<div class='pp-chain'>"
        "<div class='pp-chain-item'>01 · Flight Agent</div>"
        "<div class='pp-chain-item'>02 · Hotel Agent</div>"
        "<div class='pp-chain-item'>03 · Itinerary Agent</div>"
        "<div class='pp-chain-item'>04 · Final Agent</div>"
        "</div>",
        unsafe_allow_html=True,
    )

    st.markdown("<div class='pp-section'>Visas &amp; carriers</div>", unsafe_allow_html=True)
    st.markdown(
        "<div>"
        "<span class='pp-stamp'>LangGraph</span>"
        "<span class='pp-stamp'>Groq · Llama 3.3</span>"
        "<span class='pp-stamp'>Tavily</span>"
        "<span class='pp-stamp'>PostgreSQL</span>"
        "</div>",
        unsafe_allow_html=True,
    )

# ═══════════════════════════════════════════════════════════════════════════
# MASTHEAD
# ═══════════════════════════════════════════════════════════════════════════

st.markdown(
    "<div class='masthead'>"
    "<div class='masthead-mark'>✈ <b>AAROHI AIR</b> — ISSUED BY 4 AGENTS</div>"
    f"<div class='masthead-tag'>{datetime.now().strftime('%d %b %Y').upper()}</div>"
    "</div>",
    unsafe_allow_html=True,
)

# ═══════════════════════════════════════════════════════════════════════════
# THE BOARDING PASS — hero + input, one physical object
# ═══════════════════════════════════════════════════════════════════════════

st.markdown("<div class='pass'>", unsafe_allow_html=True)

st.markdown(
    "<div class='pass-top'>"
    "<div class='pass-eyebrow'>Where to</div>"
    "<div class='pass-route'>"
    "<div><div class='pass-city'>Anywhere</div><div class='pass-city-sub'>ORIG · YOU</div></div>"
    "<div class='pass-arrow'></div>"
    "<div><div class='pass-city pass-dest-placeholder'>Tell us</div><div class='pass-city-sub'>DEST · ???</div></div>"
    "</div>"
    "</div>",
    unsafe_allow_html=True,
)

st.markdown("<div class='perf'></div>", unsafe_allow_html=True)

st.markdown("<div class='pass-bottom'>", unsafe_allow_html=True)
st.markdown("<div class='pass-field-label'>Passenger notes — describe the trip</div>", unsafe_allow_html=True)

user_query = st.text_area(
    "trip request",
    value=st.session_state.quick_fill,
    placeholder="Plan a 7-day trip to Japan from Bhubaneswar in December, 2 travelers, mid-range budget, love street food and temples",
    height=100,
    label_visibility="collapsed",
)
st.session_state.quick_fill = user_query

st.markdown("<div class='stub-row-label'>Or stamp a quick route</div>", unsafe_allow_html=True)

QUICK = [
    "7-day Japan trip under ₹2L",
    "5-day Paris trip",
    "Dubai weekend getaway",
    "10-day Bali backpacking",
]
qcols = st.columns(len(QUICK))
for qc, label in zip(qcols, QUICK):
    with qc:
        if st.button(label, key=f"q_{label}", use_container_width=True):
            st.session_state.quick_fill = label
            st.rerun()

st.markdown("<div class='stamp-wrap'>", unsafe_allow_html=True)
generate = st.button("Issue my boarding pass", key="generate_btn")
st.markdown("</div>", unsafe_allow_html=True)

st.markdown("</div>", unsafe_allow_html=True)  # /pass-bottom
st.markdown("</div>", unsafe_allow_html=True)  # /pass

# ═══════════════════════════════════════════════════════════════════════════
# AGENT META
# ═══════════════════════════════════════════════════════════════════════════

AGENT_META = {
    "flight_agent":    ("01", "Flight coupon"),
    "hotel_agent":     ("02", "Hotel coupon"),
    "itinerary_agent": ("03", "Itinerary coupon"),
    "final_agent":     ("04", "Final coupon"),
}

# ═══════════════════════════════════════════════════════════════════════════
# RUN
# ═══════════════════════════════════════════════════════════════════════════

if generate:
    if not user_query.strip():
        st.warning("Add your passenger notes before we can issue a pass.")
    elif not thread_id:
        st.warning("Enter a Passenger ID in the sidebar first.")
    else:
        config = {"configurable": {"thread_id": thread_id}}

        # Keys match TravelState in main.py exactly — "llm_call" (singular).
        collected = {
            "flight_results": "",
            "hotel_results": "",
            "itinerary": "",
            "final_response": "",
            "llm_call": 0,
        }

        st.markdown(
            "<div class='coupon-head'>"
            "<div class='coupon-head-num'>·</div>"
            "<div class='coupon-head-text'>Tearing off your coupons</div>"
            "<div class='coupon-head-line'></div>"
            "</div>",
            unsafe_allow_html=True,
        )

        try:
            for chunk in app.stream(
                {
                    "user_query": user_query,
                    "messages": [HumanMessage(content=user_query)],
                    "flight_results": "",
                    "hotel_results": "",
                    "itinerary": "",
                    "llm_call": 0,
                },
                config=config,
                stream_mode="updates",
            ):
                for node_name, state_update in chunk.items():
                    num, label = AGENT_META.get(node_name, ("··", node_name))

                    with st.status(f"{num} · {label}", state="complete", expanded=True):
                        if node_name == "flight_agent":
                            text = state_update.get("flight_results", "")
                            collected["flight_results"] = text
                            st.markdown(text or "_No flight data returned._")

                        elif node_name == "hotel_agent":
                            text = state_update.get("hotel_results", "")
                            collected["hotel_results"] = text
                            st.markdown(text or "_No hotel data returned._")

                        elif node_name == "itinerary_agent":
                            text = state_update.get("itinerary", "")
                            collected["itinerary"] = text
                            st.markdown(text or "_No itinerary generated._")

                        elif node_name == "final_agent":
                            msgs = state_update.get("messages", [])
                            text = msgs[-1].content if msgs else ""
                            collected["final_response"] = text
                            st.markdown(text or "_No final response._")

                    if "llm_call" in state_update:
                        collected["llm_call"] = state_update["llm_call"]

        except Exception as e:
            st.error("The gate agent couldn't complete your itinerary.")
            with st.expander("Technical details"):
                st.code(str(e), language="text")
            st.stop()

        # ── manifest / metrics strip ──
        st.markdown(
            f"""
            <div class="manifest">
                <div class="manifest-cell"><div class="manifest-val">4</div><div class="manifest-lbl">Agents run</div></div>
                <div class="manifest-cell"><div class="manifest-val">{collected['llm_call']}</div><div class="manifest-lbl">LLM calls</div></div>
                <div class="manifest-cell"><div class="manifest-val">CONFIRMED</div><div class="manifest-lbl">Status</div></div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # ── final itinerary ticket ──
        if collected["final_response"]:
            st.markdown(
                "<div class='coupon-head'>"
                "<div class='coupon-head-num'>04</div>"
                "<div class='coupon-head-text'>Your itinerary</div>"
                "<div class='coupon-head-line'></div>"
                "</div>",
                unsafe_allow_html=True,
            )
            st.markdown("<div class='itinerary-ticket'>", unsafe_allow_html=True)
            st.markdown(collected["final_response"])
            st.markdown("</div>", unsafe_allow_html=True)

        # ── save to disk + download ──
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"travel_plan_{timestamp}.md"
        save_dir = os.path.join(os.path.dirname(__file__), "travel_plans")

        file_content = f"""# Travel Plan
**Query:** {user_query}
**Generated:** {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
**Passenger ID:** {thread_id}

---

## Flight Information
{collected['flight_results'] or 'N/A'}

---

## Hotel Information
{collected['hotel_results'] or 'N/A'}

---

## Itinerary
{collected['itinerary'] or 'N/A'}

---

## Final Travel Plan
{collected['final_response'] or 'N/A'}

---
*LLM Calls: {collected['llm_call']}*
"""
        try:
            os.makedirs(save_dir, exist_ok=True)
            with open(os.path.join(save_dir, filename), "w", encoding="utf-8") as f:
                f.write(file_content)
            saved_ok = True
        except OSError:
            saved_ok = False

        dl_col, info_col = st.columns([1, 3])
        with dl_col:
            st.download_button("↓ Download pass", data=file_content,
                                file_name=filename, mime="text/markdown",
                                use_container_width=True)
        with info_col:
            if saved_ok:
                st.markdown(f"<div class='save-strip'>Filed to <code>travel_plans/{filename}</code></div>",
                            unsafe_allow_html=True)
            else:
                st.markdown("<div class='save-strip'>Couldn't file to disk — use the download button.</div>",
                             unsafe_allow_html=True)