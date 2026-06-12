import streamlit as st
import pdfplumber
from google import genai
import io
import os

# Visual Graphic Packages (100% Free)
import matplotlib.pyplot as plt

# ReportLab Layout & Presentation Tools
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, HRFlowable, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.colors import HexColor

# 1. Page Configuration
st.set_page_config(page_title="Executive Performance Portal", layout="wide")
st.title("📊 Executive Performance Portal & Analytics")
st.subheader("Convert client financial statements into visual, board-room ready financial summaries.")

# 2. Configure Environment Secrets
api_key = st.secrets.get("GEMINI_API_KEY")
if not api_key:
    st.error("Missing Gemini API Key. Please add it to your Streamlit secrets.")
    st.stop()

client = genai.Client(api_key=api_key)

# 3. Helper Function to Programmatically Generate Trend Charts
def generate_trend_chart():
    # Hardcoded/Extracted metrics tracking the operational turnaround data from FY22 to FY23
    years = ['FY2022', 'FY2023']
    revenue = [32120820 / 1e6, 24588893 / 1e6]  # In Millions
    gross_profit = [2168696 / 1e6, 1234558 / 1e6]  # In Millions
    net_profit = [202962 / 1e5, 251079 / 1e5]  # In Hundred Thousands for scaling visibility
    
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 4.5))
    
    # Chart 1: Revenue & Gross Profit Optimization
    x = range(len(years))
    width = 0.35
    ax1.bar([p - width/2 for p in x], revenue, width, label='Revenue (R Millions)', color='#1A2E40')
    ax1.bar([p + width/2 for p in x], gross_profit, width, label='Gross Profit (R Millions)', color='#34495E')
    ax1.set_title('Turnover & Margin Structure', fontsize=11, fontweight='bold', color='#1A2E40')
    ax1.set_xticks(x)
    ax1.set_xticklabels(years)
    ax1.legend(loc='upper right', frameon=False, fontsize=9)
    ax1.spines['top'].set_visible(False)
    ax1.spines['right'].set_visible(False)
    
    # Chart 2: Net Profit & Operational Efficiency Gains
    ax2.plot(years, net_profit, color='#2E7D32', marker='o', linewidth=2.5, label='Net Profit (R x100k)')
    ax2.set_title('Bottom-Line Efficiency Earnings', fontsize=11, fontweight='bold', color='#2E7D32')
    ax2.set_ylim(1.5, 3.0)
    ax2.spines['top'].set_visible(False)
    ax2.spines['right'].set_visible(False)
    ax2.grid(axis='y', linestyle='--', alpha=0.5)
    
    plt.tight_layout()
    chart_path = "financial_trends.png"
    plt.savefig(chart_path, dpi=200)
    plt.close()
    return chart_path

# 4. Premium Document Generation Engine
def create_pdf_report(report_text, chart_file):
    buffer = io.BytesIO()
    
    doc = SimpleDocTemplate(
        buffer, 
        pagesize=letter,
        rightMargin=54, leftMargin=54,
        topMargin=54, bottomMargin=54
    )
    
    styles = getSampleStyleSheet()
    
    # Premium Executive Branding Theme
    title_style = ParagraphStyle(
        'DocTitle', parent=styles['Heading1'],
        fontName='Helvetica-Bold', fontSize=22, leading=26,
        textColor=HexColor('#1A2E40'), spaceAfter=4
    )
    
    subtitle_style = ParagraphStyle(
        'DocSubtitle', parent=styles['Normal'],
        fontName='Helvetica', fontSize=10, leading=14,
        textColor=HexColor('#666666'), spaceAfter=15
    )
    
    heading_style = ParagraphStyle(
        'SectionHeader', parent=styles['Heading2'],
        fontName='Helvetica-Bold', fontSize=12, leading=16,
        textColor=HexColor('#1A2E40'), spaceBefore=14, spaceAfter=8,
        keepWithNext=True
    )
    
    body_style = ParagraphStyle(
        'ReportBody', parent=styles['Normal'],
        fontName='Helvetica', fontSize=10, leading=15,
        textColor=HexColor('#333333'), spaceAfter=6, alignment=TA_LEFT
    )

    story = []
    
    # Corporate Document Presentation Accent
    story.append(Paragraph("EXECUTIVE FINANCIAL PERFORMANCE ACCELERATION REPORT", title_style))
    story.append(Paragraph("Bespoke Client Insights Portfolio | Operations & Profitability Review", subtitle_style))
    story.append(HRFlowable(width="100%", thickness=2, color=HexColor('#1A2E40'), spaceAfter=15))
    
    # Safely inject our dynamically generated chart asset
    if os.path.exists(chart_file):
        story.append(Paragraph("VISUAL PERFORMANCE METRICS & TREND ANALYSIS", heading_style))
        story.append(Spacer(1, 4))
        story.append(Image(chart_file, width=480, height=216))
        story.append(Spacer(1, 12))
    
    # Ingest the refined advisory breakdown line by line
    lines = report_text.split('\n')
    for line in lines:
        clean_line = line.strip()
        if not clean_line:
            continue
            
        if clean_line.startswith(('1.', '2.', '3.', '4.', '###', '##')):
            header_text = clean_line.replace('#', '').strip().upper()
            story.append(Spacer(1, 4))
            story.append(Paragraph(header_text, heading_style))
        else:
            clean_line = clean_line.replace('**', '').replace('*', '').replace('___', '').replace('---', '')
            story.append(Paragraph(clean_line, body_style))
            
    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()

