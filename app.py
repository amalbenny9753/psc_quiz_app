import streamlit as st
import google.generativeai as genai
import json
from typing import List, Dict, Optional

# --- CONFIGURATION ---
def initialize_gemini():
    """Initialize Gemini API with error handling"""
    try:
        # Get API key from Streamlit secrets
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
    Generate {count} realistic Kerala PSC exam questions (2021-2025 pattern) on '{topic}' for {level} level.
    Language: {language}.
    
    Important requirements:
    1. Questions should be factual and exam-oriented
    2. Options should be plausible distractors
    3. Explanation should be concise and informative
    
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
        response = model.generate_content(prompt)
        # Clean response text
        text = response.text.strip()
        
        # Remove markdown code blocks if present
        if text.startswith("```"):
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:].strip()
        
        # Parse JSON
        questions = json.loads(text)
        
        # Validate structure
        if not isinstance(questions, list) or len(questions) == 0:
            raise ValueError("Invalid questions format")
        
        # Validate each question
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

# --- UI SETUP ---
st.set_page_config(
    page_title="PSC Pro Quiz",
    page_icon="📚",
    layout="centered"
)

st.title("📚 Kerala PSC AI Quiz Master")
st.markdown("*Practice with AI-generated questions based on real PSC patterns*")

# --- SIDEBAR ---
with st.sidebar:
    st.header("⚙️ Quiz Settings")
    
    lang = st.radio("Language", ["English", "Malayalam"], index=0)
    level = st.selectbox(
        "Exam Level",
        ["10th/SSLC", "Plus Two", "Degree", "Post Graduate"]
    )
    num_q = st.slider("Number of Questions", 5, 30, 10)
    topic = st.text_input("Topic", "Kerala History", placeholder="e.g., Indian Constitution")
    
    st.markdown("---")
    
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
    
    # Progress Display
    if st.session_state.questions:
        st.markdown("---")
        st.subheader("📊 Progress")
        
        total_q = len(st.session_state.questions)
        answered = len(st.session_state.user_answers)
        progress = answered / total_q
        
        st.progress(progress)
        st.write(f"Answered: **{answered}/{total_q}**")
        
        if answered > 0:
            correct, percentage = calculate_score()
            st.metric("Current Score", f"{correct}/{answered}", f"{percentage:.1f}%")
        
        # Reset button
        if st.button("🔄 Reset Quiz", use_container_width=True):
            st.session_state.user_answers = {}
            st.session_state.current_idx = 0
            st.session_state.quiz_submitted = False
            st.rerun()

# --- MAIN QUIZ INTERFACE ---
if st.session_state.questions:
    questions = st.session_state.questions
    idx = st.session_state.current_idx
    q = questions[idx]
    
    # Question Header
    col1, col2 = st.columns([3, 1])
    with col1:
        st.write(f"### Question {idx + 1} of {len(questions)}")
    with col2:
        if idx in st.session_state.user_answers:
            if st.session_state.user_answers[idx] == q['answer']:
                st.success("✓ Correct")
            else:
                st.error("✗ Wrong")
    
    st.markdown("---")
    
    # Question Text
    st.markdown(f"**{q['question']}**")
    st.write("")
    
    # Check if already answered
    already_answered = idx in st.session_state.user_answers
    selected = st.session_state.user_answers.get(idx)
    
    # Display Options
    for i, option in enumerate(q['options']):
        col1, col2 = st.columns([0.95, 0.05])
        
        with col1:
            if already_answered:
                # Show feedback with colors
                if option == q['answer']:
                    st.success(f"**{chr(65+i)}) {option}** ✓")
                elif option == selected:
                    st.error(f"**{chr(65+i)}) {option}** ✗")
                else:
                    st.write(f"{chr(65+i)}) {option}")
            else:
                # Interactive buttons
                button_type = "primary" if selected == option else "secondary"
                if st.button(
                    f"{chr(65+i)}) {option}",
                    key=f"btn_{idx}_{i}",
                    use_container_width=True,
                    type=button_type if selected == option else "secondary"
                ):
                    st.session_state.user_answers[idx] = option
                    st.rerun()
    
    # Show explanation after answering
    if already_answered:
        st.markdown("---")
        st.info(f"**💡 Explanation:** {q.get('explanation', 'No explanation available.')}")
    
    # Navigation
    st.markdown("---")
    col1, col2, col3 = st.columns([1, 1, 1])
    
    with col1:
        if st.button("⬅️ Previous", disabled=idx == 0, use_container_width=True):
            st.session_state.current_idx -= 1
            st.rerun()
    
    with col2:
        # Jump to specific question
        jump_to = st.number_input(
            "Jump to Q#",
            min_value=1,
            max_value=len(questions),
            value=idx + 1,
            key="jump_input"
        )
        if jump_to != idx + 1:
            st.session_state.current_idx = jump_to - 1
            st.rerun()
    
    with col3:
        if idx < len(questions) - 1:
            if st.button("Next ➡️", use_container_width=True):
                st.session_state.current_idx += 1
                st.rerun()
        else:
            if st.button("📝 Finish", type="primary", use_container_width=True):
                st.session_state.quiz_submitted = True
                st.rerun()
    
    # Final Results
    if st.session_state.quiz_submitted and len(st.session_state.user_answers) == len(questions):
        st.markdown("---")
        st.balloons()
        
        correct, percentage = calculate_score()
        total = len(questions)
        
        st.success("### 🎉 Quiz Completed!")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Score", f"{correct}/{total}")
        with col2:
            st.metric("Percentage", f"{percentage:.1f}%")
        with col3:
            if percentage >= 80:
                st.metric("Grade", "Excellent! 🌟")
            elif percentage >= 60:
                st.metric("Grade", "Good! 👍")
            else:
                st.metric("Grade", "Keep Practicing! 💪")

else:
    # Welcome Screen
    st.info("👈 Configure your quiz settings in the sidebar and click **Generate New Quiz** to begin!")
    
    st.markdown("""
    ### How to Use:
    1. **Choose your language** (English/Malayalam)
    2. **Select exam level** and number of questions
    3. **Enter a topic** you want to practice
    4. Click **Generate New Quiz**
    5. Answer questions and get instant feedback!
    
    ### Features:
    - ✅ Real-time answer validation
    - 📊 Progress tracking
    - 💡 Detailed explanations
    - 🎯 Customizable difficulty levels
    - 🔄 Multiple practice sessions
    """)
    
    st.warning("⚠️ **Note:** Make sure to add your Gemini API key to `.streamlit/secrets.toml` before generating quizzes!")