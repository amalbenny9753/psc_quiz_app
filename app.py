import streamlit as st
import google.generativeai as genai
import json
import textwrap
from datetime import datetime
from typing import List, Dict, Optional

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

# --- RICH COLORFUL SVG ICONS (TRUE TURN INSPIRED) ---
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

# --- DARK COLORFUL THEME + CLEAR LABEL VISIBILITY ---
render_html("""
<style>
footer {visibility: hidden;}
[data-testid="stToolbar"] {display: none !important;}
[data-testid="stDecoration"] {display: none !important;}
[data-testid="stStatusWidget"] {display: none !important;}
.stDeployButton {display: none !important;}
#MainMenu {visibility: hidden;}

header[data-testid="stHeader"] {
background-color: transparent !important;
visibility: visible !important;
}
[data-testid="stSidebar"] {
background-color: #0e1525 !important;
border-right: 1px solid #24324d !important;
visibility: visible !important;
}
[data-testid="stSidebarCollapsedControl"] {
visibility: visible !important;
display: flex !important;
z-index: 999999 !important;
}

.stApp {
background-color: #080c14;
color: #f8fafc;
}

.block-container {
max-width: 960px;
padding-top: 1.15rem;
padding-bottom: 3rem;
}

/* Make ALL Streamlit widget labels & text crisp and visible on dark background */
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

/* Setup container card */
.setup-card {
background: #11192c;
border: 1px solid #263659;
border-radius: 20px;
padding: 1.1rem 1.15rem;
margin-bottom: 1rem;
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
@keyframes sparkBurst {
0% { transform: translate(0, 0) scale(0.4); opacity: 1; }
100% { transform: translate(var(--tx), var(--ty)) scale(1.15); opacity: 0; }
}
.cracker-box {
position: relative;
overflow: hidden;
display: flex;
align-items: center;
gap: 10px;
background: linear-gradient(120deg, #064e3b 0%, #065f46 60%, #0f766e 100%);
border: 1px solid #34d399;
border-radius: 14px;
padding: 0.75rem 1rem;
margin: 0.5rem 0 0.8rem 0;
color: #ecfdf5 !important;
font-weight: 700;
}
.cracker-ico {
display: inline-flex;
animation: crackerPop 0.45s ease-out;
}
.spark {
position: absolute;
right: 26px;
top: 50%;
width: 8px;
height: 8px;
border-radius: 50%;
animation: sparkBurst 0.65s ease-out forwards;
pointer-events: none;
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

if "cfg_lang" not in st.session_state:
    st.session_state.cfg_lang = "English"
if "cfg_level" not in st.session_state:
    st.session_state.cfg_level = "10th/SSLC"
if "cfg_num_q" not in st.session_state:
    st.session_state.cfg_num_q = 10
if "cfg_topic" not in st.session_state:
    st.session_state.cfg_topic = "Kerala History"

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
            st.session_state.questions = questions
            st.session_state.current_idx = 0
            st.session_state.user_answers = {}
            st.session_state.just_answered_idx = None
            st.session_state.current_attempt_logged = False
            st.session_state.page = "quiz"
            st.rerun()

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
    render_html(f"""
    <div class="cracker-box">
    <span class="cracker-ico">{SVG_ICONS["cracker"]}</span>
    <span>ശരിയായ ഉത്തരം! മികച്ച പ്രകടനം</span>
    <span class="spark" style="background:#ef4444; --tx:-24px; --ty:-22px;"></span>
    <span class="spark" style="background:#10b981; --tx:24px; --ty:-20px;"></span>
    <span class="spark" style="background:#f59e0b; --tx:-20px; --ty:20px;"></span>
    <span class="spark" style="background:#3b82f6; --tx:22px; --ty:22px;"></span>
    <span class="spark" style="background:#ec4899; --tx:0px; --ty:-28px;"></span>
    </div>
    """)

# --- SIDEBAR ---
with st.sidebar:
    st.markdown("### Navigation")

    if st.button("Home / Quiz Setup", use_container_width=True, key="sb_nav_home"):
        reset_to_home()
        st.rerun()

    if st.button(f"Attempt Log ({len(st.session_state.attempt_logs)})", use_container_width=True, key="sb_nav_logs"):
        st.session_state.page = "logs"
        st.rerun()

    if st.session_state.questions and st.session_state.page != "score":
        if st.button("Active Quiz", use_container_width=True, key="sb_nav_quiz"):
            st.session_state.page = "quiz"
            st.rerun()

    st.divider()
    st.markdown("### Quiz Settings")

    sb_lang = st.radio(
        "Language",
        ["English", "Malayalam"],
        index=["English", "Malayalam"].index(st.session_state.cfg_lang),
        horizontal=True,
        key="sb_lang"
    )
    sb_level = st.selectbox(
        "Exam Level",
        ["10th/SSLC", "Plus Two", "Degree", "Post Graduate"],
        index=["10th/SSLC", "Plus Two", "Degree", "Post Graduate"].index(st.session_state.cfg_level),
        key="sb_level"
    )
    sb_num_q = st.slider("Number of Questions", 5, 200, st.session_state.cfg_num_q, key="sb_num_q")
    sb_topic = st.text_input("Topic", value=st.session_state.cfg_topic, placeholder="e.g., Indian Constitution", key="sb_topic")

    if st.button("Start Exam", type="primary", use_container_width=True, key="sb_start_btn"):
        start_quiz(sb_topic, sb_lang, sb_num_q, sb_level)

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
                            st.session_state.page = "quiz"
                            st.rerun()

# --- TOP HEADER ---
render_html(f"""
<div class="top-app-bar">
<div class="top-app-left">
{SVG_ICONS["brand"]}
<div>
<p class="top-app-sub">Hello, Aspirant</p>
<h2 class="top-app-title">Kerala PSC Quiz Studio</h2>
</div>
</div>
<span class="tag">Attempt #{st.session_state.attempt_count}</span>
</div>
""")

top_c1, top_c2, top_c3 = st.columns(3)
with top_c1:
    if st.button("Home", use_container_width=True, key="top_home"):
        reset_to_home()
        st.rerun()
with top_c2:
    if st.button(f"Attempt Log ({len(st.session_state.attempt_logs)})", use_container_width=True, key="top_logs"):
        st.session_state.page = "logs"
        st.rerun()
with top_c3:
    if st.button("Quiz Setup", use_container_width=True, key="top_setup"):
        st.session_state.page = "home"
        st.rerun()

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

        st.markdown("")
        for item in logs:
            render_html(f"""
            <div class="log-card">
            <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:6px;">
            <strong style="font-size:1rem; color:#ffffff;">{item['topic']}</strong>
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
        if st.button("Start Next Attempt", use_container_width=True, key="score_next_attempt"):
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
                st.success(f"**{prefix} {option}** — Right Answer")
            elif option == selected:
                st.error(f"**{prefix} {option}** — Your Answer")
            else:
                render_html(f"<div style='padding:0.5rem 0.8rem; color:#cbd5e1; background:#111827; border-radius:10px; margin-bottom:0.35rem;'>{prefix} {option}</div>")
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
    weak_area = logs[0]["topic"] if (logs and logs[0]["wrong"] > 0) else "None"

    render_html(f"""
    <div class="prep-panel">
    <div class="prep-title">Your Preparation Status</div>
    <div class="mini-stat-grid">
    <div class="mini-stat-card">
    <div class="mini-stat-icon">{SVG_ICONS["trophy"]}</div>
    <div class="mini-stat-val">#{st.session_state.attempt_count}</div>
    <div class="mini-stat-lbl">Current Attempt</div>
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
    <div class="cat-grid">
    <div class="cat-tile-blue">
    <div class="cat-icon">{SVG_ICONS["history_icon"]}</div>
    <div class="cat-name">Kerala History</div>
    </div>
    <div class="cat-tile-green">
    <div class="cat-icon">{SVG_ICONS["const_icon"]}</div>
    <div class="cat-name">Constitution</div>
    </div>
    <div class="cat-tile-amber">
    <div class="cat-icon">{SVG_ICONS["ca_icon"]}</div>
    <div class="cat-name">Current Affairs</div>
    </div>
    </div>
    """)

    render_html('<div class="setup-card"><h3 style="margin:0 0 0.75rem 0; color:#ffffff;">Select & Start Exam</h3></div>')
    h_col1, h_col2 = st.columns(2)
    with h_col1:
        h_lang = st.radio(
            "Language",
            ["English", "Malayalam"],
            index=["English", "Malayalam"].index(st.session_state.cfg_lang),
            horizontal=True,
            key="h_lang"
        )
        h_level = st.selectbox(
            "Exam Level",
            ["10th/SSLC", "Plus Two", "Degree", "Post Graduate"],
            index=["10th/SSLC", "Plus Two", "Degree", "Post Graduate"].index(st.session_state.cfg_level),
            key="h_level"
        )
    with h_col2:
        h_num_q = st.slider("Number of Questions", 5, 200, st.session_state.cfg_num_q, key="h_num_q")
        h_topic = st.text_input("Topic", value=st.session_state.cfg_topic, placeholder="e.g., Indian Constitution", key="h_topic")

    if st.button("Start Exam", type="primary", use_container_width=True, key="h_start_btn"):
        start_quiz(h_topic, h_lang, h_num_q, h_level)
