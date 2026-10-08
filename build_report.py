"""Build report.pdf from report.md and team.json. Requires: pip install reportlab."""

from __future__ import annotations

import json
from pathlib import Path
import re
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    Flowable, KeepTogether, PageBreak, Paragraph, Preformatted,
    SimpleDocTemplate, Spacer, Table, TableStyle,
)

ROOT = Path(__file__).resolve().parent
INK = colors.HexColor("#17324a")
TEAL = colors.HexColor("#007f78")
MUTED = colors.HexColor("#536b7c")
PALE = colors.HexColor("#edf5f7")
WIDTH = A4[0] - 104


def register_fonts():
    candidates = [
        (Path("C:/Windows/Fonts/segoeui.ttf"), Path("C:/Windows/Fonts/segoeuib.ttf")),
        (Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"), Path("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf")),
    ]
    for regular, bold in candidates:
        if regular.exists() and bold.exists():
            pdfmetrics.registerFont(TTFont("Body", str(regular)))
            pdfmetrics.registerFont(TTFont("Body-Bold", str(bold)))
            pdfmetrics.registerFontFamily("Body", normal="Body", bold="Body-Bold", italic="Body", boldItalic="Body-Bold")
            return "Body", "Body-Bold"
    return "Helvetica", "Helvetica-Bold"


FONT, BOLD = register_fonts()
STYLES = {
    "body": ParagraphStyle("BodyText", fontName=FONT, fontSize=10, leading=14, textColor=INK, spaceAfter=7),
    "h1": ParagraphStyle("Title", fontName=BOLD, fontSize=36, leading=42, textColor=INK, spaceBefore=14, spaceAfter=12),
    "h2": ParagraphStyle("Section", fontName=BOLD, fontSize=20, leading=25, textColor=INK, spaceAfter=12, keepWithNext=True),
    "h3": ParagraphStyle("Subsection", fontName=BOLD, fontSize=11.5, leading=15, textColor=TEAL, spaceBefore=9, spaceAfter=5, keepWithNext=True),
    "cell": ParagraphStyle("Cell", fontName=FONT, fontSize=9, leading=12, textColor=INK),
    "head": ParagraphStyle("Head", fontName=BOLD, fontSize=9, leading=12, textColor=colors.white),
    "list": ParagraphStyle("List", fontName=FONT, fontSize=9.8, leading=13.7, textColor=INK, leftIndent=13, firstLineIndent=-11, spaceAfter=5),
    "code": ParagraphStyle("Code", fontName="Courier", fontSize=8.1, leading=11, textColor=INK, backColor=PALE, borderPadding=10, spaceBefore=5, spaceAfter=12),
    "caption": ParagraphStyle("Caption", fontName=FONT, fontSize=8.5, leading=11, textColor=MUTED, alignment=TA_CENTER, spaceAfter=7),
}


def markup(text):
    text = escape(text)
    text = re.sub(r"\[([^\]]+)\]\((https?://[^ )]+)\)", r'<a href="\2" color="#007f78">\1</a>', text)
    text = re.sub(r"`([^`]+)`", r'<font name="Courier" size="8.7">\1</font>', text)
    text = re.sub(r"\*\*([^*]+)\*\*", r"<b>\1</b>", text)
    return text


def p(text, style="body"):
    return Paragraph(markup(text), STYLES[style])


def make_table(rows, widths=None):
    n = len(rows[0])
    if widths is None:
        if n == 2:
            widths = [WIDTH * .32, WIDTH * .68]
        elif n == 3:
            widths = [WIDTH * .13, WIDTH * .29, WIDTH * .58]
        else:
            widths = [WIDTH / n] * n
    content = [[p(cell.strip(), "head" if i == 0 else "cell") for cell in row] for i, row in enumerate(rows)]
    table = Table(content, colWidths=widths, repeatRows=1, hAlign="LEFT")
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), INK),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [PALE, colors.white]),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("LINEBELOW", (0, -1), (-1, -1), .5, colors.HexColor("#d3e2e8")),
    ]))
    return table


