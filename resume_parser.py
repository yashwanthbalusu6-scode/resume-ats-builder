"""Resume parser - extract text from PDF/DOCX."""
import re
from pathlib import Path
from typing import Any, Dict, List

try:
    from PyPDF2 import PdfReader
except ImportError:
    PdfReader = None

try:
    from docx import Document
except ImportError:
    Document = None


class ResumeParser:
    """Parse resume from PDF/DOCX."""

    SECTION_HEADERS = {
        "contact": r"(?:contact|personal info|header)",
        "summary": r"(?:professional summary|summary|objective|profile)",
        "experience": r"(?:professional experience|work experience|experience)",
        "skills": r"(?:skills|technical skills|competencies)",
        "education": r"(?:education|academic|degree)",
    }

    def __init__(self, file_path: str):
        self.file_path = Path(file_path)
        self.text: str = ""
        self.sections: Dict[str, str] = {}

    def parse(self) -> Dict[str, Any]:
        try:
            if self.file_path.suffix.lower() == ".pdf":
                self._parse_pdf()
            elif self.file_path.suffix.lower() in (".docx", ".doc"):
                self._parse_docx()
            else:
                self.text = self.file_path.read_text(encoding="utf-8", errors="ignore")
            self._extract_sections()
            return {"full_text": self.text, "sections": self.sections}
        except Exception as e:
            return {"full_text": "", "sections": {}, "error": str(e)}

    def _parse_pdf(self) -> None:
        if not PdfReader:
            raise ImportError("PyPDF2 required")
        reader = PdfReader(str(self.file_path))
        text_parts: List[str] = []
        for page in reader.pages:
            try:
                t = page.extract_text() or ""
                text_parts.append(t)
            except Exception:
                continue
        self.text = "\n".join([t for t in text_parts if t])

    def _parse_docx(self) -> None:
        if not Document:
            raise ImportError("python-docx required")
        doc = Document(str(self.file_path))
        self.text = "\n".join([p.text for p in doc.paragraphs if p.text.strip()])

    def _extract_sections(self) -> None:
        lines = self.text.split("\n")
        current_section = "contact"
        current_content: List[str] = []

        for line in lines:
            found = False
            for section, pattern in self.SECTION_HEADERS.items():
                if re.search(pattern, line.lower()):
                    if current_content:
                        self.sections[current_section] = "\n".join(current_content)
                    current_section = section
                    current_content = []
                    found = True
                    break
            if not found and line.strip():
                current_content.append(line)

        if current_content:
            self.sections[current_section] = "\n".join(current_content)
