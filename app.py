import streamlit as st
import streamlit.components.v1 as components
import google.generativeai as genai
import html
import json
import math
import random
import textwrap
from datetime import datetime
from typing import List, Dict, Optional

# Optional helper used to keep the Attempt Log in the phone's browser storage (survives closing the app).
# If the package is not installed the app still works, but the log resets on every fresh open.
try:
    from streamlit_js_eval import streamlit_js_eval
    HAS_JS_EVAL = True
except Exception:
    HAS_JS_EVAL = False

# --- PAGE CONFIG ---
st.set_page_config(
    page_title="PSC Pro Quiz",
    page_icon="📖",
    layout="wide",
    initial_sidebar_state="expanded"
)

def render_html(html_str: str):
    """Render HTML cleanly without accidental Markdown code-block indentation"""
    st.markdown(textwrap.dedent(html_str).strip(), unsafe_allow_html=True)

# --- RICH COLORFUL SVG ICONS ---
SVG_ICONS = {
    "brand": (
        '<svg width="38" height="38" viewBox="0 0 40 40" fill="none" xmlns="http://www.w3.org/2000/svg">'
        '<rect width="40" height="40" rx="12" fill="url(#brandGrad)"/>'
        '<path d="M11 12.5C11 11.1193 12.1193 10 13.5 10H19V30H13.5C12.1193 30 11 28.8807 11 27.5V12.5Z" fill="#FDE047"/>'
        '<path d="M29 12.5C29 11.1193 27.8807 10 26.5 10H21V30H26.5C27.8807 30 29 28.8807 29 27.5V12.5Z" fill="#34D399"/>'
        '<circle cx="20" cy="19" r="3.4" fill="#FB7185"/>'
        '<defs><linearGradient id="brandGrad" x1="0" y1="0" x2="40" y2="40" gradientUnits="userSpaceOnUse">'
        '<stop stop-color="#2563EB"/><stop offset="1" stop-color="#7C3AED"/></linearGradient></defs>'
        '</svg>'
    ),
    "trophy": (
        '<svg width="24" height="24" viewBox="0 0 24 24" fill="none">'
        '<path d="M7 4H17V10C17 12.7614 14.7614 15 12 15C9.23858 15 7 12.7614 7 10V4Z" fill="#FACC15" stroke="#FEF08A" stroke-width="1.5"/>'
        '<path d="M7 6H4.5C4.5 9 6 10.5 7.5 11M17 6H19.5C19.5 9 18 10.5 16.5 11" stroke="#FBBF24" stroke-width="1.8" stroke-linecap="round"/>'
        '<path d="M10 15H14V18H10V15ZM8 18H16V20.5H8V18Z" fill="#F59E0B"/>'
        '</svg>'
    ),
    "target_score": (
        '<svg width="24" height="24" viewBox="0 0 24 24" fill="none">'
        '<circle cx="12" cy="12" r="9" fill="#10B981" fill-opacity="0.22" stroke="#34D399" stroke-width="2"/>'
        '<circle cx="12" cy="12" r="5" fill="#10B981" fill-opacity="0.45" stroke="#6EE7B7" stroke-width="1.8"/>'
        '<circle cx="12" cy="12" r="2" fill="#A7F3D0"/>'
        '</svg>'
    ),
    "focus_book": (
        '<svg width="24" height="24" viewBox="0 0 24 24" fill="none">'
        '<rect x="3" y="4" width="18" height="16" rx="3" fill="#FB7185" fill-opacity="0.25" stroke="#F43F5E" stroke-width="1.8"/>'
        '<line x1="12" y1="4" x2="12" y2="20" stroke="#FDA4AF" stroke-width="1.8"/>'
        '<path d="M6.5 8.5H9.5M6.5 12H9.5M14.5 8.5H17.5M14.5 12H17.5" stroke="#FFE4E6" stroke-width="1.6" stroke-linecap="round"/>'
        '</svg>'
    ),
    "history_icon": (
        '<svg width="24" height="24" viewBox="0 0 24 24" fill="none">'
        '<circle cx="12" cy="12" r="9" fill="#3B82F6" fill-opacity="0.25" stroke="#60A5FA" stroke-width="2"/>'
        '<path d="M12 7V12L15.5 14" stroke="#93C5FD" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"/>'
        '</svg>'
    ),
    "const_icon": (
        '<svg width="24" height="24" viewBox="0 0 24 24" fill="none">'
        '<rect x="4" y="3" width="16" height="18" rx="3" fill="#10B981" fill-opacity="0.25" stroke="#34D399" stroke-width="2"/>'
        '<path d="M8 8H16M8 12H16M8 16H13" stroke="#A7F3D0" stroke-width="2" stroke-linecap="round"/>'
        '</svg>'
    ),
    "ca_icon": (
        '<svg width="24" height="24" viewBox="0 0 24 24" fill="none">'
        '<rect x="3" y="5" width="18" height="15" rx="3" fill="#F59E0B" fill-opacity="0.25" stroke="#FBBF24" stroke-width="2"/>'
        '<path d="M3 10H21" stroke="#FDE047" stroke-width="2"/>'
        '<circle cx="8" cy="15" r="1.5" fill="#FEF08A"/>'
        '<path d="M12 15H17" stroke="#FEF08A" stroke-width="2" stroke-linecap="round"/>'
        '</svg>'
    ),
    "bulb": (
        '<svg width="22" height="22" viewBox="0 0 24 24" fill="none">'
        '<path d="M9 18H15M10 21H14" stroke="#FACC15" stroke-width="2.2" stroke-linecap="round"/>'
        '<path d="M15.2 14.2C16.4 13.1 17.5 11.4 17.5 9.2C17.5 6.16 15.04 3.7 12 3.7C8.96 3.7 6.5 6.16 6.5 9.2C6.5 11.4 7.6 13.1 8.8 14.2C9.3 14.7 9.6 15.3 9.7 16H14.3C14.4 15.3 14.7 14.7 15.2 14.2Z" fill="#FACC15" fill-opacity="0.3" stroke="#FDE047" stroke-width="2"/>'
        '</svg>'
    ),
    "cracker": (
        '<svg width="26" height="26" viewBox="0 0 32 32" fill="none">'
        '<path d="M6 26L14 12L20 18L6 26Z" fill="#F59E0B" stroke="#FDE047" stroke-width="1.8" stroke-linejoin="round"/>'
        '<circle cx="22" cy="8" r="2.5" fill="#F472B6"/>'
        '<circle cx="26" cy="13" r="2.2" fill="#34D399"/>'
        '<circle cx="18" cy="6" r="2" fill="#60A5FA"/>'
        '<circle cx="25" cy="21" r="2" fill="#FACC15"/>'
        '</svg>'
    ),
    "right_sym": (
        '<svg width="22" height="22" viewBox="0 0 24 24" fill="none">'
        '<circle cx="12" cy="12" r="10" fill="#10B981" fill-opacity="0.25" stroke="#34D399" stroke-width="2"/>'
        '<polyline points="7.5 12.5 10.5 15.5 16.5 9" stroke="#6EE7B7" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"/>'
        '</svg>'
    ),
    "wrong_sym": (
        '<svg width="22" height="22" viewBox="0 0 24 24" fill="none">'
        '<circle cx="12" cy="12" r="10" fill="#F43F5E" fill-opacity="0.25" stroke="#FB7185" stroke-width="2"/>'
        '<line x1="8.5" y1="8.5" x2="15.5" y2="15.5" stroke="#FDA4AF" stroke-width="2.5" stroke-linecap="round"/>'
        '<line x1="15.5" y1="8.5" x2="8.5" y2="15.5" stroke="#FDA4AF" stroke-width="2.5" stroke-linecap="round"/>'
        '</svg>'
    ),
    "attempt_sym": (
        '<svg width="22" height="22" viewBox="0 0 24 24" fill="none">'
        '<circle cx="12" cy="12" r="10" fill="#3B82F6" fill-opacity="0.25" stroke="#60A5FA" stroke-width="2"/>'
        '<path d="M12 7V12L15 14" stroke="#93C5FD" stroke-width="2.3" stroke-linecap="round" stroke-linejoin="round"/>'
        '</svg>'
    ),
    "marks_sym": (
        '<svg width="22" height="22" viewBox="0 0 24 24" fill="none">'
        '<polygon points="12 2.5 14.9 8.4 21.4 9.3 16.7 13.9 17.8 20.4 12 17.3 6.2 20.4 7.3 13.9 2.6 9.3 9.1 8.4 12 2.5" fill="#F59E0B" fill-opacity="0.3" stroke="#FDE047" stroke-width="1.8" stroke-linejoin="round"/>'
        '</svg>'
    )
}

