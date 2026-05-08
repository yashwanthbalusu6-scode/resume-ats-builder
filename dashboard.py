"""
🚀 ATS Resume & Job Application Suite
A professional, portfolio-ready Streamlit application.
"""

import os
import tempfile
from datetime import datetime
from typing import Any, Dict, Optional

import pandas as pd
import streamlit as st

from ai_client import detect_provider, has_any_key
from ats_scorer import ATSScorer
from cover_letter_generator import CoverLetterGenerator
from database import ApplicationRecord, get_session, init_db
from error_handler import handle_error
from interview_prep import InterviewPrepGenerator
from job_parser import JobParser
from resume_optimizer import ResumeOptimizer
from resume_parser import ResumeParser

# ── Page Configuration ───────────────────────────────────────────────────────
st.set_page_config(
    page_title="ATS Resume Suite | Professional Optimizer",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS for Portfolio Polish ──────────────────────────────────────────
st.markdown("""
    <style>
    .main {
        background-color: #f8f9fa;
    }
    .stButton>button {
        border-radius: 8px;
        font-weight: 600;
        transition: all 0.3s;
    }
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(0,0,0,0.1);
    }
    .header-container {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2.5rem;
        border-radius: 12px;
        color: white;
        margin-bottom: 2rem;
        box-shadow: 0 10px 20px rgba(0,0,0,0.1);
    }
    .footer {
        text-align: center;
        padding: 2rem;
        color: #6c757d;
        font-size: 0.9rem;
        border-top: 1px solid #dee2e6;
        margin-top: 4rem;
    }
    .metric-card {
        background: white;
        padding: 1.5rem;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        border: 1px solid #eee;
    }
    </style>
""", unsafe_allow_html=True)

# ── Session State Initialization ──────────────────────────────────────────────
def init_session_state():
    st.session_state.setdefault("resume_text", "")
    st.session_state.setdefault("job_desc", "")
    st.session_state.setdefault("api_key", "")
    st.session_state.setdefault("ats_result", None)
    st.session_state.setdefault("optimized_result", None)
    st.session_state.setdefault("cover_letter_result", None)
    st.session_state.setdefault("interview_result", None)
    st.session_state.setdefault("yep_api_key", "")
    st.session_state.setdefault("anthropic_api_key", "")

init_session_state()

# Initialize Database
try:
    init_db()
except Exception as e:
    st.error(f"Database initialization error: {e}")

# ── Helpers ──────────────────────────────────────────────────────────────────
def _ai_keys() -> Dict[str, Optional[str]]:
    key = st.session_state.api_key.strip()
    if key.startswith("yep_"):
        return {"yep_api_key": key, "anthropic_api_key": None}
    return {"yep_api_key": None, "anthropic_api_key": key}

def _get_score_color(score: int) -> str:
    if score < 60: return "red"
    if score < 80: return "orange"
    return "green"

SAMPLE_RESUME = """John Doe
Software Engineer | john.doe@email.com | (555) 123-4567

EXPERIENCE
Senior Backend Engineer — TechCorp (2021-Present)
- Led development of Python microservices using FastAPI and PostgreSQL
- Optimized database queries, reducing latency by 40%
- Mentored junior developers and implemented CI/CD pipelines

Software Developer — StartupInc (2018-2021)
- Built responsive web applications using React and Node.js
- Integrated third-party APIs and managed AWS infrastructure

SKILLS
Python, FastAPI, Django, PostgreSQL, Docker, Kubernetes, AWS, Git, React

EDUCATION
B.S. Computer Science — State University
"""

SAMPLE_JOB = """Senior Python Developer

We are looking for a Senior Python Developer to join our backend team. 

Responsibilities:
- Design and implement scalable backend services using Python and FastAPI
- Work with PostgreSQL databases and optimize query performance
- Containerize applications with Docker and deploy to Kubernetes/AWS
- Collaborate with frontend teams to integrate REST APIs

Requirements:
- 5+ years of experience in Python development
- Strong knowledge of FastAPI or Django
- Experience with PostgreSQL and database design
- Familiarity with AWS and CI/CD practices
"""

# ── Sidebar ──────────────────────────────────────────────────────────────────
with st.sidebar:
    st.title("⚙️ Configuration")
    
    st.markdown("### 🔑 API Key")
    api_key = st.text_input(
        "Enter Provider Key",
        value=st.session_state.api_key,
        type="password",
        placeholder="AIza... (Gemini) or sk-...",
        help="Get a FREE Gemini key at aistudio.google.com/apikey"
    )
    st.session_state.api_key = api_key
    
    if api_key:
        provider = detect_provider(api_key)
        st.success(f"Detected: {provider}")
    else:
        st.info("💡 Use Google Gemini for a FREE experience!")

    st.markdown("---")
    st.markdown("### 🔗 Quick Links")
    st.markdown("- [Get Free Gemini Key](https://aistudio.google.com/apikey)")
    st.markdown("- [Hiring? Contact Me](https://linkedin.com/in/yashwanth-Balusu)")
    st.markdown("- [Source Code](https://github.com/yashwanthbalusu6-scode/resume-ats-builder)")

    if st.button("🧹 Clear All Data", use_container_width=True, type="secondary"):
        for key in ["resume_text", "job_desc", "ats_result", "optimized_result", "cover_letter_result", "interview_result"]:
            if key in st.session_state:
                del st.session_state[key]
            st.session_state[key] = "" if "text" in key or "desc" in key else None
        st.rerun()

# ── Header & Hero ────────────────────────────────────────────────────────────
st.markdown("""
    <div class="header-container">
        <h1 style='margin:0;'>🚀 ATS Resume & Job Application Suite</h1>
        <p style='font-size:1.2rem; opacity:0.9; margin-top:0.5rem;'>
            Optimize your resume, beat the bots, and land your dream job with AI.
        </p>
    </div>
""", unsafe_allow_html=True)

# ── Main Tabs ────────────────────────────────────────────────────────────────
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "🎯 Resume Optimizer", 
    "💌 Cover Letter", 
    "🎤 Interview Prep", 
    "📊 Tracker", 
    "📈 Analytics"
])

