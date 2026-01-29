import streamlit as st
import google.generativeai as genai
import json
import time
import os
from fpdf import FPDF
from google.api_core import exceptions

# --- CONFIGURATION ---
GEN_API_KEY = st.secrets["GEMINI_KEY"]
genai.configure(api_key=GEN_API_KEY)
# Using the latest 2026 stable-preview model name
model = genai.GenerativeModel('gemini-3-flash-preview')

def get_psc_questions(topic, language, count, level):
    prompt = f"""
    Generate {count} REAL Kerala PSC questions (2021-2025) on '{topic}' for {level} level.
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
    
    for attempt in range(3):
        try:
            response = model.generate_content(prompt)
            # Remove markdown formatting if the AI includes it
            clean_text = response.text.replace("```json", "").replace("```", "").strip()
            return json.loads(clean_text)
        except exceptions.ResourceExhausted:
            wait_time = (attempt + 1) * 12 # 2026 Free Tier is stricter; wait longer
            if attempt < 2:
                st.warning(f"🚦 API Busy (Rate Limit). Retrying in {wait_time}s...")
                time.sleep(wait_time)
            else:
                st.error("Daily limit reached. Please try again tomorrow or reduce the number of questions.")
                return None
        except Exception as e:
            st.error(f"Generation Error: {e}")
            return None

def generate_revision_notes(wrong_questions, language):
    topics_list = [q.get('sub_topic', 'General') for q in wrong_questions]
    prompt = f"""
    The student got these Kerala PSC topics wrong: {set(topics_list)}.
    Provide high-yield bulleted revision notes in {language} for these areas.
    Focus on repeated PSC facts.
    """
    try:
        response = model.generate_content(prompt)
        return response.text
    except:
        return "Could not generate notes. Please try again later."

def create_pdf(notes_text):
    try:
        pdf = FPDF()
        pdf.add_page()
        
        font_path = "NotoSansMalayalam-Regular.ttf"
        
        if os.path.exists(font_path):
            pdf.add_font('Malayalam', '', font_path)
            pdf.set_font('Malayalam', size=12)
        else:
            # Better fallback: warn the user the font is missing
            pdf.set_font("Arial", size=12)
            notes_text = "ERROR: Malayalam font file not found on server.\n\n" + notes_text.encode('ascii', 'ignore').decode('ascii')
            
        pdf.multi_cell(0, 10, txt=notes_text)
        return bytes(pdf.output()) 
        
    except Exception as e:
        st.error(f"PDF creation failed: {e}")
        return None

# --- SESSION STATE ---
for key in ["questions", "current_idx", "user_answers", "quiz_finished"]:
    if key not in st.session_state:
        if key == "questions": st.session_state[key] = None
        elif key == "current_idx": st.session_state[key] = 0
        elif key == "user_answers": st.session_state[key] = {}
        elif key == "quiz_finished": st.session_state[key] = False

# --- UI ---
st.set_page_config(page_title="PSC AI Tutor", layout="centered")

with st.sidebar:
    st.header("Exam Settings")
    lang = st.radio("Language", ["English", "Malayalam"])
    level = st.selectbox("Exam Level", ["10th/SSLC", "Plus Two", "Degree"])
    num_q = st.slider("Questions", 5, 20, 10) # Lowered max to 20 to avoid token limits
    topic = st.text_input("Topic", "General Knowledge")
    
    if st.button("Start New Quiz"):
        with st.spinner("Fetching latest PSC questions..."):
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
                    st.write(option)
            else:
                if st.button(option, key=f"q_{idx}_{option}", use_container_width=True):
                    st.session_state.user_answers[idx] = option
                    st.rerun()

        if selected:
            st.info(f"**Explanation:** {q.get('explanation', 'No details available.')}")
            
        col1, col2 = st.columns(2)
        with col1:
            if st.button("⬅️ Previous") and idx > 0:
                st.session_state.current_idx -= 1
                st.rerun()
        with col2:
            if idx < len(st.session_state.questions) - 1:
                if st.button("Next ➡️"):
                    st.session_state.current_idx += 1
                    st.rerun()
            else:
                if st.button("Finish & See Results 🏆"):
                    st.session_state.quiz_finished = True
                    st.rerun()
    else:
        # --- RESULTS PAGE ---
        st.balloons()
        correct_count = sum(1 for i, q in enumerate(st.session_state.questions) if st.session_state.user_answers.get(i) == q['answer'])
        st.title(f"Score: {correct_count} / {len(st.session_state.questions)}")
        
        wrong_q = [st.session_state.questions[i] for i, q in enumerate(st.session_state.questions) 
                   if st.session_state.user_answers.get(i) != q['answer']]
        
        if wrong_q:
            st.subheader("Revision Strategy 🧠")
            with st.spinner("AI is preparing your custom notes..."):
                notes = generate_revision_notes(wrong_q, lang)
                st.markdown(notes)
                
                pdf_bytes = create_pdf(notes)
                if pdf_bytes:
                    st.download_button(
                        label="📥 Download Malayalam Study Notes (PDF)",
                        data=pdf_bytes,
                        file_name="PSC_Notes.pdf",
                        mime="application/pdf"
                    )
        else:
            st.success("Perfect Score! You are a PSC Pro!")
else:
    st.info("👈 Set your topic and click 'Start New Quiz' in the sidebar!")