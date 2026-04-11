import datetime
from dotenv import load_dotenv
import os
import io
import streamlit as st
import pytesseract
from PIL import Image
import pdf2image
import google.generativeai as genai

load_dotenv() # Loads environment variables

genai.configure(api_key=os.getenv("MY_API_KEY")) # Sets a global API key


# Turn PDF to image
def convert_pdf_to_image(uploaded_file):
    if uploaded_file is None:
        st.warning("Please upload a file.")
        return None 
    try:
        bytes_data = uploaded_file.getvalue() # Gets this file's binary data
        images = pdf2image.convert_from_bytes(bytes_data) # Converts PDF to images
        return images # Return the list of images

    except Exception as e:
        st.error(f"An error occured while converting the PDF: {e}")
        return None # Ensure the function always returns something

def send_to_gemini(job_description, extracted_text):
    # Sends job description and resume to Gemini for comparison

    model = genai.GenerativeModel(model_name='gemini-2.5-flash')

    today = datetime.now().strftime("%B %d, %Y")

    prompt = f"""
Act as a hiring AI that evaluates resumes against job descriptions.

**Today's Date:** {today}
Use this date to accurately calculate employment durations and determine whether dates on the resume are in the past or future. Do not flag past dates as errors.

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

    try:
        response = model.generate_content(prompt, generation_config={"temperature": 0})
        print(f"Raw API Response: {response}")

        if hasattr(response, 'text'):
            print(f"Gemini Response: {response.text}")
            return response.text
        else:
            print("No text found in response.")
            return "Error: No text found in resposne."
        
    except Exception as e:
        print(f"Error occured: {e}")
        return f"API Error: {e}"

def main():
    st.title("Resume Job Match Analyzer")

    #Input Fields
    job_description = st.text_area("Paste Job Description:", height=200) # Creates job description text area
    uploaded_file = st.file_uploader(label="Choose a file", type="pdf") # Uploads PDF

    # Process PDF using convert function and extracts images
    # Initialize extracted text
    extracted_text = None # Creates variable inside of main() scope to be used later

    if uploaded_file: 
        images = convert_pdf_to_image(uploaded_file)

        if images:
            st.image(images, caption=[f"Page {i+1}" for i in range(len(images))])
            # Use Pytesseract to convert image to string
            extracted_text = "\n".join(pytesseract.image_to_string(img) for img in images)
            print(f"---------EXTRACTED TEXT----------\n{extracted_text}")
            # st.text_area("Resume", extracted_text, height=200) # Displays it to streamlit frontend
        else:
            st.error("Failed to extract text.")


    # Send to gemini

    if st.button("Compare with Gemini"):
        status_placeholder = st.empty() # Creates empty place holder 
        st.divider()

        if not job_description:
            st.error("Please paste a job description")
        elif not extracted_text: 
            st.error("Please upload a resume before proceeding.")
        else:
            status_placeholder.info("Processing with Gemini...")
            result = send_to_gemini(job_description, extracted_text)

            status_placeholder.success("✅ Analysis Complete!")

            # Display the full analysis
            st.subheader("Gemini's Analysis:")
            st.markdown(result) # General explanation


# Runs the app
if __name__ == "__main__":
    main()