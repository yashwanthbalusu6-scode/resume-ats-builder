FROM python:3.10-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*
RUN useradd -m -u 1000 user
USER user
ENV HOME=/home/user PATH=/home/user/.local/bin:$PATH
WORKDIR $HOME/app
COPY --chown=user requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt
COPY --chown=user . .
EXPOSE 8501
HEALTHCHECK --interval=30s --timeout=3s CMD curl -f http://localhost:8501/_stcore/health || exit 1
CMD ["streamlit", "run", "dashboard.py", \
     "--server.address=0.0.0.0", \
     "--server.port=8501", \
     "--server.headless=true", \
     "--server.enableXsrfProtection=false", \
     "--server.fileWatcherType=none", \
     "--browser.gatherUsageStats=false"]
