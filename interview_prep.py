"""Interview prep generator using Claude API"""
import os
import json
from anthropic import Anthropic

client = Anthropic()


class InterviewPrepGenerator:
    """Generate interview questions using Claude."""
    
    def __init__(self, resume: str, job: str, company: str, role: str):
        self.resume = resume
        self.job = job
        self.company = company
        self.role = role
    
    def generate(self) -> dict:
        """Generate interview questions."""
        prompt = f"""Generate 10 interview questions for {self.role} at {self.company}.

RESUME: {self.resume}
JOB: {self.job}

Include STAR examples and talking points for each."""
        
        try:
            message = client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=3000,
                messages=[{"role": "user", "content": prompt}]
            )
            return {'questions': message.content[0].text}
        except Exception as e:
            return {'error': str(e)}
