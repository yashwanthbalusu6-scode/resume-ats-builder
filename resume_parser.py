"""Resume parser - extract text from PDF/DOCX with better error handling."""
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
    SECTION_HEADERS = {
        "contact": r"(?:contact|personal info)",
        "summary": r"(?:professional summary|summary|objective|profile|about)",
        "experience": r"(?:professional experience|work experience|experience|employment)",
        "skills": r"(?:skills|technical skills|competencies|technologies)",
        "education": r"(?:education|academic|qualifications)",
        "projects": r"(?:projects|portfolio|side projects)",
        "certifications": r"(?:certifications|certificates|licenses)",
    }
    
    def __init__(self, file_path: str):
        self.file_path = Path(file_path)
        self.text: str = ""
        self.sections: Dict[str, str] = {}
    
    def parse(self) -> Dict[str, Any]:
        try:
            ext = self.file_path.suffix.lower()
            if ext == ".pdf":
                self._parse_pdf()
            elif ext in (".docx", ".doc"):
                self._parse_docx()
            else:
                self.text = self.file_path.read_text(encoding="utf-8", errors="ignore")
            
            if not self.text.strip():
                return {"full_text": "", "sections": {}, "error": "No text could be extracted. The file may be image-based (needs OCR) or empty."}
            
            self._extract_sections()
            return {"full_text": self.text, "sections": self.sections}
        except Exception as e:
            return {"full_text": "", "sections": {}, "error": f"{type(e).__name__}: {str(e)}"}
    
    def _parse_pdf(self) -> None:
        if not PdfReader:
            raise ImportError("PyPDF2 not installed. Run: pip install PyPDF2")
        reader = PdfReader(str(self.file_path))
        text_parts: List[str] = []
        for page in reader.pages:
            try:
                t = page.extract_text() or ""
                if t.strip():
                    text_parts.append(t)
            except Exception:
                continue
        self.text = "\n".join(text_parts)
    
    def _parse_docx(self) -> None:
        if not Document:
            raise ImportError("python-docx not installed. Run: pip install python-docx")
        doc = Document(str(self.file_path))
        parts: List[str] = []
        # Extract paragraphs
        for p in doc.paragraphs:
            if p.text.strip():
                parts.append(p.text)
        # Extract tables
        for table in doc.tables:
            for row in table.rows:
                for cell in row.cells:
                    if cell.text.strip():
                        parts.append(cell.text)
        self.text = "\n".join(parts)
    
    def _extract_sections(self) -> None:
        lines = self.text.split("\n")
        current_section = "header"
        current_content: List[str] = []
        for line in lines:
            line_lower = line.lower().strip()
            found = False
            for section, pattern in self.SECTION_HEADERS.items():
                if re.search(pattern, line_lower) and len(line.strip()) < 50:
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
