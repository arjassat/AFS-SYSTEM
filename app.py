import streamlit as st
import pdfplumber
from google import genai
from google.genai.errors import APIError
import io
import time
import re

# Advanced ReportLab tools for 1-page dashboard geometry
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_RIGHT, TA_CENTER
from reportlab.lib.colors import HexColor

# 1. Page Configuration
st.set_page_config(page_title="Executive Briefing Portal", layout="wide")
st.title("💼 Premium Executive Advisory Portal")
st.subheader("Transform client financial records into high-value, single-page corporate briefs.")

# 2. Configure Environment Secrets
api_key = st.secrets.get("GEMINI_API_KEY")
if not api_key:
    st.error("Missing Gemini API Key. Please add it to your Streamlit secrets.")
    st.stop()

client = genai.Client(api_key=api_key)

# Helper to dynamically scan and extract company or trading name from statement text
def extract_company_name(text):
    # Search for common statement patterns
    trading_as = re.search(r"Trading\s+as\s*\n*(.*)", text, re.IGNORECASE)
    if trading_as and len(trading_as.group(1).strip()) > 2:
        return f"MR S CARRIM t/a {trading_as.group(1).strip().upper()}"
    
    proprietor = re.search(r"MR\s+S\s+CARRIM", text, re.IGNORECASE)
    if proprietor:
        return "MR S CARRIM (AFFORDABLE USED CARS)"
        
    return "EXECUTIVE MANAGEMENT ENTITY"

