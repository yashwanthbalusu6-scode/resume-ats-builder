---
title: ATS Resume Platform
emoji: 🚀
colorFrom: blue
colorTo: purple
sdk: docker
sdk_version: "20.10"
app_file: dashboard.py
pinned: false
---

# 🚀 ATS Resume & Job Application Platform

Advanced AI-powered resume optimizer for job applications.

## Features

📄 **Tab 1: Resume Optimizer**
- ATS Score (0-100)
- Keyword matching
- Smart optimization via Claude

💌 **Tab 2: Cover Letter Generator**
- AI-generated cover letters
- Multiple variants
- Customized for each job

🎤 **Tab 3: Interview Prep**
- 10-15 interview questions
- STAR framework examples
- Talking points

📊 **Tab 4: Application Tracker**
- Track all applications
- Response rate analytics

🎯 **Tab 5: Skills Analytics**
- Skills gap analysis
- Market insights

## Installation

```bash
pip install -r requirements.txt
```

## Run Locally

```bash
streamlit run dashboard.py
```

## Deploy to HF Spaces

1. Push to GitHub
2. Create HF Space (Docker SDK)
3. Set ANTHROPIC_API_KEY secret
4. Done!

## Tech Stack

- Streamlit
- Claude AI
- SQLite
- Docker

Built with ❤️ using Streamlit + Claude AI
