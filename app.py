import streamlit as st
import google.generativeai as genai
import json
import time
import os
from fpdf import FPDF
from google.api_core import exceptions

# --- 1. ROBUST CONFIGURATION ---
# This looks for GEMINI_KEYS in your .streamlit/secrets.toml
ALL_KEYS = st.secrets.get("GEMINI_KEYS", [])

# If the list is empty, try to find a single key GEMINI_KEY
if not ALL_KEYS:
    single = st.secrets.get("GEMINI_KEY")
    if single:
        ALL_KEYS = [single]

# --- 2. SESSION STATE INITIALIZATION ---
# We use this to keep the quiz alive and rotate keys silently
if "key_index" not in st.session_state: st.session_state.key_index = 0
if "questions" not in st.session_state: st.session_state.questions = None
if "current_idx" not in st.session_state: st.session_state.current_idx = 0
if "user_answers" not in st.session_state: st.session_state.user_answers = {}
if "quiz_finished" not in st.session_state: st.session_state.quiz_finished = False

# --- 3. HELPER FUNCTIONS ---

def get_model():
    """Rotates keys and returns a fresh model instance."""
    if not ALL_KEYS:
        return None
    current_key = ALL_KEYS[st.session_state.key_index]
    genai.configure(api_key=current_key)
    return genai.GenerativeModel('gemini-1.5-flash')

def rotate_key():
    st.session_state.key_index = (st.session_state.key_index + 1) % len(ALL_KEYS)
    st.toast(f"🔄 Rotating to API Key {st.session_state.key_index + 1}...", icon="⏳")

def get_psc_questions(topic, language, count, level):
    """Fetches questions with automatic retry and key rotation."""
    for attempt in range(len(ALL_KEYS)):
        model = get_model()
        if not model: return None
        
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
        Return ONLY the raw JSON.
        """
        
        try:
            response = model.generate_content(prompt)
            # Robust JSON cleaning
            clean_text = response.text.strip()
            if "```json" in clean_text:
                clean_text = clean_text.split("```json")[1].split("```")[0].strip()
            elif "```" in clean_text:
                clean_text = clean_text.split("```")[1].split("```")[0].strip()
            
            return json.loads(clean_text)
            
        except exceptions.ResourceExhausted:
            rotate_key()
            time.sleep(2) # Backoff delay
            continue
        except Exception as e:
            rotate_key()
            continue
            
    return None

def create_pdf(notes_text):
    try:
        pdf = FPDF()
        pdf.add_page()
        # Fallback to Arial if Malayalam font is missing
        font_path = "NotoSansMalayalam-Regular.ttf"
        if os.path.exists(font_path):
            pdf.add_font('Malayalam', '', font_path)
            pdf.set_font('Malayalam', size=12)
        else:
            pdf.set_font("Arial", size=12)
        pdf.multi_cell(0, 10, txt=notes_text)
        return bytes(pdf.output()) 
    except:
        return None

# --- 4. UI LAYOUT ---
st.set_page_config(page_title="PSC AI Tutor Pro", layout="centered")

# Error message if keys are missing
if not ALL_KEYS:
    st.error("🚨 Configuration Error: No API keys found.")
    st.info("Check: Is your folder named '.streamlit' and your file 'secrets.toml'?")
    st.stop()

with st.sidebar:
    st.header("⚙️ Settings")
    st.success(f"Connected to {len(ALL_KEYS)} Keys")
    lang = st.radio("Language", ["English", "Malayalam"])
    level = st.selectbox("Level", ["10th/SSLC", "Plus Two", "Degree"])
    num_q = st.slider("Questions", 5, 20, 10)
    topic = st.text_input("Topic", "Kerala Geography")
    
    if st.button("🚀 Start New Quiz"):
        with st.spinner("Fetching Questions..."):
            questions = get_psc_questions(topic, lang, num_q, level)
            if questions:
                st.session_state.questions = questions
                st.session_state.current_idx = 0
                st.session_state.user_answers = {}
                st.session_state.quiz_finished = False
                st.rerun()

# --- 5. MAIN QUIZ ENGINE ---
if st.session_state.questions:
    if not st.session_state.quiz_finished:
        idx = st.session_state.current_idx
        q = st.session_state.questions[idx]
        
        st.progress((idx + 1) / len(st.session_state.questions))
        st.subheader(f"Q{idx+1}: {q['question']}")
        
        selected = st.session_state.user_answers.get(idx)
        for option in q['options']:
            if selected:
                if option == q['answer']: st.success(f"✅ {option}")
                elif option == selected: st.error(f"❌ {option}")
                else: st.write(f"⚪ {option}")
            else:
                if st.button(option, key=f"q_{idx}_{option}", use_container_width=True):
                    st.session_state.user_answers[idx] = option
                    st.rerun()

        if selected:
            st.info(f"**Explanation:** {q.get('explanation', '')}")
            if idx < len(st.session_state.questions) - 1:
                if st.button("Next Question ➡️"):
                    st.session_state.current_idx += 1
                    st.rerun()
            else:
                if st.button("Finish Quiz 🏆"):
                    st.session_state.quiz_finished = True
                    st.rerun()
    else:
        # Results Page
        st.balloons()
        correct = sum(1 for i, q in enumerate(st.session_state.questions) if st.session_state.user_answers.get(i) == q['answer'])
        st.title(f"Score: {correct} / {len(st.session_state.questions)}")
        
        if st.button("🔄 Restart Quiz"):
            st.session_state.questions = None
            st.rerun()
else:
    st.info("👈 Enter a topic in the sidebar and click 'Start New Quiz' to begin.")