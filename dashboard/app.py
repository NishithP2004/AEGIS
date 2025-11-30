"""
AEGIS Dashboard - Automated Answer Script Grading System
A Streamlit-based web interface for submitting answer scripts and viewing grading results.
"""

import streamlit as st
import json
import time
import os
import requests
import redis
from datetime import datetime
from typing import Dict, Optional, List, Any
import pandas as pd
from api_client import AEGISClient

# Configuration
API_BASE_URL = st.secrets.get("API_BASE_URL", "http://localhost:8000")
OCR_SERVER_URL = os.environ.get("OCR_SERVER_URL", st.secrets.get("OCR_SERVER_URL", "http://localhost:5000"))

# Redis Configuration
redis_host = os.environ.get("REDIS_HOST", st.secrets.get("REDIS_HOST", "localhost"))
redis_port = os.environ.get("REDIS_PORT", st.secrets.get("REDIS_PORT", 6379))
redis_user = os.environ.get("REDIS_USERNAME", st.secrets.get("REDIS_USERNAME", ""))
redis_password = os.environ.get("REDIS_PASSWORD", st.secrets.get("REDIS_PASSWORD", ""))

if redis_password:
    if redis_user:
        REDIS_URL = f"redis://{redis_user}:{redis_password}@{redis_host}:{redis_port}/0"
    else:
        REDIS_URL = f"redis://:{redis_password}@{redis_host}:{redis_port}/0"
else:
    REDIS_URL = os.environ.get("REDIS_URL", f"redis://{redis_host}:{redis_port}/0")

AGENT_NAME = "aegis-agent"

# Initialize Client
client = AEGISClient(base_url=API_BASE_URL)

