from dotenv import load_dotenv
import os
import streamlit as st

load_dotenv()
API_KEY = os.getenv("MY_API_KEY")

'''
    1. Create a field for job description
    2. Upload PDF
    3. Turn PDF to image 
    4. Process image and send to Google Gemini Pro
    5. Create Prompts Template[Multiple Prompts]
'''

