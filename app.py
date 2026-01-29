import streamlit as st
import google.generativeai as genai
import json
import time
import os
from fpdf import FPDF
from google.api_core import exceptions

# --- CONFIGURATION ---
# List your 20 keys in secrets.toml as GEMINI_KEYS = ["key1", "key2", ...]
ALL_KEYS = st.secrets.get("GEMINI_KEYS", [])

if "key_index" not in st.session_state:
    st.session_state.key_index = 0

def get_model(model_name="gemini-1.5-flash"):
    """Configures the current key and returns the model."""
    if not ALL_KEYS:
        st.error("No API keys found!")
        return None
    current_key = ALL_KEYS[st.session_state.key_index]
    genai.configure(api_key=current_key)
    return genai.GenerativeModel(model_name)

def rotate_key():
    """Moves to the next key in the list."""
    st.session_state.key_index = (st.session_state.key_index + 1) % len(ALL_KEYS)
    st.toast(f"🔄 Rotating to Key {st.session_state.key_index + 1}...", icon="⏳")

def call_gemini_smart(prompt, model_name="gemini-1.5-flash"):
    """Attempts to call Gemini with automatic rotation and backoff."""
    max_retries = len(ALL_KEYS)
    backoff_time = 2 # Seconds to wait after a 429 error
    
    for attempt in range(max_retries):
        try:
            model = get_model(model_name)
            response = model.generate_content(prompt)
            # Clean JSON formatting
            clean_text = response.text.replace("```json", "").replace("```", "").strip()
            return json.loads(clean_text)
            
        except exceptions.ResourceExhausted:
            if attempt < max_retries - 1:
                rotate_key()
                time.sleep(backoff_time)
                backoff_time *= 1.5 # Increase wait time slightly each time
                continue
            else:
                st.error("🚨 All keys are rate-limited. Please wait 2-3 minutes.")
                return None
        except Exception as e:
            # Fallback for JSON parsing errors or other issues
            st.warning(f"Attempt {attempt+1} failed. Retrying...")
            rotate_key()
            continue
    return None

# --- CORE FUNCTIONS ---
def get_psc_questions(topic, language, count, level):
    prompt = f"""
    Generate {count} REAL Kerala PSC questions on '{topic}' for {level} level.
    Language: {language}.
    Format as a JSON list of dictionaries:
    [{{
      "question": "...", 
      "options": ["A", "B", "C", "D"], 
      "answer": "Exact correct string",
      "explanation": "Brief context/fact in {language}",
      "sub_topic": "Specific sub-area"
    }}]
    Return ONLY raw JSON.
    """
    return call_gemini_smart(prompt)

def generate_revision_notes(wrong_questions, language):
    if not wrong_questions: return "Great job! No mistakes to revise."
    
    topics = {q.get('sub_topic', 'General') for q in wrong_questions}
    prompt = f"Provide detailed Kerala PSC revision notes in {language} for these topics: {topics}. Format as Markdown."
    
    # We use a simpler call here as it's not a JSON list
    try:
        model = get_model("gemini-1.5-flash")
        response = model.generate_content(prompt)
        return response.text
    except:
        return "Revision notes unavailable. Please try again in a moment."

# --- PDF GENERATION ---
def create_pdf(notes_text):
    try:
        pdf = FPDF()
        pdf.add_page()
        # Ensure NotoSansMalayalam-Regular.ttf is in your root folder
        font_path = "NotoSansMalayalam-Regular.ttf"
        if os.path.exists(font_path):
            pdf.add_font('Malayalam', '', font_path)
            pdf.set_font('Malayalam', size=12)
        else:
            pdf.set_font("Arial", size=12)
        pdf.multi_cell(0, 10, txt=notes_text)
        return bytes(pdf.output()) 
    except Exception as e:
        st.error(f"PDF Error: {e}")
        return None

# --- UI LAYOUT ---
st.set_page_config(page_title="PSC AI Tutor Pro", layout="centered")

# Initialize Session States
if "questions" not in st.session_state: st.session_state.questions = None
if "current_idx" not in st.session_state: st.session_state.current_idx = 0
if "user_answers" not in st.session_state: st.session_state.user_answers = {}
if "quiz_finished" not in st.session_state: st.session_state.quiz_finished = False

with st.sidebar:
    st.title("⚙️ Exam Settings")
    lang = st.radio("Language", ["English", "Malayalam"])
    level = st.selectbox("Exam Level", ["10th/SSLC", "Plus Two", "Degree"])
    num_q = st.slider("Questions", 5, 20, 10)
    topic = st.text_input("Topic", "Kerala Renaissance")
    
    if st.button("🚀 Start New Quiz"):
        with st.spinner("Generating fresh questions..."):
            res = get_psc_questions(topic, lang, num_q, level)
            if res:
                st.session_state.questions = res
                st.session_state.current_idx = 0
                st.session_state.user_answers = {}
                st.session_state.quiz_finished = False
                st.rerun()

# --- MAIN QUIZ UI ---
if st.session_state.questions:
    if not st.session_state.quiz_finished:
        idx = st.session_state.current_idx
        q = st.session_state.questions[idx]
        
        st.progress((idx + 1) / len(st.session_state.questions))
        st.write(f"**Question {idx + 1} of {len(st.session_state.questions)}**")
        st.subheader(q['question'])
        
        selected = st.session_state.user_answers.get(idx)
        
        for option in q['options']:
            if selected:
                if option == q['answer']:
                    st.success(f"✅ {option}")
                elif option == selected:
                    st.error(f"❌ {option}")
                else:
                    st.write(f"⚪ {option}")
            else:
                if st.button(option, key=f"btn_{idx}_{option}", use_container_width=True):
                    st.session_state.user_answers[idx] = option
                    st.rerun()

        if selected:
            st.info(f"**Explanation:** {q.get('explanation', 'No explanation provided.')}")
            col1, col2 = st.columns([1,1])
            with col1:
                if idx < len(st.session_state.questions) - 1:
                    if st.button("Next Question ➡️"):
                        st.session_state.current_idx += 1
                        st.rerun()
                else:
                    if st.button("Finish & See Results 🏆"):
                        st.session_state.quiz_finished = True
                        st.rerun()
    else:
        # Results Page
        st.title("📊 Your Performance")
        correct_count = sum(1 for i, q in enumerate(st.session_state.questions) if st.session_state.user_answers.get(i) == q['answer'])
        st.metric("Score", f"{correct_count} / {len(st.session_state.questions)}")
        
        if st.button("📝 Generate Revision Notes & PDF"):
            wrong_qs = [st.session_state.questions[i] for i, q in enumerate(st.session_state.questions) if st.session_state.user_answers.get(i) != q['answer']]
            with st.spinner("Analyzing your weak spots..."):
                notes = generate_revision_notes(wrong_qs, lang)
                st.markdown(notes)
                pdf_data = create_pdf(notes)
                if pdf_data:
                    st.download_button("📥 Download Malayalam/English PDF", data=pdf_data, file_name="PSC_Revision_Notes.pdf")

else:
    st.info("👈 Set your topic in the sidebar and click 'Start New Quiz' to begin your PSC preparation!")