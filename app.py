import streamlit as st
import pdfplumber
from google import genai
import io

# Import professional ReportLab components
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER
from reportlab.lib.colors import HexColor

# 1. Page Configuration
st.set_page_config(page_title="Executive Performance Reporter", layout="wide")
st.title("📈 Executive Financial Performance Portal")
st.subheader("Upload Annual Financial Statements to compile a clean, client-facing advisory report.")

# 2. Configure Environment Secrets
api_key = st.secrets.get("GEMINI_API_KEY")
if not api_key:
    st.error("Missing Gemini API Key. Please add it to your Streamlit secrets.")
    st.stop()

client = genai.Client(api_key=api_key)

# 3. Upgraded Styling Engine for Professional Client PDFs
def create_pdf_report(report_text):
    buffer = io.BytesIO()
    
    # Premium geometric boundaries 
    doc = SimpleDocTemplate(
        buffer, 
        pagesize=letter,
        rightMargin=54, leftMargin=54,
        topMargin=54, bottomMargin=54
    )
    
    styles = getSampleStyleSheet()
    
    # Custom Corporate Brand Palette (Deep Charcoal and Slate Blue)
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=22,
        leading=26,
        textColor=HexColor('#1A2E40'),
        spaceAfter=4,
        alignment=TA_LEFT
    )
    
    subtitle_style = ParagraphStyle(
        'DocSubtitle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=10,
        leading=14,
        textColor=HexColor('#555555'),
        spaceAfter=15
    )
    
    heading_style = ParagraphStyle(
        'SectionHeader',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=12,
        leading=16,
        textColor=HexColor('#2C3E50'),
        spaceBefore=14,
        spaceAfter=6,
        keepWithNext=True
    )
    
    body_style = ParagraphStyle(
        'ReportBody',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=10,
        leading=15,
        textColor=HexColor('#333333'),
        spaceAfter=6,
        alignment=TA_LEFT
    )

    story = []
    
    # Elegant Top Header Layout
    story.append(Paragraph("FINANCIAL PERFORMANCE & MANAGEMENT REPORT", title_style))
    story.append(Paragraph("Prepared for Client Presentation | Executive Summary", subtitle_style))
    story.append(HRFlowable(width="100%", thickness=1.5, color=HexColor('#2C3E50'), spaceAfter=15))
    
    # Process and build text layout
    lines = report_text.split('\n')
    for line in lines:
        clean_line = line.strip()
        if not clean_line:
            continue
            
        # Parse standard sections beautifully
        if clean_line.startswith(('1.', '2.', '3.', '4.', '###', '##')):
            header_text = clean_line.replace('#', '').strip().upper()
            story.append(Spacer(1, 4))
            story.append(Paragraph(header_text, heading_style))
        else:
            # Strip standard raw markdown characters safely
            clean_line = clean_line.replace('**', '').replace('*', '').replace('___', '').replace('---', '')
            story.append(Paragraph(clean_line, body_style))
            
    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()

# 4. File Uploader Interface
uploaded_files = st.file_uploader(
    "Upload Financial PDFs", 
    type=["pdf"], 
    accept_multiple_files=True
)

if uploaded_files:
    st.info("Extracting operational figures safely...")
    
    combined_raw_text = ""
    for uploaded_file in uploaded_files:
        combined_raw_text += f"\n=== FINANCIAL YEAR DATA: {uploaded_file.name} ===\n"
        with pdfplumber.open(io.BytesIO(uploaded_file.read())) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    combined_raw_text += f"\n{page_text}"

    st.success("Financial data structured successfully!")

    # 5. The Guardrailed Prompt Template
    analysis_prompt = f"""
    You are an elite corporate financial consultant and executive growth advisor.
    Review the following raw numbers from the client's financial statements:
    
    {combined_raw_text}
    
    Generate a concise, high-impact business performance report designed directly for the client. 
    
    CRITICAL INSTRUCTIONS:
    - Focus strictly on practical business performance metrics (revenue trends, gross profit margins, overhead efficiency, and cash flow deployment).
    - NEVER mention, critique, or point out the absence of inventory, the lack of liabilities, missing disclosures, or any accounting disclosure compliance failures. The financials must look robust, deliberate, and sound.
    - If liability figures are zero, frame liquidity purely around "Cash Reserve Cushion", "Asset Availability", or "Working Capital Flexibility".
    - Keep the output short, sharp, polished, and immediately digestible for a business owner.
    
    Structure the report with these exact sections:
    
    1. EXECUTIVE FINANCIAL SUMMARY
       - Give a clear, motivating review of where the business sits and how it is looking overall.
       - Provide a crisp list of key comparative numbers (Revenue, Gross Profit, Net Profit, and Liquid Cash Balances) across the available years.
    
    2. PROFITABILITY & OVERHEAD PERFORMANCE
       - Track Gross Profit margin changes clearly.
       - Highlight positive cost-reduction measures or areas where expenditure was successfully optimized.
    
    3. CAPITAL POSITION & CASH VELOCITY
       - Highlight cash reserve movements and stability.
       - Comment on the strength of the business's asset baseline and immediate cash funding availability.
    
    4. STRATEGIC GROWTH RECOMMENDATIONS
       - Provide 2-3 concise, forward-looking strategic goals to optimize bottom-line performance or scale margins in the next cycle.
    
    Tone: Sophisticated, business-oriented, consultative, and positive. Avoid long technical filler and markdown text tables.
    """

    if st.button("🚀 Generate Client Presentation Report"):
        with st.spinner("Compiling executive metrics..."):
            try:
                response = client.models.generate_content(
                    model='gemini-2.5-flash',
                    contents=analysis_prompt
                )
                
                report_text = response.text
                
                st.markdown("### 📋 Executive Preview")
                st.markdown(report_text)
                st.write("---")
                
                # Render clean corporate PDF matching instructions
                pdf_bytes = create_pdf_report(report_text)
                
                col1, col2 = st.columns(2)
                with col1:
                    st.download_button(
                        label="📥 Download Executive PDF Report",
                        data=pdf_bytes,
                        file_name="Executive_Financial_Report.pdf",
                        mime="application/pdf"
                    )
                with col2:
                    st.download_button(
                        label="📥 Download Raw Text Draft",
                        data=report_text,
                        file_name="Executive_Financial_Report.txt",
                        mime="text/plain"
                    )
                
            except Exception as e:
                st.error(f"Generation error resolved with: {e}")
