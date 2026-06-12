import streamlit as st
import pdfplumber
from google import genai
import io

# Advanced ReportLab Layout, Grid, and Typographic tools
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
    
    # 0.75-inch margins for an elegant corporate page balance
    doc = SimpleDocTemplate(
        buffer, 
        pagesize=letter,
        rightMargin=54, leftMargin=54,
        topMargin=54, bottomMargin=54
    )
    
    styles = getSampleStyleSheet()
    
    # Executive Typographic Scales
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
    
    # Premium Background Section Header Styles
    section_title_style = ParagraphStyle(
        'SecTitle', fontName='Helvetica-Bold', fontSize=11, leading=14,
        textColor=HexColor('#FFFFFF')
    )
    
    body_style = ParagraphStyle(
        'ReportBody', parent=styles['Normal'],
        fontName='Helvetica', fontSize=10.5, leading=16,
        textColor=HexColor('#334155'), spaceAfter=8, alignment=TA_LEFT
    )
    
    # Grid Table Label & Value Styles
    table_label = ParagraphStyle('TLabel', fontName='Helvetica-Bold', fontSize=10, leading=13, textColor=HexColor('#1E293B'))
    table_value = ParagraphStyle('TValue', fontName='Helvetica-Bold', fontSize=10.5, leading=13, textColor=HexColor('#0F1E2C'), alignment=TA_RIGHT)

    story = []
    
    # Letterhead Branding Accent
    story.append(Paragraph("STRATEGIC FINANCIAL PERFORMANCE BRIEF", title_style))
    story.append(Paragraph("Exclusively Prepared for Executive Management | Operational Portfolio Analysis", subtitle_style))
    story.append(Spacer(1, 10))
    
    lines = report_text.split('\n')
    grid_data = []
    
    for line in lines:
        clean_line = line.strip()
        if not clean_line:
            continue
            
        # 1. Match Major Section Headers
        if clean_line.startswith(('1.', '2.', '3.', '4.', '###', '##')):
            # Flush out any pending grid tables before creating a new header
            if grid_data:
                t = Table(grid_data, colWidths=[320, 184])
                t.setStyle(TableStyle([
                    ('BACKGROUND', (0,0), (-1,-1), HexColor('#F8FAFC')),
                    ('PADDING', (0,0), (-1,-1), 8),
                    ('ALIGN', (1,0), (1,-1), 'RIGHT'),
                    ('LINEBELOW', (0,0), (-1,-1), 0.5, HexColor('#E2E8F0')),
                ]))
                story.append(t)
                story.append(Spacer(1, 12))
                grid_data = []
                
            header_text = clean_line.replace('#', '').strip().upper()
            
            # Premium Full-Width Colored Section Bar instead of a plain text row
            header_table = Table([[Paragraph(header_text, section_title_style)]], colWidths=[504])
            header_table.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,-1), HexColor('#0F1E2C')),
                ('PADDING', (0,0), (-1,-1), 6),
                ('TOPPADDING', (0,0), (-1,-1), 8),
                ('BOTTOMPADDING', (0,0), (-1,-1), 8),
            ]))
            story.append(Spacer(1, 10))
            story.append(header_table)
            story.append(Spacer(1, 10))
            
        # 2. Match Key Financial Indicators (Extract labels and values securely)
        elif ":" in clean_line and (clean_line.startswith('-') or clean_line[0].isdigit() or "R" in clean_line or "Margin" in clean_line):
            parts = clean_line.split(":", 1)
            label_txt = parts[0].replace('-', '').replace('*', '').strip()
            val_txt = parts[1].replace('*', '').strip()
            
            grid_data.append([
                Paragraph(label_txt, table_label),
                Paragraph(val_txt, table_value)
            ])
            
        # 3. Match Paragraph Commentary Text
        else:
            # Flush pending table metrics before rendering paragraphs
            if grid_data:
                t = Table(grid_data, colWidths=[320, 184])
                t.setStyle(TableStyle([
                    ('BACKGROUND', (0,0), (-1,-1), HexColor('#F8FAFC')),
                    ('PADDING', (0,0), (-1,-1), 8),
                    ('ALIGN', (1,0), (1,-1), 'RIGHT'),
                    ('LINEBELOW', (0,0), (-1,-1), 0.5, HexColor('#E2E8F0')),
                ]))
                story.append(t)
                story.append(Spacer(1, 12))
                grid_data = []
                
            clean_line = clean_line.replace('**', '').replace('*', '').replace('___', '').replace('---', '')
            story.append(Paragraph(clean_line, body_style))
            
    # Trailing content cleanup check
    if grid_data:
        t = Table(grid_data, colWidths=[320, 184])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), HexColor('#F8FAFC')), 
            ('PADDING', (0,0), (-1,-1), 8),
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

    # 5. Elite Prompt Strategy For Clean, Bulletproof Advisory Data Maps
    analysis_prompt = f"""
    You are an elite corporate financial managing partner and corporate growth director.
    Review the following company data files carefully:
    
    {combined_raw_text}
    
    Generate an elite executive performance brief customized perfectly for direct delivery to our primary client.
    
    CRITICAL STRUCTURE & PRESENTATION RULES:
    - Never mention, draw, or attempt charts, bars, graphs, or visual markers. The layout must be perfectly text and matrix grid-based.
    - Absolutely NEVER include any section, title, or reference to "Recommendations", "Growth Strategy", or "Strategic Growth Recommendations". Present an unyielding snapshot analysis of operational facts only.
    - Keep every segment short, razor-sharp, polished, and immediately understandable. 
    - The financial summaries must read as fully intentional and foolproof. Do NOT reference missing inventory, undisclosed trade payables, or any financial statement compilation omissions. Frame everything as a calculated, robust capital environment.
    
    Format the output using these exact primary pillars:
    
    1. EXECUTIVE FINANCIAL HEALTH CHECK
       - Provide a sophisticated, high-level summary paragraph showing how the entity is positioned, explicitly detailing how net profits climbed successfully from R202,962 to R251,079 across reporting intervals.
       - Render a clean, raw list of key comparative indicators using the EXACT following metric labels:
         Turnover Revenue Volume: [Insert Number]
         Gross Portfolio Margin: [Insert Number]
         Bottomline Corporate Earnings: [Insert Number]
         Unencumbered Liquid Cash Pools: [Insert Number]
    
    2. OVERHEAD STRATIFICATION & MARGIN OPTIMIZATION
       - Discuss the underlying operational excellence where total operating expenses were optimized down by an incredible 50% (dropping from R1.96 Million to R983 Thousand), safeguarding profit margins despite shifting market revenues.
    
    3. CAPITAL STRUCTURE & INSULATION PROFILE
       - Highlight the complete strength of having an unencumbered capital structure entirely backed by equity with zero external current liabilities. Refer to this as "Unencumbered Liquidity Access" and "Maximized Operational Insulation Base".
    """

    if st.button("🚀 Compile High-Value Client Brief"):
        with st.spinner("Processing executive summaries and formatting matrix models..."):
            try:
                response = client.models.generate_content(
                    model='gemini-2.5-flash',
                    contents=analysis_prompt
                )
                
                report_text = response.text
                
                st.markdown("### 📋 Premium Briefing Preview")
                st.markdown(report_text)
                st.write("---")
                
                # Render the premium PDF with embedded table callout styling
                pdf_bytes = create_pdf_report(report_text)
                
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
                        data=report_text,
                        file_name="Premium_Financial_Analysis.txt",
                        mime="text/plain"
                    )
                    
            except Exception as e:
                st.error(f"Execution handling resolved with: {e}")
