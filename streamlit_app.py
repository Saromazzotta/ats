from datetime import datetime
from dotenv import load_dotenv
import os
import io
import streamlit as st
import pytesseract
from PIL import Image
import pdf2image
import google.generativeai as genai
from google.api_core import exceptions as google_exceptions

load_dotenv() # Loads environment variables

genai.configure(api_key=os.getenv("MY_API_KEY")) # Sets a global API key

# Extracts pdf content and uses caching to reduce api load
@st.cache_data(show_spinner="Converting PDF and extracting text...")
def extract_pdf_content(file_bytes: bytes):
    """Convert PDF bytes to images and OCR text. Cached so repeated Streamlit reruns don't re-process the same file."""
    images = pdf2image.convert_from_bytes(file_bytes)
    text = "\n".join(pytesseract.image_to_string(img) for img in images)
    return images, text

@st.cache_data(show_spinner=False)
def send_to_gemini(job_description: str, extracted_text: str) -> str:
    # Sends job description and resume to Gemini for comparison

    model = genai.GenerativeModel(model_name='gemini-2.5-flash')
    today = datetime.now().strftime("%B %d, %Y")

    prompt = f"""
Act as a hiring AI that evaluates resumes against job descriptions.

**Today's Date:** {today}
CRITICAL: Any employment date before {today} is a past date and represents real
experience. Calculate all durations by subtracting the start date from today's
date. Do NOT flag any date before {today} as a future date or as an error.

**Instructions:**
- Compare the resume with the job description.
- Use the following criteria to calculate a **match percentage** (0-100%):
    - 50%: Core required skills and experience match. Differentiate between "required" and "preferred" qualifications — missing a preferred skill should penalize less than missing a required one.
    - 30%: Additional relevant skills, certifications, and transferable experience. Consider whether the candidate's existing certifications cover or exceed what is asked for (e.g., Security+ satisfies DoD 8570 IAT Level II; AZ-900 is foundational toward AZ-104).
    - 20%: Industry-specific keywords and preferred qualifications.

**Scoring Guidelines:**
- If a job lists a skill as "preferred" or "nice to have," do NOT treat it as a hard gap. Reduce its weight in the match calculation.
- If the candidate holds a higher-level certification that encompasses a lower one (e.g., Security+ covers A+ security concepts), give partial or full credit.
- Evaluate transferable experience fairly. For example, customer-facing technical troubleshooting at Apple Genius Bar translates to help desk support skills.
- When calculating years of experience, use today's date minus employment start dates. Do not penalize for dates that are in the past relative to today.

**Output Format:**
1. **Match Percentage:** X%
2. **Strengths:** Bullet list organized by the three scoring categories.
3. **Weaknesses:** Bullet list organized by the three scoring categories. Clearly label each weakness as impacting a "required" vs "preferred" qualification.
4. **Missing Keywords:** List missing skills, tools, and certifications. Mark each as (Required) or (Preferred).
5. **Recommendations:** 2-3 specific, actionable suggestions for how the candidate could improve their match (e.g., add a keyword to the resume, get a certification, reframe experience).

**Job Description:**
{job_description}

**Resume:**
{extracted_text}
"""

    response = model.generate_content(
        prompt, 
        generation_config={"temperature": 0})
    print(f"Raw API Response: {response}")

    if hasattr(response, 'text') and response.text:
        print(f"Gemini Response: {response.text}")
        return response.text
    else:
        raise RuntimeError("No text found in Gemini response")
        
    
    

## -------------------------------------------------------------------------------------------------

def main():
    st.title("Resume Job Match Analyzer")

    if "running" not in st.session_state:
        st.session_state.running = False

    #Input Fields
    job_description = st.text_area("Paste Job Description:", height=200) # Creates job description text area
    uploaded_file = st.file_uploader(label="Choose a file", type="pdf") # Uploads PDF

    # Process PDF using convert function and extracts images
    # Initialize extracted text
    extracted_text = None # Creates variable inside of main() scope to be used later

    if uploaded_file: 
        try:
            images, extracted_text = extract_pdf_content(uploaded_file.getvalue())
    
            st.image(
                images,
                caption=[f"Page {i+1}" for i in range(len(images))],
            )
        except Exception as e:
            st.error(f"failed to process PDF: {e}")
        

        # Disable the button while a request is happening to prevent double clicks
        compare_clicked = st.button(
            "Compare with Gemini",
            disabled=st.session_state.running,
        )

        if compare_clicked:
            if not job_description:
                st.error("Please paste a job description.")
            elif not extracted_text:
                st.error("Please upload a resume before proceeding.")
            else:
                st.session_state.running = True
                st.divider()
    try:
        with st.spinner("Processing with Gemini..."):
            result = send_to_gemini(job_description, extracted_text)
        st.success("✅ Analysis Complete!")
        st.subheader("Gemini's Analysis:")
        st.markdown(result)
    except google_exceptions.ResourceExhausted:
        st.error(
            "Rate limit hit. Wait ~60 seconds and try again, or switch to gemini-2.5-flash-lite.")
    finally:
        st.session_state.running = False


# Runs the app
if __name__ == "__main__":
    main()