# 5. File Uploader Interface
uploaded_files = st.file_uploader(
    "Upload Financial PDFs (Select multiple for comparative multi-year profiling)", 
    type=["pdf"], 
    accept_multiple_files=True
)

if uploaded_files:
    st.info("Mapping financial vectors safely into memory...")
    
    combined_raw_text = ""
    for uploaded_file in uploaded_files:
        combined_raw_text += f"\n=== FINANCIAL BALANCES INGESTED: {uploaded_file.name} ===\n"
        with pdfplumber.open(io.BytesIO(uploaded_file.read())) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    combined_raw_text += f"\n{page_text}"

    st.success("Analysis model synchronized!")

    # 6. Sharp, Professional Prompt Design
    analysis_prompt = f"""
    You are an elite financial strategist and executive director of business intelligence.
    Review the following corporate data files:
    
    {combined_raw_text}
    
    Generate an incredibly sleek, high-level business performance brief structured directly for our client presentation.
    
    CRITICAL RESTRICTIONS & DIRECTIONS:
    - Focus exclusively on highlighting performance wins: notice and praise how net profit rose from R202,962 to R251,079 despite market adjustments, driven by an incredible 50% slash in operational overhead costs.
    - NEVER include a section or point named "Strategic Growth Recommendations" or "Recommendations". The client wants an analysis, not to be given homework.
    - NEVER mention, hint at, or critique missing inventory accounts, absence of liability entries, or compliance gaps. The financial profile must read as entirely foolproof, intentional, and robust.
    - If current liabilities read as zero, refer to the entity's position as having "Unencumbered Liquidity Access", "Optimal Capital Insulation", and "Maximized Operational Cushion".
    - Keep paragraphs punchy, corporate, elite, and focused on showcasing strong financial standing.
    
    Format the brief using these exact primary pillars:
    
    1. EXECUTIVE FINANCIAL HEALTH CHECK
       - A summary overview indicating how the business is currently sitting, framing the transition between reporting cycles as a deliberate strategy of margin protection.
       - A clean list presenting the core figures (Turnover Revenue, Gross Profit, Bottom-line Net Profits, and Closing Favourable Cash Pools) across the active comparative cycles.
    
    2. MARGIN PERFORMANCE & OVERHEAD OPTIMIZATION
       - Discuss the Gross Profit margins and explicitly detail the massive efficiency success where expenses were cut down from R1.96M to R983k, showing strong operational control.
    
    3. CAPITAL FREEDOM & CASH INSULATION
       - Review the absolute stability of the owner's unencumbered capital structure and immediate cash funding availability.
    """

    if st.button("🚀 Generate High-Impact Client Brief"):
        with st.spinner("Rendering financial visualizations and generating copy..."):
            try:
                response = client.models.generate_content(
                    model='gemini-2.5-flash',
                    contents=analysis_prompt
                )
                
                report_text = response.text
                
                # Instantly draw and output graphic assets in real time
                chart_img = generate_trend_chart()
                
                # Split Streamlit view window into columns for interactive preview
                st.markdown("### 📋 Executive Presentation Preview")
                st.image(chart_img, caption="Automated Client Trend Interface Metrics")
                st.markdown(report_text)
                st.write("---")
                
                # Pack text and charts together into a standalone downloadable PDF binary
                pdf_bytes = create_pdf_report(report_text, chart_img)
                
                col1, col2 = st.columns(2)
                with col1:
                    st.download_button(
                        label="📥 Download Eye-Catching PDF Portfolio",
                        data=pdf_bytes,
                        file_name="Executive_Financial_Portfolio.pdf",
                        mime="application/pdf"
                    )
                with col2:
                    st.download_button(
                        label="📥 Download Plain Text Draft",
                        data=report_text,
                        file_name="Executive_Financial_Report.txt",
                        mime="text/plain"
                    )
                
                # Clean up local temporary file system after buffer compilation
                if os.path.exists(chart_img):
                    os.remove(chart_img)
                    
            except Exception as e:
                st.error(f"Execution handling resolved with: {e}")
