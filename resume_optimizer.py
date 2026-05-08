"""Resume optimizer using Claude via YepAPI or Anthropic."""
from typing import Any, Dict, Optional

from ai_client import call_ai


class ResumeOptimizer:
    """Optimize resume using Claude."""

    def __init__(
        self,
        resume: str,
        job: str,
        yep_api_key: Optional[str] = None,
        anthropic_api_key: Optional[str] = None,
    ):
        self.resume = resume
        self.job = job
        self.yep_api_key = yep_api_key
        self.anthropic_api_key = anthropic_api_key

    def optimize(self) -> Dict[str, Any]:
        prompt = f"""Optimize this resume for this job.

RESUME:
{self.resume}

JOB:
{self.job}

Return:
1. The optimized resume text
2. A bulleted list of changes you made and why
"""
        try:
            result = call_ai(
                prompt,
                yep_api_key=self.yep_api_key,
                anthropic_api_key=self.anthropic_api_key,
                max_tokens=2500,
            )
            if "error" in result:
                return {"error": result["error"]}
            return {"optimized": result["text"], "provider": result.get("provider")}
        except Exception as e:
            return {"error": str(e)}
