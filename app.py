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
    
    /* Energy meter styling */
    .energy-meter {
        background: linear-gradient(90deg, #00ff88, #ffcc00, #ff4444);
        height: 20px;
        border-radius: 10px;
        margin: 1rem 0;
    }
    
    /* Status badges */
    .badge-high { background: #ff4757; padding: 5px 15px; border-radius: 20px; color: white; }
    .badge-medium { background: #ffa502; padding: 5px 15px; border-radius: 20px; color: white; }
    .badge-low { background: #2ed573; padding: 5px 15px; border-radius: 20px; color: white; }
    .badge-break { background: #3742fa; padding: 5px 15px; border-radius: 20px; color: white; }
    
    /* Sidebar styling */
    .css-1d391kg { background: rgba(26, 26, 46, 0.95); }
    
    /* Button styling */
    .stButton > button {
        background: linear-gradient(90deg, #00d2ff, #3a7bd5);
        color: white;
        border: none;
        border-radius: 25px;
        padding: 0.75rem 2rem;
        font-weight: bold;
        transition: all 0.3s ease;
    }
    
    .stButton > button:hover {
        transform: scale(1.05);
        box-shadow: 0 5px 20px rgba(0, 210, 255, 0.4);
    }
    
    /* Metric cards */
    .metric-container {
        background: rgba(255, 255, 255, 0.05);
        border-radius: 15px;
        padding: 1rem;
        text-align: center;
        border: 1px solid rgba(255, 255, 255, 0.1);
    }
    
    /* Agent log styling */
    .agent-log {
        background: rgba(0, 0, 0, 0.3);
        border-left: 4px solid #00d2ff;
        padding: 1rem;
        margin: 0.5rem 0;
        border-radius: 0 10px 10px 0;
    }
</style>
""", unsafe_allow_html=True)

# --- GEMINI AI CONFIGURATION ---
def get_gemini_model():
    """Get or create Gemini model from session state"""
    if 'gemini_model' in st.session_state and st.session_state.gemini_model:
        # Recreate model to ensure it's using correct version
        if 'gemini_api_key' in st.session_state and st.session_state.gemini_api_key:
            try:
                genai.configure(api_key=st.session_state.gemini_api_key)
                return genai.GenerativeModel('gemini-2.0-flash')
            except:
                return st.session_state.gemini_model
        return st.session_state.gemini_model
    return None

def configure_gemini_with_key(api_key):
    """Configure Gemini AI with provided API key"""
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-2.0-flash')
        st.session_state.gemini_model = model
        st.session_state.gemini_api_key = api_key
        return model
    except Exception as e:
        st.error(f"Failed to configure Gemini: {e}")
        return None

def analyze_task_with_ai(model, task_name):
    """Use Gemini AI to analyze task and determine intensity"""
    prompt = f"""Analyze this task and determine its mental intensity level.
Task: "{task_name}"

Classify into ONE of these categories and explain why:
1. "High Intensity (Coding/Math)" - Complex problem-solving, coding, mathematics, deep analysis
2. "Medium Intensity (Theory/Reading)" - Reading, research, learning concepts, documentation
3. "Low Intensity (Meeting/Email)" - Emails, meetings, routine tasks, administrative work

Respond in JSON format:
{{"intensity": "category name exactly as shown above", "reason": "brief explanation", "tips": "one wellbeing tip for this task"}}
"""
    try:
        response = model.generate_content(prompt)
        # Extract JSON from response
        text = response.text
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

Provide 3 personalized recommendations to improve wellbeing and productivity.
Keep each recommendation under 50 words. Be specific and actionable.

Respond in JSON format:
{{"recommendations": ["recommendation 1", "recommendation 2", "recommendation 3"], "overall_assessment": "brief 1-sentence assessment"}}
"""
    try:
        # Recreate model to ensure correct version
        if 'gemini_api_key' in st.session_state:
            genai.configure(api_key=st.session_state.gemini_api_key)
            fresh_model = genai.GenerativeModel('gemini-2.0-flash')
            response = fresh_model.generate_content(prompt)
        else:
            response = model.generate_content(prompt)
        text = response.text
        json_match = re.search(r'\{.*\}', text, re.DOTALL)
        if json_match:
            return json.loads(json_match.group())
    except Exception as e:
        st.error(f"AI Recommendations failed: {e}")
    return None

def get_break_activity_suggestion(model, recent_tasks):
    """AI suggests what to do during a break based on recent tasks"""
    prompt = f"""Based on these recent tasks: {recent_tasks}
Suggest ONE specific 5-minute break activity that would help mental recovery.
Be creative and specific. Response should be under 30 words, just the activity description."""
    try:
        response = model.generate_content(prompt)
        return response.text.strip()
    except:
        return "Take a short walk or do some stretching exercises."

# --- 1. THE AGENT'S INTERNAL MODEL (The "Brain") ---
ENERGY_MODEL = {
    "High Intensity (Coding/Math)": {"cost": 35, "icon": "●", "color": "#ff4757"},
    "Medium Intensity (Theory/Reading)": {"cost": 15, "icon": "●", "color": "#ffa502"},
    "Low Intensity (Meeting/Email)": {"cost": 5, "icon": "●", "color": "#2ed573"},
    "Recovery Break": {"cost": -25, "icon": "●", "color": "#3742fa"}
}

MAX_FATIGUE_LIMIT = 80

def get_fatigue_color(fatigue):
    """Returns color based on fatigue level"""
    if fatigue < 30: return "#2ed573"  # Green
    elif fatigue < 60: return "#ffa502"  # Orange
    else: return "#ff4757"  # Red

def get_fatigue_status(fatigue):
    """Returns status text based on fatigue level"""
    if fatigue < 30: return "Optimal"
    elif fatigue < 50: return "Moderate"
    elif fatigue < 70: return "Elevated"
    else: return "Critical"

def run_agent_scheduler(tasks):
    """Deliberative Agent logic with enhanced visualization"""
    schedule = []
    fatigue_history = [{"step": 0, "fatigue": 0, "event": "Start"}]
    current_fatigue = 0
    
    log_container = st.container()
    
    with log_container:
        st.markdown("### Agent Processing...")
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        for idx, (task_name, difficulty) in enumerate(tasks):
            # Simulate processing time for effect
            time.sleep(0.3)
            progress_bar.progress((idx + 1) / len(tasks))
            
            energy_cost = ENERGY_MODEL[difficulty]["cost"]
            
            # AGENT REASONING: Check if this task causes burnout
            if current_fatigue + energy_cost > MAX_FATIGUE_LIMIT:
                status_text.markdown(f"""
                <div class="agent-log">
                    ⚠️ <strong>ALERT:</strong> Fatigue at {current_fatigue}% → Adding '{task_name}' = {current_fatigue + energy_cost}%
                    <br>🛡️ <strong>PROTECTIVE ACTION:</strong> Inserting Recovery Break
                </div>
                """, unsafe_allow_html=True)
                
                time.sleep(0.5)
                
                schedule.append({
                    "Step": len(schedule) + 1,
                    "Task": "RECOVERY BREAK",
                    "Type": "Agent Intervention",
                    "Energy": "-25",
                    "Fatigue": max(0, current_fatigue - 25)
                })
                current_fatigue = max(0, current_fatigue - 25)
                fatigue_history.append({
                    "step": len(fatigue_history),
                    "fatigue": current_fatigue,
                    "event": "Recovery Break"
                })
            
            # Add the actual task
            current_fatigue += energy_cost
            schedule.append({
                "Step": len(schedule) + 1,
                "Task": task_name,
                "Type": "User Task",
                "Energy": f"+{energy_cost}",
                "Fatigue": current_fatigue
            })
            fatigue_history.append({
                "step": len(fatigue_history),
                "fatigue": current_fatigue,
                "event": task_name
            })
        
        status_text.markdown("""
        <div class="agent-log">
            ✅ <strong>OPTIMIZATION COMPLETE</strong> - Schedule is burnout-proof!
        </div>
        """, unsafe_allow_html=True)
    
    return schedule, fatigue_history, current_fatigue

# --- 2. THE USER INTERFACE ---

# Header
st.markdown('<h1 class="main-header">AI Burnout Prevention Agent</h1>', unsafe_allow_html=True)
st.markdown("""
<p style="text-align: center; color: #888; font-size: 1.1rem;">
    A Deliberative AI Agent that protects your cognitive wellbeing by intelligently scheduling recovery breaks
</p>
""", unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.markdown("## Task Control Center")
    st.markdown("---")
    
    # AI Configuration Section
    st.markdown("### 🤖 AI Configuration")
    
    # Check if already configured
    gemini_model = get_gemini_model()
    
    if not gemini_model:
        api_key_input = st.text_input("Enter Gemini API Key", type="password", 
                                       help="Get your free API key from https://aistudio.google.com/app/apikey")
        if api_key_input:
            with st.spinner("Connecting to AI..."):
                gemini_model = configure_gemini_with_key(api_key_input)
            if gemini_model:
                st.success("✅ AI Connected!")
                time.sleep(0.5)
                st.rerun()
    else:
        st.success("✅ AI Connected")
        if st.button("🔄 Reset API Key", use_container_width=True):
            st.session_state.gemini_model = None
            st.session_state.gemini_api_key = None
            st.rerun()
    
    ai_enabled = gemini_model is not None
    
    st.markdown("---")
    
    # Task input
    st.markdown("### Add New Task")
    task_input = st.text_input("Task Name", placeholder="e.g., Learn Neural Networks")
    
    # AI Auto-classify option
    use_ai_classify = st.checkbox("🧠 AI Auto-classify intensity", value=ai_enabled, disabled=not ai_enabled)
    
    difficulty_options = [k for k in ENERGY_MODEL.keys() if "Recovery" not in k]
    
    if use_ai_classify and ai_enabled:
        difficulty_input = st.selectbox("Mental Intensity", difficulty_options, 
                                         help="AI will suggest intensity when you add the task")
    else:
        difficulty_input = st.selectbox("Mental Intensity", difficulty_options)
    
    col1, col2 = st.columns(2)
    with col1:
        add_btn = st.button("Add Task", use_container_width=True)
    with col2:
        clear_btn = st.button("Clear All", use_container_width=True)
    
    # Session State
    if 'task_list' not in st.session_state:
        st.session_state.task_list = []
    
    if 'ai_insights' not in st.session_state:
        st.session_state.ai_insights = {}
    
    if add_btn and task_input:
        final_difficulty = difficulty_input
        
        # AI Classification
        if use_ai_classify and ai_enabled and gemini_model:
            with st.spinner("🧠 AI analyzing task..."):
                ai_result = analyze_task_with_ai(gemini_model, task_input)
                if ai_result:
                    final_difficulty = ai_result.get("intensity", difficulty_input)
                    st.session_state.ai_insights[task_input] = ai_result
                    st.info(f"🤖 AI classified as: **{final_difficulty.split('(')[0].strip()}**")
                    st.caption(f"Reason: {ai_result.get('reason', 'N/A')}")
                    st.caption(f"💡 Tip: {ai_result.get('tips', 'N/A')}")
        
        st.session_state.task_list.append((task_input, final_difficulty))
        st.success(f"Added: {task_input}")
    
    if clear_btn:
        st.session_state.task_list = []
        st.rerun()
    
    # Show task queue
    st.markdown("---")
    st.markdown("### Task Queue")
    
    if st.session_state.task_list:
        for idx, (t, d) in enumerate(st.session_state.task_list):
            icon = ENERGY_MODEL[d]["icon"]
            st.markdown(f"""
            <div class="task-card">
                <strong>{icon} {t}</strong><br>
                <small style="color: #888;">{d}</small>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info("No tasks added yet")
    
    # Energy model reference
    st.markdown("---")
    st.markdown("### Energy Cost Reference")
    for name, data in ENERGY_MODEL.items():
        cost = data["cost"]
        color = data["color"]
        icon = data["icon"]
        sign = "+" if cost > 0 else ""
        st.markdown(f"""
        <div style="display: flex; justify-content: space-between; padding: 5px 0;">
            <span>{icon} {name.split('(')[0]}</span>
            <span style="color: {color}; font-weight: bold;">{sign}{cost}</span>
        </div>
        """, unsafe_allow_html=True)

# Main Content Area
if st.session_state.task_list:
    # Metrics Row
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Tasks Queued", len(st.session_state.task_list))
    with col2:
        total_energy = sum(ENERGY_MODEL[d]["cost"] for _, d in st.session_state.task_list)
        st.metric("Total Energy Cost", f"+{total_energy}")
    with col3:
        high_intensity = sum(1 for _, d in st.session_state.task_list if "High" in d)
        st.metric("High Intensity Tasks", high_intensity)
    with col4:
        st.metric("Fatigue Limit", f"{MAX_FATIGUE_LIMIT}%")
    
    st.markdown("---")
    
    # Run Button
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        run_btn = st.button("Run Agent Optimizer", use_container_width=True, type="primary")
    
    if run_btn:
        st.markdown("---")
        
        # Run the agent
        final_schedule, fatigue_history, final_fatigue = run_agent_scheduler(st.session_state.task_list)
        
        st.markdown("---")
        
        # Results Section
        col1, col2 = st.columns([1, 1])
        
        with col1:
            st.markdown("### Optimized Schedule")
            
            df = pd.DataFrame(final_schedule)
            
            # Style the dataframe
            def highlight_breaks(row):
                if "BREAK" in str(row["Task"]):
                    return ['background-color: rgba(55, 66, 250, 0.3)'] * len(row)
                return [''] * len(row)
            
            styled_df = df.style.apply(highlight_breaks, axis=1)
            st.dataframe(styled_df, use_container_width=True, hide_index=True)
        
        with col2:
            st.markdown("### Cognitive Load Analysis")
            
            # Create chart data
            chart_df = pd.DataFrame(fatigue_history)
            
            # Line chart with Streamlit
            st.line_chart(chart_df.set_index("step")["fatigue"], use_container_width=True)
            
            # Final status
            status = get_fatigue_status(final_fatigue)
            color = get_fatigue_color(final_fatigue)
            
            st.markdown(f"""
            <div style="text-align: center; padding: 1rem; background: rgba(255,255,255,0.05); border-radius: 15px;">
                <h2 style="color: {color};">{status}</h2>
                <h3>Final Fatigue: {final_fatigue}%</h3>
                <p style="color: #888;">{"Within optimal range" if final_fatigue < 50 else "Schedule optimized for sustainability"}</p>
            </div>
            """, unsafe_allow_html=True)
        
        # Summary cards
        st.markdown("---")
        st.markdown("### Session Summary")
        
        breaks_inserted = sum(1 for s in final_schedule if "BREAK" in s["Task"])
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown(f"""
            <div class="metric-container">
                <h2>{breaks_inserted}</h2>
                <p>Recovery Breaks Inserted</p>
            </div>
            """, unsafe_allow_html=True)
        with col2:
            st.markdown(f"""
            <div class="metric-container">
                <h2>{final_fatigue}%</h2>
                <p>Final Cognitive Load</p>
            </div>
            """, unsafe_allow_html=True)
        with col3:
            burnout_prevented = "Yes" if breaks_inserted > 0 else "Not Required"
            st.markdown(f"""
            <div class="metric-container">
                <h2>{burnout_prevented}</h2>
                <p>Burnout Prevented</p>
            </div>
            """, unsafe_allow_html=True)
        
        st.success("Schedule optimization complete. The AI agent has ensured sustainable cognitive load throughout your day.")
        
        # AI Recommendations Section
        if ai_enabled and gemini_model:
            st.markdown("---")
            st.markdown("### 🤖 AI-Powered Recommendations")
            
            with st.spinner("Generating personalized recommendations..."):
                ai_recs = get_ai_recommendations(gemini_model, st.session_state.task_list, final_fatigue)
            
            if ai_recs:
                st.markdown(f"""
                <div style="background: rgba(0, 210, 255, 0.1); padding: 1rem; border-radius: 10px; border-left: 4px solid #00d2ff; margin-bottom: 1rem;">
                    <strong>📊 Overall Assessment:</strong> {ai_recs.get('overall_assessment', 'N/A')}
                </div>
                """, unsafe_allow_html=True)
                
                rec_cols = st.columns(3)
                for idx, rec in enumerate(ai_recs.get('recommendations', [])):
                    with rec_cols[idx]:
                        st.markdown(f"""
                        <div class="task-card">
                            <h4>💡 Tip {idx + 1}</h4>
                            <p style="color: #ccc;">{rec}</p>
                        </div>
                        """, unsafe_allow_html=True)

else:
    # Empty state
    st.markdown("""
    <div style="text-align: center; padding: 4rem 2rem; background: rgba(255,255,255,0.02); border-radius: 20px; border: 2px dashed rgba(255,255,255,0.1);">
        <h2 style="color: #00d2ff;">Ready to Optimize Your Schedule</h2>
        <p style="color: #888; font-size: 1.1rem;">
            Add your tasks in the sidebar and let the <strong>Gemini AI</strong> create<br>
            a burnout-proof schedule tailored to your cognitive limits.
        </p>
        <br>
        <p style="color: #666;">
            Start by adding tasks in the <strong>Task Control Center</strong>
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Feature highlights
    st.markdown("---")
    st.markdown("### How It Works (Now Powered by AI!)")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        <div class="task-card" style="text-align: center;">
            <h4>1. Add Tasks</h4>
            <p style="color: #888;">Input your tasks - <strong>AI auto-classifies</strong> intensity using Gemini</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="task-card" style="text-align: center;">
            <h4>2. AI Analysis</h4>
            <p style="color: #888;"><strong>Gemini AI</strong> analyzes cognitive load and detects burnout risks</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
        <div class="task-card" style="text-align: center;">
            <h4>3. Smart Recommendations</h4>
            <p style="color: #888;"><strong>AI-generated</strong> personalized wellbeing tips and break suggestions</p>
        </div>
        """, unsafe_allow_html=True)