import io
import re
from typing import Any, Dict, List

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (HRFlowable, KeepTogether, ListFlowable, ListItem, PageBreak, Paragraph,
                                SimpleDocTemplate, Spacer, Table, TableStyle)


def esc(value: Any) -> str:
    if value is None:
        return ""
    return str(value).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def _as_list(value: Any) -> List[str]:
    if not value:
        return []
    if isinstance(value, str):
        parts = re.split(r"\n|;|,(?![^()]*\))", value) if "\n" in value or ";" in value else value.split(",")
        return [p.strip(" •-\t") for p in parts if p.strip(" •-\t")]
    if isinstance(value, (list, tuple)):
        out = []
        for v in value:
            if isinstance(v, dict):
                v = v.get("name") or v.get("title") or ""
            if str(v).strip():
                out.append(str(v).strip(" •-\t"))
        return out
    return [str(value)]


def _link(url: str, label: str = None) -> str:
    if not url:
        return ""
    href = url if url.startswith("http") else f"https://{url}"
    shown = label or re.sub(r"^https?://(www\.)?", "", url).rstrip("/")
    return f'<link href="{esc(href)}" color="#1d4ed8">{esc(shown)}</link>'


# ═══════════════════════════ STUDY NOTES ═══════════════════════════
class PDFNotesGenerator:
    """A4 study-notes PDFs: a single topic, or a whole-roadmap last-minute cheat sheet."""

    @staticmethod
    def _styles():
        base = getSampleStyleSheet()
        return {
            "title": ParagraphStyle("NTitle", parent=base["Title"], fontName="Helvetica-Bold", fontSize=18, leading=22,
                                    textColor=colors.HexColor("#1e1b4b"), alignment=0, spaceAfter=2),
            "meta": ParagraphStyle("NMeta", parent=base["Normal"], fontName="Helvetica", fontSize=9, textColor=colors.HexColor("#6366f1"), spaceAfter=8),
            "h2": ParagraphStyle("NH2", parent=base["Heading2"], fontName="Helvetica-Bold", fontSize=11.5, leading=14,
                                 textColor=colors.HexColor("#312e81"), spaceBefore=9, spaceAfter=4, keepWithNext=True),
            "stage": ParagraphStyle("NStage", parent=base["Heading1"], fontName="Helvetica-Bold", fontSize=14, leading=18,
                                    textColor=colors.white, backColor=colors.HexColor("#4f46e5"), borderPadding=(5, 6, 5, 6), spaceBefore=6, spaceAfter=8),
            "topic": ParagraphStyle("NTopic", parent=base["Heading2"], fontName="Helvetica-Bold", fontSize=12, leading=15,
                                    textColor=colors.HexColor("#1e1b4b"), spaceBefore=8, spaceAfter=3, keepWithNext=True),
            "body": ParagraphStyle("NBody", parent=base["Normal"], fontName="Helvetica", fontSize=9.5, leading=13.5, textColor=colors.HexColor("#1f2937")),
            "small": ParagraphStyle("NSmall", parent=base["Normal"], fontName="Helvetica", fontSize=8.5, leading=12, textColor=colors.HexColor("#374151")),
            "code": ParagraphStyle("NCode", parent=base["Code"], fontName="Courier", fontSize=8, leading=10.5, backColor=colors.HexColor("#f3f4f6"),
                                   borderPadding=6, textColor=colors.HexColor("#111827")),
        }

    @staticmethod
    def _bullets(items: List[str], style) -> ListFlowable:
        return ListFlowable([ListItem(Paragraph(esc(i), style), leftIndent=10) for i in items if i],
                            bulletType="bullet", start="•", leftIndent=12, bulletFontSize=8)

    @staticmethod
    def _topic_flowables(notes: Dict[str, Any], st: Dict[str, ParagraphStyle], compact: bool = False) -> list:
        flow = []
        if notes.get("executive_summary") and not compact:
            flow += [Paragraph("Overview", st["h2"]), Paragraph(esc(notes["executive_summary"]), st["body"])]
        if notes.get("internals_and_architecture") and not compact:
            flow += [Paragraph("How it works", st["h2"]), Paragraph(esc(notes["internals_and_architecture"]), st["body"])]
        concepts = notes.get("key_concepts") or []
        if concepts:
            flow.append(Paragraph("Key concepts", st["h2"]))
            items = [f"<b>{esc(c.get('name'))}</b>{(' — ' + esc(c.get('explanation'))) if c.get('explanation') else ''}" for c in concepts]
            flow.append(ListFlowable([ListItem(Paragraph(i, st["body"]), leftIndent=10) for i in items], bulletType="bullet", start="•", leftIndent=12))
        explained = notes.get("explained") or []
        if explained:
            flow.append(Paragraph("Explained simply", st["h2"]))
            for item in explained:
                flow.append(KeepTogether([Paragraph(f"<b>{esc(item.get('point'))}</b>", st["body"]),
                                          Paragraph(esc(item.get("explanation")), st["small"]), Spacer(1, 3)]))
        if notes.get("last_minute_notes"):
            flow += [Paragraph("Last-minute notes", st["h2"]), PDFNotesGenerator._bullets(notes["last_minute_notes"], st["body"])]
        if notes.get("code_example") and not compact:
            code = esc(notes["code_example"]).replace("\n", "<br/>").replace("  ", "&nbsp;&nbsp;")
            flow += [Paragraph("Code example", st["h2"]), Paragraph(code, st["code"])]
        qas = notes.get("interview_questions") or []
        if qas:
            flow.append(Paragraph("Interview questions", st["h2"]))
            for qa in qas:
                flow.append(KeepTogether([Paragraph(f"<b>Q. {esc(qa.get('question'))}</b>", st["body"]),
                                          Paragraph(f"A. {esc(qa.get('ideal_answer'))}", st["small"]), Spacer(1, 4)]))
        if notes.get("common_pitfalls") and not compact:
            flow += [Paragraph("Common pitfalls", st["h2"]), PDFNotesGenerator._bullets(notes["common_pitfalls"], st["body"])]
        res = notes.get("resources") or {}
        links = [f"Docs: {_link(d['url'], d['title'])}" for d in res.get("docs", [])] + \
                [f"Video: {_link(v['url'], v['title'])}" for v in res.get("videos", [])]
        if links:
            flow += [Paragraph("Resources", st["h2"])] + [Paragraph(l, st["small"]) for l in links]
        return flow

    @staticmethod
    def _doc(buffer: io.BytesIO, title: str) -> SimpleDocTemplate:
        return SimpleDocTemplate(buffer, pagesize=A4, leftMargin=18 * mm, rightMargin=18 * mm, topMargin=16 * mm, bottomMargin=16 * mm,
                                 title=title, author="GapX AI")

    @staticmethod
    def _footer(canvas, doc):
        canvas.saveState()
        canvas.setFont("Helvetica", 7.5)
        canvas.setFillColor(colors.HexColor("#9ca3af"))
        canvas.drawString(18 * mm, 9 * mm, "GapX AI · Placement preparation notes")
        canvas.drawRightString(A4[0] - 18 * mm, 9 * mm, f"Page {doc.page}")
        canvas.restoreState()

    @staticmethod
    def generate_notes_pdf(notes: Dict[str, Any]) -> io.BytesIO:
        buffer = io.BytesIO()
        st = PDFNotesGenerator._styles()
        story = [Paragraph(esc(notes.get("title", "Study Notes")), st["title"]),
                 Paragraph(esc(f"{notes.get('stage', '')} · {notes.get('role', '')}"), st["meta"]),
                 HRFlowable(width="100%", thickness=0.8, color=colors.HexColor("#c7d2fe"), spaceAfter=4)]
        story += PDFNotesGenerator._topic_flowables(notes, st)
        doc = PDFNotesGenerator._doc(buffer, notes.get("title", "Study Notes"))
        doc.build(story, onFirstPage=PDFNotesGenerator._footer, onLaterPages=PDFNotesGenerator._footer)
        buffer.seek(0)
        return buffer

    @staticmethod
    def generate_cheatsheet_pdf(role: str, topics: List[Dict[str, Any]]) -> io.BytesIO:
        buffer = io.BytesIO()
        st = PDFNotesGenerator._styles()
        story = [Paragraph(esc(f"{role}: Last-Minute Revision Notes"), st["title"]),
                 Paragraph(f"{len(topics)} topics · concepts, revision bullets, interview questions and video links", st["meta"]),
                 HRFlowable(width="100%", thickness=0.8, color=colors.HexColor("#c7d2fe"), spaceAfter=6)]
        current_stage = None
        for notes in topics:
            if notes.get("stage") != current_stage:
                current_stage = notes.get("stage")
                story.append(Paragraph(esc(current_stage), st["stage"]))
            story.append(Paragraph(esc(notes.get("title")), st["topic"]))
            story += PDFNotesGenerator._topic_flowables(notes, st, compact=True)
            story.append(HRFlowable(width="100%", thickness=0.4, color=colors.HexColor("#e5e7eb"), spaceBefore=6, spaceAfter=2))
        doc = PDFNotesGenerator._doc(buffer, f"{role} Last-Minute Notes")
        doc.build(story, onFirstPage=PDFNotesGenerator._footer, onLaterPages=PDFNotesGenerator._footer)
        buffer.seek(0)
        return buffer