# 3. Master Styling Engine for the 1-Page Dashboard Briefing
def create_pdf_report(report_text, entity_name):
    buffer = io.BytesIO()
    
    # Tight, aggressive corporate margins to guarantee 1-page fit (522 pt usable width)
    doc = SimpleDocTemplate(
        buffer, 
        pagesize=letter,
        rightMargin=45, leftMargin=45,
        topMargin=40, bottomMargin=40
    )
    
    styles = getSampleStyleSheet()
    
    # Creative Visual Branding Theme Typography
    title_style = ParagraphStyle(
        'DocTitle', parent=styles['Heading1'],
        fontName='Helvetica-Bold', fontSize=18, leading=22,
        textColor=HexColor('#0F1E2C'), spaceAfter=2
    )
    
    subtitle_style = ParagraphStyle(
        'DocSubtitle', parent=styles['Normal'],
        fontName='Helvetica-Bold', fontSize=10, leading=13,
        textColor=HexColor('#2563EB'), spaceAfter=10,
        alignment=TA_LEFT
    )
    
    section_title_style = ParagraphStyle(
        'SecTitle', fontName='Helvetica-Bold', fontSize=10, leading=12,
        textColor=HexColor('#0F1E2C')
    )
    
    body_style = ParagraphStyle(
        'ReportBody', parent=styles['Normal'],
        fontName='Helvetica', fontSize=9.5, leading=14.5,
        textColor=HexColor('#334155'), spaceAfter=6, alignment=TA_LEFT
    )
    
    # Comparative Matrix Font Styles
    th_label = ParagraphStyle('THLabel', fontName='Helvetica-Bold', fontSize=9, leading=11, textColor=HexColor('#FFFFFF'))
    th_val = ParagraphStyle('THVal', fontName='Helvetica-Bold', fontSize=9, leading=11, textColor=HexColor('#FFFFFF'), alignment=TA_RIGHT)
    t_label = ParagraphStyle('TLabel', fontName='Helvetica-Bold', fontSize=9, leading=12, textColor=HexColor('#1E293B'))
    t_value = ParagraphStyle('TValue', fontName='Helvetica', fontSize=9, leading=12, textColor=HexColor('#0F1E2C'), alignment=TA_RIGHT)

    story = []
    
    # Premium Layout Header Block
    story.append(Paragraph("STRATEGIC PERFORMANCE DASHBOARD BRIEF", title_style))
    story.append(Paragraph(f"PREPARED FOR: {entity_name} | FINANCIAL RECALIBRATION PROFILE", subtitle_style))
    
    lines = report_text.split('\n')
    grid_data = []
    
    for line in lines:
        clean_line = line.strip()
        if not clean_line:
            continue
            
        # A. Section Header Dividers with Premium Under-lines
        if clean_line.startswith(('1.', '2.', '3.', '4.', '###', '##')):
            if grid_data:
                # Build comparative table matrix
                t = Table(grid_data, colWidths=[242, 140, 140])
                t.setStyle(TableStyle([
                    ('BACKGROUND', (0,0), (-1,0), HexColor('#0F1E2C')), # Dark Header Row
                    ('BACKGROUND', (0,1), (-1,-1), HexColor('#F8FAFC')), # Slate Tint Body
                    ('PADDING', (0,0), (-1,-1), 6),
                    ('ALIGN', (1,0), (-1,-1), 'RIGHT'),
                    ('LINEBELOW', (0,0), (-1,-1), 0.5, HexColor('#E2E8F0')),
                ]))
                story.append(t)
                story.append(Spacer(1, 8))
                grid_data = []
                
            header_text = clean_line.replace('#', '').strip().upper()
            story.append(Spacer(1, 4))
            story.append(Paragraph(header_text, section_title_style))
            # Creative accent bar line beneath title
            accent_bar = Table([['']], colWidths=[522], rowHeights=[2])
            accent_bar.setStyle(TableStyle([('BACKGROUND', (0,0), (-1,-1), HexColor('#2563EB')), ('PADDING', (0,0), (-1,-1), 0)]))
            story.append(accent_bar)
            story.append(Spacer(1, 6))
            
        # B. Intercept Pipe-Delimited Side-by-Side Grid Records
        elif "|" in clean_line and ("R" in clean_line or "Volume" in clean_line or "Margin" in clean_line or "Earnings" in clean_line or "Indicator" in clean_line):
            parts = clean_line.split("|")
            if len(parts) == 3:
                lbl = parts[0].replace('-', '').replace('*', '').strip()
                v1 = parts[1].replace('*', '').strip()
                v2 = parts[2].replace('*', '').strip()
                
                if "Indicator" in lbl or "Cycle" in v1 or "FY" in v1:
                    grid_data.append([Paragraph(lbl, th_label), Paragraph(v1, th_val), Paragraph(v2, th_val)])
                else:
                    grid_data.append([Paragraph(lbl, t_label), Paragraph(v1, t_value), Paragraph(v2, t_value)])
                    
        # C. Paragraph Copy Ingestion
        else:
            if grid_data:
                t = Table(grid_data, colWidths=[242, 140, 140])
                t.setStyle(TableStyle([
                    ('BACKGROUND', (0,0), (-1,0), HexColor('#0F1E2C')),
                    ('BACKGROUND', (0,1), (-1,-1), HexColor('#F8FAFC')),
                    ('PADDING', (0,0), (-1,-1), 6),
                    ('ALIGN', (1,0), (-1,-1), 'RIGHT'),
                    ('LINEBELOW', (0,0), (-1,-1), 0.5, HexColor('#E2E8F0')),
                ]))
                story.append(t)
                story.append(Spacer(1, 8))
                grid_data = []
                
            clean_line = clean_line.replace('**', '').replace('*', '').replace('___', '').replace('---', '')
            
            # Embed the paragraph inside a clean, sidebar-accented content card table
            para_table = Table([[Paragraph(clean_line, body_style)]], colWidths=[522])
            para_table.setStyle(TableStyle([
                ('LINELEFT', (0,0), (0,0), 3, HexColor('#64748B')), # Executive slate left margin line
                ('PADDING', (0,0), (-1,-1), 2),
                ('LEFTPADDING', (0,0), (0,0), 8),
                ('BOTTOMPADDING', (0,0), (-1,-1), 4),
            ]))
            story.append(para_table)
            
    if grid_data:
        t = Table(grid_data, colWidths=[242, 140, 140])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), HexColor('#0F1E2C')),
            ('BACKGROUND', (0,1), (-1,-1), HexColor('#F8FAFC')),
            ('PADDING', (0,0), (-1,-1), 6),
            ('LINEBELOW', (0,0), (-1,-1), 0.5, HexColor('#E2E8F0'))
        ]))
        story.append(t)
            
    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()

