import streamlit as st
import google.generativeai as genai
import json
import time
import os
from fpdf import FPDF
from google.api_core import exceptions

# --- 1. CRITICAL CONFIG CHECK ---
# Ensure your secrets are loaded correctly
ALL_KEYS = st.secrets.get("GEMINI_KEYS", [])

if not ALL_KEYS:
    st.error("🚨 Configuration Error: No API keys found in secrets.toml!")
    st.stop() # Stops the app here so you know the config is wrong

if "key_index" not in st.session_state:
    st.session_state.key_index = 0

def get_model(model_name="gemini-1.5-flash"):
    current_key = ALL_KEYS[st.session_state.key_index]
    genai.configure(api_key=current_key)
    return genai.GenerativeModel(model_name)

def rotate_key():
    st.session_state.key_index = (st.session_state.key_index + 1) % len(ALL_KEYS)
    st.toast(f"🔄 Trying Key {st.session_state.key_index + 1}...", icon="⏳")

def get_psc_questions(topic, language, count, level):
    # Try every key you have
    for attempt in range(len(ALL_KEYS)):
        try:
            model = get_model()
            prompt = f"Generate {count} REAL Kerala PSC questions on '{topic}' for {level} level in {language}. Format as JSON list only."
            
            response = model.generate_content(prompt)
            
            # Clean response text
            raw_text = response.text.strip()
            if "```json" in raw_text:
                raw_text = raw_text.split("```json")[1].split("```")[0].strip()
            elif "```" in raw_text:
                raw_text = raw_text.split("```")[1].split("```")[0].strip()

            # Attempt to parse
            data = json.loads(raw_text)
            return data

        except exceptions.ResourceExhausted:
            rotate_key()
            time.sleep(1) # Breath for the API
            continue 
        except json.JSONDecodeError:
            st.warning(f"⚠️ Key {st.session_state.key_index + 1} gave bad data. Rotating...")
            rotate_key()
            continue
        except Exception as e:
            st.error(f"❌ Critical Error on Key {st.session_state.key_index + 1}: {e}")
            rotate_key()
            continue
            
    return None

# --- UI LOGIC ---
st.set_page_config(page_title="PSC AI Tutor Pro", layout="centered")

# Initialize Session States
for key in ["questions", "current_idx", "user_answers", "quiz_finished"]:
    if key not in st.session_state:
        st.session_state[key] = None if key == "questions" else (0 if key == "current_idx" else ({} if key == "user_answers" else False))

with st.sidebar:
    st.title("⚙️ Exam Settings")
    lang = st.radio("Language", ["English", "Malayalam"])
    level = st.selectbox("Exam Level", ["10th/SSLC", "Plus Two", "Degree"])
    num_q = st.slider("Questions", 5, 20, 10)
    topic = st.text_input("Topic", "Indian Constitution")
    
    if st.button("🚀 Start New Quiz"):
        # Reset everything before starting
        st.session_state.questions = None 
        
        with st.spinner("Talking to Gemini..."):
            questions = get_psc_questions(topic, lang, num_q, level)
            if questions:
                st.session_state.questions = questions
                st.session_state.current_idx = 0
                st.session_state.user_answers = {}
                st.session_state.quiz_finished = False
                st.rerun() # Force the UI to refresh and see the new questions
            else:
                st.error("Could not generate questions. Check your keys or topic name.")

# --- MAIN DISPLAY ---
if st.session_state.questions:
    # (Existing Quiz Logic)
    idx = st.session_state.current_idx
    st.write(f"Question {idx + 1} of {len(st.session_state.questions)}")
    # ... rest of your quiz UI code ...
else:
    # This is what shows if questions is None
    st.info("👋 Welcome! Select a topic in the sidebar and click 'Start New Quiz' to begin.")