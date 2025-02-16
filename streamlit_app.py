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
        Give a match percentage (0-100%) and explain the reasoning behind it.
        Compare the resume with the job description. Identify strengths and weaknessess.
        List missing skills, certifications, or experiences that the job requires but the resume lacks.

        **Job Description:**
        {job_description}

        **Resume:**
        {extracted_text}
        """

    try:
        response = model.generate_content(prompt)
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
        if not job_description:
            st.error("Please paste a job description")
        elif not extracted_text: 
            st.error("Please upload a resume before proceeding.")
        else:
            print("✅ Both Job Description and Extracted Text are available.")
            st.info("Processing with Gemini Pro...")
            result = send_to_gemini(job_description, extracted_text)
            st.text_area("Gemini's Analysis: ", result, height=1000)


# Runs the app
if __name__ == "__main__":
    main()