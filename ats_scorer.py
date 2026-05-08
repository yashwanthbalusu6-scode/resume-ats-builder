"""ATS scoring algorithm."""
import re
from typing import Any, Dict


class ATSScorer:
    """Score resume against job (0-100)."""

    def __init__(self, resume: str, job: str):
        self.resume = (resume or "").lower()
        self.job = (job or "").lower()

    def score(self) -> Dict[str, Any]:
        try:
            keywords = self._score_keywords()
            formatting = self._score_formatting()
            sections = self._score_sections()
            readability = self._score_readability()
            overall = int(keywords * 0.4 + formatting * 0.25 + sections * 0.2 + readability * 0.15)
            return {
                "overall": overall,
                "keywords": int(keywords),
                "formatting": int(formatting),
                "sections": int(sections),
                "readability": int(readability),
            }
        except Exception as e:
            return {
                "overall": 0,
                "keywords": 0,
                "formatting": 0,
                "sections": 0,
                "readability": 0,
                "error": str(e),
            }

    def _score_keywords(self) -> float:
        keywords = set(re.findall(r"\b([a-z]+[\w\-]*)\b", self.job))
        keywords = {k for k in keywords if len(k) > 3}
        if not keywords:
            return 50.0
        matches = sum(1 for k in keywords if k in self.resume)
        return (matches / len(keywords)) * 100

    def _score_formatting(self) -> float:
        return 85.0 if "|" not in self.resume else 70.0

    def _score_sections(self) -> float:
        sections = ["experience", "skills", "education", "contact"]
        present = sum(1 for s in sections if s in self.resume)
        return (present / len(sections)) * 100

    def _score_readability(self) -> float:
        return 80.0
