"""Cover letter generator using Claude via YepAPI or Anthropic."""
from typing import Any, Dict, Optional

from ai_client import call_ai


class CoverLetterGenerator:
    """Generate cover letters using Claude."""

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

    def generate(self, tone: str = "formal") -> Dict[str, Any]:
        prompt = f"""Write a {tone} cover letter for {self.role} at {self.company}.

RESUME: {self.resume}
JOB: {self.job}

Write 2 distinct variants. Label them clearly as "Variant 1" and "Variant 2"."""
        try:
            result = call_ai(
                prompt,
                yep_api_key=self.yep_api_key,
                anthropic_api_key=self.anthropic_api_key,
                max_tokens=1800,
            )
            if "error" in result:
                return {"error": result["error"]}
            return {"letter": result["text"], "provider": result.get("provider")}
        except Exception as e:
            return {"error": str(e)}