# --- DARK COLORFUL THEME + HIGH-CONTRAST OPTION FEEDBACK ---
render_html("""
<style>
/* ---- Hide only the unwanted items (GitHub, Edit, Deploy, menu, footer) ---- */
footer {visibility: hidden;}
#MainMenu {visibility: hidden;}
[data-testid="stMainMenu"] {display: none !important;}
[data-testid="stToolbarActions"] {display: none !important;}
[data-testid="stAppDeployButton"] {display: none !important;}
[data-testid="stDecoration"] {display: none !important;}
[data-testid="stStatusWidget"] {display: none !important;}
.stDeployButton {display: none !important;}
.viewerBadge_container__r5tak, [class*="viewerBadge"] {display: none !important;}

/* ---- Keep header + toolbar alive so the sidebar toggle stays visible ---- */
header[data-testid="stHeader"] {
background-color: transparent !important;
visibility: visible !important;
display: flex !important;
}
[data-testid="stToolbar"] {
visibility: visible !important;
display: flex !important;
background: transparent !important;
}

/* ---- Sidebar open/close buttons: always visible, high contrast ---- */
[data-testid="stSidebarCollapsedControl"],
[data-testid="stExpandSidebarButton"],
[data-testid="stSidebarCollapseButton"],
[data-testid="collapsedControl"] {
visibility: visible !important;
display: flex !important;
opacity: 1 !important;
z-index: 999999 !important;
}
[data-testid="stExpandSidebarButton"],
[data-testid="stSidebarCollapsedControl"] button {
background: #1d2b4a !important;
border: 1px solid #3b5a9a !important;
border-radius: 12px !important;
}
[data-testid="stExpandSidebarButton"] svg,
[data-testid="stSidebarCollapsedControl"] svg,
[data-testid="stSidebarCollapseButton"] svg,
[data-testid="collapsedControl"] svg,
[data-testid="stExpandSidebarButton"] span,
[data-testid="stSidebarCollapseButton"] span {
color: #ffffff !important;
fill: #ffffff !important;
}

[data-testid="stSidebar"] {
background-color: #0e1525 !important;
border-right: 1px solid #24324d !important;
visibility: visible !important;
}

.stApp {
background-color: #080c14;
color: #f8fafc;
}

.block-container {
max-width: 960px;
padding-top: 3.2rem;
padding-bottom: 3rem;
}

/* Labels & widget text visibility */
label, .stRadio label, .stSelectbox label, .stSlider label, .stTextInput label,
[data-testid="stWidgetLabel"] p, [data-testid="stMarkdownContainer"] p,
[data-testid="stMarkdownContainer"] h3, [data-testid="stMarkdownContainer"] h4 {
color: #f1f5f9 !important;
opacity: 1 !important;
}
.stRadio div[role="radiogroup"] label span,
.stSelectbox div[data-baseweb="select"] span,
.stSlider div[data-testid="stTickBarMin"],
.stSlider div[data-testid="stTickBarMax"],
[data-testid="stThumbValue"] {
color: #f8fafc !important;
opacity: 1 !important;
}

/* Expander (in-page Exam Options) */
[data-testid="stExpander"] {
background: #121c33 !important;
border: 1px solid #28395e !important;
border-radius: 16px !important;
}
[data-testid="stExpander"] summary p,
[data-testid="stExpander"] summary span,
[data-testid="stExpander"] summary svg {
color: #f8fafc !important;
fill: #f8fafc !important;
font-weight: 700 !important;
}

/* Fix Streamlit alert text contrast so answered options are clearly readable */
[data-testid="stAlert"] p,
[data-testid="stAlert"] span,
[data-testid="stAlert"] strong,
[data-testid="stAlert"] div {
color: #0f172a !important;
opacity: 1 !important;
}

/* Custom high-contrast answered option cards */
.opt-right {
background: linear-gradient(135deg, #065f46 0%, #047857 100%);
border: 1.5px solid #34d399;
border-radius: 12px;
padding: 0.72rem 1rem;
margin-bottom: 0.45rem;
color: #ffffff !important;
font-weight: 700;
}
.opt-wrong {
background: linear-gradient(135deg, #9f1239 0%, #be123c 100%);
border: 1.5px solid #fb7185;
border-radius: 12px;
padding: 0.72rem 1rem;
margin-bottom: 0.45rem;
color: #ffffff !important;
font-weight: 700;
}
.opt-neutral {
background: #111827;
border: 1px solid #263554;
border-radius: 12px;
padding: 0.68rem 1rem;
margin-bottom: 0.45rem;
color: #cbd5e1 !important;
font-weight: 600;
}

/* Top bar */
.top-app-bar {
display: flex;
align-items: center;
justify-content: space-between;
background: linear-gradient(135deg, #111b31 0%, #16223d 100%);
border: 1px solid #28385c;
border-radius: 18px;
padding: 0.9rem 1.15rem;
margin-bottom: 0.85rem;
box-shadow: 0 8px 22px rgba(0, 0, 0, 0.35);
}
.top-app-left {
display: flex;
align-items: center;
gap: 12px;
}
.top-app-sub {
font-size: 0.78rem;
color: #93c5fd !important;
margin: 0;
font-weight: 600;
}
.top-app-title {
font-size: 1.18rem;
font-weight: 800;
color: #ffffff !important;
margin: 0;
}

/* Preparation status panel */
.prep-panel {
background: linear-gradient(145deg, #121c33 0%, #17233f 100%);
border: 1px solid #28395e;
border-radius: 20px;
padding: 1.1rem;
margin-bottom: 0.9rem;
box-shadow: 0 10px 24px rgba(0, 0, 0, 0.3);
}
.prep-title {
font-size: 1.05rem;
font-weight: 800;
color: #ffffff !important;
margin: 0 0 0.85rem 0;
}
.mini-stat-grid {
display: grid;
grid-template-columns: repeat(3, 1fr);
gap: 0.65rem;
}
.mini-stat-card {
background: #1b2847;
border: 1px solid #2f4370;
border-radius: 16px;
padding: 0.85rem 0.55rem;
text-align: center;
}
.mini-stat-icon {
display: flex;
justify-content: center;
margin-bottom: 0.3rem;
}
.mini-stat-val {
font-size: 1.1rem;
font-weight: 800;
color: #ffffff !important;
}
.mini-stat-lbl {
font-size: 0.75rem;
color: #cbd5e1 !important;
margin-top: 0.2rem;
font-weight: 600;
}

/* Colorful category tiles */
.cat-grid {
display: grid;
grid-template-columns: repeat(3, 1fr);
gap: 0.65rem;
margin-bottom: 1rem;
}
.cat-tile-blue {
background: linear-gradient(160deg, #15223d 0%, #10192e 100%);
border: 1px solid #2b4c8c;
border-radius: 16px;
padding: 0.95rem 0.6rem;
text-align: center;
}
.cat-tile-green {
background: linear-gradient(160deg, #102a26 0%, #0d1d24 100%);
border: 1px solid #1e6b58;
border-radius: 16px;
padding: 0.95rem 0.6rem;
text-align: center;
}
.cat-tile-amber {
background: linear-gradient(160deg, #2b2112 0%, #191614 100%);
border: 1px solid #8a5a18;
border-radius: 16px;
padding: 0.95rem 0.6rem;
text-align: center;
}
.cat-icon {
display: flex;
justify-content: center;
margin-bottom: 0.45rem;
}
.cat-name {
font-size: 0.85rem;
font-weight: 700;
color: #f8fafc !important;
}

/* Tags & Question */
.meta-row {
display: flex;
flex-wrap: wrap;
gap: 0.45rem;
margin-bottom: 0.85rem;
}
.tag {
padding: 0.26rem 0.72rem;
border-radius: 999px;
font-size: 0.78rem;
font-weight: 700;
background: #1d2b4a;
color: #93c5fd !important;
border: 1px solid #364f82;
}
.tag-green {
background: #064e3b;
color: #6ee7b7 !important;
border-color: #10b981;
}
.tag-red {
background: #4c0519;
color: #fda4af !important;
border-color: #f43f5e;
}

.q-box {
background: linear-gradient(135deg, #131d34 0%, #192642 100%);
border: 1px solid #2c3f69;
border-left: 6px solid #38bdf8;
border-radius: 16px;
padding: 1.2rem 1.35rem;
margin-bottom: 1rem;
}
.q-text {
font-size: 1.08rem;
font-weight: 700;
line-height: 1.62;
color: #ffffff !important;
margin: 0;
}

/* Cracker animation */
@keyframes crackerPop {
0% { transform: scale(0.75) rotate(-8deg); opacity: 0.3; }
50% { transform: scale(1.15) rotate(6deg); opacity: 1; }
100% { transform: scale(1) rotate(0deg); opacity: 1; }
}
@keyframes confettiFly {
0% { transform: translate(0, 0) rotate(0deg) scale(0.3); opacity: 0; }
12% { opacity: 1; }
70% { opacity: 1; }
100% { transform: translate(var(--tx), var(--ty)) rotate(var(--rot)) scale(1); opacity: 0; }
}
@keyframes crackerShake {
0% { transform: scale(0.3) rotate(-30deg); }
40% { transform: scale(1.5) rotate(18deg); }
70% { transform: scale(1.1) rotate(-10deg); }
100% { transform: scale(1) rotate(0deg); }
}
@keyframes boxGlow {
0% { box-shadow: 0 0 0 0 rgba(52, 211, 153, 0.75); }
100% { box-shadow: 0 0 0 26px rgba(52, 211, 153, 0); }
}
@keyframes textSlide {
0% { transform: translateX(-14px); opacity: 0; }
100% { transform: translateX(0); opacity: 1; }
}
.cracker-box {
position: relative;
overflow: visible;
display: flex;
align-items: center;
gap: 10px;
background: linear-gradient(120deg, #064e3b 0%, #065f46 60%, #0f766e 100%);
border: 1px solid #34d399;
border-radius: 14px;
padding: 0.85rem 1rem;
margin: 0.5rem 0 0.8rem 0;
color: #ecfdf5 !important;
font-weight: 700;
animation: boxGlow 0.9s ease-out;
}
.cracker-ico {
display: inline-flex;
animation: crackerShake 0.7s ease-out;
}
.cracker-txt {
animation: textSlide 0.5s ease-out 0.15s both;
}
.confetti {
position: absolute;
top: 50%;
width: 8px;
height: 13px;
border-radius: 2px;
opacity: 0;
pointer-events: none;
z-index: 50;
animation: confettiFly 1.2s cubic-bezier(0.15, 0.7, 0.3, 1) both;
animation-delay: var(--d);
}

/* Hide stale (greyed-out) alert boxes while the app is re-rendering */
div[data-stale="true"]:has([data-testid="stAlert"]),
div[data-stale="true"]:has(.log-card) {
display: none !important;
}

/* Explanation */
.exp-card {
display: flex;
gap: 10px;
align-items: flex-start;
background: #1f1a12;
border: 1px solid #92400e;
border-left: 5px solid #facc15;
border-radius: 14px;
padding: 0.95rem 1.1rem;
margin-top: 0.8rem;
color: #fef08a !important;
}

/* Colorful score blocks on finish page */
.result-grid {
display: grid;
grid-template-columns: repeat(2, 1fr);
gap: 0.75rem;
margin: 0.85rem 0 1.1rem 0;
}
.block-attempt {
background: linear-gradient(135deg, #1e40af 0%, #3b82f6 100%);
border: 1px solid #60a5fa;
border-radius: 16px;
padding: 1rem;
color: #ffffff !important;
}
.block-right {
background: linear-gradient(135deg, #065f46 0%, #10b981 100%);
border: 1px solid #34d399;
border-radius: 16px;
padding: 1rem;
color: #ffffff !important;
}
.block-wrong {
background: linear-gradient(135deg, #9f1239 0%, #f43f5e 100%);
border: 1px solid #fb7185;
border-radius: 16px;
padding: 1rem;
color: #ffffff !important;
}
.block-score {
background: linear-gradient(135deg, #92400e 0%, #f59e0b 100%);
border: 1px solid #fbbf24;
border-radius: 16px;
padding: 1rem;
color: #ffffff !important;
}
.block-head {
display: flex;
align-items: center;
gap: 7px;
font-size: 0.84rem;
font-weight: 800;
color: #ffffff !important;
}
.block-num {
font-size: 1.5rem;
font-weight: 800;
margin-top: 0.35rem;
color: #ffffff !important;
}

.improve-card {
background: #23121d;
border: 1px solid #9f1239;
border-left: 5px solid #fb7185;
border-radius: 16px;
padding: 1rem 1.15rem;
color: #ffe4e6 !important;
margin-bottom: 1rem;
}

.log-card {
background: #131d34;
border: 1px solid #2b3f69;
border-radius: 16px;
padding: 1rem 1.15rem;
margin-bottom: 0.75rem;
}

/* Buttons */
div.stButton > button {
border-radius: 12px !important;
font-weight: 700 !important;
border: 1px solid #324975 !important;
background-color: #18243d !important;
color: #f8fafc !important;
}
div.stButton > button:hover {
border-color: #60a5fa !important;
background-color: #213254 !important;
}
div.stButton > button[kind="primary"] {
background: linear-gradient(90deg, #2563eb 0%, #7c3aed 55%, #0d9488 100%) !important;
color: #ffffff !important;
border: none !important;
}
</style>
""")

