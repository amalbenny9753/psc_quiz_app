import streamlit as st
import google.generativeai as genai
import json
import textwrap
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

# --- CUSTOM SVG ICON LIBRARY ---
SVG_ICONS = {
    "brand": (
        '<svg width="34" height="34" viewBox="0 0 36 36" fill="none" xmlns="http://www.w3.org/2000/svg">'
        '<rect width="36" height="36" rx="10" fill="rgba(255,255,255,0.2)"/>'
        '<path d="M9 11.5C9 10.1193 10.1193 9 11.5 9H17V27H11.5C10.1193 27 9 25.8807 9 24.5V11.5Z" fill="#FDE047"/>'
        '<path d="M27 11.5C27 10.1193 25.8807 9 24.5 9H19V27H24.5C25.8807 27 27 25.8807 27 24.5V11.5Z" fill="#5EEAD4"/>'
        '<circle cx="18" cy="18" r="3.2" fill="#FB7185"/>'
        '</svg>'
    ),
    "gear": (
        '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#4F46E5" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">'
        '<circle cx="12" cy="12" r="3.2"/>'
        '<path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 1 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 1 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 1 1-2.83-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 1 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 1 1 2.83-2.83l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 1 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 1 1 2.83 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 1 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z"/>'
        '</svg>'
    ),
    "chart": (
        '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#0D9488" stroke-width="2.3" stroke-linecap="round" stroke-linejoin="round">'
        '<rect x="3" y="12" width="4" height="8" rx="1.5" fill="#99F6E4"/>'
        '<rect x="10" y="7" width="4" height="13" rx="1.5" fill="#5EEAD4"/>'
        '<rect x="17" y="4" width="4" height="16" rx="1.5" fill="#2DD4BF"/>'
        '</svg>'
    ),
    "grid": (
        '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#E11D48" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">'
        '<rect x="3" y="3" width="7" height="7" rx="1.5" fill="#FFE4E6"/>'
        '<rect x="14" y="3" width="7" height="7" rx="1.5" fill="#E0E7FF"/>'
        '<rect x="3" y="14" width="7" height="7" rx="1.5" fill="#FEF3C7"/>'
        '<rect x="14" y="14" width="7" height="7" rx="1.5" fill="#CCFBF1"/>'
        '</svg>'
    ),
    "bulb": (
        '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#D97706" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">'
        '<path d="M9 18h6" fill="#FEF08A"/>'
        '<path d="M10 22h4"/>'
        '<path d="M15.09 14c.18-.98.65-1.74 1.41-2.5A4.65 4.65 0 0 0 18 8 6 6 0 0 0 6 8c0 1 .23 2.23 1.5 3.5A4.61 4.61 0 0 1 8.91 14" fill="#FEF9C3"/>'
        '</svg>'
    ),
    "check": (
        '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#15803D" stroke-width="2.8" stroke-linecap="round" stroke-linejoin="round">'
        '<circle cx="12" cy="12" r="10" fill="#DCFCE7"/>'
        '<polyline points="8 12.5 10.8 15.3 16.2 9.5"/>'
        '</svg>'
    ),
    "cross": (
        '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#B91C1C" stroke-width="2.8" stroke-linecap="round" stroke-linejoin="round">'
        '<circle cx="12" cy="12" r="10" fill="#FEE2E2"/>'
        '<line x1="9" y1="9" x2="15" y2="15"/>'
        '<line x1="15" y1="9" x2="9" y2="15"/>'
        '</svg>'
    ),
    "bolt": (
        '<svg width="22" height="22" viewBox="0 0 24 24" fill="#F59E0B" stroke="#B45309" stroke-width="1.8" stroke-linejoin="round">'
        '<polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/>'
        '</svg>'
    ),
    "spark": (
        '<svg width="22" height="22" viewBox="0 0 24 24" fill="#10B981" stroke="#047857" stroke-width="1.8" stroke-linejoin="round">'
        '<path d="M12 2L14.8 9.2L22 12L14.8 14.8L12 22L9.2 14.8L2 12L9.2 9.2L12 2Z"/>'
        '</svg>'
    ),
    "compass": (
        '<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#4F46E5" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">'
        '<circle cx="12" cy="12" r="9.5" fill="#E0E7FF"/>'
        '<polygon points="16.24 7.76 14.12 14.12 7.76 16.24 9.88 9.88 16.24 7.76" fill="#6366F1"/>'
        '</svg>'
    ),
    "cracker": (
        '<svg width="26" height="26" viewBox="0 0 32 32" fill="none" xmlns="http://www.w3.org/2000/svg">'
        '<path d="M6 26L14 12L20 18L6 26Z" fill="#F59E0B" stroke="#B45309" stroke-width="1.8" stroke-linejoin="round"/>'
        '<path d="M11 17L15 21" stroke="#FEF08A" stroke-width="2" stroke-linecap="round"/>'
        '<circle cx="22" cy="8" r="2.2" fill="#EC4899"/>'
        '<circle cx="26" cy="13" r="2" fill="#10B981"/>'
        '<circle cx="18" cy="6" r="1.8" fill="#3B82F6"/>'
        '<path d="M23 4V6.5M25 18H27.5" stroke="#F97316" stroke-width="2" stroke-linecap="round"/>'
        '</svg>'
    )
}