# ═══════════════════════════ RESUME ═══════════════════════════
class PDFResumeGenerator:
    """One-column, A4, ATS-friendly resume.

    ATS rules followed: single column, real selectable text, standard section headings,
    no tables/images/icons for content, consistent dates, and clickable profile links.
    """

    SECTION_ORDER_FRESHER = ["summary", "education", "skills", "projects", "experience", "certifications", "achievements", "interests"]
    SECTION_ORDER_EXPERIENCED = ["summary", "skills", "experience", "projects", "education", "certifications", "achievements", "interests"]

    @staticmethod
    def _styles():
        base = getSampleStyleSheet()
        ink, muted = colors.HexColor("#111827"), colors.HexColor("#374151")
        return {
            "name": ParagraphStyle("RName", parent=base["Title"], fontName="Helvetica-Bold", fontSize=19, leading=23, textColor=ink, alignment=TA_CENTER, spaceAfter=1),
            "headline": ParagraphStyle("RHead", parent=base["Normal"], fontName="Helvetica", fontSize=10.5, leading=13, textColor=muted, alignment=TA_CENTER, spaceAfter=3),
            "contact": ParagraphStyle("RContact", parent=base["Normal"], fontName="Helvetica", fontSize=8.8, leading=12, textColor=muted, alignment=TA_CENTER),
            "section": ParagraphStyle("RSection", parent=base["Heading2"], fontName="Helvetica-Bold", fontSize=10.5, leading=13, textColor=ink, spaceBefore=8, spaceAfter=1, keepWithNext=True),
            "item": ParagraphStyle("RItem", parent=base["Normal"], fontName="Helvetica-Bold", fontSize=9.8, leading=12.5, textColor=ink),
            "sub": ParagraphStyle("RSub", parent=base["Normal"], fontName="Helvetica-Oblique", fontSize=9, leading=11.5, textColor=muted),
            "date": ParagraphStyle("RDate", parent=base["Normal"], fontName="Helvetica", fontSize=9, leading=12.5, textColor=muted, alignment=2),
            "body": ParagraphStyle("RBody", parent=base["Normal"], fontName="Helvetica", fontSize=9.3, leading=12.6, textColor=ink),
            "bullet": ParagraphStyle("RBullet", parent=base["Normal"], fontName="Helvetica", fontSize=9.2, leading=12.2, textColor=ink),
        }

    @staticmethod
    def _rule():
        return HRFlowable(width="100%", thickness=0.7, color=colors.HexColor("#111827"), spaceBefore=1, spaceAfter=4)

    @staticmethod
    def _row(left: str, right: str, st) -> Table:
        """Title on the left, dates on the right (a layout-only table ATS parsers read left to right)."""
        width = A4[0] - 32 * mm - 12  # frame width (page minus margins and frame padding)
        t = Table([[Paragraph(left, st["item"]), Paragraph(esc(right), st["date"])]], colWidths=[width * 0.72, width * 0.28])
        t.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP"), ("LEFTPADDING", (0, 0), (-1, -1), 0),
                               ("RIGHTPADDING", (0, 0), (-1, -1), 0), ("TOPPADDING", (0, 0), (-1, -1), 0), ("BOTTOMPADDING", (0, 0), (-1, -1), 0)]))
        return t

    @staticmethod
    def _bullets(lines: List[str], st) -> list:
        lines = [l for l in lines if l]
        if not lines:
            return []
        return [ListFlowable([ListItem(Paragraph(esc(l), st["bullet"]), leftIndent=9) for l in lines],
                             bulletType="bullet", start="•", leftIndent=11, bulletFontSize=8, spaceBefore=1)]

    @staticmethod
    def generate_resume_pdf(data: Dict[str, Any]) -> io.BytesIO:
        st = PDFResumeGenerator._styles()
        buffer = io.BytesIO()
        name = data.get("name") or data.get("full_name") or "Candidate Name"
        doc = SimpleDocTemplate(buffer, pagesize=A4, leftMargin=16 * mm, rightMargin=16 * mm, topMargin=13 * mm, bottomMargin=13 * mm,
                                title=f"{name} - Resume", author=name, subject=data.get("headline") or "Resume")
        story = [Paragraph(esc(name), st["name"])]
        if data.get("headline"):
            story.append(Paragraph(esc(data["headline"]), st["headline"]))

        contact = [esc(x) for x in (data.get("phone"), data.get("email"), data.get("location")) if x]
        contact += [_link(data[k]) for k in ("linkedin", "github", "portfolio") if data.get(k)]
        if contact:
            story.append(Paragraph("  |  ".join(contact), st["contact"]))
        story.append(Spacer(1, 3))

        def section(title: str, flowables: list):
            if flowables:
                story.append(KeepTogether([Paragraph(title.upper(), st["section"]), PDFResumeGenerator._rule(), flowables[0]]))
                story.extend(flowables[1:])

        builders = {
            "summary": lambda: [Paragraph(esc(data["summary"]), st["body"])] if data.get("summary") else [],
            "skills": lambda: PDFResumeGenerator._skills(data, st),
            "experience": lambda: PDFResumeGenerator._experience(data, st),
            "projects": lambda: PDFResumeGenerator._projects(data, st),
            "education": lambda: PDFResumeGenerator._education(data, st),
            "certifications": lambda: PDFResumeGenerator._bullets(_as_list(data.get("certifications")), st),
            "achievements": lambda: PDFResumeGenerator._bullets(_as_list(data.get("achievements")) + _as_list(data.get("hackathons")), st),
            "interests": lambda: [Paragraph(esc(", ".join(_as_list(data.get("interests")))), st["body"])] if _as_list(data.get("interests")) else [],
        }
        titles = {"summary": "Professional Summary", "skills": "Technical Skills", "experience": "Experience", "projects": "Projects",
                  "education": "Education", "certifications": "Certifications", "achievements": "Achievements", "interests": "Interests"}
        has_experience = bool(data.get("experience") or data.get("internships"))
        order = PDFResumeGenerator.SECTION_ORDER_EXPERIENCED if has_experience and not data.get("is_fresher", False) else PDFResumeGenerator.SECTION_ORDER_FRESHER
        for key in order:
            section(titles[key], builders[key]())

        doc.build(story)
        buffer.seek(0)
        return buffer

    @staticmethod
    def _skills(data: Dict[str, Any], st) -> list:
        rows = [("Languages", _as_list(data.get("languages"))), ("Frameworks & Libraries", _as_list(data.get("frameworks"))),
                ("Tools & Platforms", _as_list(data.get("tools"))), ("Core Skills", _as_list(data.get("skills")))]
        seen, out = set(), []
        for label, items in rows:
            uniq = [i for i in items if i.lower() not in seen]
            seen.update(i.lower() for i in uniq)
            if uniq:
                out.append(Paragraph(f"<b>{label}:</b> {esc(', '.join(uniq))}", st["body"]))
        return out

    @staticmethod
    def _experience(data: Dict[str, Any], st) -> list:
        out = []
        for e in list(data.get("experience") or []) + list(data.get("internships") or []):
            if not isinstance(e, dict):
                continue
            role, company = e.get("role") or e.get("title") or "", e.get("company") or e.get("organization") or ""
            left = f"{esc(role)}{(' — ' + esc(company)) if company else ''}"
            out.append(PDFResumeGenerator._row(left, e.get("dates") or e.get("duration") or "", st))
            if e.get("location"):
                out.append(Paragraph(esc(e["location"]), st["sub"]))
            out += PDFResumeGenerator._bullets(_as_list(e.get("bullets") or e.get("description")), st)
            out.append(Spacer(1, 4))
        return out

    @staticmethod
    def _projects(data: Dict[str, Any], st) -> list:
        out = []
        for p in data.get("projects") or []:
            if not isinstance(p, dict):
                continue
            title = p.get("name") or p.get("title") or "Project"
            stack = p.get("stack") or p.get("technologies") or ""
            left = f"{esc(title)}{(' | <font name=Helvetica-Oblique>' + esc(stack) + '</font>') if stack else ''}"
            out.append(PDFResumeGenerator._row(left, p.get("dates") or "", st))
            if p.get("link"):
                out.append(Paragraph(_link(p["link"]), st["sub"]))
            out += PDFResumeGenerator._bullets(_as_list(p.get("bullets") or p.get("description")), st)
            out.append(Spacer(1, 4))
        return out

    @staticmethod
    def _education(data: Dict[str, Any], st) -> list:
        items = data.get("education_items") or []
        if not items and data.get("education"):
            items = [{"degree": data.get("education"), "institution": data.get("college"), "year": data.get("semester") or data.get("grad_year"), "cgpa": data.get("cgpa")}]
        out = []
        for ed in items:
            if not isinstance(ed, dict):
                continue
            out.append(PDFResumeGenerator._row(esc(ed.get("degree") or ""), str(ed.get("year") or ""), st))
            sub = ", ".join(x for x in [str(ed.get("institution") or ""), f"CGPA: {ed['cgpa']}" if ed.get("cgpa") else ""] if x)
            if sub:
                out.append(Paragraph(esc(sub), st["sub"]))
            out.append(Spacer(1, 3))
        return out