# ── Tab 1: Resume Optimizer ──────────────────────────────────────────────────
with tab1:
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📝 Your Resume")
        uploaded = st.file_uploader(
            "📤 Upload resume (PDF or DOCX)",
            type=["pdf", "docx"],
            help="Supports PDF and DOCX. Text-based PDFs work best.",
            key="resume_uploader",
        )

        if uploaded is not None:
            try:
                suffix = os.path.splitext(uploaded.name)[1] or ".pdf"
                with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
                    tmp.write(uploaded.getvalue())
                    tmp_path = tmp.name
                try:
                    parser = ResumeParser(tmp_path)
                    parsed = parser.parse()
                    if parsed.get("error"):
                        st.error(f"❌ {parsed['error']}")
                    elif parsed.get("full_text", "").strip():
                        extracted = parsed["full_text"]
                        if "resume_text" in st.session_state:
                            del st.session_state["resume_text"]
                        st.session_state["resume_text"] = extracted
                        st.success(f"✅ Extracted {len(extracted)} chars from {uploaded.name}")
                        st.rerun()
                finally:
                    try:
                        os.unlink(tmp_path)
                    except Exception:
                        pass
            except Exception as e:
                err = handle_error(e, "Resume Upload")
                st.error(err["error"])
                st.info(f"💡 {err['suggestion']}")

        if st.button("📋 Use Sample Resume", key="sample_res"):
            if "resume_text" in st.session_state:
                del st.session_state["resume_text"]
            st.session_state.resume_text = SAMPLE_RESUME
            st.rerun()

        st.text_area(
            "Or Paste Resume Text",
            height=300,
            key="resume_text",
            placeholder="Resume content will appear here after upload, or paste manually...",
        )
        st.caption(f"Characters: {len(st.session_state.get('resume_text', ''))}")

    with col2:
        st.subheader("💼 Job Description")
        if st.button("📋 Use Sample Job", key="sample_job"):
            if "job_desc" in st.session_state:
                del st.session_state["job_desc"]
            st.session_state.job_desc = SAMPLE_JOB
            st.rerun()
            
        st.text_area(
            "Paste Job Description Here",
            height=390,
            key="job_desc",
            placeholder="Paste the full job posting...",
        )
        st.caption(f"Characters: {len(st.session_state.get('job_desc', ''))}")

    st.markdown("---")
    
    resume_ready = bool(st.session_state.get("resume_text", "").strip())
    job_ready = bool(st.session_state.get("job_desc", "").strip())
    has_inputs = resume_ready and job_ready
    has_key = bool(st.session_state.api_key.strip())
    
    btn_col1, btn_col2 = st.columns(2)
    
    with btn_col1:
        if st.button(
            "📊 Calculate ATS Score (FREE)",
            disabled=not has_inputs,
            use_container_width=True,
            type="primary"
        ):
            try:
                with st.spinner("Analyzing keywords and formatting..."):
                    scorer = ATSScorer(st.session_state.resume_text, st.session_state.job_desc)
                    st.session_state.ats_result = scorer.score()
                    st.toast("Analysis Complete!", icon="✅")
            except Exception as e:
                st.session_state.ats_result = handle_error(e, "ATS Scoring")

    with btn_col2:
        if st.button("🤖 AI Optimize Resume", use_container_width=True, disabled=not (has_inputs and has_key)):
            try:
                with st.spinner("AI is rewriting your resume for maximum impact..."):
                    opt = ResumeOptimizer(st.session_state.resume_text, st.session_state.job_desc, **_ai_keys())
                    st.session_state.optimized_result = opt.optimize()
                    st.toast("Resume Optimized!", icon="✨")
            except Exception as e:
                st.session_state.optimized_result = handle_error(e, "AI Optimization")

    # Results Display
    if st.session_state.ats_result:
        res = st.session_state.ats_result
        if res.get("error"):
            st.error(res["error"])
            if res.get("suggestion"):
                st.info(f"💡 {res['suggestion']}")
        else:
            st.markdown("### 📊 ATS Analysis Results")
            score = res["overall"]
            color = _get_score_color(score)
            
            st.markdown(f"<h2 style='text-align:center; color:{color};'>Overall Match: {score}%</h2>", unsafe_allow_html=True)
            st.progress(score / 100)
            
            m1, m2, m3, m4 = st.columns(4)
            m1.metric("Keywords", f"{res['keywords']}%")
            m2.metric("Formatting", f"{res['formatting']}%")
            m3.metric("Sections", f"{res['sections']}%")
            m4.metric("Readability", f"{res['readability']}%")

    if st.session_state.optimized_result:
        opt = st.session_state.optimized_result
        if opt.get("error"):
            st.error(opt["error"])
            if opt.get("suggestion"):
                st.info(f"💡 {opt['suggestion']}")
        else:
            st.markdown("---")
            st.markdown("### ✨ AI Optimized Content")
            st.markdown(opt["optimized"])
            st.download_button(
                "⬇️ Download Optimized Resume",
                data=opt["optimized"],
                file_name="optimized_resume.md",
                mime="text/markdown",
                use_container_width=True
            )

