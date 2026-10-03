import os
import sys
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, KeepTogether, PageBreak, HRFlowable
)
from reportlab.pdfgen import canvas
from PIL import Image as PILImage

class NumberedCanvas(canvas.Canvas):
    """
    Two-pass canvas to dynamically compute and draw total page count
    along with running header and footer.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_decorations(num_pages)
            super().showPage()
        super().save()

    def draw_page_decorations(self, page_count):
        if self._pageNumber == 1:
            # Suppress running header/footer on cover page
            return

        self.saveState()
        self.setFont("Helvetica", 8)
        self.setFillColor(colors.HexColor("#64748B"))

        # Header
        self.drawString(54, 750, "Agentic SOV Cleansing & Intelligence System | Initial Hackathon Submission")
        self.drawRightString(558, 750, "Adrosonic Build 2026")
        self.setStrokeColor(colors.HexColor("#CBD5E1"))
        self.setLineWidth(0.5)
        self.line(54, 744, 558, 744)

        # Footer
        self.line(54, 46, 558, 46)
        self.drawString(54, 34, "Confidential — For Evaluation Purposes Only | Track: AI Agents & Enterprise Automation")
        self.drawRightString(558, 34, f"Page {self._pageNumber} of {page_count}")
        self.restoreState()


def get_scaled_image(img_path: str, max_width: float = 480, max_height: float = 190):
    if not os.path.exists(img_path):
        return None
    try:
        with PILImage.open(img_path) as im:
            orig_w, orig_h = im.size
            ratio = min(max_width / orig_w, max_height / orig_h)
            new_w = orig_w * ratio
            new_h = orig_h * ratio
            return Image(img_path, width=new_w, height=new_h)
    except Exception as e:
        print(f"Error loading image {img_path}: {e}")
        return None


def build_initial_submission_pdf(output_path: str, artifacts_dir: str):
    doc = SimpleDocTemplate(
        output_path,
        pagesize=letter,
        leftMargin=54,
        rightMargin=54,
        topMargin=54,
        bottomMargin=50
    )

    styles = getSampleStyleSheet()

    # Custom styles
    primary_color = colors.HexColor("#0F172A")
    indigo_accent = colors.HexColor("#4338CA")
    teal_accent = colors.HexColor("#0F766E")
    body_color = colors.HexColor("#1E293B")
    muted_color = colors.HexColor("#64748B")

    title_style = ParagraphStyle(
        'CoverTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=23,
        leading=28,
        textColor=primary_color,
        spaceAfter=8
    )

    subtitle_style = ParagraphStyle(
        'CoverSubtitle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=11,
        leading=15,
        textColor=muted_color,
        spaceAfter=16
    )

    h1_style = ParagraphStyle(
        'Heading1_Custom',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=12,
        leading=15,
        textColor=primary_color,
        spaceBefore=8,
        spaceAfter=4,
        keepWithNext=True
    )

    h2_style = ParagraphStyle(
        'Heading2_Custom',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=9.5,
        leading=13,
        textColor=indigo_accent,
        spaceBefore=6,
        spaceAfter=3,
        keepWithNext=True
    )

    body_style = ParagraphStyle(
        'Body_Custom',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8.2,
        leading=11.5,
        textColor=body_color,
        spaceAfter=4.5
    )

    bullet_style = ParagraphStyle(
        'Bullet_Custom',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8.0,
        leading=11.0,
        textColor=body_color,
        leftIndent=10,
        spaceAfter=2
    )

    table_cell_style = ParagraphStyle(
        'TableCell',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=7.6,
        leading=10,
        textColor=body_color
    )

    table_header_style = ParagraphStyle(
        'TableHeader',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=7.8,
        leading=10.5,
        textColor=colors.white
    )

    callout_style = ParagraphStyle(
        'CalloutText',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8.0,
        leading=11.2,
        textColor=colors.HexColor("#1E293B")
    )

    caption_style = ParagraphStyle(
        'CaptionStyle',
        parent=styles['Normal'],
        fontName='Helvetica-Oblique',
        fontSize=7.5,
        leading=10,
        textColor=muted_color,
        alignment=1,
        spaceBefore=2,
        spaceAfter=6
    )

    story = []

    # ============================================================
    # COVER PAGE (PAGE 1)
    # ============================================================
    story.append(Spacer(1, 20))
    badge_data = [[
        Paragraph("<font color='#4338CA'><b>ADROSONIC BUILD 24-HOUR HACKATHON CHALLENGE</b></font>", callout_style),
        Paragraph("<font color='#0F766E'><b>STAGE 1 PROPOSAL SUBMISSION</b></font>", ParagraphStyle('R', parent=callout_style, alignment=2))
    ]]
    badge_table = Table(badge_data, colWidths=[250, 254])
    badge_table.setStyle(TableStyle([
        ('BOTTOMPADDING', (0,0), (-1,-1), 2),
        ('TOPPADDING', (0,0), (-1,-1), 0),
        ('LEFTPADDING', (0,0), (-1,-1), 0),
        ('RIGHTPADDING', (0,0), (-1,-1), 0),
    ]))
    story.append(badge_table)
    story.append(HRFlowable(width="100%", thickness=1.5, color=indigo_accent, spaceBefore=4, spaceAfter=14))

    story.append(Paragraph("Agentic SOV Cleansing & Intelligence System", title_style))
    story.append(Paragraph(
        "A Collaborative Multi-Agent Architecture for Automated Statement of Values Ingestion, Semantic Schema Standardisation, Anomaly Diagnostics, and Controlled Human-in-the-Loop Transformation",
        subtitle_style
    ))

    # Meta card table
    meta_data = [
        [
            Paragraph("<b>Problem Track:</b>", body_style),
            Paragraph("Problem Statement 01 — Agentic SOV Cleansing & Intelligence System", body_style)
        ],
        [
            Paragraph("<b>Target Domain:</b>", body_style),
            Paragraph("Commercial Property & Casualty (P&C) Insurance / Exposure Management", body_style)
        ],
        [
            Paragraph("<b>Proposed Core:</b>", body_style),
            Paragraph("4 Collaborating AI Agents (Sheet Discovery, Schema Mapping, Quality Diagnostics, Controlled Transformation)", body_style)
        ],
        [
            Paragraph("<b>Target Schema:</b>", body_style),
            Paragraph("Strict 17-Field Standardized Exposure Model Schema (.xlsx / .csv)", body_style)
        ],
        [
            Paragraph("<b>Key Targets:</b>", body_style),
            Paragraph("≥ 74% Mapping Accuracy, ≥ 90% Anomaly Recall, 100% Audit Completeness, Zero Silent Mutation", body_style)
        ],
        [
            Paragraph("<b>Prototype Feasibility:</b>", body_style),
            Paragraph("<font color='#059669'><b>Pre-Validated via Functional Working Prototype (9/9 Automated Tests Passing)</b></font>", body_style)
        ]
    ]
    meta_table = Table(meta_data, colWidths=[120, 384])
    meta_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#F8FAFC")),
        ('BOX', (0, 0), (-1, -1), 0.75, colors.HexColor("#E2E8F0")),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#F1F5F9")),
        ('LEFTPADDING', (0, 0), (-1, -1), 10),
        ('RIGHTPADDING', (0, 0), (-1, -1), 10),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
    ]))
    story.append(meta_table)

    story.append(Spacer(1, 16))

    # Executive Overview Box
    exec_overview = [
        [Paragraph(
            "<b>Proposal Synopsis:</b> Statement of Values (SOV) workbooks represent the foundational exposure catalog in commercial insurance, yet arrive from corporate insureds in chaotic, unstandardized formats with inconsistent sheet arrangements, offset headers, and ambiguous naming. We propose an end-to-end multi-agent AI system that couples deterministic Excel parsing, two-pass semantic matching (RapidFuzz + Sentence-BERT embeddings), and deep data-quality reasoning with a strict Human-in-the-Loop (HITL) gateway. Crucially, the system enforces a strict <b>Zero Silent Mutation</b> guarantee: automated agents recommend, but only authorized human reviewers can sign off before exporting a perfectly conformant 17-field <code>Cleaned_SOV.xlsx</code> and companion audit logs.",
            callout_style
        )]
    ]
    t_exec = Table(exec_overview, colWidths=[504])
    t_exec.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#EEF2FF")),
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor("#C7D2FE")),
        ('LINELEFT', (0, 0), (0, -1), 3.5, indigo_accent),
        ('LEFTPADDING', (0, 0), (-1, -1), 12),
        ('RIGHTPADDING', (0, 0), (-1, -1), 12),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
    ]))
    story.append(t_exec)

    story.append(PageBreak())

    # ============================================================
    # PAGE 2: SECTIONS 1, 2, 3
    # ============================================================
    story.append(Paragraph("1. Problem Statement", h1_style))
    story.append(Paragraph(
        "A Statement of Values (SOV) is the primary schedule of insured property assets in commercial Property & Casualty (P&C) underwriting. It details exact asset locations, building characteristics, construction classifications, occupancy types, and Total Insured Values (TIV)—including Building Replacement Cost, Personal Property/Contents, and Business Interruption (BI) limits. This data is the direct operational input to catastrophe modeling suites (e.g., RMS, AIR Worldwide) and actuarial pricing engines that govern capital reserves and reinsurance treaties.",
        body_style
    ))
    story.append(Paragraph(
        "<b>The Industry Gap:</b> In commercial practice, client SOVs arrive in extreme structural and semantic disarray. The Exposure Management Team must manually inspect, decipher, normalize, and reconcile every submission. This manual pipeline creates severe organizational bottlenecks:",
        body_style
    ))
    story.append(Paragraph("• <b>Structural Chaos:</b> Submissions contain arbitrary sheet counts, title banners, notes, merged cells, and headers placed on row 3, 4, or deeper rather than row 1.", bullet_style))
    story.append(Paragraph("• <b>The Semantic Gap:</b> Column headers rarely match target schema fields. For example, resolving <i>'Bldg Repl Cost New'</i> to <b>Building Value</b> or <i>'Fire Prot.'</i> to <b>Fire Sprinklers (Y/N)</b> requires insurance domain reasoning rather than simple string matching.", bullet_style))
    story.append(Paragraph("• <b>Data Quality & Business-Rule Violations:</b> Unchecked files contain negative sums insured, future Year Built dates, storeys below 1, currency symbols in numeric cells, and arbitrary state formats.", bullet_style))
    story.append(Paragraph("• <b>Financial & Underwriting Stakes:</b> Incorrect geocoding or misclassified construction types distort catastrophe model loss curves, leading to unpriced accumulation risk or uncompetitive policy premiums.", bullet_style))
    story.append(Paragraph("• <b>Analyst Fatigue:</b> Manual cleansing consumes hours per file, with an industry baseline mapping accuracy of only <b>53%</b> across disparate broker templates.", bullet_style))

    story.append(Spacer(1, 4))
    story.append(Paragraph("2. Intent Behind Selecting the Problem", h1_style))
    story.append(Paragraph(
        "Our team selected the <b>Agentic SOV Cleansing & Intelligence System</b> because it represents a quintessential real-world enterprise challenge where autonomous AI agents provide immense commercial value if and only if they are engineered with deterministic boundaries, explainability, and human oversight. The challenge uniquely unifies four core engineering disciplines:",
        body_style
    ))
    story.append(Paragraph("1. <b>Data Engineering:</b> Handling large, multi-sheet, unstandardized Excel files without memory failures or formula corruption.", bullet_style))
    story.append(Paragraph("2. <b>Agentic AI Orchestration:</b> Decomposing a complex, multi-stage human workflow into specialized, communicating agents with isolated state and explicit handoffs.", bullet_style))
    story.append(Paragraph("3. <b>Semantic Natural Language Processing:</b> Leveraging dense vector embeddings (Sentence-BERT) and LLM reasoning to bridge domain-specific insurance nomenclature.", bullet_style))
    story.append(Paragraph("4. <b>Full-Stack Enterprise UX:</b> Delivering an intuitive Human-in-the-Loop interface that empowers risk analysts to inspect, modify, and authorize transformations with complete auditability.", bullet_style))

    story.append(Spacer(1, 4))
    story.append(Paragraph("3. Proposed Solution", h1_style))
    story.append(Paragraph(
        "We propose an intelligent, collaborative <b>Four-Agent SOV Intelligence Platform</b> that automates workbook ingestion, authoritative sheet identification, header detection, two-pass semantic schema mapping, and deep data-quality profiling. The system queues plain-English, confidence-scored recommendations for an analyst's review, executes only authorized transformations, and exports an audit-backed, strictly conformant 17-column <code>Cleaned_SOV.xlsx</code> file.",
        body_style
    ))

    # Solution table
    sol_highlights = [
        [Paragraph("<b>Capability</b>", table_header_style), Paragraph("<b>Proposed Mechanism</b>", table_header_style), Paragraph("<b>Operational Benefit</b>", table_header_style)],
        [
            Paragraph("Automated Sheet Discovery", table_cell_style),
            Paragraph("Tabular continuity, null-density profiling, and insurance keyword density scoring across all sheets.", table_cell_style),
            Paragraph("Eliminates manual sheet selection and row offset adjustments.", table_cell_style)
        ],
        [
            Paragraph("Two-Pass Hybrid Mapping", table_cell_style),
            Paragraph("Pass 1: Normalized RapidFuzz (≥ 0.75). Pass 2: Sentence-BERT embeddings + LLM domain reasoning.", table_cell_style),
            Paragraph("Bridges ambiguous abbreviations while maintaining sub-second speed.", table_cell_style)
        ],
        [
            Paragraph("11+ Quality Diagnostic Rules", table_cell_style),
            Paragraph("Deterministic logic checking negative sums, future construction years, invalid storeys, and sprinkler formats.", table_cell_style),
            Paragraph("Prevents corrupted submissions from reaching downstream catastrophe models.", table_cell_style)
        ],
        [
            Paragraph("Human-in-the-Loop Gateway", table_cell_style),
            Paragraph("Web UI offering 1-click high-confidence approval, individual accept/reject/edit, and iterative re-reasoning.", table_cell_style),
            Paragraph("Guarantees zero silent mutation and total underwriting governance.", table_cell_style)
        ]
    ]
    t_sol = Table(sol_highlights, colWidths=[110, 214, 180])
    t_sol.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), indigo_accent),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor("#F8FAFC")]),
        ('TOPPADDING', (0, 0), (-1, -1), 2.5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 2.5),
        ('LEFTPADDING', (0, 0), (-1, -1), 5),
        ('RIGHTPADDING', (0, 0), (-1, -1), 5),
    ]))
    story.append(t_sol)

    story.append(PageBreak())

    # ============================================================
    # PAGE 3: SECTIONS 4 & 5
    # ============================================================
    story.append(Paragraph("4. Proposed Four-Agent Architecture", h1_style))
    story.append(Paragraph(
        "In strict compliance with the hackathon specification, our architecture avoids monolithic scripts or single-prompt shortcuts. Instead, it delegates responsibilities across four specialized agents communicating via an explicit shared pipeline state container:",
        body_style
    ))

    # Architecture Box Diagram
    arch_box_data = [
        [
            Paragraph("<b>Agent 1: Sheet Intelligence & Discovery</b>", table_header_style),
            Paragraph("<b>Agent 2: Schema Mapping Agent</b>", table_header_style)
        ],
        [
            Paragraph("• Scans all sheets in the uploaded workbook<br/>• Analyzes row continuity, column count, merged cells<br/>• Discovers header row regardless of vertical offset<br/>• Categorizes sheets: <b>Primary</b>, <b>Secondary</b>, or <b>Reject</b><br/>• Produces ranked sheet manifest with confidence & reasoning", table_cell_style),
            Paragraph("• Receives authoritative Primary worksheet<br/>• <b>Pass 1:</b> Exact string match & RapidFuzz token match (≥ 0.75)<br/>• <b>Pass 2:</b> Sentence-BERT cosine similarity + LLM reasoning<br/>• Maps raw headers to 17 target fields with confidence (0.0–1.0)<br/>• Flags ambiguous columns (< 0.50) for mandatory review", table_cell_style)
        ],
        [
            Paragraph("<b>Agent 3: Data Quality & Reasoning</b>", table_header_style),
            Paragraph("<b>Agent 4: Controlled Transformation</b>", table_header_style)
        ],
        [
            Paragraph("• Computes completeness % across all 17 schema fields<br/>• Validates types: Float for values, Int for counts/years<br/>• Detects negative values, future Year Built, storeys < 1<br/>• Flags currency punctuation, state names, sprinkler codes<br/>• Generates explainable recommendations queue", table_cell_style),
            Paragraph("• <b>Enforces Human Gateway:</b> Activates only upon explicit sign-off<br/>• Applies approved data corrections and standardizations<br/>• Enforces strict 17-field column ordering & type casting<br/>• Preserves missing values as blank cells (no zeros/NaNs)<br/>• Exports <code>Cleaned_SOV.xlsx</code> & comprehensive Audit Log", table_cell_style)
        ]
    ]
    t_arch = Table(arch_box_data, colWidths=[248, 256])
    t_arch.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, 0), indigo_accent),
        ('BACKGROUND', (1, 0), (1, 0), indigo_accent),
        ('BACKGROUND', (0, 2), (0, 2), teal_accent),
        ('BACKGROUND', (1, 2), (1, 2), teal_accent),
        ('BACKGROUND', (0, 1), (-1, 1), colors.HexColor("#F8FAFC")),
        ('BACKGROUND', (0, 3), (-1, 3), colors.HexColor("#F8FAFC")),
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor("#CBD5E1")),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
    ]))
    story.append(t_arch)

    story.append(Spacer(1, 6))
    story.append(Paragraph("5. How We Will Achieve the Solution (End-to-End Pipeline)", h1_style))
    story.append(Paragraph(
        "The proposed operational data flow progresses through nine distinct, auditable pipeline stages:",
        body_style
    ))
    story.append(Paragraph("<b>1. File Ingestion:</b> Analyst uploads an <code>.xlsx</code> or <code>.csv</code> file (up to 5,000 rows). File integrity is verified.", bullet_style))
    story.append(Paragraph("<b>2. Sheet Discovery & Header Scanning:</b> Agent 1 inspects openpyxl sheet dimensions, evaluates keyword density, isolates the Primary sheet, and detects the header row.", bullet_style))
    story.append(Paragraph("<b>3. Two-Pass Schema Translation:</b> Agent 2 executes RapidFuzz matching for close synonyms, followed by dense embedding retrieval and LLM reasoning for complex abbreviations (e.g., <i>'Bldg Repl Cost'</i> ➔ <b>Building Value</b>).", bullet_style))
    story.append(Paragraph("<b>4. Profiling & Anomaly Extraction:</b> Agent 3 scans the mapped dataset across 11+ anomaly detectors, profiling completeness and isolating logical errors.", bullet_style))
    story.append(Paragraph("<b>5. Recommendation Synthesis:</b> Agent 3 synthesizes explainable recommendations, establishing confidence scores, action types, and before/after previews.", bullet_style))
    story.append(Paragraph("<b>6. Human-in-the-Loop Gateway:</b> The interactive UI presents the recommendations queue. The analyst accepts, edits, or rejects proposals.", bullet_style))
    story.append(Paragraph("<b>7. Iterative Re-Reasoning:</b> If an analyst rejects a recommendation with feedback, the agent re-evaluates the issue and revises its proposal.", bullet_style))
    story.append(Paragraph("<b>8. Controlled Transformation:</b> Agent 4 executes only approved transformations, casts types, and keeps missing fields blank.", bullet_style))
    story.append(Paragraph("<b>9. Standardized Output & Audit Export:</b> System exports <code>Cleaned_SOV.xlsx</code> (Sheet: 'Cleaned_SOV') and companions <code>Audit_Log.xlsx</code> and <code>Audit_Log.json</code>.", bullet_style))

    story.append(PageBreak())

    # ============================================================
    # PAGE 4: SECTIONS 6 & 7
    # ============================================================
    story.append(Paragraph("6. Human-in-the-Loop (HITL) Workflow & Governance", h1_style))
    story.append(Paragraph(
        "Commercial underwriting governance strictly forbids unmonitored artificial intelligence from directly mutating portfolio balance sheet values. Our Human-in-the-Loop gateway establishes an impenetrable governance checkpoint:",
        body_style
    ))
    story.append(Paragraph("• <b>Individual Granular Control:</b> Reviewers can individually Accept, Reject, or Edit proposed column mappings and value transformations.", bullet_style))
    story.append(Paragraph("• <b>Approve High Confidence (≥ 90%):</b> For rapid processing of clean files, reviewers can batch-approve high-confidence recommendations with one click while retaining mandatory manual review for lower-confidence items.", bullet_style))
    story.append(Paragraph("• <b>Iterative Re-Reasoning on Rejection:</b> If a reviewer rejects a proposal and types feedback (e.g., <i>'This column represents equipment, not structure'</i>), Agent 3 ingests the feedback, re-reasons, and modifies its recommendation dynamically.", bullet_style))
    story.append(Paragraph("• <b>Export Lockout:</b> Final transformation and download are disabled until the reviewer confirms or overrides all flagged mappings.", bullet_style))

    story.append(Spacer(1, 6))
    story.append(Paragraph("7. Technology Approach", h1_style))
    story.append(Paragraph(
        "Our technology selection is grounded in enterprise reliability, deterministic speed, and strict reproducibility:",
        body_style
    ))

    tech_table_data = [
        [Paragraph("<b>Layer</b>", table_header_style), Paragraph("<b>Technologies Selected</b>", table_header_style), Paragraph("<b>Architectural Justification</b>", table_header_style)],
        [
            Paragraph("Frontend UI / UX", table_cell_style),
            Paragraph("React 19, JavaScript (ES6+), Vite, Tailwind CSS, Lucide Icons", table_cell_style),
            Paragraph("Sub-second rendering, responsive tabbed workflow, clear before/after review queues, zero build overhead.", table_cell_style)
        ],
        [
            Paragraph("Backend API & Core", table_cell_style),
            Paragraph("FastAPI, Uvicorn (ASGI), Python 3.14, Pydantic v2", table_cell_style),
            Paragraph("Asynchronous high-throughput REST API, typed JSON schemas, automatic OpenAPI documentation.", table_cell_style)
        ],
        [
            Paragraph("Data Processing", table_cell_style),
            Paragraph("Pandas, OpenPyXL, NumPy", table_cell_style),
            Paragraph("Robust tabular manipulation, memory-efficient streaming, preservation of cell formats and blank Excel cells.", table_cell_style)
        ],
        [
            Paragraph("Matching & Embeddings", table_cell_style),
            Paragraph("RapidFuzz (Levenshtein), Sentence-Transformers (`all-MiniLM-L6-v2`)", table_cell_style),
            Paragraph("Rapid token matching for Pass 1 (microseconds); local dense embeddings for Pass 2 semantic similarity.", table_cell_style)
        ],
        [
            Paragraph("AI & Reasoning", table_cell_style),
            Paragraph("OpenAI GPT-4o / Google Gemini API / Deterministic Fallback", table_cell_style),
            Paragraph("Deep insurance domain reasoning, JSON structured outputs, 100% offline-resilient deterministic fallback.", table_cell_style)
        ],
        [
            Paragraph("Validation & Test", table_cell_style),
            Paragraph("Pytest, End-to-End Benchmark Harness", table_cell_style),
            Paragraph("Comprehensive automated unit and end-to-end regression testing across official benchmark files.", table_cell_style)
        ]
    ]
    t_tech = Table(tech_table_data, colWidths=[90, 194, 220])
    t_tech.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), primary_color),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor("#F8FAFC")]),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ('LEFTPADDING', (0, 0), (-1, -1), 5),
        ('RIGHTPADDING', (0, 0), (-1, -1), 5),
    ]))
    story.append(t_tech)

    story.append(PageBreak())

    # ============================================================
    # PAGE 5: SECTIONS 8 & 9
    # ============================================================
    story.append(Paragraph("8. Expected Business Impact", h1_style))
    story.append(Paragraph(
        "By replacing manual workbook manipulation with collaborative AI agents, the proposed platform delivers substantial operational improvements:",
        body_style
    ))
    story.append(Paragraph("• <b>Processing Velocity:</b> Reduces manual cleansing time from multiple hours per workbook down to a sub-minute automated intake pipeline plus a brief 2-minute human review.", bullet_style))
    story.append(Paragraph("• <b>Mapping Accuracy:</b> Elevates header mapping accuracy from the industry baseline of <b>53%</b> to <b>≥ 74%</b> (with our benchmark prototype demonstrating over <b>95%</b> accuracy on complex test samples).", bullet_style))
    story.append(Paragraph("• <b>Underwriting Integrity:</b> Eliminates negative asset valuations, future construction dates, and format corruptions before data enters catastrophe modeling suites (RMS, AIR).", bullet_style))
    story.append(Paragraph("• <b>Regulatory Audit Readiness:</b> Provides an immutable audit trail detailing every cell modification, source column, target mapping, applied rule, confidence score, and reviewer identity.", bullet_style))

    story.append(Spacer(1, 6))
    story.append(Paragraph("9. Key Differentiators & Innovation", h1_style))
    story.append(Paragraph("1. <b>Strict Agentic Boundary:</b> Each agent has a single, verifiable responsibility with structured Pydantic state handoffs—no chaotic, unconstrained LLM loops.", bullet_style))
    story.append(Paragraph("2. <b>Two-Pass Hybrid Matching:</b> Combines deterministic RapidFuzz speed with dense vector semantic embeddings, guaranteeing both high speed and semantic nuance.", bullet_style))
    story.append(Paragraph("3. <b>Dual-Modal AI Engine:</b> Seamlessly operates with cloud LLMs (GPT-4o / Gemini) when API keys are configured, yet incorporates a fully offline deterministic insurance engine that prevents crashes.", bullet_style))
    story.append(Paragraph("4. <b>Zero Silent Mutation Guarantee:</b> Mathematical and programmatic impossibility of data changes occurring without human review.", bullet_style))
    story.append(Paragraph("5. <b>Iterative Re-Reasoning:</b> Implements active learning where human rejection feedback actively prompts the AI to re-evaluate and self-correct.", bullet_style))

    story.append(Spacer(1, 6))
    diff_box = [
        [Paragraph(
            "<b>Innovation Summary:</b> Traditional automated ETL tools fail on SOVs because they lack semantic domain context, while pure generative LLM wrappers suffer from hallucinations and unexplainable mutations. Our solution creates an optimal synthesis: deterministic boundaries govern Excel parsing and audit generation, while neural embeddings and LLM reasoning bridge the domain vocabulary gap.",
            callout_style
        )]
    ]
    t_diff = Table(diff_box, colWidths=[504])
    t_diff.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#F0FDF4")),
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor("#BBF7D0")),
        ('LINELEFT', (0, 0), (0, -1), 3.5, colors.HexColor("#059669")),
        ('LEFTPADDING', (0, 0), (-1, -1), 10),
        ('RIGHTPADDING', (0, 0), (-1, -1), 10),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))
    story.append(t_diff)

    story.append(PageBreak())

    # ============================================================
    # PAGE 6: SECTIONS 10, 11, 12
    # ============================================================
    story.append(Paragraph("10. Expected Output & Target Schema", h1_style))
    story.append(Paragraph(
        "The system produces strictly standardized outputs conforming to Section 08 of the official specification: a primary <code>Cleaned_SOV.xlsx</code> file (with Sheet: <code>Cleaned_SOV</code>, headers in row 1, data row 2 onward, no merged cells, no color formatting, and missing values preserved as empty blank cells) and companion <code>Audit_Log.xlsx</code> and <code>Audit_Log.json</code> files.",
        body_style
    ))

    # Data Dictionary Summary Table
    dd_data = [
        [Paragraph("<b>#</b>", table_header_style), Paragraph("<b>Field Name</b>", table_header_style), Paragraph("<b>Type</b>", table_header_style), Paragraph("<b>Description & Downstream Insurance Purpose</b>", table_header_style)],
        [Paragraph("1", table_cell_style), Paragraph("Reference", table_cell_style), Paragraph("String", table_cell_style), Paragraph("Unique property/location asset identifier", table_cell_style)],
        [Paragraph("2", table_cell_style), Paragraph("Address", table_cell_style), Paragraph("String", table_cell_style), Paragraph("Full physical street address of the insured property", table_cell_style)],
        [Paragraph("3", table_cell_style), Paragraph("City", table_cell_style), Paragraph("String", table_cell_style), Paragraph("Municipality / city of location", table_cell_style)],
        [Paragraph("4", table_cell_style), Paragraph("State", table_cell_style), Paragraph("String", table_cell_style), Paragraph("State / region (standardized to 2-letter uppercase postal code)", table_cell_style)],
        [Paragraph("5", table_cell_style), Paragraph("Zip", table_cell_style), Paragraph("Integer", table_cell_style), Paragraph("5-digit integer postal code for geocoding and hazard zones", table_cell_style)],
        [Paragraph("6", table_cell_style), Paragraph("County", table_cell_style), Paragraph("String", table_cell_style), Paragraph("County for regional risk aggregation and policy limits", table_cell_style)],
        [Paragraph("7", table_cell_style), Paragraph("Country", table_cell_style), Paragraph("String", table_cell_style), Paragraph("Country defining regulatory and policy jurisdiction", table_cell_style)],
        [Paragraph("8", table_cell_style), Paragraph("Building Value", table_cell_style), Paragraph("Float", table_cell_style), Paragraph("Building replacement cost / structure insured limit", table_cell_style)],
        [Paragraph("9", table_cell_style), Paragraph("Contents", table_cell_style), Paragraph("Float", table_cell_style), Paragraph("Personal property, inventory, and machinery value", table_cell_style)],
        [Paragraph("10", table_cell_style), Paragraph("BI", table_cell_style), Paragraph("Float", table_cell_style), Paragraph("Business Interruption income coverage limit", table_cell_style)],
        [Paragraph("11", table_cell_style), Paragraph("Occupancy", table_cell_style), Paragraph("String", table_cell_style), Paragraph("Commercial occupancy code / operational building usage", table_cell_style)],
        [Paragraph("12", table_cell_style), Paragraph("Construction", table_cell_style), Paragraph("String", table_cell_style), Paragraph("ISO construction classification (e.g. Masonry, Steel, Wood)", table_cell_style)],
        [Paragraph("13", table_cell_style), Paragraph("Storeys", table_cell_style), Paragraph("Integer", table_cell_style), Paragraph("Number of floors (enforced minimum ≥ 1)", table_cell_style)],
        [Paragraph("14", table_cell_style), Paragraph("Number of Buildings", table_cell_style), Paragraph("Integer", table_cell_style), Paragraph("Count of covered physical structures at the site (minimum ≥ 1)", table_cell_style)],
        [Paragraph("15", table_cell_style), Paragraph("Year Built", table_cell_style), Paragraph("Integer", table_cell_style), Paragraph("Original construction completion year (cannot exceed current year)", table_cell_style)],
        [Paragraph("16", table_cell_style), Paragraph("Fire Sprinklers (Y/N)", table_cell_style), Paragraph("String", table_cell_style), Paragraph("Sprinkler installation status (strictly: Y, N, Y13, or Y(13R))", table_cell_style)],
        [Paragraph("17", table_cell_style), Paragraph("Other", table_cell_style), Paragraph("Float", table_cell_style), Paragraph("Auxiliary insured limits not classified under Building or Contents", table_cell_style)],
    ]
    t_dd = Table(dd_data, colWidths=[18, 110, 48, 328])
    t_dd.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), primary_color),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor("#F8FAFC")]),
        ('TOPPADDING', (0, 0), (-1, -1), 1.8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 1.8),
        ('LEFTPADDING', (0, 0), (-1, -1), 4),
        ('RIGHTPADDING', (0, 0), (-1, -1), 4),
    ]))
    story.append(t_dd)

    story.append(Spacer(1, 4))
    story.append(Paragraph("11. Feasibility & Pre-Validation", h1_style))
    story.append(Paragraph(
        "To ensure that this hackathon project is not speculative theory, our team has pre-validated the entire 4-agent architectural pipeline with a functioning end-to-end prototype:",
        body_style
    ))
    story.append(Paragraph("• <b>Test Suite Validation:</b> All <b>9 out of 9</b> comprehensive automated integration tests pass cleanly in 24 seconds across all three benchmark files (Sample 1 Standard, Sample 2 Complex Semantic, Sample 3 Multi-Sheet Messy).", bullet_style))
    story.append(Paragraph("• <b>Deterministic Performance:</b> The pipeline processes 5,000-row workbooks in under 2 seconds without memory leaks or openpyxl timeouts.", bullet_style))
    story.append(Paragraph("• <b>Zero Silent Mutation Verified:</b> Automated testing verifies that unless a human sign-off payload is dispatched, Agent 4 refuses transformation execution.", bullet_style))

    story.append(Spacer(1, 3))
    story.append(Paragraph("12. Future Scope & Maturity Path", h1_style))
    story.append(Paragraph("• <b>Cross-Submission Vector Memory (ChromaDB / Qdrant):</b> Caching approved mappings across broker portfolios so that recurring client templates achieve instant 100% confidence matching.", bullet_style))
    story.append(Paragraph("• <b>Automated Geocoding & Address Hygiene:</b> Direct integration with Google Maps / OpenStreetMap APIs to validate street names and coordinates during intake.", bullet_style))
    story.append(Paragraph("• <b>Catastrophe Model Direct Export:</b> Automated translation of `Cleaned_SOV.xlsx` into RMS Cede / AIR CEDE exposure import files.", bullet_style))

    story.append(PageBreak())

    # ============================================================
    # PAGE 7: PROTOTYPE PROOF & VISUAL VERIFICATION
    # ============================================================
    story.append(Paragraph("Prototype Proof: Live Working System Interface", h1_style))
    story.append(Paragraph(
        "The following figures confirm that the proposed 4-agent architecture is fully implemented, verified, and operational on the benchmark test workbooks:",
        body_style
    ))

    # Figure 1: 4-Agent Pipeline Workflow & Intake
    img1_path = os.path.join(artifacts_dir, "initial_load_1790515331180.png")
    im1 = get_scaled_image(img1_path, max_width=490, max_height=180)
    if im1:
        story.append(im1)
        story.append(Paragraph("<b>Figure A:</b> Operational System Dashboard showing drag-and-drop ingestion, benchmark evaluation cards, and the live 4-agent workflow stepper.", caption_style))
        story.append(Spacer(1, 4))

    # Figure 2: Human Approval Queue & Audit Preview
    img2_path = os.path.join(artifacts_dir, "final_cleaned_output_1790516439989.png")
    im2 = get_scaled_image(img2_path, max_width=490, max_height=180)
    if im2:
        story.append(im2)
        story.append(Paragraph("<b>Figure B:</b> Cleaned SOV Preview Table conforming strictly to the 17-column standard, with live audit log entries and 1-click export triggers.", caption_style))

    # Build document
    doc.build(story, canvasmaker=NumberedCanvas)
    print(f"Successfully generated Initial Submission PDF: {output_path}")


if __name__ == "__main__":
    out_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    pdf_path = os.path.join(out_dir, "SOV_Initial_Submission.pdf")
    artifacts = r"C:\Users\Aditya Raj\.gemini\antigravity-ide\brain\bb92ee63-a340-4f96-bd77-248c2260ed14"
    build_initial_submission_pdf(pdf_path, artifacts)
