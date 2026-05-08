"""Streamlit dashboard - ATS Resume Platform."""
import os
import tempfile
from datetime import datetime
from typing import Any, Dict, Optional

import pandas as pd
import streamlit as st

from ai_client import has_any_key
from ats_scorer import ATSScorer
from cover_letter_generator import CoverLetterGenerator
from database import ApplicationRecord, get_session, init_db
from interview_prep import InterviewPrepGenerator
from job_parser import JobParser
from resume_optimizer import ResumeOptimizer
from resume_parser import ResumeParser

st.set_page_config(page_title="ATS Resume Platform", page_icon="🚀", layout="wide")
st.title("🚀 ATS Resume & Job Application Suite")

try:
    init_db()
except Exception as e:
    st.warning(f"Database init issue: {e}")


def _ss_default(key: str, value: Any) -> None:
    if key not in st.session_state:
        st.session_state[key] = value


_ss_default("yep_api_key", "")
_ss_default("anthropic_api_key", "")
_ss_default("resume_text", "")
_ss_default("job_desc", "")
_ss_default("ats_result", None)
_ss_default("optimized_result", None)
_ss_default("cover_letter_result", None)
_ss_default("interview_result", None)
_ss_default("show_interview", False)


with st.sidebar:
    st.markdown("### 🔑 Choose your AI Provider")
    st.markdown(
        "**Option 1 (Recommended):** "
        "[Get FREE YepAPI key →](https://yepapi.com) ($5 free, no card)"
    )
    yep_key = st.text_input(
        "YepAPI Key (FREE $5 credit - get yours at yepapi.com)",
        value=st.session_state.yep_api_key,
        placeholder="yep_sk_...",
        type="password",
        key="yep_input",
    )
    st.session_state.yep_api_key = yep_key

    st.markdown("**Option 2:** [Anthropic Console →](https://console.anthropic.com)")
    ant_key = st.text_input(
        "Anthropic API Key (console.anthropic.com)",
        value=st.session_state.anthropic_api_key,
        placeholder="sk-ant-...",
        type="password",
        key="ant_input",
    )
    st.session_state.anthropic_api_key = ant_key

    if has_any_key(yep_key, ant_key):
        provider = "YepAPI" if yep_key else "Anthropic"
        st.success(f"✅ {provider} key loaded — AI features unlocked")
    else:
        # Fall back to env var if running on HF Spaces with secret set
        env_ant = os.getenv("ANTHROPIC_API_KEY", "")
        if env_ant:
            st.session_state.anthropic_api_key = env_ant
            st.info("✅ Using ANTHROPIC_API_KEY from environment")
        else:
            st.info("🔓 Enter an API key above to unlock AI features — YepAPI gives $5 free!")

    st.markdown("---")
    st.caption("Free features (no key needed): ATS scoring, job parsing, application tracker, analytics")


def _ai_unlocked() -> bool:
    return has_any_key(st.session_state.yep_api_key, st.session_state.anthropic_api_key)


def _ai_keys() -> Dict[str, Optional[str]]:
    return {
        "yep_api_key": st.session_state.yep_api_key or None,
        "anthropic_api_key": st.session_state.anthropic_api_key or None,
    }


tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📄 Resume Optimizer",
    "💌 Cover Letter",
    "🎤 Interview Prep",
    "📊 Tracker",
    "🎯 Analytics",
])