# --- GEMINI CONFIGURATION ---
def initialize_gemini():
    """Initialize Gemini API with error handling"""
    try:
        api_key = st.secrets.get("GEMINI_KEY") or st.secrets.get("GEN_API_KEY")
        if not api_key:
            st.error("API key not found in secrets.toml. Please add GEMINI_KEY to your secrets.")
            return None

        genai.configure(api_key=api_key)
        return genai.GenerativeModel('gemini-3-flash-preview')
    except Exception as e:
        st.error(f"Failed to initialize Gemini API: {str(e)}")
        return None

model = initialize_gemini()

def get_psc_questions(topic: str, language: str, count: int, level: str) -> Optional[List[Dict]]:
    """Generate PSC questions using Gemini API with robust error handling"""
    if not model:
        st.error("Model not initialized. Please check your API key.")
        return None

    prompt = f"""
    Generate {count} highly accurate and realistic Kerala PSC exam questions (2021-2026 pattern) on '{topic}' for {level} level.
    Language: {language}.

    Important requirements:
    1. Questions and answers MUST be 100% factually correct and verified according to standard Kerala PSC syllabus.
    2. Options should be plausible distractors.
    3. Explanation should be concise and accurate in {language}.

    Format as a JSON list of dictionaries:
    [{{
      "question": "Question text here",
      "options": ["Option A", "Option B", "Option C", "Option D"],
      "answer": "Exact correct option string",
      "explanation": "Brief explanation in {language}"
    }}]

    Return ONLY valid JSON, no markdown formatting.
    """

    try:
        response = model.generate_content(
            prompt,
            generation_config=genai.types.GenerationConfig(
                temperature=0.2
            )
        )

        text = response.text.strip()

        if text.startswith("```"):
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:].strip()

        questions = json.loads(text)

        if not isinstance(questions, list) or len(questions) == 0:
            raise ValueError("Invalid questions format")

        for q in questions:
            if not all(key in q for key in ['question', 'options', 'answer', 'explanation']):
                raise ValueError("Missing required fields in question")
            if len(q['options']) != 4:
                raise ValueError("Each question must have exactly 4 options")
            if q['answer'] not in q['options']:
                raise ValueError("Answer must be one of the options")

        return questions

    except json.JSONDecodeError as e:
        st.error(f"Failed to parse API response: {str(e)}")
        st.code(response.text if 'response' in locals() else "No response")
        return None
    except Exception as e:
        st.error(f"Error generating questions: {str(e)}")
        return None

