import os
import sys
from dataclasses import dataclass, field
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
)
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# ------------------------------------------------------------------------------
# Font Registration (Cross-Platform Windows / Linux)
# ------------------------------------------------------------------------------
def register_fonts():
    font_paths = [
        ('Arial', 'C:/Windows/Fonts/arial.ttf'),
        ('Arial-Bold', 'C:/Windows/Fonts/arialbd.ttf'),
        ('Arial-Italic', 'C:/Windows/Fonts/ariali.ttf'),
    ]
    for name, path in font_paths:
        if os.path.exists(path):
            pdfmetrics.registerFont(TTFont(name, path))
        else:
            print(f"Warning: Font {name} at {path} not found. Standard fonts will be used.")

register_fonts()


# ------------------------------------------------------------------------------
# Two-Pass Canvas for Accurate Header & "Page X of Y" Footer (English)
# ------------------------------------------------------------------------------
class NumberedCanvas(canvas.Canvas):
    def __init__(self, *args, **kwargs):
        super(NumberedCanvas, self).__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_decorations(num_pages)
            super(NumberedCanvas, self).showPage()
        super(NumberedCanvas, self).save()

    def draw_page_decorations(self, page_count):
        self.saveState()
        self.setFont('Arial', 8)
        self.setFillColor(colors.HexColor('#64748B'))

        # Top Header (pages > 1)
        if self._pageNumber > 1:
            header_text = getattr(self, '_doc_header_title', "AI Football Scouting Assistant -- Executive Technical Case Study")
            self.drawString(15 * mm, 287 * mm, header_text)
            self.setStrokeColor(colors.HexColor('#CBD5E1'))
            self.setLineWidth(0.5)
            self.line(15 * mm, 284 * mm, 195 * mm, 284 * mm)

        # Bottom Footer (all pages)
        page_text = f"Page {self._pageNumber} of {page_count}"
        self.drawRightString(195 * mm, 10 * mm, page_text)
        footer_link = getattr(self, '_doc_footer_link', "GitHub: https://github.com/Creeepling/ai-football-scouting-bot")
        self.drawString(15 * mm, 10 * mm, f"{footer_link} | Confidential")
        self.setStrokeColor(colors.HexColor('#CBD5E1'))
        self.setLineWidth(0.5)
        self.line(15 * mm, 14 * mm, 195 * mm, 14 * mm)
        self.restoreState()


# ------------------------------------------------------------------------------
# Generic Data Structure for Any Project Case Study
# ------------------------------------------------------------------------------
@dataclass
class ProjectCaseStudy:
    project_name: str
    subtitle: str
    tech_stack: list[str]
    github_url: str
    my_role: str
    problem: list[str]
    architecture_overview: str
    architecture_flow: str
    what_i_personally_built: list[str]
    what_was_technically_difficult: list[str]
    result: list[str]
    demo_url: str = ""
    what_i_would_do_differently: list[str] = field(default_factory=list)


