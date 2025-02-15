from dotenv import load_dotenv
import os
import streamlit as st
from PIL import Image
import pdf2image
import google.generativeai as genai

load_dotenv() # Loads environment variables

# Pass the api key inside of genai.configure to make it easily reusable. Sets an API key globally 
genai.configure(api_key=os.getenv("MY_API_KEY"))



'''
    1. Create a field for job description
    2. Upload PDF
    3. Turn PDF to image 
    4. Process image and send to Google Gemini Pro
    5. Create Prompts Template[Multiple Prompts]
'''

# Create a field for job description
job_description = st.text_area("Paste Job Description:", height=200)


# Upload PDF
uploaded_file = st.file_uploader(label="Choose a file", type="pdf")

def file_checker(uploaded_file):
    if uploaded_file is not None:
        st.success(f"File uploaded: {uploaded_file.name}")
        # To read file as bytes:
    else:
        st.warning("Please upload a file.")


# Turn PDF to image

def convert_pdf_to_image(uploaded_file):
    bytes_data = uploaded_file.getvalue()
    st.write(bytes_data)