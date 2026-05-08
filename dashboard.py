"""Streamlit dashboard - ATS Resume & Job Application Suite."""
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
from interview_prep import InterviewPrepGenerator
from job_parser import JobParser
from resume_optimizer import ResumeOptimizer
from resume_parser import ResumeParser

st.set_page_config(page_title="ATS Resume Suite", page_icon="🚀", layout="wide")

# ── Session state defaults (must come before any UI) ─────────────────────────
st.session_state.setdefault("resume_text", "")
st.session_state.setdefault("job_desc", "")
st.session_state.setdefault("yep_api_key", "")
st.session_state.setdefault("anthropic_api_key", "")
st.session_state.setdefault("ats_result", None)
st.session_state.setdefault("optimized_result", None)
st.session_state.setdefault("cover_letter_result", None)
st.session_state.setdefault("interview_result", None)

# Initialize DB once
try:
    init_db()
except Exception as e:
    st.warning(f"Database init issue: {e}")


# ── Helpers ──────────────────────────────────────────────────────────────────
def _ai_unlocked() -> bool:
    return has_any_key(
        st.session_state.get("yep_api_key", ""),
        st.session_state.get("anthropic_api_key", ""),
    )


def _ai_keys() -> Dict[str, Optional[str]]:
    return {
        "yep_api_key": st.session_state.get("yep_api_key") or None,
        "anthropic_api_key": st.session_state.get("anthropic_api_key") or None,
    }


SAMPLE_RESUME = """John Doe
Software Engineer | john@example.com | (555) 123-4567

EXPERIENCE
Senior Backend Engineer — Acme Corp (2021-2024)
- Built Python microservices on AWS handling 10M req/day
- Led migration from monolith to Kubernetes-based architecture
- Mentored 4 junior engineers on Django, FastAPI, PostgreSQL

Software Engineer — Beta Inc (2018-2021)
- Designed REST APIs with Flask and SQL
- Implemented CI/CD pipelines using GitHub Actions and Docker

SKILLS
Python, Django, FastAPI, AWS, Docker, Kubernetes, PostgreSQL, Redis, Git

EDUCATION
B.S. Computer Science — State University (2018)

CONTACT
john@example.com | linkedin.com/in/johndoe
"""

SAMPLE_JOB = """Senior Python Engineer at TechStartup

TechStartup is hiring a Senior Python Engineer to join our backend team.

Responsibilities:
- Design and build scalable Python microservices
- Work with FastAPI, Django, and PostgreSQL
- Deploy to AWS using Docker and Kubernetes
- Mentor junior engineers

Requirements:
- 5+ years of Python experience
- Strong knowledge of REST APIs, microservices, SQL
- Experience with AWS, Docker, Kubernetes
- CI/CD pipeline experience
"""


# ── Sidebar ──────────────────────────────────────────────────────────────────
with st.sidebar:
    st.title("🚀 ATS Resume Suite")
    st.markdown("### 🔑 Add API Key (Optional - any provider works)")

    api_key_input = st.text_input(
        "API Key (YepAPI, Anthropic, or OpenAI)",
        value=(st.session_state.yep_api_key or st.session_state.anthropic_api_key),
        placeholder="yep_... or sk-ant-... or sk-...",
        type="password",
        help=(
            "Get FREE $5 at yepapi.com | sk-ant from console.anthropic.com | "
            "sk- from OpenAI"
        ),
        key="api_key_input",
    )

    # Auto-detect: route key to correct slot
    key_clean = (api_key_input or "").strip()
    if key_clean.startswith("yep_"):
        st.session_state.yep_api_key = key_clean
        st.session_state.anthropic_api_key = ""
    elif key_clean:
        st.session_state.anthropic_api_key = key_clean
        st.session_state.yep_api_key = ""
    else:
        st.session_state.yep_api_key = ""
        st.session_state.anthropic_api_key = ""

    if _ai_unlocked():
        prov = detect_provider(key_clean)
        st.success(f"✅ Detected: {prov}")
    else:
        # Try env var (HF Spaces secret)
        env_ant = os.getenv("ANTHROPIC_API_KEY", "").strip()
        env_yep = os.getenv("YEP_API_KEY", "").strip()
        if env_yep:
            st.session_state.yep_api_key = env_yep
            st.success("✅ Using YEP_API_KEY from environment")
        elif env_ant:
            st.session_state.anthropic_api_key = env_ant
            st.success("✅ Using ANTHROPIC_API_KEY from environment")
        else:
            st.info("🔓 ATS scoring works free without keys")

    st.markdown("---")
    st.caption(
        "Free features (no key): ATS scoring, job parsing, "
        "application tracker, analytics."
    )

    if st.button("🧹 Clear All", use_container_width=True, help="Reset all inputs"):
        for k in [
            "resume_text", "job_desc", "ats_result", "optimized_result",
            "cover_letter_result", "interview_result",
        ]:
            st.session_state[k] = "" if k in ("resume_text", "job_desc") else None
        st.rerun()