# --- SESSION STATE INITIALIZATION ---
if "page" not in st.session_state:
    st.session_state.page = "home"  # "home" | "quiz" | "score" | "logs"
if "questions" not in st.session_state:
    st.session_state.questions = None
if "current_idx" not in st.session_state:
    st.session_state.current_idx = 0
if "user_answers" not in st.session_state:
    st.session_state.user_answers = {}
if "attempt_count" not in st.session_state:
    st.session_state.attempt_count = 1
if "attempt_logs" not in st.session_state:
    st.session_state.attempt_logs = []
if "current_attempt_logged" not in st.session_state:
    st.session_state.current_attempt_logged = False
if "just_answered_idx" not in st.session_state:
    st.session_state.just_answered_idx = None
if "logs_loaded" not in st.session_state:
    st.session_state.logs_loaded = False
if "pending_start" not in st.session_state:
    st.session_state.pending_start = None
if "close_sidebar" not in st.session_state:
    st.session_state.close_sidebar = False

if "cfg_lang" not in st.session_state:
    st.session_state.cfg_lang = "English"
if "cfg_level" not in st.session_state:
    st.session_state.cfg_level = "10th/SSLC"
if "cfg_num_q" not in st.session_state:
    st.session_state.cfg_num_q = 10
if "cfg_topic" not in st.session_state:
    st.session_state.cfg_topic = "Kerala History"

# --- LOAD SAVED ATTEMPT LOG FROM THE BROWSER (once per fresh open) ---
LOG_STORAGE_KEY = "psc_attempt_logs_v1"
LOG_FIELDS = ("time", "attempt", "topic", "level", "lang", "right", "wrong", "total", "percent")

