import streamlit as st
import pdfplumber
from google import genai
import io

# 1. Page Configuration
st.set_page_config(page_title="Firm Financial Reporter", layout="wide")
st.title("📊 Client Financial Statement Analyzer")
st.subheader("Upload Annual Financial Statements to generate a professional PDF analysis report.")

# 2. Get Secure API Key from Streamlit Environment
# This keeps your free key totally hidden from the web
api_key = st.secrets.get("GEMINI_API_KEY")

if not api_key:
    st.error("Missing Gemini API Key. Please add it to your Streamlit secrets.")
    st.stop()

# Initialize the Gemini Client
client = genai.Client(api_key=api_key)

# 3. File Uploader Interface
uploaded_files = st.file_uploader(
    "Upload Financial PDFs (Select multiple to compare years)", 
    type=["pdf"], 
    accept_multiple_files=True
)

if uploaded_files:
    st.info(f"Processing {len(uploaded_files)} document(s)...")
    
    # Store extracted text from all uploaded files
    combined_raw_text = ""
    
    for uploaded_file in uploaded_files:
        combined_raw_text += f"\n=== DOCUMENT: {uploaded_file.name} ===\n"
        # Open PDF from memory without saving to a local disk
        with pdfplumber.open(io.BytesIO(uploaded_file.read())) as pdf:
            for i, page in enumerate(pdf.pages):
                page_text = page.extract_text()
                if page_text:
                    combined_raw_text += f"\n--- Page {i+1} ---\n{page_text}"

    st.success("PDF Data safely extracted into memory!")

    # 4. Define the Expert Accounting Prompt
    analysis_prompt = f"""
    You are a senior professional chartered accountant and commercial financial auditor.
    Analyze the following extracted financial data from the client's financial statements:
    
    {combined_raw_text}
    
    Generate a rigorous, executive-level financial analysis report to present to the client.
    Your report MUST include the following specific sections:
    
    1. EXECUTIVE SUMMARY & STANDING
       - Where is the business currently sitting? Give an immediate high-level health check.
       - A summary table comparing Key Figures (Revenue, Gross Profit, Net Profit, Cash Balances) across the available financial years.
    
    2. PROFITABILITY ANALYSIS
       - Detail the Gross Profit (GP) increase or decrease in both currency amounts and margin percentages.
       - Comment on revenue growth/contraction trends.
       - Analyze overhead expenditure efficiency (Are operational expenses rising faster than revenue?).
    
    3. LIQUIDITY & FINANCIAL STANDING
       - Calculate and comment on the Current Ratio (Current Assets / Current Liabilities).
       - Calculate and comment on the Acid-Test / Quick Ratio.
       - Point out any red flags, such as cash trapped in trade debtors (receivables) while bank balances drop, or high reliance on drawings.
    
    4. STRATEGIC RECOMMENDATIONS
       - Provide 3-4 professional, actionable business recommendations based on the data to optimize their cash positioning, protect margins, or manage liabilities next year.
    
    Tone: Highly professional, objective, advisory, and polished. Do not use generic filler.
    """

    # 5. Run Free AI Generation
    if st.button("🚀 Generate Client Report"):
        with st.spinner("Analyzing financials and calculating metrics..."):
            try:
                # Use the fast, powerful, and free-tier eligible flash model
                response = client.models.generate_content(
                    model='gemini-2.5-flash',
                    contents=analysis_prompt
                )
                
                # Render the resulting report on screen
                st.markdown("### 📋 Deployed Financial Report Preview")
                report_text = response.text
                st.markdown(report_text)
                
                # 6. Enable Free Text Exporting 
                # Allows you to easily copy-paste or download directly into Microsoft Word/Docs
                st.download_button(
                    label="📥 Download Report as Text (.txt File)",
                    data=report_text,
                    file_name="Financial_Analysis_Report.txt",
                    mime="text/plain"
                )
                
            except Exception as e:
                st.error(f"An error occurred during generation: {e}")
