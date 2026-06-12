import streamlit as st
import pdfplumber
from google import genai
import io

# Import ReportLab tools for reliable, safe layout handling
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT

# 1. Page Configuration
st.set_page_config(page_title="Firm Financial Reporter", layout="wide")
st.title("📊 Client Financial Statement Analyzer")
st.subheader("Upload Annual Financial Statements to generate professional text and PDF analysis reports.")

# 2. Configure Environment Secrets
api_key = st.secrets.get("GEMINI_API_KEY")
if not api_key:
    st.error("Missing Gemini API Key. Please add it to your Streamlit secrets.")
    st.stop()

client = genai.Client(api_key=api_key)

# 3. Robust Helper Function to Convert Text into a Clean ReportLab PDF
def create_pdf_report(report_text):
    buffer = io.BytesIO()
    
    # Setup document geometry securely
    doc = SimpleDocTemplate(
        buffer, 
        pagesize=letter,
        rightMargin=54, leftMargin=54, # 0.75 inch clean standard margins
        topMargin=54, bottomMargin=54
    )
    
    styles = getSampleStyleSheet()
    
    # Build corporate styles
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=20,
        leading=24,
        spaceAfter=15
    )
    
    heading_style = ParagraphStyle(
        'SectionHeader',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=13,
        leading=16,
        spaceBefore=12,
        spaceAfter=6,
        keepWithNext=True # Prevents headers floating at the bottom of a page
    )
    
    body_style = ParagraphStyle(
        'ReportBody',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=10,
        leading=14,
        spaceAfter=6,
        alignment=TA_LEFT
    )

    story = []
    
    # Document Header
    story.append(Paragraph("FINANCIAL ANALYSIS REPORT", title_style))
    story.append(Spacer(1, 10))
    
    # Process text line by line to keep formatting highly professional
    lines = report_text.split('\n')
    for line in lines:
        clean_line = line.strip()
        if not clean_line:
            continue
            
        # Strip away standard markdown headers and style them natively
        if clean_line.startswith(('1.', '2.', '3.', '4.', '###', '##')):
            header_text = clean_line.replace('#', '').strip()
            story.append(Paragraph(header_text, heading_style))
        else:
            # Clean up common raw markdown formatting indicators safely
            clean_line = clean_line.replace('**', '').replace('*', '').replace('___', '').replace('---', '')
            story.append(Paragraph(clean_line, body_style))
            
    # Build PDF layout in memory safely
    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()

# 4. File Uploader Interface
uploaded_files = st.file_uploader(
    "Upload Financial PDFs (Select multiple to compare years)", 
    type=["pdf"], 
    accept_multiple_files=True
)

if uploaded_files:
    st.info(f"Processing {len(uploaded_files)} document(s)...")
    
    combined_raw_text = ""
    for uploaded_file in uploaded_files:
        combined_raw_text += f"\n=== DOCUMENT: {uploaded_file.name} ===\n"
        with pdfplumber.open(io.BytesIO(uploaded_file.read())) as pdf:
            for i, page in enumerate(pdf.pages):
                page_text = page.extract_text()
                if page_text:
                    combined_raw_text += f"\n--- Page {i+1} ---\n{page_text}"

    st.success("PDF Data safely extracted into memory!")

    analysis_prompt = f"""
    You are a senior professional chartered accountant and commercial financial auditor.
    Analyze the following extracted financial data from the client's financial statements:
    
    {combined_raw_text}
    
    Generate a rigorous, executive-level financial analysis report to present to the client.
    Your report MUST include the following specific sections:
    
    1. EXECUTIVE SUMMARY & STANDING
       - Where is the business currently sitting? Give an immediate high-level health check.
       - A summary list comparing Key Figures (Revenue, Gross Profit, Net Profit, Cash Balances) across available years.
    
    2. PROFITABILITY ANALYSIS
       - Detail the Gross Profit (GP) increase or decrease in currency and margin percentages.
       - Comment on revenue growth/contraction trends and overhead expenditure efficiency.
    
    3. LIQUIDITY & FINANCIAL STANDING
       - Calculate and comment on the Current Ratio and Acid-Test / Quick Ratio.
       - Point out any operational risks or cash-flow bottlenecks.
    
    4. STRATEGIC RECOMMENDATIONS
       - Provide 3-4 professional, actionable business recommendations based on the numbers.
    
    Tone: Highly professional, objective, and advisory. Avoid building ASCII/Markdown tables with complex vertical bar symbols; output data points in clean text rows or structured itemized lists.
    """

    if st.button("🚀 Generate Client Report"):
        with st.spinner("Analyzing financials and compiling metrics..."):
            try:
                response = client.models.generate_content(
                    model='gemini-2.5-flash',
                    contents=analysis_prompt
                )
                
                report_text = response.text
                
                st.markdown("### 📋 Deployed Financial Report Preview")
                st.markdown(report_text)
                st.write("---")
                
                # Generate ReportLab PDF in real-time without layout or horizontal bugs
                pdf_bytes = create_pdf_report(report_text)
                
                # Split layout into two download options
                col1, col2 = st.columns(2)
                
                with col1:
                    st.download_button(
                        label="📥 Download Report as PDF (.pdf File)",
                        data=pdf_bytes,
                        file_name="Financial_Analysis_Report.pdf",
                        mime="application/pdf"
                    )
                    
                with col2:
                    st.download_button(
                        label="📥 Download Report as Text (.txt File)",
                        data=report_text,
                        file_name="Financial_Analysis_Report.txt",
                        mime="text/plain"
                    )
                
            except Exception as e:
                st.error(f"An error occurred during generation: {e}")
