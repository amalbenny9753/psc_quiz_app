import streamlit as st
import google.generativeai as genai
import json
import time
import os
from fpdf import FPDF
from google.api_core import exceptions

# --- KEY ROTATION & API CONFIG ---
# This pulls the list of keys you added to secrets.toml
ALL_KEYS = st.secrets.get("GEMINI_KEYS", [])

# Store the index of the "active" key in session state
if "key_index" not in st.session_state:
    st.session_state.key_index = 0

def configure_next_key():
    """Rotates to the next available API key."""
    if not ALL_KEYS:
        st.error("No API keys found in secrets.toml!")
        return None
    
    st.session_state.key_index = (st.session_state.key_index + 1) % len(ALL_KEYS)
    current_key = ALL_KEYS[st.session_state.key_index]
    genai.configure(api_key=current_key)
    # Using 1.5-flash for the highest free tier limits (1500 RPM)
    return genai.GenerativeModel('gemini-1.5-flash')

def get_psc_questions(topic, language, count, level):
    # Try every key in your list at least once
    for _ in range(len(ALL_KEYS)):
        model = configure_next_key()
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
            clean_text = response.text.replace("```json", "").replace("```", "").strip()
            return json.loads(clean_text)
        
        except exceptions.ResourceExhausted:
            # Silent rotation: show a toast instead of an error box
            st.toast(f"🔄 Key {st.session_state.key_index + 1} busy. Rotating...", icon="⏳")
            time.sleep(1) # Small delay to respect IP limits
            continue # Try the next key
            
        except Exception as e:
            st.error(f"Something went wrong. Let's try again.")
            return None

    st.error("🚨 All API keys are currently exhausted. Please try again in an hour.")
    return None

# --- REVISION NOTES & PDF (Updated to use rotation) ---
def generate_revision_notes(wrong_questions, language):
    model = configure_next_key()
    topics_list = [q.get('sub_topic', 'General') for q in wrong_questions]
    prompt = f"The student got these Kerala PSC topics wrong: {set(topics_list)}. Provide revision notes in {language}."
    try:
        response = model.generate_content(prompt)
        return response.text
    except:
        return "Notes generation temporarily unavailable due to high traffic."

def create_pdf(notes_text):
    try:
        pdf = FPDF()
        pdf.add_page()
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

# --- UI & SESSION STATE ---
for key in ["questions", "current_idx", "user_answers", "quiz_finished"]:
    if key not in st.session_state:
        if key == "questions": st.session_state[key] = None
        elif key == "current_idx": st.session_state[key] = 0
        elif key == "user_answers": st.session_state[key] = {}
        elif key == "quiz_finished": st.session_state[key] = False

st.set_page_config(page_title="PSC AI Tutor Pro", layout="centered")

with st.sidebar:
    st.title("⚙️ Settings")
    lang = st.radio("Language", ["English", "Malayalam"])
    level = st.selectbox("Exam Level", ["10th/SSLC", "Plus Two", "Degree"])
    num_q = st.slider("Questions", 5, 20, 10)
    topic = st.text_input("Topic", "Indian History")
    
    if st.button("Start New Quiz"):
        with st.spinner("Searching Question Bank..."):
            questions = get_psc_questions(topic, lang, num_q, level)
            if questions:
                st.session_state.questions = questions
                st.session_state.current_idx = 0
                st.session_state.user_answers = {}
                st.session_state.quiz_finished = False
                st.rerun()

# --- MAIN QUIZ LOGIC ---
if st.session_state.questions:
    if not st.session_state.quiz_finished:
        idx = st.session_state.current_idx
        q = st.session_state.questions[idx]
        
        st.write(f"Question {idx + 1} of {len(st.session_state.questions)}")
        st.subheader(q['question'])
        
        selected = st.session_state.user_answers.get(idx)
        for option in q['options']:
            if selected:
                if option == q['answer']: st.success(f"✅ {option}")
                elif option == selected: st.error(f"❌ {option}")
                else: st.write(option)
            else:
                if st.button(option, key=f"q_{idx}_{option}", use_container_width=True):
                    st.session_state.user_answers[idx] = option
                    st.rerun()

        if selected:
            st.info(f"**Explanation:** {q.get('explanation', '')}")
            if idx < len(st.session_state.questions) - 1:
                if st.button("Next ➡️"):
                    st.session_state.current_idx += 1
                    st.rerun()
            else:
                if st.button("Finish 🏆"):
                    st.session_state.quiz_finished = True
                    st.rerun()
    else:
        st.title("Quiz Results")
        correct = sum(1 for i, q in enumerate(st.session_state.questions) if st.session_state.user_answers.get(i) == q['answer'])
        st.metric("Total Score", f"{correct}/{len(st.session_state.questions)}")
        
        if st.button("Generate Revision Notes"):
            wrong_q = [st.session_state.questions[i] for i, q in enumerate(st.session_state.questions) if st.session_state.user_answers.get(i) != q['answer']]
            notes = generate_revision_notes(wrong_q, lang)
            st.markdown(notes)
            pdf = create_pdf(notes)
            if pdf:
                st.download_button("Download PDF", data=pdf, file_name="notes.pdf")
else:
    st.info("Set a topic and click 'Start New Quiz' to begin!")