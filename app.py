import streamlit as st
import google.generativeai as genai
import json
from typing import List, Dict, Optional

# --- PAGE CONFIG ---
st.set_page_config(
    page_title="PSC Pro Quiz",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- CUSTOM LAYOUT STYLING (MOBILE SIDEBAR FIXED) ---
st.markdown("""
<style>
    /* Hide footer and deploy/manage toolbar without hiding the sidebar toggle */
    footer {visibility: hidden;}
    [data-testid="stToolbar"] {display: none !important;}
    [data-testid="stDecoration"] {display: none !important;}
    .stDeployButton {display: none !important;}
    #MainMenu {visibility: hidden;}

    /* Keep header transparent so sidebar toggle button (>) stays visible & clickable */
    header[data-testid="stHeader"] {
        background-color: transparent !important;
    }

    /* Main container spacing */
    .block-container {
        max-width: 920px;
        padding-top: 1.5rem;
        padding-bottom: 3rem;
    }

    /* Hero banner */
    .quiz-hero {
        background: linear-gradient(135deg, #0f172a 0%, #1e3a8a 60%, #0d9488 100%);
        color: #ffffff;
        padding: 1.4rem 1.75rem;
        border-radius: 16px;
        margin-bottom: 1.25rem;
        box-shadow: 0 10px 25px rgba(15, 23, 42, 0.14);
    }
    .quiz-hero h1 {
        margin: 0;
        font-size: 1.75rem;
        font-weight: 700;
        color: #ffffff;
    }
    .quiz-hero p {
        margin: 0.35rem 0 0 0;
        font-size: 0.95rem;
        color: #e2e8f0;
    }

    /* Top strip inside quiz */
    .status-strip {
        display: flex;
        flex-wrap: wrap;
        gap: 0.6rem;
        align-items: center;
        justify-content: space-between;
        background-color: #f8fafc;
        border: 1px solid #e2e8f0;
        border-radius: 12px;
        padding: 0.75rem 1rem;
        margin-bottom: 1rem;
    }
    .pill {
        display: inline-block;
        padding: 0.25rem 0.7rem;
        border-radius: 999px;
        font-size: 0.82rem;
        font-weight: 600;
        background-color: #e0e7ff;
        color: #1e3a8a;
    }
    .pill-green {
        background-color: #dcfce7;
        color: #166534;
    }
    .pill-red {
        background-color: #fee2e2;
        color: #991b1b;
    }

    /* Question card */
    .question-card {
        background-color: #ffffff;
        border: 1px solid #e2e8f0;
        border-left: 5px solid #2563eb;
        border-radius: 14px;
        padding: 1.35rem 1.5rem;
        margin-bottom: 1.1rem;
        box-shadow: 0 4px 14px rgba(15, 23, 42, 0.04);
    }
    .question-text {
        font-size: 1.12rem;
        font-weight: 600;
        line-height: 1.6;
        color: #0f172a;
        margin: 0;
    }

    /* Option buttons */
    div.stButton > button {
        text-align: left !important;
        justify-content: flex-start !important;
        border-radius: 10px !important;
        padding: 0.65rem 1rem !important;
        font-weight: 500 !important;
        transition: all 0.15s ease !important;
    }
    div.stButton > button:hover {
        transform: translateY(-1px);
        border-color: #2563eb !important;
    }

    /* Feature cards on welcome screen */
    .feature-box {
        background-color: #f8fafc;
        border: 1px solid #e2e8f0;
        border-radius: 12px;
        padding: 1rem;
        height: 100%;
    }
    .feature-box h4 {
        margin: 0 0 0.4rem 0;
        font-size: 0.98rem;
        color: #0f172a;
    }
    .feature-box p {
        margin: 0;
        font-size: 0.88rem;
        color: #475569;
        line-height: 1.45;
    }
</style>
""", unsafe_allow_html=True)

# --- CONFIGURATION ---
def initialize_gemini():
    """Initialize Gemini API with error handling"""
    try:
        api_key = st.secrets.get("GEMINI_KEY") or st.secrets.get("GEN_API_KEY")
        if not api_key:
            st.error("⚠️ API key not found in secrets.toml. Please add GEMINI_KEY to your secrets.")
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

def calculate_score() -> tuple:
    """Calculate current score and percentage"""
    if not st.session_state.user_answers:
        return 0, 0.0

    correct = sum(
        1 for idx, answer in st.session_state.user_answers.items()
        if answer == st.session_state.questions[idx]['answer']
    )
    total = len(st.session_state.user_answers)
    percentage = (correct / total * 100) if total > 0 else 0

    return correct, percentage

# --- SESSION STATE INITIALIZATION ---
if "questions" not in st.session_state:
    st.session_state.questions = None
if "current_idx" not in st.session_state:
    st.session_state.current_idx = 0
if "user_answers" not in st.session_state:
    st.session_state.user_answers = {}
if "quiz_submitted" not in st.session_state:
    st.session_state.quiz_submitted = False

# --- HERO HEADER ---
st.markdown("""
<div class="quiz-hero">
    <h1>📚 Kerala PSC AI Quiz Master</h1>
    <p>Interactive practice deck tailored to Kerala PSC exam patterns</p>
</div>
""", unsafe_allow_html=True)

# --- SIDEBAR ---
with st.sidebar:
    st.markdown("### ⚙️ Quiz Setup")

    lang = st.radio("Language", ["English", "Malayalam"], index=0, horizontal=True)
    level = st.selectbox(
        "Exam Level",
        ["10th/SSLC", "Plus Two", "Degree", "Post Graduate"]
    )
    num_q = st.slider("Number of Questions", 5, 200, 10)
    topic = st.text_input("Topic", "Kerala History", placeholder="e.g., Indian Constitution")

    st.divider()

    if st.button("🎯 Generate New Quiz", type="primary", use_container_width=True):
        with st.spinner("Generating questions... This may take a moment."):
            questions = get_psc_questions(topic, lang, num_q, level)

            if questions:
                st.session_state.questions = questions
                st.session_state.current_idx = 0
                st.session_state.user_answers = {}
                st.session_state.quiz_submitted = False
                st.success(f"✅ Generated {len(questions)} questions!")
                st.rerun()

    if st.session_state.questions:
        st.divider()
        st.markdown("### 📊 Session Tracker")

        total_q = len(st.session_state.questions)
        answered = len(st.session_state.user_answers)
        progress = answered / total_q

        st.progress(progress)
        st.caption(f"Answered: **{answered} / {total_q}**")

        if answered > 0:
            correct, percentage = calculate_score()
            st.metric("Current Score", f"{correct}/{answered}", f"{percentage:.1f}%")

        if st.button("🔄 Reset Quiz", use_container_width=True):
            st.session_state.user_answers = {}
            st.session_state.current_idx = 0
            st.session_state.quiz_submitted = False
            st.rerun()

        st.divider()
        st.markdown("### 🔢 Question Palette")

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
                            button_label = f"•{q_num + 1}"

                        if st.button(button_label, key=f"nav_{q_num}", use_container_width=True):
                            st.session_state.current_idx = q_num
                            st.rerun()

# --- MAIN QUIZ INTERFACE ---
if st.session_state.questions:
    questions = st.session_state.questions
    idx = st.session_state.current_idx
    q = questions[idx]

    answered_count = len(st.session_state.user_answers)
    already_answered = idx in st.session_state.user_answers
    selected = st.session_state.user_answers.get(idx)

    if already_answered:
        if selected == q['answer']:
            status_badge = '<span class="pill pill-green">✓ Correct</span>'
        else:
            status_badge = '<span class="pill pill-red">✗ Incorrect</span>'
    else:
        status_badge = '<span class="pill">Unanswered</span>'

    st.markdown(f"""
    <div class="status-strip">
        <div>
            <span class="pill">Question {idx + 1} of {len(questions)}</span>
            <span class="pill">{level}</span>
            <span class="pill">{topic}</span>
        </div>
        <div>
            <span class="pill">Attempted: {answered_count}/{len(questions)}</span>
            {status_badge}
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown(f"""
    <div class="question-card">
        <p class="question-text">{q['question']}</p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("#### Choose an Option")
    for i, option in enumerate(q['options']):
        label_prefix = f"{chr(65 + i)})"
        if already_answered:
            if option == q['answer']:
                st.success(f"**{label_prefix} {option}**  —  Correct Answer ✓")
            elif option == selected:
                st.error(f"**{label_prefix} {option}**  —  Your Selection ✗")
            else:
                st.markdown(f"<div style='padding: 0.45rem 0.75rem; color: #64748b;'>{label_prefix} {option}</div>", unsafe_allow_html=True)
        else:
            button_type = "primary" if selected == option else "secondary"
            if st.button(
                f"{label_prefix}  {option}",
                key=f"btn_{idx}_{i}",
                use_container_width=True,
                type=button_type
            ):
                st.session_state.user_answers[idx] = option
                st.rerun()

    if already_answered:
        st.info(f"**💡 Explanation:** {q.get('explanation', 'No explanation available.')}")

    st.divider()
    nav1, nav2, nav3 = st.columns([1.2, 1, 1.2])

    with nav1:
        if st.button("⬅️ Previous", disabled=idx == 0, use_container_width=True, key=f"prev_{idx}"):
            st.session_state.current_idx -= 1
            st.rerun()

    with nav2:
        st.markdown(f"<div style='text-align:center; padding-top:0.45rem; font-weight:600;'>{idx + 1} / {len(questions)}</div>", unsafe_allow_html=True)

    with nav3:
        if idx < len(questions) - 1:
            if st.button("Next ➡️", use_container_width=True, key=f"next_{idx}"):
                st.session_state.current_idx += 1
                st.rerun()
        else:
            if st.button("📝 Finish Quiz", type="primary", use_container_width=True, key=f"finish_{idx}"):
                st.session_state.quiz_submitted = True
                st.rerun()

    if st.session_state.quiz_submitted and len(st.session_state.user_answers) == len(questions):
        st.divider()
        st.balloons()

        correct, percentage = calculate_score()
        total = len(questions)

        st.success("### 🎉 Quiz Completed!")

        m1, m2, m3 = st.columns(3)
        with m1:
            st.metric("Score", f"{correct}/{total}")
        with m2:
            st.metric("Accuracy", f"{percentage:.1f}%")
        with m3:
            if percentage >= 80:
                st.metric("Performance", "Excellent 🌟")
            elif percentage >= 60:
                st.metric("Performance", "Good 👍")
            else:
                st.metric("Performance", "Keep Going 💪")

else:
    st.info("👈 മുകളിൽ ഇടതുവശത്തുള്ള **`>`** ബട്ടൺ ടാപ്പ് ചെയ്ത് സൈഡ്‌ബാർ തുറക്കുക; എന്നിട്ട് Language, Level, Topic, ചോദ്യങ്ങളുടെ എണ്ണം എന്നിവ സെറ്റ് ചെയ്ത് **Generate New Quiz** ക്ലിക്ക് ചെയ്യുക.")

    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown("""
        <div class="feature-box">
            <h4>⚡ Instant Feedback</h4>
            <p>ഓരോ ചോദ്യത്തിനും ഉത്തരം നൽകുമ്പോൾ തന്നെ ശരി/തെറ്റ് തിരിച്ചറിയാം.</p>
        </div>
        """, unsafe_allow_html=True)
    with c2:
        st.markdown("""
        <div class="feature-box">
            <h4>💡 Quick Explanations</h4>
            <p>തെറ്റിയാലും ശരിയായാലും കൃത്യമായ വിശദീകരണം ഉടൻ ലഭിക്കും.</p>
        </div>
        """, unsafe_allow_html=True)
    with c3:
        st.markdown("""
        <div class="feature-box">
            <h4>🧭 Easy Navigation</h4>
            <p>സൈഡ്‌ബാറിലെ Question Palette വഴി ഏത് ചോദ്യത്തിലേക്കും വേഗം പോകാം.</p>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("")
    st.warning("⚠️ **Note:** Make sure to add your Gemini API key to `.streamlit/secrets.toml` before generating quizzes!")
