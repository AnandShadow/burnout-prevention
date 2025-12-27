import streamlit as st
import pandas as pd
import time
import google.generativeai as genai
import json
import re

# --- PAGE CONFIG ---
st.set_page_config(
    page_title="AI Wellbeing Scheduler", 
    page_icon="🧠", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- CUSTOM CSS FOR CREATIVE UI ---
st.markdown("""
<style>
    /* Main gradient background effect */
    .stApp {
        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
    }
    
    /* Glowing header effect */
    .main-header {
        text-align: center;
        padding: 2rem;
        background: linear-gradient(90deg, #00d2ff, #3a7bd5, #00d2ff);
        background-size: 200% auto;
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        animation: shine 3s linear infinite;
        font-size: 3rem;
        font-weight: bold;
    }
    
    @keyframes shine {
        to { background-position: 200% center; }
    }
    
    /* Card styling */
    .task-card {
        background: rgba(255, 255, 255, 0.05);
        border-radius: 15px;
        padding: 1.5rem;
        margin: 0.5rem 0;
        border: 1px solid rgba(255, 255, 255, 0.1);
        backdrop-filter: blur(10px);
        transition: transform 0.3s ease, box-shadow 0.3s ease;
    }
    
    .task-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 10px 30px rgba(0, 210, 255, 0.2);
    }
    
    /* Agent log styling */
    .agent-log {
        background: rgba(0, 0, 0, 0.3);
        border-left: 4px solid #00d2ff;
        padding: 1rem;
        margin: 0.5rem 0;
        border-radius: 0 10px 10px 0;
    }
    
    /* Metric cards */
    .metric-container {
        background: rgba(255, 255, 255, 0.05);
        border-radius: 15px;
        padding: 1rem;
        text-align: center;
        border: 1px solid rgba(255, 255, 255, 0.1);
    }
    
    /* Button styling */
    .stButton > button {
        border-radius: 25px;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

# --- GEMINI AI CONFIGURATION ---
def get_gemini_model():
    """Get or create Gemini model from session state"""
    if 'gemini_api_key' in st.session_state and st.session_state.gemini_api_key:
        try:
            genai.configure(api_key=st.session_state.gemini_api_key)
            return genai.GenerativeModel('gemini-2.0-flash')
        except Exception as e:
            st.error(f"Error configuring Gemini: {e}")
            return None
    return None

def analyze_task_with_ai(model, task_name):
    """Use Gemini AI to analyze task and determine intensity"""
    prompt = f"""Analyze this task and determine its mental intensity level.
    Task: "{task_name}"

    Classify into ONE of these categories and explain why:
    1. "High Intensity (Coding/Math)"
    2. "Medium Intensity (Theory/Reading)"
    3. "Low Intensity (Meeting/Email)"

    Respond in JSON format only:
    {{"intensity": "category name exactly as shown above", "reason": "brief explanation", "tips": "one wellbeing tip for this task"}}
    """
    try:
        response = model.generate_content(prompt)
        text = response.text
        # CLEANUP: Remove markdown code blocks if present (CRITICAL FIX)
        text = text.replace("```json", "").replace("```", "").strip()
        
        json_match = re.search(r'\{.*\}', text, re.DOTALL)
        if json_match:
            return json.loads(json_match.group())
    except Exception as e:
        st.error(f"AI Analysis failed: {e}")
    return None

def get_ai_recommendations(model, tasks, final_fatigue):
    """Get AI-powered personalized recommendations"""
    task_summary = ", ".join([f"{t[0]} ({t[1]})" for t in tasks])
    prompt = f"""You are a wellbeing coach AI. Based on this schedule:
    Tasks: {task_summary}
    Final cognitive load: {final_fatigue}%

    Provide 3 personalized recommendations.
    Respond in JSON format only:
    {{"recommendations": ["rec 1", "rec 2", "rec 3"], "overall_assessment": "brief 1-sentence assessment"}}
    """
    try:
        response = model.generate_content(prompt)
        text = response.text
        # CLEANUP: Remove markdown code blocks if present (CRITICAL FIX)
        text = text.replace("```json", "").replace("```", "").strip()

        json_match = re.search(r'\{.*\}', text, re.DOTALL)
        if json_match:
            return json.loads(json_match.group())
    except Exception as e:
        st.error(f"AI Recommendations failed: {e}")
    return None

# --- AGENT INTERNAL MODEL ---
ENERGY_MODEL = {
    "High Intensity (Coding/Math)": {"cost": 35, "icon": "🔴", "color": "#ff4757"},
    "Medium Intensity (Theory/Reading)": {"cost": 15, "icon": "🟠", "color": "#ffa502"},
    "Low Intensity (Meeting/Email)": {"cost": 5, "icon": "🟢", "color": "#2ed573"},
    "Recovery Break": {"cost": -25, "icon": "☕", "color": "#3742fa"}
}
MAX_FATIGUE_LIMIT = 80

def get_fatigue_status(fatigue):
    if fatigue < 30: return "Optimal", "#2ed573"
    elif fatigue < 60: return "Moderate", "#ffa502"
    else: return "Critical", "#ff4757"

def run_agent_scheduler(tasks):
    schedule = []
    fatigue_history = [{"step": 0, "fatigue": 0, "event": "Start"}]
    current_fatigue = 0
    
    log_container = st.container()
    
    with log_container:
        st.markdown("### 🤖 Agent Processing...")
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        for idx, (task_name, difficulty) in enumerate(tasks):
            time.sleep(0.2) # Visual effect
            progress_bar.progress((idx + 1) / len(tasks))
            
            energy_cost = ENERGY_MODEL[difficulty]["cost"]
            
            # --- AGENT REASONING ---
            if current_fatigue + energy_cost > MAX_FATIGUE_LIMIT:
                status_text.markdown(f"""
                <div class="agent-log">
                    ⚠️ <strong>ALERT:</strong> Fatigue would hit {current_fatigue + energy_cost}%<br>
                    🛡️ <strong>ACTION:</strong> Inserting Recovery Break
                </div>
                """, unsafe_allow_html=True)
                time.sleep(0.5)
                
                # Insert Break
                schedule.append({"Task": "☕ RECOVERY BREAK", "Type": "Agent Intervention", "Fatigue": max(0, current_fatigue - 25)})
                current_fatigue = max(0, current_fatigue - 25)
                fatigue_history.append({"step": len(fatigue_history), "fatigue": current_fatigue, "event": "Break"})
            
            # Add User Task
            current_fatigue += energy_cost
            schedule.append({"Task": task_name, "Type": "User Task", "Fatigue": current_fatigue})
            fatigue_history.append({"step": len(fatigue_history), "fatigue": current_fatigue, "event": task_name})
        
        status_text.success("✅ Optimization Complete!")
            
    return schedule, fatigue_history, current_fatigue

# --- UI LAYOUT ---
st.markdown('<h1 class="main-header">AI Burnout Prevention Agent</h1>', unsafe_allow_html=True)
st.caption("Hybrid Agent: Generative Perception (Gemini) + Deliberative Planning")

# Sidebar
with st.sidebar:
    st.header("⚙️ Configuration")
    
    # API Key Handling
    if 'gemini_api_key' not in st.session_state:
        api_key = st.text_input("Enter Google Gemini API Key", type="password")
        if api_key:
            st.session_state.gemini_api_key = api_key
            st.rerun()
    else:
        st.success("✅ AI Connected")
        if st.button("Disconnect AI"):
            del st.session_state.gemini_api_key
            st.rerun()

    st.divider()
    
    # Task Input
    st.subheader("Add Task")
    task_name = st.text_input("Task Name", placeholder="e.g. Study Neural Networks")
    
    # Auto-classify logic
    ai_mode = 'gemini_api_key' in st.session_state
    use_ai = st.checkbox("🧠 Auto-detect Intensity", value=ai_mode, disabled=not ai_mode)
    
    manual_difficulty = st.selectbox("Manual Intensity", [k for k in ENERGY_MODEL.keys() if "Recovery" not in k])
    
    if st.button("Add Task", type="primary", use_container_width=True):
        if task_name:
            if 'task_list' not in st.session_state: st.session_state.task_list = []
            
            final_diff = manual_difficulty
            if use_ai and ai_mode:
                model = get_gemini_model()
                with st.spinner("AI analyzing..."):
                    res = analyze_task_with_ai(model, task_name)
                    if res:
                        final_diff = res.get("intensity", manual_difficulty)
                        st.info(f"AI Classified as: {final_diff}")
            
            st.session_state.task_list.append((task_name, final_diff))
            st.success("Added!")
            time.sleep(0.5)
            st.rerun()

    if st.button("Clear All"):
        st.session_state.task_list = []
        st.rerun()

# Main Area
if 'task_list' in st.session_state and st.session_state.task_list:
    # 1. Task Queue Display
    st.subheader("📋 Current Task Queue")
    for t, d in st.session_state.task_list:
        icon = ENERGY_MODEL[d]["icon"]
        st.markdown(f"""
        <div class="task-card">
            <strong>{icon} {t}</strong><br>
            <small>{d}</small>
        </div>
        """, unsafe_allow_html=True)

    # 2. Run Button
    if st.button("🚀 Run Agent Scheduler", type="primary", use_container_width=True):
        st.divider()
        final_sched, history, final_fatigue = run_agent_scheduler(st.session_state.task_list)
        
        # 3. Results
        col1, col2 = st.columns([1, 1.5])
        
        with col1:
            st.subheader("Final Schedule")
            df = pd.DataFrame(final_sched)
            st.dataframe(df, use_container_width=True, hide_index=True)
            
            csv = df.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📥 Download Schedule as CSV",
                data=csv,
                file_name="my_optimized_schedule.csv",
                mime="text/csv",
                key='download-csv'
            )
            
        with col2:
            st.subheader("Cognitive Load Analysis")
            chart_data = pd.DataFrame(history)
            st.line_chart(chart_data.set_index("step")["fatigue"])
            
            status_label, status_color = get_fatigue_status(final_fatigue)
            st.markdown(f"""
            <div class="metric-container">
                <h2 style="color: {status_color}">{final_fatigue}%</h2>
                <p>Final Fatigue Level ({status_label})</p>
            </div>
            """, unsafe_allow_html=True)

else:
    st.info("👈 Add tasks in the sidebar to begin!")