class Architecture(Flowable):
    def __init__(self):
        super().__init__()
        self.width, self.height = WIDTH, 82

    def draw(self):
        c = self.canv
        box = 143
        for x, title, desc in ((0, "main.py", "Tkinter controls + display"), (174, "engine.py", "Rules + BFS + visible snapshot"), (348, "hints.py", "Deductions + risk ranking")):
            c.setFillColor(PALE)
            c.roundRect(x, 20, box, 53, 7, fill=1, stroke=0)
            c.setFillColor(TEAL)
            c.setFont(BOLD, 11)
            c.drawCentredString(x + box / 2, 53, title)
            c.setFillColor(INK)
            c.setFont(FONT, 7.7)
            c.drawCentredString(x + box / 2, 35, desc)
        c.setStrokeColor(TEAL)
        for x in (146, 320):
            c.line(x, 47, x + 25, 47)
            c.line(x + 25, 47, x + 20, 50)
            c.line(x + 25, 47, x + 20, 44)
        c.setFillColor(MUTED)
        c.setFont(FONT, 8)
        c.drawCentredString(WIDTH / 2, 4, "The hint engine sees the public snapshot, never the hidden mine layout.")


class BFSExample(Flowable):
    def __init__(self):
        super().__init__()
        self.width, self.height = WIDTH, 130

    def draw(self):
        c = self.canv
        size = 29
        for x0, title, opened in ((72, "Before: click (3,3)", False), (326, "After BFS: 8 safe cells", True)):
            c.setFont(BOLD, 9)
            c.setFillColor(INK)
            c.drawCentredString(x0 + size * 1.5, 116, title)
            for r in range(3):
                for col in range(3):
                    x, y = x0 + col * size, 16 + (2 - r) * size
                    mine = r == col == 0
                    value = 1 if r <= 1 and col <= 1 else 0
                    c.setFillColor(PALE if opened else INK)
                    c.roundRect(x, y, size - 2, size - 2, 3, fill=1, stroke=0)
                    c.setFont(BOLD, 11)
                    c.setFillColor(TEAL if opened else colors.white)
                    text = "M" if mine else (str(value) if opened else "?")
                    c.drawCentredString(x + 13.5, y + 10, text)
                    if (r, col) == (2, 2):
                        c.setStrokeColor(colors.HexColor("#e7a82c"))
                        c.setLineWidth(2)
                        c.roundRect(x, y, size - 2, size - 2, 3, fill=0, stroke=1)
        c.setStrokeColor(TEAL)
        c.setLineWidth(1.5)
        c.line(197, 62, 282, 62)
        c.line(282, 62, 275, 66)
        c.line(282, 62, 275, 58)
        c.setFont(BOLD, 9)
        c.setFillColor(TEAL)
        c.drawCentredString(240, 75, "BFS")
        c.setFont(FONT, 8)
        c.setFillColor(MUTED)
        c.drawCentredString(WIDTH / 2, 1, "M is shown for explanation. Zero labels represent blank tiles in the game.")


def footer(canvas, doc):
    canvas.saveState()
    canvas.setFillColor(MUTED)
    canvas.setFont(FONT, 8)
    canvas.drawString(52, A4[1] - 31, "CO3061  /  HOMEWORK 1")
    canvas.drawRightString(A4[0] - 52, A4[1] - 31, "MINESWEEPER  /  TOPIC 1")
    canvas.setStrokeColor(colors.HexColor("#cbdfe5"))
    canvas.line(52, A4[1] - 39, A4[0] - 52, A4[1] - 39)
    canvas.drawString(52, 29, "Python + Tkinter  |  Design and algorithm report")
    canvas.drawRightString(A4[0] - 52, 29, str(doc.page))
    canvas.restoreState()