class PDFExtractor:
    """Robust multi-engine PDF text extractor with normalization and fallback decoders."""

    @staticmethod
    def normalize_text(text: str) -> str:
        if not text:
            return ""
        import unicodedata
        import re
        # Unicode normalization (NFKC fixes combined accents and special characters)
        text = unicodedata.normalize("NFKC", text)
        # Replace common ligatures and special bullet characters
        ligatures = {
            "ﬁ": "fi", "ﬂ": "fl", "ﬀ": "ff", "ﬃ": "ffi", "ﬄ": "ffl",
            "–": "-", "—": "-", "\u2013": "-", "\u2014": "-",
            "\u2018": "'", "\u2019": "'", "\u201c": '"', "\u201d": '"',
            "\u2022": "•", "\u25cf": "•", "\u00a0": " ", "\ufeff": ""
        }
        for k, v in ligatures.items():
            text = text.replace(k, v)
        # Strip non-printable / control characters except \n, \r, \t
        text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]", "", text)
        # Replace 3+ consecutive newlines with 2
        text = re.sub(r"\n{3,}", "\n\n", text)
        return text.strip()

    @classmethod
    def extract_text(cls, pdf_bytes: bytes) -> str:
        if not pdf_bytes or len(pdf_bytes) < 10:
            return ""

        extracted = ""
        import logging
        log = logging.getLogger(__name__)

        # Engine 1: pypdf (PdfReader)
        try:
            import pypdf
            reader = pypdf.PdfReader(io.BytesIO(pdf_bytes))
            pages_text = []
            for i, page in enumerate(reader.pages):
                try:
                    t = page.extract_text()
                    if t and t.strip():
                        pages_text.append(t.strip())
                except Exception as pe:
                    log.debug(f"pypdf page {i} warning: {pe}")
            if pages_text:
                extracted = "\n\n".join(pages_text)
        except Exception as e:
            log.debug(f"pypdf extraction failed: {e}")

        # Engine 2: pdfminer.six (if pypdf returned empty or very short text)
        if len(extracted.strip()) < 40:
            try:
                from pdfminer.high_level import extract_text as pdfminer_extract_text
                miner_text = pdfminer_extract_text(io.BytesIO(pdf_bytes))
                if miner_text and len(miner_text.strip()) > len(extracted.strip()):
                    extracted = miner_text
            except Exception as e:
                log.debug(f"pdfminer extraction failed: {e}")

        # Engine 3: Fallback regex uncompressed stream parser for raw text objects
        if len(extracted.strip()) < 40:
            try:
                import re
                text_chunks = re.findall(rb"\(([\w\s\.\,\:\;\-\_\@\/\(\)]+)\)\s*(?:Tj|\'|\")", pdf_bytes)
                if text_chunks:
                    extracted = "\n".join([chunk.decode("latin1", errors="ignore") for chunk in text_chunks if chunk])
            except Exception as e:
                log.debug(f"Stream regex extraction failed: {e}")

        return cls.normalize_text(extracted)

