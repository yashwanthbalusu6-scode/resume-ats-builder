"""Resume parser - extract text from PDF, DOCX, DOC, TXT, RTF, MD."""
import re
import zipfile
from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    from PyPDF2 import PdfReader
except ImportError:
    PdfReader = None

try:
    import pdfplumber  # type: ignore
except ImportError:
    pdfplumber = None  # type: ignore

try:
    from docx import Document
except ImportError:
    Document = None


class ResumeParser:
    """Parse resume text from common file formats with multiple fallbacks."""

    SECTION_HEADERS = {
        "contact": r"(?:contact|personal info|header)",
        "summary": r"(?:professional summary|summary|objective|profile)",
        "experience": r"(?:professional experience|work experience|experience)",
        "skills": r"(?:skills|technical skills|competencies)",
        "education": r"(?:education|academic|degree)",
    }

    SUPPORTED_EXTS = {".pdf", ".docx", ".doc", ".txt", ".rtf", ".md"}

    def __init__(self, file_path: str):
        self.file_path = Path(file_path)
        self.text: str = ""
        self.sections: Dict[str, str] = {}
        self.method_used: Optional[str] = None
        self.warnings: List[str] = []

    def parse(self) -> Dict[str, Any]:
        try:
            ext = self.file_path.suffix.lower()
            if ext == ".pdf":
                self._parse_pdf()
            elif ext == ".docx":
                self._parse_docx()
            elif ext == ".doc":
                self._parse_doc()
            elif ext == ".rtf":
                self._parse_rtf()
            elif ext in (".txt", ".md", ""):
                self._parse_text()
            else:
                # Last-resort: try as text
                self._parse_text()
                self.warnings.append(
                    f"Unknown extension '{ext}' — read as plain text"
                )

            self.text = self._clean(self.text)
            self._extract_sections()

            if not self.text.strip():
                return {
                    "full_text": "",
                    "sections": {},
                    "method": self.method_used,
                    "warnings": self.warnings,
                    "error": (
                        "No text could be extracted. "
                        "If your PDF is scanned/image-based, please paste the resume "
                        "text directly into the text area."
                    ),
                }

            if len(self.text.strip()) < 100:
                self.warnings.append(
                    f"Only {len(self.text.strip())} characters extracted — "
                    "the file may be mostly images. Consider pasting text directly."
                )

            return {
                "full_text": self.text,
                "sections": self.sections,
                "method": self.method_used,
                "warnings": self.warnings,
            }
        except Exception as e:
            return {
                "full_text": "",
                "sections": {},
                "method": self.method_used,
                "warnings": self.warnings,
                "error": str(e),
            }

    # ── PDF ──────────────────────────────────────────────────────────────────
    def _parse_pdf(self) -> None:
        # Try PyPDF2 first
        text = ""
        if PdfReader is not None:
            try:
                reader = PdfReader(str(self.file_path))
                parts: List[str] = []
                for page in reader.pages:
                    try:
                        parts.append(page.extract_text() or "")
                    except Exception:
                        continue
                text = "\n".join(p for p in parts if p)
                if text.strip():
                    self.method_used = "PyPDF2"
            except Exception as e:
                self.warnings.append(f"PyPDF2 failed: {e}")

        # Fallback to pdfplumber if PyPDF2 returned nothing useful
        if not text.strip() and pdfplumber is not None:
            try:
                parts = []
                with pdfplumber.open(str(self.file_path)) as pdf:
                    for page in pdf.pages:
                        try:
                            parts.append(page.extract_text() or "")
                        except Exception:
                            continue
                text = "\n".join(p for p in parts if p)
                if text.strip():
                    self.method_used = "pdfplumber"
            except Exception as e:
                self.warnings.append(f"pdfplumber failed: {e}")

        if not text.strip() and PdfReader is None and pdfplumber is None:
            raise ImportError("Install PyPDF2 or pdfplumber to parse PDFs")

        self.text = text

    # ── DOCX ─────────────────────────────────────────────────────────────────
    def _parse_docx(self) -> None:
        if Document is None:
            # Fallback: read raw XML from the .docx zip
            self._parse_docx_raw()
            return
        try:
            doc = Document(str(self.file_path))
            paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
            # Also pull text from tables (resumes often use tables for layout)
            for table in doc.tables:
                for row in table.rows:
                    for cell in row.cells:
                        if cell.text.strip():
                            paragraphs.append(cell.text)
            self.text = "\n".join(paragraphs)
            self.method_used = "python-docx"
        except Exception as e:
            self.warnings.append(f"python-docx failed: {e}")
            self._parse_docx_raw()

    def _parse_docx_raw(self) -> None:
        try:
            with zipfile.ZipFile(self.file_path) as z:
                with z.open("word/document.xml") as f:
                    xml = f.read().decode("utf-8", errors="ignore")
            text = re.sub(r"<[^>]+>", " ", xml)
            text = re.sub(r"\s+", " ", text).strip()
            self.text = text
            self.method_used = "docx-xml-fallback"
        except Exception as e:
            raise RuntimeError(f"Could not read DOCX: {e}")

    # ── DOC (legacy Word) ────────────────────────────────────────────────────
    def _parse_doc(self) -> None:
        # python-docx does NOT support legacy .doc; do a best-effort byte scan
        try:
            data = self.file_path.read_bytes()
            # Pull printable ASCII runs
            text = re.sub(rb"[^\x20-\x7E\n\r\t]+", b" ", data)
            text = text.decode("utf-8", errors="ignore")
            text = re.sub(r"\s{2,}", " ", text).strip()
            self.text = text
            self.method_used = "doc-byte-scan"
            self.warnings.append(
                "Legacy .doc support is best-effort. "
                "Save as .docx or .pdf for higher fidelity."
            )
        except Exception as e:
            raise RuntimeError(f"Could not read .doc: {e}")

    # ── RTF ──────────────────────────────────────────────────────────────────
    def _parse_rtf(self) -> None:
        try:
            raw = self.file_path.read_text(encoding="utf-8", errors="ignore")
            # Strip RTF control words and groups
            text = re.sub(r"\\[a-zA-Z]+-?\d*\s?", "", raw)
            text = re.sub(r"[{}]", "", text)
            text = re.sub(r"\\'[0-9a-fA-F]{2}", "", text)
            self.text = text
            self.method_used = "rtf-strip"
        except Exception as e:
            raise RuntimeError(f"Could not read RTF: {e}")

    # ── TXT / MD ─────────────────────────────────────────────────────────────
    def _parse_text(self) -> None:
        for enc in ("utf-8", "latin-1", "cp1252"):
            try:
                self.text = self.file_path.read_text(encoding=enc, errors="ignore")
                self.method_used = f"text ({enc})"
                return
            except Exception:
                continue
        self.text = self.file_path.read_text(encoding="utf-8", errors="ignore")
        self.method_used = "text (utf-8 lossy)"

    # ── Cleaning ─────────────────────────────────────────────────────────────
    @staticmethod
    def _clean(text: str) -> str:
        # Normalize line endings and collapse runs of blank lines
        text = text.replace("\r\n", "\n").replace("\r", "\n")
        text = re.sub(r"\n{3,}", "\n\n", text)
        # Strip leading/trailing whitespace per line
        text = "\n".join(line.rstrip() for line in text.split("\n"))
        return text.strip()

    # ── Section extraction ───────────────────────────────────────────────────
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
