import streamlit as st
import google.generativeai as genai
import json
from fpdf import FPDF

# --- CONFIGURATION ---
GEN_API_KEY = st.secrets["GEMINI_KEY"]
genai.configure(api_key=GEN_API_KEY)
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
    response = model.generate_content(prompt)
    text = response.text.replace("```json", "").replace("```", "").strip()
    return json.loads(text)

def generate_revision_notes(wrong_questions, language):
    topics_list = [q['sub_topic'] for q in wrong_questions]
    prompt = f"""
    The student got these topics wrong: {set(topics_list)}.
    Provide high-yield bulleted revision notes in {language} for these specific areas based on Kerala PSC trends.
    """
    response = model.generate_content(prompt)
    return response.text

# def create_pdf(notes_text):
#     pdf = FPDF()
#     pdf.add_page()
#     pdf.set_font("Arial", size=12)
#     # multi_cell handles long text wrapping
#     pdf.multi_cell(0, 10, txt=notes_text.encode('latin-1', 'replace').decode('latin-1'))
#     return pdf.output()

def create_pdf(notes_text):
    try:
        pdf = FPDF()
        pdf.add_page()
        
        font_path = "NotoSansMalayalam-Regular.ttf"
        
        import os
        if os.path.exists(font_path):
            pdf.add_font('Malayalam', '', font_path)
            pdf.set_font('Malayalam', size=12)
        else:
            pdf.set_font("Arial", size=12)
            notes_text = notes_text.encode('ascii', 'ignore').decode('ascii')
            
        pdf.multi_cell(0, 10, txt=notes_text)
        
        # Convert the output to standard bytes to prevent StreamlitAPIException
        pdf_output = pdf.output()
        return bytes(pdf_output) 
        # --- CRITICAL FIX END ---
        
    except Exception as e:
        print(f"PDF Error: {e}")
        return None

# --- SESSION STATE ---
if "questions" not in st.session_state:
    st.session_state.questions = None
if "current_idx" not in st.session_state:
    st.session_state.current_idx = 0
if "user_answers" not in st.session_state:
    st.session_state.user_answers = {}
if "quiz_finished" not in st.session_state:
    st.session_state.quiz_finished = False

# --- UI ---
st.set_page_config(page_title="PSC AI Tutor", layout="centered")

with st.sidebar:
    st.header("Exam Settings")
    lang = st.radio("Language", ["English", "Malayalam"])
    level = st.selectbox("Exam Level", ["10th/SSLC", "Plus Two", "Degree"])
    num_q = st.slider("Questions", 5, 50, 10)
    topic = st.text_input("Topic", "General Knowledge")
    
    if st.button("Start New Quiz"):
        with st.spinner("Preparing your quiz..."):
            st.session_state.questions = get_psc_questions(topic, lang, num_q, level)
            st.session_state.current_idx = 0
            st.session_state.user_answers = {}
            st.session_state.quiz_finished = False
            st.rerun()

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
            st.info(f"**Fact:** {q['explanation']}")
            
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
        score = sum(1 for i, q in enumerate(st.session_state.questions) if st.session_state.user_answers.get(i) == q['answer'])
        st.title(f"Your Score: {score} / {len(st.session_state.questions)}")
        
        wrong_q = [st.session_state.questions[i] for i, q in enumerate(st.session_state.questions) 
                   if st.session_state.user_answers.get(i) != q['answer']]
        
        if wrong_q:
            st.subheader("Areas for Improvement 🧠")
            with st.spinner("Generating custom study notes..."):
                notes = generate_revision_notes(wrong_q, lang)
                st.markdown(notes)
                
                # PDF Generation
                pdf_bytes = create_pdf(notes)
                st.download_button(
                    label="📥 Download Study Notes as PDF",
                    data=pdf_bytes,
                    file_name="PSC_Revision_Notes.pdf",
                    mime="application/pdf"
                )
        else:
            st.success("Perfect Score! You're ready for the exam!")
else:
    st.info("👈 Set your topic and click 'Start New Quiz' in the sidebar!")