import streamlit as st
import pdfplumber
from google import genai
import io
from fpdf import FPDF

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

# 3. Helper Function to Convert Text into a Clean, Formatted PDF
def create_pdf_report(report_text):
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    
    # Simple, professional styling
    pdf.set_font("Helvetica", size=11)
    
    # Split raw text into individual lines to render cleanly
    lines = report_text.split('\n')
    
    for line in lines:
        # If it looks like a major header (e.g., "1. EXECUTIVE SUMMARY")
        if line.strip().startswith(('1.', '2.', '3.', '4.', '###', '##')):
            pdf.ln(5)  # Add extra space before header
            pdf.set_font("Helvetica", style="B", size=13)
            # Remove markdown syntax if present
            clean_header = line.replace('#', '').strip()
            pdf.cell(0, 8, txt=clean_header, ln=True)
            pdf.set_font("Helvetica", size=11) # Reset font style
            pdf.ln(2)
        # If it's a list point or table separator line, keep formatting basic
        elif line.strip().startswith('-') or line.strip().startswith('|'):
            pdf.set_font("Courier", size=10)  # Use fixed-width font for clean data alignment
            pdf.cell(0, 5, txt=line, ln=True)
            pdf.set_font("Helvetica", size=11)
        else:
            # Handle standard paragraph text line wrapping gracefully
            pdf.multi_cell(0, 6, txt=line)
            
    # Output the PDF data straight into an in-memory byte buffer
    pdf_output = pdf.output()
    return bytes(pdf_output)

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
    
    Tone: Highly professional, objective, and advisory. Avoid markdown tables using complex symbols; use standard text lines or lists so it draws clearly on a PDF document page.
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
                
                # Generate PDF download in real-time
                pdf_bytes = create_pdf_report(report_text)
                
                # Split layout into two parallel download buttons
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