# ── Tab 2: Cover Letter ──────────────────────────────────────────────────────
with tab2:
    st.subheader("💌 AI Cover Letter Generator")
    c1, c2 = st.columns([2, 1])
    
    with c1:
        cl_company = st.text_input("Company Name", placeholder="e.g. Google")
        cl_role = st.text_input("Target Role", placeholder="e.g. Senior Software Engineer")
    with c2:
        cl_tone = st.selectbox("Tone", ["Formal", "Enthusiastic", "Professional", "Creative"])
    
    if st.button("✨ Generate My Cover Letter", use_container_width=True, type="primary", disabled=not (has_inputs and has_key)):
        try:
            with st.spinner("Writing a winning cover letter..."):
                gen = CoverLetterGenerator(st.session_state.resume_text, st.session_state.job_desc, cl_company, cl_role, **_ai_keys())
                st.session_state.cover_letter_result = gen.generate(tone=cl_tone.lower())
                st.toast("Generated!", icon="💌")
        except Exception as e:
            st.session_state.cover_letter_result = handle_error(e, "Cover Letter Generation")

    if st.session_state.cover_letter_result:
        res = st.session_state.cover_letter_result
        if res.get("error"):
            st.error(res["error"])
            if res.get("suggestion"):
                st.info(f"💡 {res['suggestion']}")
        else:
            st.markdown(res["letter"])
            st.download_button("⬇️ Download Cover Letter", res["letter"], "cover_letter.md", use_container_width=True)