# ── Main ─────────────────────────────────────────────────────────────────────
st.title("🚀 ATS Resume & Job Application Suite")

tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📄 Resume Optimizer",
    "💌 Cover Letter",
    "🎤 Interview Prep",
    "📊 Tracker",
    "🎯 Analytics",
])


# ── Tab 1: Resume Optimizer ──────────────────────────────────────────────────
with tab1:
    st.header("📄 Resume Optimizer")
    st.write(
        "Upload a PDF/DOCX resume or paste text. "
        "ATS scoring is free (no API key)."
    )

    col_a, col_b = st.columns(2)

    with col_a:
        uploaded = st.file_uploader(
            "Upload resume (PDF, DOCX, DOC, TXT, RTF, MD)",
            type=["pdf", "docx", "doc", "txt", "rtf", "md"],
            help="Any common resume format. Text is auto-extracted.",
        )
        if uploaded is not None:
            try:
                suffix = os.path.splitext(uploaded.name)[1] or ".pdf"
                with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
                    tmp.write(uploaded.getvalue())
                    tmp_path = tmp.name
                try:
                    parsed = ResumeParser(tmp_path).parse()
                    if parsed.get("error"):
                        st.error(f"Parse error: {parsed['error']}")
                        for w in parsed.get("warnings") or []:
                            st.warning(w)
                    elif parsed.get("full_text"):
                        st.session_state.resume_text = parsed["full_text"]
                        method = parsed.get("method") or "auto"
                        st.success(
                            f"✅ Parsed {uploaded.name} "
                            f"({len(parsed['full_text'])} chars · via {method})"
                        )
                        for w in parsed.get("warnings") or []:
                            st.warning(w)
                    else:
                        st.error(
                            "Could not extract text. "
                            "If this is a scanned PDF, paste the resume below instead."
                        )
                finally:
                    try:
                        os.unlink(tmp_path)
                    except Exception:
                        pass
            except Exception as e:
                st.error(f"Upload failed: {e}")

        if st.button("📋 Use sample resume", key="sample_resume_btn"):
            st.session_state.resume_text = SAMPLE_RESUME
            st.rerun()

        resume_text = st.text_area(
            "Or paste resume text",
            value=st.session_state.resume_text,
            height=240,
            key="resume_textarea",
            help="Paste plain-text resume content",
        )
        st.session_state.resume_text = resume_text
        st.caption(f"📝 {len(resume_text)} characters")

    with col_b:
        if st.button("📋 Use sample job description", key="sample_job_btn"):
            st.session_state.job_desc = SAMPLE_JOB
            st.rerun()

        job_desc = st.text_area(
            "Paste job description",
            value=st.session_state.job_desc,
            height=300,
            key="job_textarea",
            help="Paste the full job posting text",
        )
        st.session_state.job_desc = job_desc
        st.caption(f"📝 {len(job_desc)} characters")

    st.divider()

    has_inputs = bool(
        st.session_state.resume_text.strip() and st.session_state.job_desc.strip()
    )
    has_key = _ai_unlocked()

    c1, c2 = st.columns(2)

    with c1:
        ats_clicked = st.button(
            "📊 Calculate ATS Score (FREE)",
            disabled=not has_inputs,
            use_container_width=True,
            help=(
                "Free — works without API key. Add resume & job description first."
                if not has_inputs
                else "Compute ATS keyword/format/section/readability score"
            ),
            key="btn_ats",
        )

    with c2:
        opt_clicked = st.button(
            "🤖 Optimize with AI",
            disabled=not (has_inputs and has_key),
            use_container_width=True,
            help=(
                "Requires resume, job description, AND an API key in the sidebar"
                if not (has_inputs and has_key)
                else "Rewrite your resume to match this job using AI"
            ),
            key="btn_opt",
        )

    if not has_inputs:
        st.caption("💡 Add both a resume and a job description to enable buttons.")
    elif not has_key:
        st.caption("💡 Add an API key in the sidebar to unlock AI optimization.")

    if ats_clicked:
        with st.spinner("Scoring resume against job description…"):
            try:
                scorer = ATSScorer(
                    st.session_state.resume_text, st.session_state.job_desc
                )
                st.session_state.ats_result = scorer.score()
                st.toast("ATS score computed", icon="📊")
            except Exception as e:
                st.session_state.ats_result = {"error": str(e)}

    if opt_clicked:
        with st.spinner("Calling AI to optimize your resume…"):
            try:
                opt = ResumeOptimizer(
                    st.session_state.resume_text,
                    st.session_state.job_desc,
                    **_ai_keys(),
                )
                st.session_state.optimized_result = opt.optimize()
                if "error" not in st.session_state.optimized_result:
                    st.toast("Resume optimized", icon="✨")
            except Exception as e:
                st.session_state.optimized_result = {"error": str(e)}

    # ── ATS Results
    if st.session_state.ats_result:
        r = st.session_state.ats_result
        if r.get("error"):
            st.error(f"Score error: {r['error']}")
        else:
            st.subheader(f"ATS Score: {r['overall']}/100")
            st.progress(min(int(r["overall"]), 100) / 100)
            m1, m2, m3, m4 = st.columns(4)
            m1.metric("Keywords", f"{r['keywords']}/100")
            m2.metric("Formatting", f"{r['formatting']}/100")
            m3.metric("Sections", f"{r['sections']}/100")
            m4.metric("Readability", f"{r['readability']}/100")

            try:
                jp = JobParser(st.session_state.job_desc).parse()
                with st.expander("Parsed job details"):
                    st.write(f"**Title:** {jp.get('job_title', '—')}")
                    st.write(f"**Company:** {jp.get('company', '—')}")
                    skills = jp.get("required_skills") or []
                    st.write(f"**Skills:** {', '.join(skills) if skills else '—'}")
            except Exception as e:
                st.warning(f"Job parse: {e}")

    # ── Optimized Resume Result
    if st.session_state.optimized_result:
        res = st.session_state.optimized_result
        if res.get("error"):
            st.error(res["error"])
        else:
            st.subheader("✨ Optimized Resume")
            optimized_text = res.get("optimized", "")
            st.markdown(optimized_text)
            if res.get("provider"):
                st.caption(f"via {res['provider']}")
            st.download_button(
                "⬇️ Download Optimized Resume",
                data=optimized_text,
                file_name="optimized_resume.txt",
                mime="text/plain",
                key="dl_optimized",
                use_container_width=True,
            )