# ------------------------------------------------------------------------------
# Reusable Vertical / Portrait PDF Case Study Generator (All English)
# ------------------------------------------------------------------------------
def generate_vertical_case_study_pdf(case: ProjectCaseStudy, output_path: str = "case_study.pdf"):
    """
    Renders an executive vertical A4 case study PDF in 100% English.
    """
    doc = SimpleDocTemplate(
        output_path,
        pagesize=A4,
        leftMargin=15 * mm,
        rightMargin=15 * mm,
        topMargin=15 * mm,
        bottomMargin=18 * mm
    )

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Normal'],
        fontName='Arial-Bold',
        fontSize=15,
        leading=19,
        textColor=colors.HexColor('#0F172A'),
        spaceAfter=3
    )

    subtitle_style = ParagraphStyle(
        'DocSubTitle',
        parent=styles['Normal'],
        fontName='Arial',
        fontSize=9,
        leading=12.5,
        textColor=colors.HexColor('#475569'),
        spaceAfter=4
    )

    section_header_style = ParagraphStyle(
        'SecHeader',
        parent=styles['Normal'],
        fontName='Arial-Bold',
        fontSize=9.5,
        leading=12.5,
        textColor=colors.HexColor('#1E3A8A'),
        spaceBefore=4.5,
        spaceAfter=1.5,
        keepWithNext=True
    )

    body_style = ParagraphStyle(
        'Body',
        parent=styles['Normal'],
        fontName='Arial',
        fontSize=8,
        leading=11,
        textColor=colors.HexColor('#334155'),
        spaceAfter=1.5
    )

    bullet_style = ParagraphStyle(
        'Bullet',
        parent=styles['Normal'],
        fontName='Arial',
        fontSize=8,
        leading=11,
        textColor=colors.HexColor('#1E293B'),
        leftIndent=9,
        firstLineIndent=-5,
        spaceAfter=1
    )

    callout_style = ParagraphStyle(
        'Callout',
        parent=styles['Normal'],
        fontName='Arial',
        fontSize=8,
        leading=11,
        textColor=colors.HexColor('#0F172A')
    )

    story = []

    # 1. Header & Title
    story.append(Paragraph(f"{case.project_name} -- Project Case Study", title_style))
    story.append(Paragraph(case.subtitle, subtitle_style))

    # 2. Metadata Callout Box
    tech_pills = ", ".join(case.tech_stack)
    meta_lines = [
        f"<b>GitHub Repository:</b> <font color='#2563EB'><u><a href='{case.github_url}'>{case.github_url}</a></u></font>"
    ]
    if case.demo_url:
        meta_lines.append(f"<b>Demo / Interface:</b> {case.demo_url}")
    meta_lines.append(f"<b>Tech Stack:</b> {tech_pills}")
    meta_html = "<br/>".join(meta_lines)

    meta_p = Paragraph(meta_html, callout_style)
    meta_table = Table([[meta_p]], colWidths=[180 * mm])
    meta_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#F1F5F9')),
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#CBD5E1')),
        ('TOPPADDING', (0, 0), (-1, -1), 3.5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3.5),
        ('LEFTPADDING', (0, 0), (-1, -1), 7),
        ('RIGHTPADDING', (0, 0), (-1, -1), 7),
    ]))
    story.append(meta_table)
    story.append(Spacer(1, 2.5))

    # 3. Problem & Context
    story.append(Paragraph("1. Problem & Product Context", section_header_style))
    for p_item in case.problem:
        story.append(Paragraph(p_item, body_style))

    # 4. My Role & Ownership
    story.append(Paragraph("2. My Role & Engineering Ownership", section_header_style))
    story.append(Paragraph(case.my_role, body_style))

    # 5. Architecture & Core Philosophy
    story.append(Paragraph("3. System Architecture & Core Philosophy", section_header_style))
    story.append(Paragraph(case.architecture_overview, body_style))
    if case.architecture_flow:
        story.append(Paragraph(f"<b>Dataflow Pipeline:</b> {case.architecture_flow}", body_style))

    # 6. What I Personally Built
    story.append(Paragraph("4. What I Personally Built", section_header_style))
    for b_item in case.what_i_personally_built:
        story.append(Paragraph(f"- {b_item}", bullet_style))

    # 7. What Was Technically Difficult
    story.append(Paragraph("5. Key Technical Challenges & Solutions", section_header_style))
    for d_item in case.what_was_technically_difficult:
        story.append(Paragraph(f"- {d_item}", bullet_style))

    # 8. Results & Impact
    story.append(Paragraph("6. Results & Production Impact", section_header_style))
    for r_item in case.result:
        story.append(Paragraph(f"- {r_item}", bullet_style))

    # 9. What I Would Do Differently
    if case.what_i_would_do_differently:
        story.append(Paragraph("7. What I Would Do Differently Today", section_header_style))
        for diff_item in case.what_i_would_do_differently:
            story.append(Paragraph(f"- {diff_item}", bullet_style))

    # Build with custom NumberedCanvas
    doc.build(story, canvasmaker=NumberedCanvas)
    print(f"English Vertical Case Study PDF generated successfully at: {output_path}")