def build():
    team = json.loads((ROOT / "team.json").read_text(encoding="utf-8"))
    members = team["members"]
    group_name = team.get("group_name", "CO3061 project")
    pending = not members or any("TO COMPLETE" in str(v) or not str(v).strip() for m in members for v in (m.get("full_name", ""), m.get("contribution_percent", "")))
    if not pending:
        for member in members:
            if not 0 <= float(member["contribution_percent"]) <= 100:
                raise ValueError("Contribution percentages must be between 0 and 100.")
    lines = (ROOT / "report.md").read_text(encoding="utf-8").replace("{{GROUP_NAME}}", group_name).splitlines()
    story = []
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        i += 1
        if not line:
            continue
        if line == "---":
            story.append(PageBreak())
        elif line == "{{DRAFT_NOTICE}}":
            if pending:
                notice = Table([[p("**DRAFT - GROUP DETAILS TO COMPLETE**\nFill in names and contributions before submission.")]], colWidths=[WIDTH])
                notice.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#fff3d6")), ("BOX", (0, 0), (-1, -1), .6, colors.HexColor("#d9ae52")), ("LEFTPADDING", (0, 0), (-1, -1), 12), ("TOPPADDING", (0, 0), (-1, -1), 9), ("BOTTOMPADDING", (0, 0), (-1, -1), 6)]))
                story.extend([notice, Spacer(1, 8)])
        elif line == "{{TEAM_TABLE}}":
            rows = [["Full name", "Contribution (%)"]]
            rows.extend([[str(m.get("full_name", "TO COMPLETE")), str(m.get("contribution_percent", "TO COMPLETE"))] for m in members])
            story.extend([make_table(rows, [WIDTH * .65, WIDTH * .35]), Spacer(1, 8)])
        elif line == "{{ARCHITECTURE}}":
            story.extend([Architecture(), Spacer(1, 7)])
        elif line == "{{BFS_DIAGRAM}}":
            story.extend([BFSExample(), Spacer(1, 7)])
        elif line.startswith("```"):
            code = []
            while i < len(lines) and not lines[i].startswith("```"):
                code.append(lines[i])
                i += 1
            i += 1
            story.append(Preformatted("\n".join(code), STYLES["code"]))
        elif line.startswith("|"):
            rows = [[cell.strip() for cell in line.strip("|").split("|")]]
            while i < len(lines) and lines[i].strip().startswith("|"):
                candidate = [cell.strip() for cell in lines[i].strip().strip("|").split("|")]
                if not all(re.fullmatch(r":?-+:?", cell) for cell in candidate):
                    rows.append(candidate)
                i += 1
            story.extend([make_table(rows), Spacer(1, 9)])
        elif line.startswith("### "):
            story.append(p(line[4:], "h3"))
        elif line.startswith("## "):
            story.append(p(line[3:], "h2"))
        elif line.startswith("# "):
            story.append(p(line[2:], "h1"))
        elif line.startswith("- ") or re.match(r"^\d+\. ", line):
            story.append(p(line, "list"))
        else:
            paragraph = [line]
            while i < len(lines) and lines[i].strip() and not re.match(r"^(#|\||```|---|\{\{|- |\d+\. )", lines[i].strip()):
                paragraph.append(lines[i].strip())
                i += 1
            story.append(p(" ".join(paragraph)))
    document = SimpleDocTemplate(str(ROOT / "report.pdf"), pagesize=A4,
        rightMargin=52, leftMargin=52, topMargin=56, bottomMargin=49,
        title=f"{group_name} - Minesweeper - CO3061 Homework 1",
        author=", ".join(m.get("full_name", "") for m in members),
        subject="BFS flood fill and explainable Minesweeper hints")
    document.build(story, onFirstPage=footer, onLaterPages=footer)
    print(f"Created {ROOT / 'report.pdf'}")


if __name__ == "__main__":
    build()