if HAS_JS_EVAL and not st.session_state.logs_loaded:
    # Returns None on the very first run; the browser answers a moment later and the app reruns by itself.
    _stored = streamlit_js_eval(
        js_expressions=f"localStorage.getItem('{LOG_STORAGE_KEY}') || '[]'",
        key="psc_load_logs",
    )
    if _stored is not None:
        try:
            _loaded = json.loads(_stored) if isinstance(_stored, str) else list(_stored)
        except Exception:
            _loaded = []
        _loaded = [x for x in _loaded if isinstance(x, dict) and all(f in x for f in LOG_FIELDS)]
        # anything already logged in this session stays on top (newest first)
        st.session_state.attempt_logs = st.session_state.attempt_logs + _loaded
        st.session_state.logs_loaded = True

LANG_OPTIONS = ["English", "Malayalam"]
LEVEL_OPTIONS = ["10th/SSLC", "Plus Two", "Degree", "Post Graduate"]

def calculate_summary() -> dict:
    questions = st.session_state.questions or []
    total = len(questions)
    user_answers = st.session_state.user_answers

    correct = 0
    wrong = 0
    wrong_items = []

    for idx, q in enumerate(questions):
        if idx in user_answers:
            if user_answers[idx] == q["answer"]:
                correct += 1
            else:
                wrong += 1
                wrong_items.append((idx + 1, q["question"], user_answers[idx], q["answer"]))

    unanswered = total - (correct + wrong)
    attempted = correct + wrong
    percent = (correct / total * 100) if total > 0 else 0.0

    return {
        "attempt": st.session_state.attempt_count,
        "total": total,
        "attempted": attempted,
        "correct": correct,
        "wrong": wrong,
        "unanswered": unanswered,
        "percent": percent,
        "wrong_items": wrong_items
    }

def topic_key(topic: str) -> str:
    """Normalise topic text so 'Kerala  History' and 'kerala history' count as the same topic"""
    return " ".join(str(topic).split()).casefold()

def get_topic_stats() -> list:
    """Topic-wise summary built from the attempt log (most recently written topic first)"""
    stats = {}
    for item in st.session_state.attempt_logs:  # logs are stored newest first
        key = topic_key(item["topic"])
        if key not in stats:
            stats[key] = {
                "topic": " ".join(str(item["topic"]).split()),
                "count": 0,
                "sum_pct": 0.0,
                "best_pct": 0.0,
                "best_right": 0,
                "best_total": item["total"],
                "last_time": item["time"],
                "last_right": item["right"],
                "last_total": item["total"],
                "last_pct": item["percent"],
            }
        d = stats[key]
        d["count"] += 1
        d["sum_pct"] += item["percent"]
        if item["percent"] >= d["best_pct"]:
            d["best_pct"] = item["percent"]
            d["best_right"] = item["right"]
            d["best_total"] = item["total"]
    result = list(stats.values())
    for d in result:
        d["avg_pct"] = d["sum_pct"] / d["count"]
    return result

def attempts_for_topic(topic: str) -> int:
    key = topic_key(topic)
    return sum(1 for x in st.session_state.attempt_logs if topic_key(x["topic"]) == key)

def go_to(page_name: str):
    """Navigate from the sidebar and collapse it so the new page is visible on mobile"""
    st.session_state.page = page_name
    st.session_state.close_sidebar = True
    st.rerun()

def reset_to_home():
    """Clear active quiz state and return to Home; new questions load only after selecting & starting"""
    st.session_state.questions = None
    st.session_state.current_idx = 0
    st.session_state.user_answers = {}
    st.session_state.just_answered_idx = None
    st.session_state.current_attempt_logged = False
    st.session_state.page = "home"

def start_quiz(topic_val: str, lang_val: str, count_val: int, level_val: str):
    st.session_state.cfg_topic = topic_val
    st.session_state.cfg_lang = lang_val
    st.session_state.cfg_num_q = count_val
    st.session_state.cfg_level = level_val

    with st.spinner("Generating questions..."):
        questions = get_psc_questions(topic_val, lang_val, count_val, level_val)
        if questions:
            # Attempt number continues from how many times this topic was already written
            st.session_state.attempt_count = attempts_for_topic(topic_val) + 1
            st.session_state.questions = questions
            st.session_state.current_idx = 0
            st.session_state.user_answers = {}
            st.session_state.just_answered_idx = None
            st.session_state.current_attempt_logged = False
            st.session_state.page = "quiz"
            st.session_state.close_sidebar = True
            st.rerun()

def close_sidebar_js():
    """Programmatically collapse the sidebar (Streamlit has no official API for this)"""
    components.html(
        """
        <script>
        (function () {
            var doc = window.parent.document;
            var selectors = [
                '[data-testid="stSidebarCollapseButton"] button',
                '[data-testid="stSidebarCollapseButton"]',
                'button[kind="header"][aria-label*="sidebar" i]',
                '[data-testid="baseButton-header"]'
            ];
            var tries = 0;
            var timer = setInterval(function () {
                tries++;
                var sidebar = doc.querySelector('[data-testid="stSidebar"]');
                var open = sidebar && sidebar.getAttribute('aria-expanded') !== 'false';
                if (!open || tries > 15) { clearInterval(timer); return; }
                for (var i = 0; i < selectors.length; i++) {
                    var el = doc.querySelector('[data-testid="stSidebar"] ' + selectors[i]) || doc.querySelector(selectors[i]);
                    if (el) { el.click(); clearInterval(timer); return; }
                }
            }, 150);
        })();
        </script>
        """,
        height=0,
    )

