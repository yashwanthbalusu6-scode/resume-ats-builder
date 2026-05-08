"""Streamlit dashboard - ATS Resume Platform"""
import os
import streamlit as st
from database import init_db

st.set_page_config(page_title="ATS Resume Platform", page_icon="🚀", layout="wide")
st.title("🚀 ATS Resume & Job Application Suite")

init_db()

tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📄 Resume Optimizer",
    "💌 Cover Letter", 
    "🎤 Interview Prep",
    "📊 Tracker",
    "🎯 Analytics"
])

with tab1:
    st.header("📄 Resume Optimizer")
    st.write("Upload resume and paste job description to get ATS score (0-100)")
    
    resume_text = st.text_area("Paste your resume", height=200)
    job_desc = st.text_area("Paste job description", height=200)
    
    if resume_text and job_desc:
        if st.button("🔄 Analyze & Optimize"):
            st.info("✅ Resume analysis coming soon! (requires ANTHROPIC_API_KEY)")
            st.write("Upload and optimize features coming in v2")

with tab2:
    st.header("💌 Cover Letter Generator")
    st.write("Generate personalized cover letters")
    st.info("📝 Cover letter generation coming in v2")

with tab3:
    st.header("🎤 Interview Prep")
    st.write("Get interview questions for your target role")
    st.info("🎤 Interview prep coming in v2")

with tab4:
    st.header("📊 Application Tracker")
    st.write("Track all your job applications")
    st.info("📊 Application tracker coming in v2")

with tab5:
    st.header("🎯 Skills Analytics")
    st.write("Track your resume performance and skill gaps")
    st.info("🎯 Analytics coming in v2")

st.markdown("---")
st.markdown("🚀 ATS Resume Platform | Built with Streamlit + Claude AI")
