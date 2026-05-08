"""Job parser - extract skills and company from job description."""
import re
from typing import Any, Dict, List


class JobParser:
    """Extract skills and company from job description."""

    TECH_SKILLS = {
        "python", "java", "javascript", "typescript", "go", "rust", "c++",
        "react", "vue", "angular", "node.js", "django", "flask", "fastapi",
        "sql", "postgresql", "mongodb", "redis", "docker", "kubernetes",
        "aws", "azure", "gcp", "terraform", "git", "ci/cd",
        "tensorflow", "pytorch", "pandas", "numpy", "spark", "kafka",
        "graphql", "rest", "microservices", "linux", "bash",
    }

    def __init__(self, job_description: str):
        self.text = (job_description or "").lower()
        self.original = job_description or ""

    def parse(self) -> Dict[str, Any]:
        try:
            return {
                "job_title": self._extract_job_title(),
                "company": self._extract_company(),
                "required_skills": self._extract_skills(),
            }
        except Exception as e:
            return {
                "job_title": "Unknown Role",
                "company": "Unknown Company",
                "required_skills": [],
                "error": str(e),
            }

    def _extract_job_title(self) -> str:
        for line in self.original.split("\n")[:10]:
            if any(kw in line.lower() for kw in ["engineer", "developer", "manager", "scientist", "analyst", "designer"]):
                return line.strip()
        return "Unknown Role"

    def _extract_company(self) -> str:
        match = re.search(r"([A-Z][A-Za-z\s&]{3,30})\s+(?:is hiring|is looking|seeks|is seeking)", self.original)
        return match.group(1).strip() if match else "Unknown Company"

    def _extract_skills(self) -> List[str]:
        skills = [skill for skill in self.TECH_SKILLS if skill in self.text]
        return sorted(skills)