def enable_swipe_navigation():
    """Swipe left = Next question, swipe right = Previous question (touch screens).
    The listener is injected once into the main page and simply clicks the existing Next/Previous buttons."""
    components.html(
        """
        <script>
        (function () {
            var w = window.parent;
            var d = w.document;
            if (w.__pscSwipeInstalled) { return; }
            w.__pscSwipeInstalled = true;

            var code = `
            (function () {
                var sx = 0, sy = 0, st = 0, tracking = false;

                function findBtn(label) {
                    var btns = document.querySelectorAll('div.stButton button');
                    for (var i = 0; i < btns.length; i++) {
                        var b = btns[i];
                        if (b.closest('[data-testid="stSidebar"]')) continue;
                        if (b.innerText.trim() === label && !b.disabled) return b;
                    }
                    return null;
                }

                document.addEventListener('touchstart', function (e) {
                    if (e.touches.length !== 1) { tracking = false; return; }
                    var t = e.target;
                    // ignore swipes that start in the sidebar or on inputs/sliders
                    if (t.closest('[data-testid="stSidebar"], input, textarea, [role="slider"], [data-baseweb="select"]')) {
                        tracking = false; return;
                    }
                    sx = e.touches[0].clientX;
                    sy = e.touches[0].clientY;
                    st = Date.now();
                    tracking = true;
                }, { passive: true });

                document.addEventListener('touchend', function (e) {
                    if (!tracking) return;
                    tracking = false;
                    var t = e.changedTouches[0];
                    var dx = t.clientX - sx;
                    var dy = t.clientY - sy;
                    var dt = Date.now() - st;
                    // clear, mostly-horizontal, reasonably quick swipe
                    if (Math.abs(dx) < 70 || Math.abs(dx) < Math.abs(dy) * 1.6 || dt > 700) return;
                    var btn = dx < 0 ? findBtn('Next') : findBtn('Previous');
                    if (btn) btn.click();
                }, { passive: true });
            })();
            `;
            var s = d.createElement('script');
            s.textContent = code;
            d.head.appendChild(s);
        })();
        </script>
        """,
        height=0,
    )

def record_attempt_if_needed(summary: dict):
    if not st.session_state.current_attempt_logged:
        st.session_state.attempt_logs.insert(0, {
            "time": datetime.now().strftime("%d %b, %I:%M %p"),
            "attempt": summary["attempt"],
            "topic": st.session_state.cfg_topic,
            "level": st.session_state.cfg_level,
            "lang": st.session_state.cfg_lang,
            "right": summary["correct"],
            "wrong": summary["wrong"],
            "total": summary["total"],
            "percent": summary["percent"]
        })
        st.session_state.current_attempt_logged = True

def show_cracker():
    """Cracker pop + confetti burst from both sides of the box"""
    colors = ["#ef4444", "#10b981", "#f59e0b", "#3b82f6", "#ec4899", "#facc15", "#a78bfa", "#22d3ee"]
    pieces = []
    for i in range(30):
        angle = math.radians(random.uniform(200, 340))  # mostly upwards
        dist = random.uniform(70, 190)
        tx = int(math.cos(angle) * dist * 0.8)
        ty = int(math.sin(angle) * dist)
        rot = random.randint(-540, 540)
        delay = random.uniform(0, 0.25)
        color = colors[i % len(colors)]
        origin = "left:34px;" if i % 2 == 0 else "left:calc(100% - 34px);"
        if i % 2 == 1:
            tx = -tx  # mirror so right-side pieces fly inwards/outwards nicely
        pieces.append(
            f'<span class="confetti" style="{origin}background:{color};'
            f'--tx:{tx}px;--ty:{ty}px;--rot:{rot}deg;--d:{delay:.2f}s;"></span>'
        )
    confetti_html = "".join(pieces)
    render_html(f"""
    <div class="cracker-box">
    <span class="cracker-ico">{SVG_ICONS["cracker"]}</span>
    <span class="cracker-txt">ശരിയായ ഉത്തരം! മികച്ച പ്രകടനം</span>
    {confetti_html}
    </div>
    """)

# --- SIDEBAR (ALL SELECTION OPTIONS HERE) ---
with st.sidebar:
    st.markdown("### Navigation")

    if st.button("Home", use_container_width=True, key="sb_nav_home"):
        reset_to_home()
        go_to("home")

    if st.button(f"Attempt Log ({len(st.session_state.attempt_logs)})", use_container_width=True, key="sb_nav_logs"):
        go_to("logs")

    if st.session_state.questions and st.session_state.page != "score":
        if st.button("Active Quiz", use_container_width=True, key="sb_nav_quiz"):
            go_to("quiz")

    st.divider()
    st.markdown("### Exam Options")

    sb_lang = st.radio(
        "Language",
        LANG_OPTIONS,
        index=LANG_OPTIONS.index(st.session_state.cfg_lang),
        horizontal=True,
        key="sb_lang"
    )
    sb_level = st.selectbox(
        "Exam Level",
        LEVEL_OPTIONS,
        index=LEVEL_OPTIONS.index(st.session_state.cfg_level),
        key="sb_level"
    )
    sb_num_q = st.slider("Number of Questions", 5, 200, st.session_state.cfg_num_q, key="sb_num_q")
    sb_topic = st.text_input("Topic", value=st.session_state.cfg_topic, placeholder="e.g., Indian Constitution", key="sb_topic")

    if st.button("Start Exam", type="primary", use_container_width=True, key="sb_start_btn"):
        # Don't generate here (spinner would show inside the sidebar). Hand off to the main page.
        st.session_state.pending_start = (sb_topic, sb_lang, sb_num_q, sb_level)
        st.rerun()

    if st.session_state.questions:
        st.divider()
        total_q = len(st.session_state.questions)
        cols_per_row = 5
        for row_start in range(0, total_q, cols_per_row):
            cols = st.columns(cols_per_row)
            for i, col in enumerate(cols):
                q_num = row_start + i
                if q_num < total_q:
                    with col:
                        if q_num in st.session_state.user_answers:
                            lbl = f"✓{q_num + 1}" if st.session_state.user_answers[q_num] == st.session_state.questions[q_num]["answer"] else f"✗{q_num + 1}"
                        else:
                            lbl = f"{q_num + 1}"
                        if q_num == st.session_state.current_idx and st.session_state.page == "quiz":
                            lbl = f"•{q_num + 1}"
                        if st.button(lbl, key=f"sb_q_{q_num}", use_container_width=True):
                            st.session_state.current_idx = q_num
                            go_to("quiz")

# --- TOP HEADER ---
_in_exam = st.session_state.page in ("quiz", "score") and bool(st.session_state.questions)
_attempt_tag = f'<span class="tag">Attempt #{st.session_state.attempt_count}</span>' if _in_exam else ""
render_html(f"""
<div class="top-app-bar">
<div class="top-app-left">
{SVG_ICONS["brand"]}
<div>
<p class="top-app-sub">Hello, Aspirant</p>
<h2 class="top-app-title">Kerala PSC Quiz Studio</h2>
</div>
</div>
{_attempt_tag}
</div>
""")

# --- PENDING EXAM START (spinner shows in the MAIN page) ---
if st.session_state.pending_start:
    _topic, _lang, _count, _level = st.session_state.pending_start
    st.session_state.pending_start = None
    close_sidebar_js()  # collapse sidebar immediately, before the slow generation starts
    # While generating, hide the old page content (score page, old question...) so only the spinner shows.
    # This <style> exists only in this run, so everything returns to normal after the rerun.
    render_html("""
    <style>
    .block-container div[data-stale="true"] { display: none !important; }
    </style>
    """)
    start_quiz(_topic, _lang, _count, _level)  # reruns on success