def icon_heading(icon_key: str, title: str, color: str = "#0F172A", size: str = "1.05rem"):
    render_html(f"""
    <div style="display:flex; align-items:center; gap:8px; margin:0.2rem 0 0.6rem 0;">
    {SVG_ICONS[icon_key]}
    <span style="font-size:{size}; font-weight:700; color:{color};">{title}</span>
    </div>
    """)

# --- STYLING + RIGHT ANSWER CRACKER ANIMATION ---
render_html("""
<style>
footer {visibility: hidden;}
[data-testid="stToolbar"] {display: none !important;}
[data-testid="stDecoration"] {display: none !important;}
[data-testid="stStatusWidget"] {display: none !important;}
.stDeployButton {display: none !important;}
#MainMenu {visibility: hidden;}

/* Keep header & sidebar toggle visible and usable */
header[data-testid="stHeader"] {
background-color: transparent !important;
visibility: visible !important;
}
[data-testid="stSidebar"] {
visibility: visible !important;
}
[data-testid="stSidebarCollapsedControl"] {
visibility: visible !important;
display: flex !important;
z-index: 999999 !important;
}

.stApp {
background: linear-gradient(180deg, #f0f9ff 0%, #fdf4ff 48%, #f0fdfa 100%);
}

.block-container {
max-width: 940px;
padding-top: 1.4rem;
padding-bottom: 3rem;
}

.quiz-hero {
background: linear-gradient(120deg, #4338ca 0%, #0ea5e9 52%, #10b981 100%);
color: #ffffff;
padding: 1.45rem 1.7rem;
border-radius: 20px;
margin-bottom: 1.25rem;
box-shadow: 0 12px 28px rgba(67, 56, 202, 0.22);
border: 1px solid rgba(255, 255, 255, 0.35);
}
.quiz-hero-row {
display: flex;
align-items: center;
gap: 14px;
}
.quiz-hero h1 {
margin: 0;
font-size: 1.65rem;
font-weight: 800;
color: #ffffff;
letter-spacing: -0.01em;
}
.quiz-hero p {
margin: 0.25rem 0 0 0;
font-size: 0.92rem;
color: #f0fdfa;
font-weight: 500;
}

.status-strip {
display: flex;
flex-wrap: wrap;
gap: 0.55rem;
align-items: center;
justify-content: space-between;
background: #ffffff;
border: 1.5px solid #e0e7ff;
border-radius: 14px;
padding: 0.8rem 1rem;
margin-bottom: 1rem;
box-shadow: 0 4px 12px rgba(79, 70, 229, 0.06);
}
.pill {
display: inline-flex;
align-items: center;
gap: 5px;
padding: 0.28rem 0.75rem;
border-radius: 999px;
font-size: 0.82rem;
font-weight: 700;
background-color: #eef2ff;
color: #4338ca;
border: 1px solid #c7d2fe;
}
.pill-teal {
background-color: #ccfbf1;
color: #0f766e;
border-color: #99f6e4;
}
.pill-amber {
background-color: #fef3c7;
color: #b45309;
border-color: #fde68a;
}
.pill-green {
background-color: #dcfce7;
color: #15803d;
border-color: #86efac;
}
.pill-red {
background-color: #ffe4e6;
color: #be123c;
border-color: #fda4af;
}

@keyframes popSlideIn {
from {
opacity: 0.35;
transform: translate3d(0, 8px, 0);
}
to {
opacity: 1;
transform: translate3d(0, 0, 0);
}
}

.question-card {
background: linear-gradient(135deg, #ffffff 0%, #f8faff 100%);
border: 1.5px solid #c7d2fe;
border-left: 7px solid #6366f1;
border-radius: 18px;
padding: 1.4rem 1.55rem;
margin-bottom: 1.1rem;
box-shadow: 0 8px 20px rgba(99, 102, 241, 0.09);
animation: popSlideIn 0.2s ease-out;
}
.question-text {
font-size: 1.14rem;
font-weight: 700;
line-height: 1.62;
color: #1e1b4b;
margin: 0;
}

/* Telegram-poll style right-answer cracker burst */
@keyframes crackerPop {
0% { transform: scale(0.75) rotate(-8deg); opacity: 0.3; }
50% { transform: scale(1.12) rotate(6deg); opacity: 1; }
100% { transform: scale(1) rotate(0deg); opacity: 1; }
}
@keyframes sparkBurst {
0% { transform: translate(0, 0) scale(0.4); opacity: 1; }
100% { transform: translate(var(--tx), var(--ty)) scale(1.15); opacity: 0; }
}
.cracker-banner {
position: relative;
overflow: hidden;
display: flex;
align-items: center;
gap: 10px;
background: linear-gradient(120deg, #dcfce7 0%, #d1fae5 55%, #fef9c3 100%);
border: 1.5px solid #34d399;
border-radius: 14px;
padding: 0.75rem 1rem;
margin: 0.5rem 0 0.75rem 0;
color: #065f46;
font-weight: 700;
box-shadow: 0 6px 16px rgba(16, 185, 129, 0.16);
}
.cracker-icon-anim {
animation: crackerPop 0.45s ease-out;
display: inline-flex;
align-items: center;
}
.spark-dot {
position: absolute;
right: 28px;
top: 50%;
width: 8px;
height: 8px;
border-radius: 50%;
animation: sparkBurst 0.65s ease-out forwards;
pointer-events: none;
}

div.stButton > button {
text-align: left !important;
justify-content: flex-start !important;
border-radius: 12px !important;
padding: 0.7rem 1.05rem !important;
font-weight: 600 !important;
border: 1.5px solid #cbd5e1 !important;
background-color: #ffffff !important;
color: #0f172a !important;
transition: all 0.14s ease !important;
}
div.stButton > button:hover {
border-color: #6366f1 !important;
background-color: #eef2ff !important;
transform: translateY(-1px);
}
div.stButton > button[kind="primary"] {
background: linear-gradient(90deg, #4f46e5 0%, #0ea5e9 100%) !important;
color: #ffffff !important;
border: none !important;
box-shadow: 0 6px 14px rgba(79, 70, 229, 0.25) !important;
}
div.stButton > button[kind="primary"]:hover {
filter: brightness(1.05);
}

.exp-box {
display: flex;
align-items: flex-start;
gap: 10px;
background: linear-gradient(135deg, #fffbeb 0%, #fef3c7 100%);
border: 1.5px solid #fcd34d;
border-left: 6px solid #f59e0b;
border-radius: 14px;
padding: 1rem 1.15rem;
margin-top: 0.85rem;
color: #78350f;
}

.score-card {
background: #ffffff;
border: 1.5px solid #c7d2fe;
border-radius: 20px;
padding: 1.5rem;
box-shadow: 0 10px 24px rgba(67, 56, 202, 0.1);
margin-bottom: 1rem;
}
.improve-box {
background: #fff1f2;
border: 1.5px solid #fecdd3;
border-left: 6px solid #e11d48;
border-radius: 14px;
padding: 1rem 1.15rem;
color: #881337;
margin-top: 0.75rem;
}

.feature-card-1 {
background: linear-gradient(160deg, #ffffff 0%, #eef2ff 100%);
border: 1.5px solid #c7d2fe;
border-top: 5px solid #4f46e5;
border-radius: 16px;
padding: 1.1rem;
height: 100%;
box-shadow: 0 6px 16px rgba(79, 70, 229, 0.08);
}
.feature-card-2 {
background: linear-gradient(160deg, #ffffff 0%, #ecfdf5 100%);
border: 1.5px solid #a7f3d0;
border-top: 5px solid #10b981;
border-radius: 16px;
padding: 1.1rem;
height: 100%;
box-shadow: 0 6px 16px rgba(16, 185, 129, 0.08);
}
.feature-card-3 {
background: linear-gradient(160deg, #ffffff 0%, #fff1f2 100%);
border: 1.5px solid #fecdd3;
border-top: 5px solid #f43f5e;
border-radius: 16px;
padding: 1.1rem;
height: 100%;
box-shadow: 0 6px 16px rgba(244, 63, 94, 0.08);
}
.feature-title {
display: flex;
align-items: center;
gap: 8px;
font-weight: 700;
font-size: 1rem;
color: #0f172a;
margin-bottom: 0.45rem;
}
.feature-desc {
margin: 0;
font-size: 0.9rem;
color: #334155;
line-height: 1.5;
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

def calculate_full_summary() -> dict:
    """Calculate detailed quiz summary including attempt, correct, wrong, unanswered, and weak questions"""
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
    accuracy_on_attempted = (correct / attempted * 100) if attempted > 0 else 0.0
    score_percent = (correct / total * 100) if total > 0 else 0.0

    return {
        "attempt": st.session_state.attempt_count,
        "total": total,
        "attempted": attempted,
        "correct": correct,
        "wrong": wrong,
        "unanswered": unanswered,
        "accuracy": accuracy_on_attempted,
        "score_percent": score_percent,
        "wrong_items": wrong_items
    }

def show_cracker_burst():
    """Lightweight Telegram-poll style cracker burst for a right answer"""
    render_html(f"""
    <div class="cracker-banner">
    <span class="cracker-icon-anim">{SVG_ICONS["cracker"]}</span>
    <span>ശരിയായ ഉത്തരം! മികച്ച പ്രകടനം</span>
    <span class="spark-dot" style="background:#ef4444; --tx:-24px; --ty:-22px;"></span>
    <span class="spark-dot" style="background:#10b981; --tx:24px; --ty:-20px;"></span>
    <span class="spark-dot" style="background:#f59e0b; --tx:-20px; --ty:20px;"></span>
    <span class="spark-dot" style="background:#3b82f6; --tx:22px; --ty:22px;"></span>
    <span class="spark-dot" style="background:#ec4899; --tx:0px; --ty:-28px;"></span>
    </div>
    """)

# --- SESSION STATE INITIALIZATION ---
if "questions" not in st.session_state:
    st.session_state.questions = None
if "current_idx" not in st.session_state:
    st.session_state.current_idx = 0
if "user_answers" not in st.session_state:
    st.session_state.user_answers = {}
if "quiz_submitted" not in st.session_state:
    st.session_state.quiz_submitted = False
if "attempt_count" not in st.session_state:
    st.session_state.attempt_count = 1
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

def run_generate_quiz(topic_val, lang_val, count_val, level_val):
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
            st.session_state.quiz_submitted = False
            st.session_state.attempt_count = 1
            st.session_state.just_answered_idx = None
            st.rerun()

# --- HERO HEADER ---
render_html(f"""
<div class="quiz-hero">
<div class="quiz-hero-row">
{SVG_ICONS["brand"]}
<div>
<h1>Kerala PSC AI Quiz Master</h1>
<p>Vibrant practice studio crafted for Kerala PSC exam preparation</p>
</div>
</div>
</div>
""")

# --- SIDEBAR ---
with st.sidebar:
    icon_heading("gear", "Quiz Setup", "#4338CA")

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

    st.divider()

    if st.button("Generate New Quiz", type="primary", use_container_width=True, key="sb_gen_btn"):
        run_generate_quiz(sb_topic, sb_lang, sb_num_q, sb_level)

    if st.session_state.questions:
        st.divider()
        icon_heading("chart", "Session Tracker", "#0F766E")

        summary = calculate_full_summary()
        progress = summary["attempted"] / summary["total"] if summary["total"] > 0 else 0

        st.caption(f"Attempt: **#{summary['attempt']}**")
        st.progress(progress)
        st.caption(f"Attempted: **{summary['attempted']} / {summary['total']}**")

        if summary["attempted"] > 0:
            st.metric("Current Score", f"{summary['correct']}/{summary['attempted']}", f"{summary['accuracy']:.1f}%")

        if st.button("Reset Quiz", use_container_width=True, key="sb_reset_btn"):
            st.session_state.user_answers = {}
            st.session_state.current_idx = 0
            st.session_state.quiz_submitted = False
            st.session_state.just_answered_idx = None
            st.session_state.attempt_count += 1
            st.rerun()

        st.divider()
        icon_heading("grid", "Question Palette", "#BE123C")

        total_q = len(st.session_state.questions)
        cols_per_row = 5
        for row_start in range(0, total_q, cols_per_row):
            cols = st.columns(cols_per_row)
            for i, col in enumerate(cols):
                q_num = row_start + i
                if q_num < total_q:
                    with col:
                        if q_num in st.session_state.user_answers:
                            if st.session_state.user_answers[q_num] == st.session_state.questions[q_num]['answer']:
                                button_label = f"✓{q_num + 1}"
                            else:
                                button_label = f"✗{q_num + 1}"
                        else:
                            button_label = f"{q_num + 1}"

                        if q_num == st.session_state.current_idx:
                            button_label = f"◆{q_num + 1}"

                        if st.button(button_label, key=f"nav_{q_num}", use_container_width=True):
                            st.session_state.current_idx = q_num
                            st.session_state.quiz_submitted = False
                            st.rerun()

# --- DIRECT IN-PAGE SETUP PANEL ---
with st.expander("Quiz Setup Panel", expanded=(st.session_state.questions is None)):
    m_col1, m_col2 = st.columns(2)
    with m_col1:
        m_lang = st.radio(
            "Language",
            ["English", "Malayalam"],
            index=["English", "Malayalam"].index(st.session_state.cfg_lang),
            horizontal=True,
            key="m_lang"
        )
        m_level = st.selectbox(
            "Exam Level",
            ["10th/SSLC", "Plus Two", "Degree", "Post Graduate"],
            index=["10th/SSLC", "Plus Two", "Degree", "Post Graduate"].index(st.session_state.cfg_level),
            key="m_level"
        )
    with m_col2:
        m_num_q = st.slider("Number of Questions", 5, 200, st.session_state.cfg_num_q, key="m_num_q")
        m_topic = st.text_input("Topic", value=st.session_state.cfg_topic, placeholder="e.g., Indian Constitution", key="m_topic")

    if st.button("Generate New Quiz", type="primary", use_container_width=True, key="m_gen_btn"):
        run_generate_quiz(m_topic, m_lang, m_num_q, m_level)

# --- MAIN QUIZ / SCORE INTERFACE ---
if st.session_state.questions:
    questions = st.session_state.questions

    # Show ONLY Score Page when quiz is submitted
    if st.session_state.quiz_submitted:
        s = calculate_full_summary()

        render_html(f"""
        <div class="score-card">
        <div style="display:flex; flex-wrap:wrap; justify-content:space-between; align-items:center; gap:8px; margin-bottom:1rem;">
        <h2 style="margin:0; color:#1e1b4b;">Exam Score Report</h2>
        <span class="pill">Attempt #{s['attempt']}</span>
        <span class="pill pill-teal">{st.session_state.cfg_level}</span>
        <span class="pill pill-amber">{st.session_state.cfg_topic}</span>
        </div>
        </div>
        """)

        c1, c2, c3, c4 = st.columns(4)
        with c1:
            st.metric("Attempt", f"#{s['attempt']}")
        with c2:
            st.metric("ശരിയായവ (Right)", f"{s['correct']} / {s['total']}")
        with c3:
            st.metric("തെറ്റിയവ (Wrong)", f"{s['wrong']}")
        with c4:
            st.metric("Unanswered", f"{s['unanswered']}")

        st.markdown("")
        st.progress(s["score_percent"] / 100.0 if s["total"] > 0 else 0.0)
        st.caption(f"Overall Score: **{s['correct']}/{s['total']} ({s['score_percent']:.1f}%)**")

        # Areas to Improve section
        if s["wrong_items"] or s["unanswered"] > 0:
            items_html = ""
            for q_no, q_txt, u_ans, c_ans in s["wrong_items"]:
                items_html += (
                    f"<div style='margin-bottom:0.65rem; padding-bottom:0.5rem; border-bottom:1px dashed #fda4af;'>"
                    f"<strong>Q{q_no}:</strong> {q_txt}<br>"
                    f"<span style='color:#be123c;'>നിങ്ങളുടെ ഉത്തരം:</span> {u_ans} &nbsp;|&nbsp; "
                    f"<span style='color:#15803d;'>ശരിയായ ഉത്തരം:</span> <strong>{c_ans}</strong>"
                    f"</div>"
                )

            extra_note = ""
            if s["unanswered"] > 0:
                extra_note = f"<p style='margin:0.4rem 0 0 0;'><strong>Unanswered Questions:</strong> {s['unanswered']} ചോദ്യങ്ങൾക്ക് ഉത്തരം നൽകിയിട്ടില്ല — സമയം ക്രമീകരിച്ച് മുഴുവൻ ചോദ്യങ്ങളും ശ്രമിക്കുക.</p>"

            render_html(f"""
            <div class="improve-box">
            <h4 style="margin:0 0 0.5rem 0; color:#9f1239;">Improve ചെയ്യേണ്ട Areas ({st.session_state.cfg_topic})</h4>
            <p style="margin:0 0 0.6rem 0;">താഴെ പറയുന്ന ചോദ്യങ്ങളിലെ ആശയങ്ങൾ ഒരിക്കൽ കൂടി റിവൈസ് ചെയ്യുക:</p>
            {items_html}
            {extra_note}
            </div>
            """)
        else:
            st.success("എല്ലാ ചോദ്യങ്ങളും കൃത്യമായി ഉത്തരം നൽകി! ഇപ്പോൾ Improve ചെയ്യേണ്ട ഭാഗങ്ങൾ ഒന്നും ഇല്ല.")

        st.markdown("")
        b1, b2 = st.columns(2)
        with b1:
            if st.button("Back to Questions", use_container_width=True, key="back_to_q_btn"):
                st.session_state.quiz_submitted = False
                st.rerun()
        with b2:
            if st.button("Start Next Attempt", type="primary", use_container_width=True, key="next_attempt_btn"):
                st.session_state.user_answers = {}
                st.session_state.current_idx = 0
                st.session_state.quiz_submitted = False
                st.session_state.just_answered_idx = None
                st.session_state.attempt_count += 1
                st.rerun()

    else:
        idx = st.session_state.current_idx
        q = questions[idx]

        summary = calculate_full_summary()
        already_answered = idx in st.session_state.user_answers
        selected = st.session_state.user_answers.get(idx)

        if already_answered:
            if selected == q['answer']:
                status_badge = f'<span class="pill pill-green">{SVG_ICONS["check"]} Correct</span>'
            else:
                status_badge = f'<span class="pill pill-red">{SVG_ICONS["cross"]} Incorrect</span>'
        else:
            status_badge = '<span class="pill pill-amber">Unanswered</span>'

        render_html(f"""
        <div class="status-strip">
        <div style="display:flex; flex-wrap:wrap; gap:6px;">
        <span class="pill">Attempt #{summary['attempt']}</span>
        <span class="pill">Q {idx + 1} / {len(questions)}</span>
        <span class="pill pill-teal">{st.session_state.cfg_level}</span>
        <span class="pill pill-amber">{st.session_state.cfg_topic}</span>
        </div>
        <div style="display:flex; flex-wrap:wrap; gap:6px; align-items:center;">
        <span class="pill">Attempted: {summary['attempted']}/{len(questions)}</span>
        {status_badge}
        </div>
        </div>
        """)

        render_html(f"""
        <div class="question-card">
        <p class="question-text">{q['question']}</p>
        </div>
        """)

        # Show cracker animation only right when this question is answered correctly
        if already_answered and selected == q['answer'] and st.session_state.just_answered_idx == idx:
            show_cracker_burst()

        st.markdown("**Select an Option**")
        for i, option in enumerate(q['options']):
            label_prefix = f"{chr(65 + i)})"
            if already_answered:
                if option == q['answer']:
                    st.success(f"**{label_prefix} {option}** — Correct Answer")
                elif option == selected:
                    st.error(f"**{label_prefix} {option}** — Your Selection")
                else:
                    render_html(
                        f"<div style='padding: 0.55rem 0.85rem; color: #64748b; background:#ffffff; border-radius:10px; margin-bottom:0.35rem;'>{label_prefix} {option}</div>"
                    )
            else:
                button_type = "primary" if selected == option else "secondary"
                if st.button(
                    f"{label_prefix}  {option}",
                    key=f"btn_{idx}_{i}",
                    use_container_width=True,
                    type=button_type
                ):
                    st.session_state.user_answers[idx] = option
                    st.session_state.just_answered_idx = idx if option == q['answer'] else None
                    st.rerun()

        if already_answered:
            render_html(f"""
            <div class="exp-box">
            <div style="margin-top:2px;">{SVG_ICONS["bulb"]}</div>
            <div><strong>Explanation:</strong> {q.get('explanation', 'No explanation available.')}</div>
            </div>
            """)

        st.divider()
        nav1, nav2, nav3 = st.columns([1.2, 1, 1.2])

        with nav1:
            if st.button("Previous", disabled=idx == 0, use_container_width=True, key=f"prev_{idx}"):
                st.session_state.current_idx -= 1
                st.session_state.just_answered_idx = None
                st.rerun()

        with nav2:
            render_html(
                f"<div style='text-align:center; padding-top:0.5rem; font-weight:700; color:#4338ca;'>{idx + 1} / {len(questions)}</div>"
            )

        with nav3:
            if idx < len(questions) - 1:
                if st.button("Next", use_container_width=True, key=f"next_{idx}"):
                    st.session_state.current_idx += 1
                    st.session_state.just_answered_idx = None
                    st.rerun()
            else:
                if st.button("Finish Quiz", type="primary", use_container_width=True, key=f"finish_{idx}"):
                    st.session_state.quiz_submitted = True
                    st.session_state.just_answered_idx = None
                    st.rerun()

else:
    c1, c2, c3 = st.columns(3)
    with c1:
        render_html(f"""
        <div class="feature-card-1">
        <div class="feature-title">{SVG_ICONS["bolt"]}<span>Instant Feedback</span></div>
        <p class="feature-desc">ഓരോ ചോദ്യത്തിനും ഉത്തരം നൽകുമ്പോൾ തന്നെ ശരി/തെറ്റ് തിരിച്ചറിയാം.</p>
        </div>
        """)
    with c2:
        render_html(f"""
        <div class="feature-card-2">
        <div class="feature-title">{SVG_ICONS["spark"]}<span>Quick Explanations</span></div>
        <p class="feature-desc">തെറ്റിയാലും ശരിയായാലും കൃത്യമായ വിശദീകരണം ഉടൻ ലഭിക്കും.</p>
        </div>
        """)
    with c3:
        render_html(f"""
        <div class="feature-card-3">
        <div class="feature-title">{SVG_ICONS["compass"]}<span>Easy Navigation</span></div>
        <p class="feature-desc">Question Palette വഴിയോ Next/Previous ബട്ടൺ വഴിയോ വേഗം മാറാം.</p>
        </div>
        """)
