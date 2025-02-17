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

    model = genai.GenerativeModel(model_name='gemini-1.5-flash')
    prompt = f"""
        Act as a hiring AI that evaluates resumes against job descriptions.

        **Instructions:** 
        - Compare the resume with the job description.
            - Identify **strengths** and **weaknesses** in skills, experience, and certifications.
            - List **missing keywords** (skills, tools, certifications) required for the job.
            - Provide a **match percentage** (0-100%) based on relevance. 
            - Keep answers **concise and structured**.

        **Job Description:**  
        {job_description}

        **Resume:**  
        {extracted_text}

        **Output Format:**  
        **Match Percentage:** XX%  
        **Strengths:**  
            - Skill 1  
            - Skill 2  
        **Weaknesses:**  
            - Area 1  
            - Area 2  
        **Missing Keywords:**  
            - Keyword 1  
            - Keyword 2  
        **Reasoning:** (Brief explanation)
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
    #Input Fields
    job_description = st.text_area("Paste Job Description:", height=200) # Creates job description text area
    uploaded_file = st.file_uploader(label="Choose a file", type="pdf") # Uploads PDF

    # Process PDF using convert function and extracts images
    if "extracted_text":
        extracted_text = None # Creates variable inside of main() scope to be used later

    if uploaded_file: 
        images = convert_pdf_to_image(uploaded_file)

        if images:
            st.image(images, caption="Images")
            # Use Pytesseract to convert image to string
            extracted_text = pytesseract.image_to_string(images[0])
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
            st.write(result) # General explanation

            # Extract missing keywords dynamically (if formatted properly)
            missing_keywords = []
            for line in result.split("\n"):
                if "Missing Keywords:" in line:
                    missing_keywords.extend(line.replace("Missing Keywords:", "").split(","))

            if missing_keywords:
                st.subheader("🔎 Missing Keywords:")

                with st.expander("Click to view issing keywords"):
                    for keyword in missing_keywords:
                        st.checkbox(keyword.strip(), key=f"kw_{keyword.strip()}")



# Runs the app
if __name__ == "__main__":
    main()