# ── Tab 3: Interview Prep ────────────────────────────────────────────────────
with tab3:
    st.subheader("🎤 Interview Preparation")
    st.info("AI will generate questions based on your resume and the job description.")
    
    if st.button("🎯 Generate Interview Guide", use_container_width=True, type="primary", disabled=not (has_inputs and has_key)):
        try:
            with st.spinner("Preparing interview questions and STAR-format answers..."):
                prep = InterviewPrepGenerator(st.session_state.resume_text, st.session_state.job_desc, "Company", "Role", **_ai_keys())
                st.session_state.interview_result = prep.generate()
                st.toast("Guide Ready!", icon="🎯")
        except Exception as e:
            st.session_state.interview_result = handle_error(e, "Interview Prep Generation")

    if st.session_state.interview_result:
        res = st.session_state.interview_result
        if res.get("error"):
            st.error(res["error"])
            if res.get("suggestion"):
                st.info(f"💡 {res['suggestion']}")
        else:
            st.markdown(res["questions"])
            st.download_button("⬇️ Download Interview Prep Guide", res["questions"], "interview_prep.md", use_container_width=True)

# ── Tab 4: Application Tracker ───────────────────────────────────────────────
with tab4:
    st.subheader("📊 Job Application Tracker")
    
    with st.expander("➕ Log New Application"):
        t1, t2 = st.columns(2)
        new_title = t1.text_input("Job Title")
        new_comp = t2.text_input("Company")
        new_status = st.selectbox("Status", ["applied", "interview", "offer", "rejected"])
        new_notes = st.text_area("Notes")
        
        if st.button("💾 Save Application", use_container_width=True):
            if new_title and new_comp:
                session = get_session()
                rec = ApplicationRecord(
                    job_title=new_title,
                    company=new_comp,
                    status=new_status,
                    notes=new_notes,
                    date_applied=datetime.utcnow(),
                    ats_score=st.session_state.ats_result["overall"] if st.session_state.ats_result else 0
                )
                session.add(rec)
                session.commit()
                session.close()
                st.success("Application logged!")
                st.rerun()
            else:
                st.warning("Please enter Title and Company.")

    # Display Table
    try:
        session = get_session()
        rows = session.query(ApplicationRecord).order_by(ApplicationRecord.date_applied.desc()).all()
        session.close()
        if rows:
            df = pd.DataFrame([{
                "Date": r.date_applied.strftime("%Y-%m-%d"),
                "Title": r.job_title,
                "Company": r.company,
                "Score": r.ats_score,
                "Status": r.status
            } for r in rows])
            st.dataframe(df, use_container_width=True)
        else:
            st.info("No applications logged yet.")
    except Exception as e:
        st.error(f"Error loading tracker: {e}")

# ── Tab 5: Analytics ─────────────────────────────────────────────────────────
with tab5:
    st.subheader("📈 Your Progress Analytics")
    try:
        session = get_session()
        rows = session.query(ApplicationRecord).all()
        session.close()
        if rows:
            total = len(rows)
            st.metric("Total Applications", total)
            
            # Simple status chart
            status_df = pd.DataFrame([r.status for r in rows], columns=["Status"]).value_counts().reset_index(name="Count")
            st.bar_chart(status_df.set_index("Status"))
        else:
            st.info("Log applications to see your personalized analytics!")
    except Exception as e:
        st.error(f"Error loading analytics: {e}")

# ── Footer ───────────────────────────────────────────────────────────────────
st.markdown(f"""
    <div class="footer">
        🚀 Built by <b>Yashwanth Balusu</b> | 
        <a href="https://linkedin.com/in/yashwanth-Balusu" target="_blank">LinkedIn</a> | 
        <a href="https://github.com/yashwanthbalusu6-scode" target="_blank">GitHub</a> | 
        © {datetime.now().year}
    </div>
""", unsafe_allow_html=True)