# --- AUTO-CLOSE SIDEBAR AFTER EXAM STARTS ---
if st.session_state.close_sidebar:
    st.session_state.close_sidebar = False
    close_sidebar_js()

# --- PAGE 1: ATTEMPT LOG PAGE ---
if st.session_state.page == "logs":
    st.markdown("### Attempt Log")

    logs = st.session_state.attempt_logs
    if not logs:
        render_html("""
        <div class="log-card">
        <p style="margin:0; color:#e2e8f0;">ഇതുവരെ ഒരു exam-ഉം പൂർത്തിയാക്കിയിട്ടില്ല. Quiz എഴുതി Finish ചെയ്യുമ്പോൾ വിവരങ്ങൾ ഇവിടെ കാണാം.</p>
        </div>
        """)
    else:
        avg_pct = sum(x["percent"] for x in logs) / len(logs)
        m1, m2, m3 = st.columns(3)
        with m1:
            st.metric("Total Exams Written", f"{len(logs)}")
        with m2:
            st.metric("Average Score", f"{avg_pct:.1f}%")
        with m3:
            st.metric("Latest Score", f"{logs[0]['right']}/{logs[0]['total']}")

        # ---- Topic-wise summary ----
        st.markdown("### Topic-wise Summary")
        for d in get_topic_stats():
            t_name = html.escape(d["topic"])
            render_html(f"""
            <div class="log-card" style="border-left:5px solid #38bdf8;">
            <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:6px;">
            <strong style="font-size:1.02rem; color:#ffffff;">{t_name}</strong>
            <span class="tag">{d['count']} തവണ എഴുതി</span>
            </div>
            <div style="display:flex; flex-wrap:wrap; gap:8px; margin-top:0.6rem;">
            <span class="tag tag-green">Best: {d['best_right']}/{d['best_total']} ({d['best_pct']:.1f}%)</span>
            <span class="tag">Average: {d['avg_pct']:.1f}%</span>
            <span class="tag">Last: {d['last_right']}/{d['last_total']} ({d['last_pct']:.1f}%)</span>
            </div>
            <div style="height:7px; background:#0b1222; border-radius:99px; margin-top:0.7rem; overflow:hidden;">
            <div style="height:100%; width:{min(d['avg_pct'], 100):.0f}%; background:linear-gradient(90deg,#2563eb,#10b981);"></div>
            </div>
            <p style="margin:0.5rem 0 0 0; font-size:0.8rem; color:#94a3b8;">Last written: {d['last_time']}</p>
            </div>
            """)

        # ---- Full history ----
        st.markdown("### All Attempts")
        for item in logs:
            i_topic = html.escape(str(item['topic']))
            render_html(f"""
            <div class="log-card">
            <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:6px;">
            <strong style="font-size:1rem; color:#ffffff;">{i_topic}</strong>
            <span class="tag">Attempt #{item['attempt']}</span>
            </div>
            <p style="margin:0.35rem 0 0.55rem 0; font-size:0.84rem; color:#cbd5e1;">
            Level: {item['level']} • Language: {item['lang']} • {item['time']}
            </p>
            <div style="display:flex; flex-wrap:wrap; gap:8px;">
            <span class="tag tag-green">Right: {item['right']}</span>
            <span class="tag tag-red">Wrong: {item['wrong']}</span>
            <span class="tag">Marks: {item['right']}/{item['total']} ({item['percent']:.1f}%)</span>
            </div>
            </div>
            """)

    if st.button("Back to Home", type="primary", use_container_width=True, key="logs_back_home"):
        reset_to_home()
        st.rerun()

# --- PAGE 2: SCORE / FINISH PAGE ONLY ---
elif st.session_state.page == "score" and st.session_state.questions:
    s = calculate_summary()
    record_attempt_if_needed(s)

    st.markdown("### Exam Finished — Score Summary")
    render_html(f"""
    <div class="meta-row">
    <span class="tag">{st.session_state.cfg_topic}</span>
    <span class="tag">{st.session_state.cfg_level}</span>
    <span class="tag">{st.session_state.cfg_lang}</span>
    </div>
    <div class="result-grid">
    <div class="block-attempt">
    <div class="block-head">{SVG_ICONS["attempt_sym"]}<span>ATTEMPT NUMBER</span></div>
    <div class="block-num">#{s['attempt']}</div>
    </div>
    <div class="block-score">
    <div class="block-head">{SVG_ICONS["marks_sym"]}<span>TOTAL MARKS</span></div>
    <div class="block-num">{s['correct']} / {s['total']} ({s['percent']:.1f}%)</div>
    </div>
    <div class="block-right">
    <div class="block-head">{SVG_ICONS["right_sym"]}<span>RIGHT ANSWERS</span></div>
    <div class="block-num">{s['correct']}</div>
    </div>
    <div class="block-wrong">
    <div class="block-head">{SVG_ICONS["wrong_sym"]}<span>WRONG ANSWERS</span></div>
    <div class="block-num">{s['wrong']}</div>
    </div>
    </div>
    """)

    if s["unanswered"] > 0:
        st.info(f"Unanswered Questions: {s['unanswered']}")

    if s["wrong_items"] or s["unanswered"] > 0:
        items_html = ""
        for q_no, q_txt, u_ans, c_ans in s["wrong_items"]:
            items_html += (
                f"<div style='margin-bottom:0.65rem; padding-bottom:0.5rem; border-bottom:1px solid #6b142d;'>"
                f"<strong>Q{q_no}:</strong> {q_txt}<br>"
                f"<span style='color:#fda4af;'>Your Answer:</span> {u_ans} &nbsp;|&nbsp; "
                f"<span style='color:#6ee7b7;'>Right Answer:</span> <strong>{c_ans}</strong>"
                f"</div>"
            )
        unans_html = ""
        if s["unanswered"] > 0:
            unans_html = f"<p style='margin:0.4rem 0 0 0;'>Unanswered: <strong>{s['unanswered']}</strong> ചോദ്യങ്ങൾ കൂടി പൂർത്തിയാക്കാൻ ശ്രദ്ധിക്കുക.</p>"

        render_html(f"""
        <div class="improve-card">
        <h4 style="margin:0 0 0.5rem 0; color:#fda4af;">Improve ചെയ്യേണ്ട Areas</h4>
        {items_html}
        {unans_html}
        </div>
        """)
    else:
        st.success("എല്ലാ ചോദ്യങ്ങളും ശരിയായി ഉത്തരം നൽകി! ഇപ്പോൾ Improve ചെയ്യേണ്ട ഭാഗങ്ങൾ ഒന്നും ഇല്ല.")

    b1, b2 = st.columns(2)
    with b1:
        if st.button("Back to Home", type="primary", use_container_width=True, key="score_back_home"):
            reset_to_home()
            st.rerun()
    with b2:
        if st.button("Attempt Again", use_container_width=True, key="score_next_attempt"):
            st.session_state.attempt_count += 1
            st.session_state.user_answers = {}
            st.session_state.current_idx = 0
            st.session_state.just_answered_idx = None
            st.session_state.current_attempt_logged = False
            st.session_state.page = "quiz"
            st.rerun()