with tab1:
    st.header("📄 Resume Optimizer")
    st.write("Upload a PDF/DOCX resume or paste text. ATS scoring works without a key.")

    col_a, col_b = st.columns(2)

    with col_a:
        uploaded = st.file_uploader("Upload resume (PDF or DOCX)", type=["pdf", "docx"])
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
                    elif parsed.get("full_text"):
                        st.session_state.resume_text = parsed["full_text"]
                        st.success(f"✅ Parsed {uploaded.name} ({len(parsed['full_text'])} chars)")
                finally:
                    try:
                        os.unlink(tmp_path)
                    except Exception:
                        pass
            except Exception as e:
                st.error(f"Upload failed: {e}")

        resume_text = st.text_area(
            "Or paste resume text",
            value=st.session_state.resume_text,
            height=240,
            key="resume_textarea",
        )
        st.session_state.resume_text = resume_text

    with col_b:
        job_desc = st.text_area(
            "Paste job description",
            value=st.session_state.job_desc,
            height=300,
            key="job_textarea",
        )
        st.session_state.job_desc = job_desc

    if st.session_state.resume_text and st.session_state.job_desc:
        c1, c2 = st.columns(2)

        with c1:
            if st.button("📊 Compute ATS Score (free)", use_container_width=True):
                try:
                    scorer = ATSScorer(st.session_state.resume_text, st.session_state.job_desc)
                    st.session_state.ats_result = scorer.score()
                except Exception as e:
                    st.error(f"Score error: {e}")

        with c2:
            if st.button(
                "🤖 Optimize with AI",
                disabled=not _ai_unlocked(),
                use_container_width=True,
                help="Requires a YepAPI or Anthropic key" if not _ai_unlocked() else None,
            ):
                with st.spinner("Calling Claude..."):
                    try:
                        opt = ResumeOptimizer(
                            st.session_state.resume_text,
                            st.session_state.job_desc,
                            **_ai_keys(),
                        )
                        st.session_state.optimized_result = opt.optimize()
                    except Exception as e:
                        st.session_state.optimized_result = {"error": str(e)}

        if st.session_state.ats_result:
            r = st.session_state.ats_result
            if r.get("error"):
                st.error(f"Score error: {r['error']}")
            else:
                st.subheader(f"ATS Score: {r['overall']}/100")
                m1, m2, m3, m4 = st.columns(4)
                m1.metric("Keywords", f"{r['keywords']}/100")
                m2.metric("Formatting", f"{r['formatting']}/100")
                m3.metric("Sections", f"{r['sections']}/100")
                m4.metric("Readability", f"{r['readability']}/100")

            try:
                jp = JobParser(st.session_state.job_desc).parse()
                with st.expander("Parsed job details"):
                    st.write(f"**Title:** {jp.get('job_title')}")
                    st.write(f"**Company:** {jp.get('company')}")
                    st.write(f"**Skills:** {', '.join(jp.get('required_skills', [])) or '—'}")
            except Exception as e:
                st.warning(f"Job parse: {e}")

        if st.session_state.optimized_result:
            res = st.session_state.optimized_result
            if res.get("error"):
                st.error(res["error"])
            else:
                st.subheader("✨ Optimized Resume")
                st.markdown(res.get("optimized", ""))
                if res.get("provider"):
                    st.caption(f"via {res['provider']}")
                st.download_button(
                    "⬇️ Download Optimized Resume",
                    data=res.get("optimized", ""),
                    file_name="optimized_resume.txt",
                    mime="text/plain",
                    key="dl_optimized",
                )


with tab2:
    st.header("💌 Cover Letter Generator")
    if not _ai_unlocked():
        st.info("🔓 Enter an API key in the sidebar to unlock cover letters.")
    company = st.text_input("Company", key="cl_company")
    role = st.text_input("Role", key="cl_role")
    tone = st.selectbox("Tone", ["formal", "friendly", "enthusiastic"], key="cl_tone")

    if st.button("Generate Cover Letter", disabled=not _ai_unlocked()):
        if not (st.session_state.resume_text and st.session_state.job_desc):
            st.warning("Add resume + job description on Tab 1 first.")
        else:
            with st.spinner("Writing your cover letter..."):
                try:
                    gen = CoverLetterGenerator(
                        st.session_state.resume_text,
                        st.session_state.job_desc,
                        company or "the company",
                        role or "the role",
                        **_ai_keys(),
                    )
                    st.session_state.cover_letter_result = gen.generate(tone=tone)
                except Exception as e:
                    st.session_state.cover_letter_result = {"error": str(e)}

    if st.session_state.cover_letter_result:
        res = st.session_state.cover_letter_result
        if res.get("error"):
            st.error(res["error"])
        else:
            st.markdown(res.get("letter", ""))
            if res.get("provider"):
                st.caption(f"via {res['provider']}")
            st.download_button(
                "⬇️ Download Cover Letter",
                data=res.get("letter", ""),
                file_name="cover_letter.txt",
                mime="text/plain",
                key="dl_cover_letter",
            )


