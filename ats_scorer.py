"""ATS scoring algorithm"""
import re
from typing import Dict


class ATSScorer:
    """Score resume against job (0-100)."""
    
    def __init__(self, resume: str, job: str):
        self.resume = resume.lower()
        self.job = job.lower()
    
    def score(self) -> Dict:
        keywords = self._score_keywords()
        formatting = self._score_formatting()
        sections = self._score_sections()
        readability = self._score_readability()
        
        overall = int(keywords * 0.4 + formatting * 0.25 + sections * 0.2 + readability * 0.15)
        
        return {
            'overall': overall,
            'keywords': int(keywords),
            'formatting': int(formatting),
            'sections': int(sections),
            'readability': int(readability),
        }
    
    def _score_keywords(self) -> float:
        keywords = set(re.findall(r"\b([a-z]+[\w\-]*)\b", self.job))
        keywords = {k for k in keywords if len(k) > 3}
        matches = sum(1 for k in keywords if k in self.resume)
        return (matches / len(keywords) * 100) if keywords else 50
    
    def _score_formatting(self) -> float:
        return 85 if "|" not in self.resume else 70
    
    def _score_sections(self) -> float:
        sections = ["experience", "skills", "education", "contact"]
        present = sum(1 for s in sections if s in self.resume)
        return (present / len(sections)) * 100
    
    def _score_readability(self) -> float:
        return 80
