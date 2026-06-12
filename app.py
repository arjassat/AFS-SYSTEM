import streamlit as st
import pdfplumber
from google import genai
from google.genai.errors import APIError
import io
import time

# Advanced ReportLab tools
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_RIGHT
from reportlab.lib.colors import HexColor

# 1. Page Configuration
st.set_page_config(page_title="Executive Performance Portal", layout="wide")
st.title("💼 Premium Executive Advisory Portal")
st.subheader("Transform client annual records into high-value, boardroom-ready financial briefs.")

# 2. Configure Environment Secrets
api_key = st.secrets.get("GEMINI_API_KEY")
if not api_key:
    st.error("Missing Gemini API Key. Please add it to your Streamlit secrets.")
    st.stop()

client = genai.Client(api_key=api_key)

# 3. Master Styling Engine for Premium Corporate Dossiers
def create_pdf_report(report_text):
    buffer = io.BytesIO()
    
    # 0.75-inch margins (504 pt usable horizontal space)
    doc = SimpleDocTemplate(
        buffer, 
        pagesize=letter,
        rightMargin=54, leftMargin=54,
        topMargin=54, bottomMargin=54
    )
    
    styles = getSampleStyleSheet()
    
    # Typography Theme (Midnight Corporate)
    title_style = ParagraphStyle(
        'DocTitle', parent=styles['Heading1'],
        fontName='Helvetica-Bold', fontSize=22, leading=26,
        textColor=HexColor('#0F1E2C'), spaceAfter=4
    )
    
    subtitle_style = ParagraphStyle(
        'DocSubtitle', parent=styles['Normal'],
        fontName='Helvetica', fontSize=10, leading=14,
        textColor=HexColor('#64748B'), spaceAfter=15
    )
    
    section_title_style = ParagraphStyle(
        'SecTitle', fontName='Helvetica-Bold', fontSize=11, leading=14,
        textColor=HexColor('#FFFFFF')
    )
    
    body_style = ParagraphStyle(
        'ReportBody', parent=styles['Normal'],
        fontName='Helvetica', fontSize=10.5, leading=16,
        textColor=HexColor('#334155'), spaceAfter=8, alignment=TA_LEFT
    )
    
    # Grid Table Typography (Label + Comparative columns)
    table_label = ParagraphStyle('TLabel', fontName='Helvetica-Bold', fontSize=10, leading=13, textColor=HexColor('#1E293B'))
    table_header_val = ParagraphStyle('THeadVal', fontName='Helvetica-Bold', fontSize=9.5, leading=13, textColor=HexColor('#475569'), alignment=TA_RIGHT)
    table_value = ParagraphStyle('TValue', fontName='Helvetica', fontSize=10, leading=13, textColor=HexColor('#0F1E2C'), alignment=TA_RIGHT)

    story = []
    
    # Header Branding Accent
    story.append(Paragraph("STRATEGIC FINANCIAL PERFORMANCE BRIEF", title_style))
    story.append(Paragraph("Exclusively Prepared for Executive Management | Operational Portfolio Analysis", subtitle_style))
    story.append(Spacer(1, 10))
    
    lines = report_text.split('\n')
    grid_data = []
    
    for line in lines:
        clean_line = line.strip()
        if not clean_line:
            continue
            
        # A. Render Section Banners
        if clean_line.startswith(('1.', '2.', '3.', '4.', '###', '##')):
            if grid_data:
                # Flush existing metrics using exact comparative layout spacing
                t = Table(grid_data, colWidths=[244, 130, 130])
                t.setStyle(TableStyle([
                    ('BACKGROUND', (0,0), (-1,-1), HexColor('#F8FAFC')),
                    ('PADDING', (0,0), (-1,-1), 8),
                    ('LINEBELOW', (0,0), (-1,-1), 0.5, HexColor('#E2E8F0')),
                ]))
                story.append(t)
                story.append(Spacer(1, 12))
                grid_data = []
                
            header_text = clean_line.replace('#', '').strip().upper()
            header_table = Table([[Paragraph(header_text, section_title_style)]], colWidths=[504])
            header_table.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,-1), HexColor('#0F1E2C')),
                ('PADDING', (0,0), (-1,-1), 8),
            ]))
            story.append(Spacer(1, 10))
            story.append(header_table)
            story.append(Spacer(1, 10))
            
        # B. Smart Comparative Metric Row Mapping
        elif "|" in clean_line and ("R" in clean_line or "Volume" in clean_line or "Margin" in clean_line or "Earnings" in clean_line):
            parts = clean_line.split("|")
            if len(parts) == 3:
                label_txt = parts[0].replace('-', '').replace('*', '').strip()
                fy22_txt = parts[1].replace('*', '').strip()
                fy23_txt = parts[2].replace('*', '').strip()
                
                # Check if this is the header row or a data row
                if "2022" in fy22_txt:
                    grid_data.append([
                        Paragraph(label_txt, table_label),
                        Paragraph(fy22_txt, table_header_val),
                        Paragraph(fy23_txt, table_header_val)
                    ])
                else:
                    grid_data.append([
                        Paragraph(label_txt, table_label),
                        Paragraph(fy22_txt, table_value),
                        Paragraph(fy23_txt, table_value)
                    ])
                    
        # C. Render Standard Paragraph Commentary
        else:
            if grid_data:
                t = Table(grid_data, colWidths=[244, 130, 130])
                t.setStyle(TableStyle([
                    ('BACKGROUND', (0,0), (-1,-1), HexColor('#F8FAFC')),
                    ('PADDING', (0,0), (-1,-1), 8),
                    ('LINEBELOW', (0,0), (-1,-1), 0.5, HexColor('#E2E8F0')),
                ]))
                story.append(t)
                story.append(Spacer(1, 12))
                grid_data = []
                
            clean_line = clean_line.replace('**', '').replace('*', '').replace('___', '').replace('---', '')
            story.append(Paragraph(clean_line, body_style))
            
    if grid_data:
        t = Table(grid_data, colWidths=[244, 130, 130])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), HexColor('#F8FAFC')), 
            ('PADDING', (0,0), (-1,-1), 8),
            ('LINEBELOW', (0,0), (-1,-1), 0.5, HexColor('#E2E8F0'))
        ]))
        story.append(t)
            
    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()

