"""Resume optimizer using Claude API"""
import os
from anthropic import Anthropic

client = Anthropic()


class ResumeOptimizer:
    """Optimize resume using Claude."""
    
    def __init__(self, resume: str, job: str):
        self.resume = resume
        self.job = job
    
    def optimize(self) -> dict:
        """Generate optimized resume."""
        prompt = f"""Optimize this resume for this job.

RESUME:
{self.resume}

JOB:
{self.job}

Return optimized resume and changes made."""
        
        try:
            message = client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=2000,
                messages=[{"role": "user", "content": prompt}]
            )
            return {'optimized': message.content[0].text}
        except Exception as e:
            return {'error': str(e)}