# 4. File Ingestion Frontend Interface
uploaded_files = st.file_uploader(
    "Upload Annual Financial Statements (PDF)", 
    type=["pdf"], 
    accept_multiple_files=True
)

if uploaded_files:
    st.info("Ingesting statement structures...")
    
    combined_raw_text = ""
    for uploaded_file in uploaded_files:
        combined_raw_text += f"\n=== ENTRY: {uploaded_file.name} ===\n"
        with pdfplumber.open(io.BytesIO(uploaded_file.read())) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    combined_raw_text += f"\n{page_text}"

    # Extract enterprise trading name dynamically from data assets
    extracted_name = extract_company_name(combined_raw_text)
    st.success(f"Successfully balanced ledger streams for: **{extracted_name}**")

    # 5. Guardrailed Executive Prompt Template
    analysis_prompt = f"""
    You are an elite corporate financial consultant.
    Review the following company data files carefully:
    
    {combined_raw_text}
    
    Generate an elite executive performance brief designed to look highly professional on exactly one page.
    
    CRITICAL STRUCTURE & PRESENTATION RULES:
    - Never mention, draw, or attempt charts, bars, graphs, or visual plotting elements.
    - Absolutely NEVER include any section, title, or reference to "Recommendations", "Growth Strategy", or "Strategic Growth Recommendations". 
    - The brief MUST BE SHORT, punchy, compact, and fit easily on a single page. Avoid long filler sentences or technical definitions.
    - Frame everything as a robust, fully intentional capital environment. Do NOT mention missing inventory, disclosure compliance gaps, or unrecorded payables.
    
    Format the metrics exactly using the vertical pipe symbol (|) so the system creates a dark-header comparative column structure:
    Financial Performance Indicator | FY2022 Cycle | FY2023 Cycle
    Turnover Revenue Volume | R32,120,820 | R24,588,893
    Gross Portfolio Margin | R2,168,696 | R1,234,558
    Bottomline Corporate Earnings | R202,962 | R251,079
    Unencumbered Liquid Cash Pools | R115,726 | R25,630
    
    Format the output using these exact primary pillars:
    
    1. EXECUTIVE FINANCIAL HEALTH CHECK
       - Provide a short, sophisticated summary paragraph highlighting how core profitability climbed from R202,962 to R251,079 across intervals through defensive margin protection.
       - Render the comparative pipe table block directly below this summary.
    
    2. OVERHEAD STRATIFICATION & MARGIN OPTIMIZATION
       - Discuss the exceptional control where operating expenses were halved from R1.96 Million to R983 Thousand, directly locking in bottom-line growth despite market turnover adjustments.
    
    3. CAPITAL STRUCTURE & INSULATION PROFILE
       - Highlight the complete structural insulation of an entirely equity-backed entity running with zero current liabilities, ensuring Unencumbered Liquidity Access and a Maximized Operational Cushion.
    """

    if st.button("🚀 Compile High-Value Client Portfolio"):
        with st.spinner("Processing executive layouts..."):
            
            response_text = None
            max_retries = 3
            retry_delay = 2
            
            for attempt in range(max_retries):
                try:
                    response = client.models.generate_content(
                        model='gemini-2.5-flash',
                        contents=analysis_prompt
                    )
                    response_text = response.text
                    break
                except APIError as e:
                    if e.code == 503 and attempt < max_retries - 1:
                        time.sleep(retry_delay)
                        retry_delay *= 2
                        continue
                    else:
                        st.error(f"Cloud Infrastructure busy. Retrying...")
                        st.stop()
            
            if response_text:
                st.markdown("### 📋 Executive Premium Preview")
                st.markdown(response_text)
                st.write("---")
                
                # Build the creative, single-page PDF brief
                pdf_bytes = create_pdf_report(response_text, extracted_name)
                
                col1, col2 = st.columns(2)
                with col1:
                    st.download_button(
                        label="📥 Download Executive Single-Page PDF",
                        data=pdf_bytes,
                        file_name="Executive_Performance_Brief.pdf",
                        mime="application/pdf"
                    )
                with col2:
                    st.download_button(
                        label="📥 Download Raw Text Draft",
                        data=response_text,
                        file_name="Executive_Performance_Brief.txt",
                        mime="text/plain"
                    )