# ------------------------------------------------------------------------------
# Case Study Data in 100% English: AI Football Scouting Assistant
# ------------------------------------------------------------------------------
scouting_bot_case = ProjectCaseStudy(
    project_name="AI Football Scouting Assistant",
    subtitle="Serverless AI Analytics: Python Deterministic Stats Engine + LangChain ReAct Orchestration",
    tech_stack=[
        "Python 3.11", "Google Cloud Functions (Gen 2)", "LangChain", "Wyscout API v3",
        "MongoDB Atlas", "Google Cloud Storage", "Matplotlib", "Seaborn", "Telegram Bot API"
    ],
    github_url="https://github.com/Creeepling/ai-football-scouting-bot",
    demo_url="",
    my_role="<b>Sole AI & Backend Engineer:</b> End-to-end architecture and full-lifecycle implementation -- from mathematical metric normalization and MongoDB aggregation pipelines to LangChain ReAct agents, Matplotlib rendering engines, and GCP serverless infrastructure.",
    problem=[
        "Initial football scouting and candidate screening requires manual data collation across disparate silos (Transfermarkt for biographical details and Wyscout for raw match events), tedious Per-90 and league-relative percentile normalization, manual chart generation, and narrative drafting.",
        "The product fully automates this scouting workflow: given a raw player profile URL, the system resolves entities, queries match databases, computes deterministic league percentiles, renders visual scouting cards, and synthesizes tactical scout evaluations directly in Telegram."
    ],
    architecture_overview=(
        "<b>Core Philosophy (Deterministic Truth vs. Cognitive Synthesis):</b> Strict separation between mathematical computation and natural language generation. "
        "All statistical metrics, Per-90 conversions, percentile ranks (0-100), and Bayesian adjustments are calculated <b>deterministically in Python/Pandas</b>. "
        "The LLM is <b>never used as a source of numerical truth (numerical calculations are kept outside the LLM path)</b> and is strictly confined to fuzzy entity resolution, autonomous tool calling (ReAct loop), and qualitative tactical narrative synthesis."
    ),
    architecture_flow=(
        "Telegram Webhook <b>-></b> GCP Cloud Function Router <b>-></b> Thread-Safe Context (<code>contextvars</code>) <b>-></b> "
        "LangChain ReAct Agent <b>-></b> External APIs (Wyscout API v3, MongoDB Atlas, Serper API) <b>-></b> "
        "Deterministic Engine (Pandas / NumPy) <b>-></b> In-Memory Viz Engine (Matplotlib / Seaborn) <b>-></b> "
        "GCS Session Store <b>-></b> Telegram Bot API."
    ),
    what_i_personally_built=[
        "<b>Modular Serverless Architecture:</b> Decoupled Python service deployed on Google Cloud Functions (Gen 2 / Cloud Run) with thread-safe session isolation via <code>contextvars</code>.",
        "<b>Deterministic Stats Engine:</b> Implemented Per-90 normalization formulas, league-position percentile distributions, and Bayesian smoothing (<code>bayes_rank</code>).",
        "<b>Data Pipelines & Aggregations:</b> Multi-stage MongoDB Atlas aggregation pipelines grouping raw match events across seasons, paired with custom Wyscout API v3 REST wrappers.",
        "<b>AI Tool Registry:</b> 9 specialized LangChain tools (URL scraping, season switching, metric deep-dives, heatmaps, position breakdown).",
        "<b>Automated Visual Generator:</b> In-memory Matplotlib & Seaborn rendering pipeline generating scouting cards, peer histograms, and heatmaps with zero memory leaks.",
        "<b>DevOps & Security:</b> Zero-secret deployment via GCP Secret Manager, CI/CD in GitHub Actions using Workload Identity Federation (WIF), and Telegram webhook secret token verification."
    ],
    what_was_technically_difficult=[
        "<b>Small-Sample Variance & Outliers:</b> Players with 2 successful dribbles on 2 attempts skewed percentiles to 100%. Solved by engineering a <b>Bayesian weighted formula</b> incorporating league 80th-percentile priors: <code>(R*v + C*m)/(v + m)</code>.",
        "<b>Fuzzy Cross-Platform Resolution:</b> Unstructured Transfermarkt URLs with localized transliterations mapped to Wyscout's rigid search index via a two-stage pipeline (Google Serper API + LLM biographical extraction + Wyscout search indexing).",
        "<b>Serverless Memory Management:</b> Eliminated container memory bloat in reusable Cloud Function instances by streaming plots directly in <code>io.BytesIO</code> buffers and enforcing deterministic <code>plt.close(fig)</code> deallocations."
    ],
    result=[
        "<b>End-to-End Automation:</b> Fully automated scouting intelligence pipeline from incoming URL to visual cards and tactical reports without human intervention.",
        "<b>Multi-Turn Interactive UX:</b> Bi-lingual (EN/RU) inline keyboard menus enabling granular drill-down into specific seasons, isolated metrics, and position distributions.",
        "<b>Production Stability:</b> Stateless, thread-safe, and secure cloud architecture scaling to zero with no hardcoded credentials."
    ],
    what_i_would_do_differently=[
        "<b>Decoupled Asynchronous Queue (Cloud Tasks / Pub/Sub):</b> Offload heavy multi-season MongoDB aggregations to background workers with push callbacks to eliminate Telegram webhook timeout risks.",
        "<b>Vector Similarity Search (pgvector / Qdrant):</b> Embed normalized percentile vectors to enable automated <i>'Find statistical twins / replacement candidates'</i> search across leagues.",
        "<b>Redis Caching Layer:</b> Implement distributed caching for static Wyscout profiles and seasonal baselines to minimize third-party API costs.",
        "<b>Modern LangChain LCEL:</b> Migrate from string-based ReAct agent parsing to Pydantic Function Calling with structured outputs."
    ]
)


if __name__ == "__main__":
    out_file = sys.argv[1] if len(sys.argv) > 1 else "AI_Football_Scouting_Bot_Brief.pdf"
    generate_vertical_case_study_pdf(scouting_bot_case, out_file)
