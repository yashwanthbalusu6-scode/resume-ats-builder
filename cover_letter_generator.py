"""Cover letter generator using Claude API"""
import os
from anthropic import Anthropic

client = Anthropic()


class CoverLetterGenerator:
    """Generate cover letters using Claude."""
    
    def __init__(self, resume: str, job: str, company: str, role: str):
        self.resume = resume
        self.job = job
        self.company = company
        self.role = role
    
    def generate(self, tone: str = "formal") -> dict:
        """Generate cover letter."""
        prompt = f"""Write a {tone} cover letter for {self.role} at {self.company}.

RESUME: {self.resume}
JOB: {self.job}

Write 2 variants."""
        
        try:
            message = client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=1500,
                messages=[{"role": "user", "content": prompt}]
            )
            return {'letter': message.content[0].text}
        except Exception as e:
            return {'error': str(e)}