# ── Tab 2: Cover Letter ──────────────────────────────────────────────────────
with tab2:
    st.header("💌 Cover Letter Generator")
    st.caption("Uses the resume + job description from Tab 1.")

    if not _ai_unlocked():
        st.info("🔓 Add an API key in the sidebar to unlock cover letters.")

    company = st.text_input("Company", key="cl_company", help="Target company name")
    role = st.text_input("Role", key="cl_role", help="Job title you're applying for")
    tone = st.selectbox(
        "Tone", ["formal", "friendly", "enthusiastic"], key="cl_tone"
    )

    has_all_for_cl = bool(
        st.session_state.resume_text.strip()
        and st.session_state.job_desc.strip()
        and _ai_unlocked()
    )

    cl_clicked = st.button(
        "💌 Generate Cover Letter",
        disabled=not has_all_for_cl,
        use_container_width=True,
        help=(
            "Need resume, job description (Tab 1) AND API key in sidebar"
            if not has_all_for_cl
            else "Generate two cover letter variants"
        ),
        key="btn_cl",
    )

    if not has_all_for_cl:
        st.caption(
            "💡 Add resume + job description in Tab 1 and an API key in the sidebar."
        )

    if cl_clicked:
        with st.spinner("Writing your cover letter…"):
            try:
                gen = CoverLetterGenerator(
                    st.session_state.resume_text,
                    st.session_state.job_desc,
                    company or "the company",
                    role or "the role",
                    **_ai_keys(),
                )
                st.session_state.cover_letter_result = gen.generate(tone=tone)
                if "error" not in st.session_state.cover_letter_result:
                    st.toast("Cover letter generated", icon="💌")
            except Exception as e:
                st.session_state.cover_letter_result = {"error": str(e)}

    if st.session_state.cover_letter_result:
        res = st.session_state.cover_letter_result
        if res.get("error"):
            st.error(res["error"])
        else:
            letter_text = res.get("letter", "")
            st.markdown(letter_text)
            if res.get("provider"):
                st.caption(f"via {res['provider']}")
            st.download_button(
                "⬇️ Download Cover Letter",
                data=letter_text,
                file_name="cover_letter.txt",
                mime="text/plain",
                key="dl_cover_letter",
                use_container_width=True,
            )