with tab3:
    st.header("🎤 Interview Prep")
    if not _ai_unlocked():
        st.info("🔓 Enter an API key in the sidebar to unlock interview prep.")
    ip_company = st.text_input("Company", key="ip_company")
    ip_role = st.text_input("Role", key="ip_role")

    if st.button("🎯 Generate Interview Questions", disabled=not _ai_unlocked()):
        st.session_state.show_interview = True

    if st.session_state.show_interview and _ai_unlocked():
        if not (st.session_state.resume_text and st.session_state.job_desc):
            st.warning("Add resume + job description on Tab 1 first.")
        else:
            with st.spinner("Generating questions..."):
                try:
                    ip = InterviewPrepGenerator(
                        st.session_state.resume_text,
                        st.session_state.job_desc,
                        ip_company or "the company",
                        ip_role or "the role",
                        **_ai_keys(),
                    )
                    st.session_state.interview_result = ip.generate()
                except Exception as e:
                    st.session_state.interview_result = {"error": str(e)}
        st.session_state.show_interview = False

    if st.session_state.interview_result:
        res = st.session_state.interview_result
        if res.get("error"):
            st.error(res["error"])
        else:
            st.markdown(res.get("questions", ""))
            if res.get("provider"):
                st.caption(f"via {res['provider']}")
            st.download_button(
                "⬇️ Download Interview Questions",
                data=res.get("questions", ""),
                file_name="interview_questions.txt",
                mime="text/plain",
                key="dl_interview",
            )


with tab4:
    st.header("📊 Application Tracker")
    st.caption("Free — no API key required.")

    with st.expander("➕ Log a new application"):
        c1, c2 = st.columns(2)
        new_title = c1.text_input("Job title", key="add_title")
        new_company = c2.text_input("Company", key="add_company")
        new_score = c1.number_input("ATS Score", min_value=0, max_value=100, value=0, key="add_score")
        new_status = c2.selectbox(
            "Status", ["applied", "interview", "offer", "rejected"], key="add_status"
        )
        new_notes = st.text_area("Notes", key="add_notes")
        if st.button("Save application"):
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
            except Exception as e:
                st.error(f"Save failed: {e}")

    try:
        session = get_session()
        rows = session.query(ApplicationRecord).order_by(ApplicationRecord.date_applied.desc()).all()
        session.close()
        if rows:
            df = pd.DataFrame([{
                "Date": r.date_applied.strftime("%Y-%m-%d") if r.date_applied else "",
                "Title": r.job_title,
                "Company": r.company,
                "Score": r.ats_score,
                "Status": r.status,
                "Notes": r.notes,
            } for r in rows])
            st.dataframe(df, use_container_width=True)
        else:
            st.info("No applications logged yet.")
    except Exception as e:
        st.error(f"Could not load applications: {e}")


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
            avg_score = sum((r.ats_score or 0) for r in rows) / total if total else 0
            m1, m2, m3, m4 = st.columns(4)
            m1.metric("Applications", total)
            m2.metric("Interviews", interviews)
            m3.metric("Offers", offers)
            m4.metric("Avg ATS", f"{avg_score:.0f}")
            status_counts = pd.DataFrame(
                {"count": [total - interviews - offers - rejects, interviews, offers, rejects]},
                index=["applied", "interview", "offer", "rejected"],
            )
            st.bar_chart(status_counts)
    except Exception as e:
        st.error(f"Analytics error: {e}")


st.markdown("---")
st.markdown("🚀 ATS Resume Platform | Streamlit + Claude (YepAPI / Anthropic)")