# Page configuration
st.set_page_config(
    page_title="AEGIS - Automated Grading System",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS for better UI
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 1rem;
    }
    .sub-header {
        font-size: 1.2rem;
        color: #666;
        text-align: center;
        margin-bottom: 2rem;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 2rem;
    }
    .stTabs [data-baseweb="tab"] {
        height: 3rem;
        white-space: pre-wrap;
        font-size: 1.1rem;
    }
    .success-box {
        padding: 1rem;
        border-radius: 0.5rem;
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        color: #155724;
    }
    .warning-box {
        padding: 1rem;
        border-radius: 0.5rem;
        background-color: #fff3cd;
        border: 1px solid #ffeaa7;
        color: #856404;
    }
    .error-box {
        padding: 1rem;
        border-radius: 0.5rem;
        background-color: #f8d7da;
        border: 1px solid #f5c6cb;
        color: #721c24;
    }
    .metric-card {
        padding: 1.5rem;
        border-radius: 0.5rem;
        background-color: #f8f9fa;
        border: 1px solid #dee2e6;
        text-align: center;
        color: #333;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'grading_history' not in st.session_state:
    st.session_state.grading_history = []
if 'current_session_id' not in st.session_state:
    st.session_state.current_session_id = None
if 'grading_result' not in st.session_state:
    st.session_state.grading_result = None
if 'ocr_result_key' not in st.session_state:
    st.session_state.ocr_result_key = None


def process_events_to_result(events: List[Dict]) -> Dict:
    """Convert ADK events to the dashboard result format."""
    output = {}
    final_score = "N/A"
    
    # Map agent names to output keys
    agent_mapping = {
        "arbiter_agent": "arbiter_assessment",
        "scrutinizer_agent": "scrutinizer_analysis",
        "validator_agent": "validator_report",
        "mentor_agent": "mentor_feedback"
    }
    
    for event in events:
        author = event.get("author")
        if author in agent_mapping:
            # Extract text content
            content = ""
            if "content" in event and "parts" in event["content"]:
                for part in event["content"]["parts"]:
                    if "text" in part:
                        content += part["text"]
            
            # Append to existing content (in case of multiple messages/chunks)
            key = agent_mapping[author]
            if key in output:
                output[key] += content
            else:
                output[key] = content

    return {
        "status": "completed",
        "final_score": final_score,
        "timestamp": datetime.now().isoformat(),
        "output": output,
        "raw_events": events
    }


def render_header():
    """Render the dashboard header."""
    st.markdown('<div class="main-header">🎓 AEGIS</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="sub-header">Automated Educational Grading Intelligent System</div>',
        unsafe_allow_html=True
    )
    
    # API status indicator
    if client.health_check():
        st.success("✅ API Connected")
    else:
        st.error(f"❌ API Unavailable - Check if the server is running at {API_BASE_URL}")


def format_grading_result(result: Dict) -> None:
    """Display formatted grading results."""
    if not result:
        st.warning("No grading result available.")
        return
    
    # Handle new evaluation format
    if "evaluation" in result:
        eval_data = result["evaluation"]
        final_score = eval_data.get("final_score", "N/A")
        timestamp = result.get("timestamp", datetime.now().isoformat())
        
        st.markdown("### 📊 Grading Results")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown(f"""
            <div class="metric-card">
                <div style="font-size: 14px; color: #666;">Status</div>
                <div style="font-size: 24px; font-weight: 600;">✅ Completed</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown(f"""
            <div class="metric-card">
                <div style="font-size: 14px; color: #666;">Final Score</div>
                <div style="font-size: 24px; font-weight: 600;">{final_score}</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            st.markdown(f"""
            <div class="metric-card">
                <div style="font-size: 14px; color: #666;">Graded At</div>
                <div style="font-size: 24px; font-weight: 600;">{timestamp[:19].replace("T", " ")}</div>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown("---")
        
        # Display detailed feedback
        st.markdown("#### 📝 Evaluation Details")
        
        with st.expander("🔍 Score Reasoning", expanded=True):
            st.markdown(eval_data.get("score_reasoning", "No reasoning provided."))
            
        agent_feedback = eval_data.get("agent_feedback", {})
        if agent_feedback:
            with st.expander("👨‍🏫 Mentor Feedback", expanded=True):
                st.markdown("##### Score Justification")
                st.markdown(agent_feedback.get("score_justification", ""))
                st.markdown("##### Improvement Advice")
                st.markdown(agent_feedback.get("improvement_advice", ""))
                
        # Initial Score comparison
        if "initial_score" in eval_data:
            st.info(f"ℹ️ Initial Assessment Score: {eval_data['initial_score']}")

        with st.expander("🔧 Raw API Response"):
            st.json(result)
        return

    # Extract key information (Legacy format support)
    st.markdown("### 📊 Grading Results")
    
    # Display in columns
    col1, col2, col3 = st.columns(3)
    
    with col1:
        status = "✅ Completed" if result.get("status") == "completed" else "⏳ Processing"
        st.markdown(f"""
        <div class="metric-card">
            <div style="font-size: 14px; color: #666;">Status</div>
            <div style="font-size: 24px; font-weight: 600;">{status}</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        score = result.get("final_score", "N/A")
        st.markdown(f"""
        <div class="metric-card">
            <div style="font-size: 14px; color: #666;">Final Score</div>
            <div style="font-size: 24px; font-weight: 600;">{score}</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        timestamp = result.get("timestamp", datetime.now().isoformat())
        st.markdown(f"""
        <div class="metric-card">
            <div style="font-size: 14px; color: #666;">Graded At</div>
            <div style="font-size: 24px; font-weight: 600;">{timestamp[:19].replace("T", " ")}</div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Display detailed feedback
    if "output" in result:
        output = result["output"]
        
        # Arbiter Assessment
        if "arbiter_assessment" in output:
            with st.expander("🎯 Arbiter - Initial Assessment", expanded=True):
                st.markdown(output["arbiter_assessment"])
        
        # Scrutinizer Analysis
        if "scrutinizer_analysis" in output:
            with st.expander("🔍 Scrutinizer - Detailed Analysis"):
                st.markdown(output["scrutinizer_analysis"])
        
        # Validator Report
        if "validator_report" in output:
            with st.expander("✓ Validator - Quality Check"):
                st.markdown(output["validator_report"])
        
        # Mentor Feedback
        if "mentor_feedback" in output:
            with st.expander("👨‍🏫 Mentor - Personalized Feedback", expanded=True):
                st.markdown(output["mentor_feedback"])
    
    # Raw response (for debugging)
    with st.expander("🔧 Raw API Response"):
        st.json(result)


def get_redis_keys(pattern: str = "student_answer_script:*") -> List[str]:
    """Fetch keys from Redis matching the pattern."""
    try:
        r = redis.from_url(REDIS_URL)
        keys = [k.decode('utf-8') for k in r.keys(pattern)]
        return keys
    except Exception as e:
        st.error(f"Error connecting to Redis: {e}")
        return []


def get_redis_value(key: str) -> Optional[str]:
    """Fetch value from Redis for a given key."""
    try:
        r = redis.from_url(REDIS_URL)
        value = r.get(key)
        if value:
            return value.decode('utf-8')
        return None
    except Exception as e:
        st.error(f"Error fetching from Redis: {e}")
        return None


def process_ocr_upload(files, assignment_id):
    """Handle OCR upload."""
    ocr_url = OCR_SERVER_URL
    
    try:
        with st.spinner("Uploading files to OCR server..."):
            files_payload = []
            for i, f in enumerate(files):
                # Reset pointer just in case
                f.seek(0)
                files_payload.append((f"file{i+1}", (f.name, f.read(), "application/pdf")))
            
            response = requests.post(f"{ocr_url}/ocr", files=files_payload, timeout=60)
            response.raise_for_status()
            
            request_uuid = response.headers.get("X-Request-ID")
            if request_uuid:
                st.success(f"✅ Upload successful! Request ID: {request_uuid}")
                st.info("The file is being processed in the background. Please refresh the list below to see the result.")
            else:
                st.warning("Upload successful, but Server did not return a Request ID.")
            
    except requests.exceptions.ConnectionError:
        st.error(f"❌ Could not connect to OCR server at {ocr_url}")
    except Exception as e:
        st.error(f"❌ Error during upload: {str(e)}")


def render_ocr_tab():
    """Render the OCR and grading tab."""
    st.markdown("### 📄 OCR & Grade")
    st.markdown("Upload two PDF files to process them via OCR and then grade the result.")

    with st.form("ocr_submission_form"):
        # Assignment ID
        assignment_id = st.text_input(
            "Assignment ID *",
            placeholder="e.g., CS101-Assignment-1-OCR",
            help="Unique identifier for this assignment",
            key="ocr_assignment_id_input"
        )
        
        # File Uploader
        uploaded_files = st.file_uploader(
            "Upload Answer Scripts (Select exactly 2 PDF files) *", 
            type="pdf", 
            accept_multiple_files=True,
            key="ocr_files_input"
        )

        submit_ocr = st.form_submit_button("📤 Upload & Process OCR", use_container_width=True)

    if submit_ocr:
        if not assignment_id:
            st.error("⚠️ Assignment ID is required!")
        elif not uploaded_files or len(uploaded_files) != 2:
            st.error("⚠️ Please upload exactly two PDF files.")
        else:
            # Process OCR
            process_ocr_upload(uploaded_files, assignment_id)

    st.markdown("---")
    st.markdown("### 📋 Available OCR Results")
    
    col_refresh, _ = st.columns([1, 4])
    with col_refresh:
        if st.button("🔄 Refresh List"):
            st.rerun()

    # Fetch keys
    keys = get_redis_keys()
    
    if not keys:
        st.info("No processed scripts found in Redis.")
    else:
        # Try to sort by idle time (approximation of recency)
        try:
            r = redis.from_url(REDIS_URL)
            # Sort keys by idle time (ascending) -> most recently touched first
            keys_with_idle = []
            for k in keys:
                try:
                    idle = r.object("idletime", k)
                    keys_with_idle.append((k, idle if idle is not None else float('inf')))
                except:
                    keys_with_idle.append((k, float('inf')))
            
            keys_with_idle.sort(key=lambda x: x[1])
            keys = [k[0] for k in keys_with_idle]
        except Exception:
            pass # Fallback to unsorted if redis connection fails here

        # Display keys
        for key in keys:
            with st.container():
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.code(key, language="text")
                with col2:
                    if st.button("Select", key=f"btn_{key}"):
                        st.session_state.selected_ocr_key = key
                        st.rerun()
        
        st.markdown("---")
        
        # Evaluation Section for Selected Key
        if 'selected_ocr_key' in st.session_state and st.session_state.selected_ocr_key:
            st.markdown(f"### 🚀 Evaluate: `{st.session_state.selected_ocr_key}`")
            
            # Fetch content
            redis_content = get_redis_value(st.session_state.selected_ocr_key)
            
            if redis_content:
                with st.expander("📄 View OCR Content", expanded=True):
                    st.markdown(redis_content, unsafe_allow_html=True)
            else:
                st.error("Could not retrieve content from Redis.")
                redis_content = ""

            # Assignment ID (optional override or use from upload if we tracked it, but we don't track it per key in redis)
            # So we ask for it or use a default
            eval_assignment_id = st.text_input(
                "Assignment ID for Grading",
                value=st.session_state.get("ocr_assignment_id_input", ""),
                help="Identifier for this grading session"
            )
            
            if st.button("Evaluate Answer Script", use_container_width=True):
                if not eval_assignment_id:
                    st.error("⚠️ Please provide an Assignment ID.")
                elif not redis_content:
                    st.error("⚠️ No content to evaluate.")
                else:
                    with st.spinner("🤖 AI Agents are evaluating the OCR result..."):
                        # Use the redis content as the student answer prompt
                        # Rubric is passed as empty string as per user request
                        
                        result = client.evaluate_answer(
                            student_answer=redis_content,
                            rubric="", 
                            assignment_id=eval_assignment_id
                        )
                        
                        if result:
                            if "timestamp" not in result:
                                result["timestamp"] = datetime.now().isoformat()
                            
                            st.session_state.grading_result = result
                            st.session_state.grading_history.append({
                                "assignment_id": eval_assignment_id,
                                "timestamp": result["timestamp"],
                                "result": result
                            })
                            st.success("✅ Grading completed successfully! Check the Results tab.")
                            st.balloons()
                        else:
                            st.error("❌ Grading failed.")


def render_submission_tab():
    """Render the answer submission form."""
    st.markdown("### 📝 Submit Answer Script")
    
    with st.form("answer_submission_form"):
        # Assignment ID
        assignment_id = st.text_input(
            "Assignment ID *",
            placeholder="e.g., CS101-Assignment-1",
            help="Unique identifier for this assignment"
        )
        
        # Rubric/Answer Key
        rubric = st.text_area(
            "Grading Rubric / Answer Key *",
            height=250,
            placeholder="Enter the grading rubric or answer key here...",
            help="Detailed rubric with scoring criteria and expected answers"
        )

        # Student Answer
        student_answer = st.text_area(
            "Student Answer *",
            height=250,
            placeholder="Enter the student's answer here...",
            help="The student's complete answer to be graded"
        )
        
        # Submit button
        submitted = st.form_submit_button("🚀 Submit for Grading", use_container_width=True)
        
        if submitted:
            # Validation
            if not assignment_id or not student_answer or not rubric:
                st.error("⚠️ All fields are required!")
                return
            
            # Show progress
            st.markdown("### 🔄 Grading Progress")
            
            try:
                with st.spinner("🤖 AI Agents are evaluating the answer... This may take a minute."):
                    # Call the new evaluate endpoint
                    result = client.evaluate_answer(student_answer, rubric, assignment_id)
                
                if result:
                    # Add timestamp if not present
                    if "timestamp" not in result:
                        result["timestamp"] = datetime.now().isoformat()
                        
                    st.session_state.grading_result = result
                    st.session_state.grading_history.append({
                        "assignment_id": assignment_id,
                        "timestamp": result["timestamp"],
                        "result": result
                    })
                    st.success("✅ Grading completed successfully!")
                    st.balloons()
                else:
                    st.error("❌ Grading failed. No result produced.")
                    
            except Exception as e:
                st.error(f"Error during grading: {str(e)}")


def render_results_tab():
    """Render the grading results view."""
    st.markdown("### 📊 Grading Results")
    
    if st.session_state.grading_result:
        format_grading_result(st.session_state.grading_result)
        
        # Option to download results
        if st.button("📥 Download Results as JSON"):
            json_str = json.dumps(st.session_state.grading_result, indent=2)
            st.download_button(
                label="Download JSON",
                data=json_str,
                file_name=f"grading_result_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json"
            )
    else:
        st.info("ℹ️ No grading results yet. Submit an answer in the 'Submit' tab to get started.")


def render_history_tab():
    """Render the grading history view."""
    st.markdown("### 📚 Grading History")
    
    if not st.session_state.grading_history:
        st.info("ℹ️ No grading history yet. Submit answers to build your history.")
        return
    
    # Convert history to DataFrame for better display
    history_data = []
    for item in st.session_state.grading_history:
        history_data.append({
            "Assignment ID": item["assignment_id"],
            "Timestamp": item["timestamp"][:19].replace("T", " "),
            "Status": "Completed"
        })
    
    df = pd.DataFrame(history_data)
    st.dataframe(df, use_container_width=True)
    
    # Option to view individual results
    st.markdown("---")
    st.markdown("#### View Individual Results")
    
    selected_idx = st.selectbox(
        "Select a grading session:",
        range(len(st.session_state.grading_history)),
        format_func=lambda x: f"{st.session_state.grading_history[x]['assignment_id']} - {st.session_state.grading_history[x]['timestamp'][:19]}"
    )
    
    if st.button("View Details"):
        selected_result = st.session_state.grading_history[selected_idx]["result"]
        format_grading_result(selected_result)


def render_analytics_tab():
    """Render analytics and statistics."""
    st.markdown("### 📈 Analytics & Statistics")
    
    if not st.session_state.grading_history:
        st.info("ℹ️ No data available yet. Submit answers to see analytics.")
        return
    
    # Basic statistics
    total_graded = len(st.session_state.grading_history)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <div style="font-size: 14px; color: #666;">Total Graded</div>
            <div style="font-size: 24px; font-weight: 600;">{total_graded}</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        today_count = len([h for h in st.session_state.grading_history 
                                 if h["timestamp"][:10] == datetime.now().isoformat()[:10]])
        st.markdown(f"""
        <div class="metric-card">
            <div style="font-size: 14px; color: #666;">Today</div>
            <div style="font-size: 24px; font-weight: 600;">{today_count}</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div class="metric-card">
            <div style="font-size: 14px; color: #666;">Success Rate</div>
            <div style="font-size: 24px; font-weight: 600;">100%</div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Timeline chart
    st.markdown("#### Grading Activity Timeline")
    timeline_data = pd.DataFrame([
        {"Time": h["timestamp"][:19], "Count": 1} 
        for h in st.session_state.grading_history
    ])
    
    if not timeline_data.empty:
        st.line_chart(timeline_data.set_index("Time"))


def main():
    """Main dashboard application."""
    # Render header
    render_header()
    
    # Sidebar
    with st.sidebar:
        st.markdown("## ⚙️ Settings")
        
        # API URL configuration
        api_url = st.text_input(
            "API Base URL",
            value=API_BASE_URL,
            help="The base URL of the AEGIS API server"
        )
        
        st.markdown("---")
        
        st.markdown("## 📊 Quick Stats")
        
        graded_today = len([h for h in st.session_state.grading_history 
                                         if h["timestamp"][:10] == datetime.now().isoformat()[:10]])
        st.markdown(f"""
        <div class="metric-card" style="padding: 1rem; margin-bottom: 1rem;">
            <div style="font-size: 14px; color: #666;">Graded Today</div>
            <div style="font-size: 24px; font-weight: 600;">{graded_today}</div>
        </div>
        """, unsafe_allow_html=True)
        
        total_history = len(st.session_state.grading_history)
        st.markdown(f"""
        <div class="metric-card" style="padding: 1rem;">
            <div style="font-size: 14px; color: #666;">Total History</div>
            <div style="font-size: 24px; font-weight: 600;">{total_history}</div>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("---")
        
        # Clear history button
        if st.button("🗑️ Clear History", use_container_width=True):
            st.session_state.grading_history = []
            st.session_state.grading_result = None
            st.success("History cleared!")
            st.rerun()
    
    # Main tabs
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📝 Submit",
        "📄 OCR & Grade",
        "📊 Results",
        "📚 History",
        "📈 Analytics"
    ])
    
    with tab1:
        render_submission_tab()

    with tab2:
        render_ocr_tab()
    
    with tab3:
        render_results_tab()
    
    with tab4:
        render_history_tab()
    
    with tab5:
        render_analytics_tab()
    
    # Footer
    st.markdown("---")
    st.markdown(
        "<div style='text-align: center; color: #666;'>"
        "AEGIS - Automated Educational Grading Intelligent System | "
        f"© {datetime.now().year} | Powered by AI"
        "</div>",
        unsafe_allow_html=True
    )


if __name__ == "__main__":
    main()
