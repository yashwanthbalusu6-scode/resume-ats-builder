"""Interview prep generator using Claude via YepAPI or Anthropic."""
from typing import Any, Dict, Optional

from ai_client import call_ai


class InterviewPrepGenerator:
    """Generate interview questions using Claude."""

    def __init__(
        self,
        resume: str,
        job: str,
        company: str,
        role: str,
        yep_api_key: Optional[str] = None,
        anthropic_api_key: Optional[str] = None,
    ):
        self.resume = resume
        self.job = job
        self.company = company
        self.role = role
        self.yep_api_key = yep_api_key
        self.anthropic_api_key = anthropic_api_key

    def generate(self) -> Dict[str, Any]:
        prompt = f"""Generate 10 interview questions for {self.role} at {self.company}.

RESUME: {self.resume}
JOB: {self.job}

For each question, include:
- The question itself
- A STAR-format example answer drawn from the resume
- 2-3 talking points to emphasize"""
        try:
            result = call_ai(
                prompt,
                yep_api_key=self.yep_api_key,
                anthropic_api_key=self.anthropic_api_key,
                max_tokens=3500,
            )
            if "error" in result:
                return {"error": result["error"]}
            return {"questions": result["text"], "provider": result.get("provider")}
        except Exception as e:
            return {"error": str(e)}