# --- PAGE 3: ACTIVE QUIZ PAGE ---
elif st.session_state.page == "quiz" and st.session_state.questions:
    questions = st.session_state.questions
    idx = st.session_state.current_idx
    q = questions[idx]
    s = calculate_summary()

    already_answered = idx in st.session_state.user_answers
    selected = st.session_state.user_answers.get(idx)

    status_tag = ""
    if already_answered:
        status_tag = '<span class="tag tag-green">Right</span>' if selected == q["answer"] else '<span class="tag tag-red">Wrong</span>'

    render_html(f"""
    <div class="meta-row">
    <span class="tag">Q {idx + 1} / {len(questions)}</span>
    <span class="tag">{st.session_state.cfg_topic}</span>
    <span class="tag">{st.session_state.cfg_level}</span>
    <span class="tag">Attempted: {s['attempted']}/{len(questions)}</span>
    {status_tag}
    </div>
    <div class="q-box">
    <p class="q-text">{q['question']}</p>
    </div>
    """)

    if already_answered and selected == q["answer"] and st.session_state.just_answered_idx == idx:
        show_cracker()

    for i, option in enumerate(q["options"]):
        prefix = f"{chr(65 + i)})"
        if already_answered:
            if option == q["answer"]:
                render_html(f"<div class='opt-right'>{prefix} {option} &nbsp;—&nbsp; Right Answer ✓</div>")
            elif option == selected:
                render_html(f"<div class='opt-wrong'>{prefix} {option} &nbsp;—&nbsp; Your Answer ✗</div>")
            else:
                render_html(f"<div class='opt-neutral'>{prefix} {option}</div>")
        else:
            b_type = "primary" if selected == option else "secondary"
            if st.button(f"{prefix}  {option}", key=f"opt_{idx}_{i}", use_container_width=True, type=b_type):
                st.session_state.user_answers[idx] = option
                st.session_state.just_answered_idx = idx if option == q["answer"] else None
                st.rerun()

    if already_answered:
        render_html(f"""
        <div class="exp-card">
        <div style="margin-top:2px;">{SVG_ICONS["bulb"]}</div>
        <div><strong>Explanation:</strong> {q.get('explanation', 'No explanation available.')}</div>
        </div>
        """)

    enable_swipe_navigation()

    st.divider()
    n1, n2, n3 = st.columns([1.2, 1, 1.2])
    with n1:
        if st.button("Previous", disabled=idx == 0, use_container_width=True, key=f"p_{idx}"):
            st.session_state.current_idx -= 1
            st.session_state.just_answered_idx = None
            st.rerun()
    with n2:
        render_html(f"<div style='text-align:center; padding-top:0.45rem; font-weight:700; color:#93c5fd;'>{idx + 1} / {len(questions)}</div>")
    with n3:
        if idx < len(questions) - 1:
            if st.button("Next", use_container_width=True, key=f"nx_{idx}"):
                st.session_state.current_idx += 1
                st.session_state.just_answered_idx = None
                st.rerun()
        else:
            if st.button("Finish Exam", type="primary", use_container_width=True, key=f"fin_{idx}"):
                st.session_state.just_answered_idx = None
                st.session_state.page = "score"
                st.rerun()

# --- PAGE 4: HOME PAGE ---
else:
    logs = st.session_state.attempt_logs
    avg_score = f"{(sum(x['percent'] for x in logs)/len(logs)):.1f}%" if logs else "0.0%"
    topic_stats = get_topic_stats()
    # Focus topic = topic with the lowest average score (only if it is below 100%)
    weak_area = "None"
    if topic_stats:
        _weakest = min(topic_stats, key=lambda d: d["avg_pct"])
        if _weakest["avg_pct"] < 100:
            weak_area = html.escape(_weakest["topic"])

    render_html(f"""
    <div class="prep-panel">
    <div class="prep-title">Your Preparation Status</div>
    <div class="mini-stat-grid">
    <div class="mini-stat-card">
    <div class="mini-stat-icon">{SVG_ICONS["trophy"]}</div>
    <div class="mini-stat-val">{len(logs)}</div>
    <div class="mini-stat-lbl">Exams Written</div>
    </div>
    <div class="mini-stat-card">
    <div class="mini-stat-icon">{SVG_ICONS["target_score"]}</div>
    <div class="mini-stat-val">{avg_score}</div>
    <div class="mini-stat-lbl">Average Score</div>
    </div>
    <div class="mini-stat-card">
    <div class="mini-stat-icon">{SVG_ICONS["focus_book"]}</div>
    <div class="mini-stat-val" style="font-size:0.95rem;">{weak_area}</div>
    <div class="mini-stat-lbl">Focus Topic</div>
    </div>
    </div>
    </div>
    """)

    render_html("""
    <div class="log-card" style="border-left:5px solid #38bdf8;">
    <p style="margin:0; color:#e2e8f0; line-height:1.7;">മുകളിൽ ഇടതുവശത്തെ <strong>»</strong> ബട്ടൺ അമർത്തി സൈഡ്‌ബാർ തുറന്ന് Language, Exam Level, Number of Questions, Topic എന്നിവ സെറ്റ് ചെയ്ത് <strong>Start Exam</strong> ക്ലിക്ക് ചെയ്യുക.</p>
    </div>
    """)

# --- SAVE ATTEMPT LOG TO THE BROWSER (runs only when the log changes) ---
if HAS_JS_EVAL and st.session_state.logs_loaded:
    _payload = json.dumps(st.session_state.attempt_logs[:500], ensure_ascii=False)
    streamlit_js_eval(
        js_expressions=f"localStorage.setItem('{LOG_STORAGE_KEY}', {json.dumps(_payload)})",
        want_output=False,
        key=f"psc_save_logs_{len(st.session_state.attempt_logs)}",
    )
