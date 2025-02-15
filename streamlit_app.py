from dotenv import load_dotenv
import os
import io
import streamlit as st
from PIL import Image
import pdf2image
import google.generativeai as genai

load_dotenv() # Loads environment variables

genai.configure(api_key=os.getenv("MY_API_KEY")) # Sets a global API key

'''
    1. Create a field for job description
    2. Upload PDF
    3. Turn PDF to image 
    4. Process image and send to Google Gemini Pro
    5. Create Prompts Template[Multiple Prompts]
'''

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


def main():
    # Create a field for job description
    job_description = st.text_area("Paste Job Description:", height=200)

    # Upload PDF
    uploaded_file = st.file_uploader(label="Choose a file", type="pdf")

    # Convert file to image using function
    if uploaded_file: 
        images = convert_pdf_to_image(uploaded_file)


        if images:
            st.image(images, caption="Images")







# Runs the app
if __name__ == "__main__":
    main()