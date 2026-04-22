from datetime import datetime
import os
import time


from dotenv import load_dotenv
from google import genai
from google.api_core import exceptions as google_exceptions
import pdf2image
import pytesseract
import streamlit as st

from prompts import RESUME_ANALYSIS_SYSTEM

load_dotenv() # Loads environment variables

client = genai.Client(api_key=os.getenv("MY_API_KEY")) # Sets a global API key


# Extracts pdf content and uses caching to reduce api load
@st.cache_data(show_spinner="Converting PDF and extracting text...")
def extract_pdf_content(file_bytes: bytes):
    """Convert PDF bytes to images and OCR text. Cached so repeated Streamlit reruns don't re-process the same file."""
    images = pdf2image.convert_from_bytes(file_bytes)
    text = "\n".join(pytesseract.image_to_string(img) for img in images)
    return images, text



def _call_with_retry(prompt: str, max_retries: int = 3):
    """Helper function to call the Gemini API with retries on ServiceUnavailable errors."""
    for attempt in range(max_retries):
        try:
            return client.models.generate_content(
                model="gemini-2.5-flash-lite",
                contents=prompt,
                config={
                    "temperature": 0,
                    "system_instruction": RESUME_ANALYSIS_SYSTEM,
                    },
            )
        except google_exceptions.ServiceUnavailable:
            if attempt == max_retries - 1:
                raise
            time.sleep(2 ** attempt)  # Exponential backoff




@st.cache_data(show_spinner=False)
def send_to_gemini(job_description: str, extracted_text: str) -> str:
    today = datetime.now().strftime("%B %d, %Y")
    prompt = f"""Today's date is {today}.

Job Description:
{job_description}

Resume:
{extracted_text}"""

    response = _call_with_retry(prompt)

    if response.text:
        return response.text
    raise RuntimeError("No text found in Gemini response.")
    
    

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
                except google_exceptions.ServiceUnavailable:
                    st.error("Gemini is temporarily overloaded. This is on Google's end. Please wait a minute and try again.")
                except google_exceptions.ResourceExhausted:
                    st.error(
                        "Rate limit hit. The free tier has daily and per-minute caps. "
                        "Wait ~60 seconds and try again, or check your quota at "
                        "https://aistudio.google.com/apikey.")
                except Exception as e:
                    st.error(f"API error: {e}")
                finally:
                    st.session_state.running = False


# Runs the app
if __name__ == "__main__":
    main()