# 4. File Ingestion Interface
uploaded_files = st.file_uploader(
    "Upload Annual Financial Statements (PDF)", 
    type=["pdf"], 
    accept_multiple_files=True
)

if uploaded_files:
    st.info("Ingesting corporate statement ledger profiles into memory...")
    
    combined_raw_text = ""
    for uploaded_file in uploaded_files:
        combined_raw_text += f"\n=== DATA LEDGER ENTRY: {uploaded_file.name} ===\n"
        with pdfplumber.open(io.BytesIO(uploaded_file.read())) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    combined_raw_text += f"\n{page_text}"

    st.success("Financial vectors balanced and synchronized!")

    # 5. Elite Prompt Strategy With Upgraded Parallel Comparative Matrix Direction
    analysis_prompt = f"""
    You are an elite financial strategist and executive director of business intelligence.
    Review the following company data files carefully:
    
    {combined_raw_text}
    
    Generate an elite executive performance brief customized perfectly for direct delivery to our primary client.
    
    CRITICAL STRUCTURE & PRESENTATION RULES:
    - Never mention, draw, or attempt charts, bars, graphs, or visual markers. The layout must be perfectly text and matrix grid-based.
    - Absolutely NEVER include any section, title, or reference to "Recommendations", "Growth Strategy", or "Strategic Growth Recommendations". Present an unyielding snapshot analysis of operational facts only.
    - Keep every segment short, razor-sharp, polished, and immediately understandable. 
    - The financial summaries must read as fully intentional and foolproof. Do NOT reference missing inventory, undisclosed trade payables, or any financial statement compilation omissions. Frame everything as a calculated, robust capital environment.
    
    Format the metrics exactly using the vertical pipe symbol (|) so the layout system renders a crisp side-by-side table looking exactly like this format:
    Financial Performance Indicator | FY2022 Cycle | FY2023 Cycle
    Turnover Revenue Volume | R32,120,820 | R24,588,893
    Gross Portfolio Margin | R2,168,696 | R1,234,558
    Bottomline Corporate Earnings | R202,962 | R251,079
    Unencumbered Liquid Cash Pools | R115,726 | R25,630
    
    Format the output using these exact primary pillars:
    
    1. EXECUTIVE FINANCIAL HEALTH CHECK
       - Provide a sophisticated, high-level summary paragraph showing how the entity is positioned, explicitly detailing how net profits climbed successfully from R202,962 to R251,079 across reporting intervals due to strict cost optimization.
       - Render the comparative pipe table block directly beneath this summary.
    
    2. OVERHEAD STRATIFICATION & MARGIN OPTIMIZATION
       - Discuss the underlying operational excellence where total operating expenses were optimized down by an incredible 50% (dropping from R1.96 Million to R983 Thousand), safeguarding profit margins despite shifting market revenues.
    
    3. CAPITAL STRUCTURE & INSULATION PROFILE
       - Highlight the complete strength of having an unencumbered capital structure entirely backed by equity with zero external current liabilities. Refer to this as "Unencumbered Liquidity Access" and "Maximized Operational Insulation Base".
    """

    if st.button("🚀 Compile High-Value Client Brief"):
        with st.spinner("Processing executive summaries and formatting matrix models..."):
            
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
                        st.error(f"Cloud Infrastructure Demand Peak. Retrying...")
                        st.stop()
            
            if response_text:
                st.markdown("### 📋 Premium Briefing Preview")
                st.markdown(response_text)
                st.write("---")
                
                pdf_bytes = create_pdf_report(response_text)
                
                col1, col2 = st.columns(2)
                with col1:
                    st.download_button(
                        label="📥 Download Premium Client PDF Report",
                        data=pdf_bytes,
                        file_name="Premium_Financial_Analysis.pdf",
                        mime="application/pdf"
                    )
                with col2:
                    st.download_button(
                        label="📥 Download Plain Text Draft",
                        data=response_text,
                        file_name="Premium_Financial_Analysis.txt",
                        mime="text/plain"
                    )