# ── Tab 3: Interview Prep ────────────────────────────────────────────────────
with tab3:
    st.header("🎤 Interview Prep")
    st.caption("Uses the resume + job description from Tab 1.")

    if not _ai_unlocked():
        st.info("🔓 Add an API key in the sidebar to unlock interview prep.")

    ip_company = st.text_input("Company", key="ip_company")
    ip_role = st.text_input("Role", key="ip_role")

    has_all_for_ip = bool(
        st.session_state.resume_text.strip()
        and st.session_state.job_desc.strip()
        and _ai_unlocked()
    )

    ip_clicked = st.button(
        "🎯 Generate Interview Questions",
        disabled=not has_all_for_ip,
        use_container_width=True,
        help=(
            "Need resume, job description (Tab 1) AND API key in sidebar"
            if not has_all_for_ip
            else "Generate 10 interview questions with STAR-format answers"
        ),
        key="btn_ip",
    )

    if not has_all_for_ip:
        st.caption(
            "💡 Add resume + job description in Tab 1 and an API key in the sidebar."
        )

    if ip_clicked:
        with st.spinner("Generating interview questions…"):
            try:
                ip = InterviewPrepGenerator(
                    st.session_state.resume_text,
                    st.session_state.job_desc,
                    ip_company or "the company",
                    ip_role or "the role",
                    **_ai_keys(),
                )
                st.session_state.interview_result = ip.generate()
                if "error" not in st.session_state.interview_result:
                    st.toast("Interview questions generated", icon="🎤")
            except Exception as e:
                st.session_state.interview_result = {"error": str(e)}

    if st.session_state.interview_result:
        res = st.session_state.interview_result
        if res.get("error"):
            st.error(res["error"])
        else:
            q_text = res.get("questions", "")
            st.markdown(q_text)
            if res.get("provider"):
                st.caption(f"via {res['provider']}")
            st.download_button(
                "⬇️ Download Interview Questions",
                data=q_text,
                file_name="interview_questions.txt",
                mime="text/plain",
                key="dl_interview",
                use_container_width=True,
            )


# ── Tab 4: Application Tracker ───────────────────────────────────────────────
with tab4:
    st.header("📊 Application Tracker")
    st.caption("Free — no API key required.")

    with st.expander("➕ Log a new application", expanded=False):
        c1, c2 = st.columns(2)
        new_title = c1.text_input("Job title", key="add_title")
        new_company = c2.text_input("Company", key="add_company")
        new_score = c1.number_input(
            "ATS Score", min_value=0, max_value=100, value=0, key="add_score"
        )
        new_status = c2.selectbox(
            "Status", ["applied", "interview", "offer", "rejected"], key="add_status"
        )
        new_notes = st.text_area("Notes", key="add_notes")

        if st.button("💾 Save application", use_container_width=True, key="btn_save_app"):
            if not (new_title.strip() or new_company.strip()):
                st.warning("Add at least a title or company.")
            else:
                try:
                    session = get_session()
                    rec = ApplicationRecord(
                        job_title=new_title or "—",
                        company=new_company or "—",
                        ats_score=int(new_score),
                        status=new_status,
                        notes=new_notes or "",
                        date_applied=datetime.utcnow(),
                    )
                    session.add(rec)
                    session.commit()
                    session.close()
                    st.success("Saved.")
                    st.toast("Application saved", icon="✅")
                except Exception as e:
                    st.error(f"Save failed: {e}")

    try:
        session = get_session()
        rows = (
            session.query(ApplicationRecord)
            .order_by(ApplicationRecord.date_applied.desc())
            .all()
        )
        session.close()
        if rows:
            df = pd.DataFrame([
                {
                    "Date": r.date_applied.strftime("%Y-%m-%d") if r.date_applied else "",
                    "Title": r.job_title,
                    "Company": r.company,
                    "Score": r.ats_score,
                    "Status": r.status,
                    "Notes": r.notes,
                }
                for r in rows
            ])
            st.dataframe(df, use_container_width=True)
        else:
            st.info("No applications logged yet.")
    except Exception as e:
        st.error(f"Could not load applications: {e}")


# ── Tab 5: Analytics ─────────────────────────────────────────────────────────
with tab5:
    st.header("🎯 Skills Analytics")
    st.caption("Free — no API key required.")
    try:
        session = get_session()
        rows = session.query(ApplicationRecord).all()
        session.close()
        if not rows:
            st.info("Log applications in Tab 4 to see analytics.")
        else:
            total = len(rows)
            interviews = sum(1 for r in rows if r.status == "interview")
            offers = sum(1 for r in rows if r.status == "offer")
            rejects = sum(1 for r in rows if r.status == "rejected")
            avg_score = (
                sum((r.ats_score or 0) for r in rows) / total if total else 0
            )
            m1, m2, m3, m4 = st.columns(4)
            m1.metric("Applications", total)
            m2.metric("Interviews", interviews)
            m3.metric("Offers", offers)
            m4.metric("Avg ATS", f"{avg_score:.0f}")
            status_counts = pd.DataFrame(
                {
                    "count": [
                        max(total - interviews - offers - rejects, 0),
                        interviews,
                        offers,
                        rejects,
                    ]
                },
                index=["applied", "interview", "offer", "rejected"],
            )
            st.bar_chart(status_counts)
    except Exception as e:
        st.error(f"Analytics error: {e}")


st.markdown("---")
st.markdown(
    "🚀 ATS Resume Suite | Streamlit + Claude "
    "(YepAPI / Anthropic / OpenAI auto-detect)"
)
