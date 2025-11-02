import os
import io
import requests
from docx import Document
from google import genai
from google.genai import types

from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# 🚨 Configuration
# NOTE: Replace with your actual S3 link
S3_DOCX_URL = "https://hack-coms-ursmart.s3.us-east-2.amazonaws.com/courses/1/materials/1/437c8224-0d63-46ca-96a6-37f3a478ff29.docx"
PROMPT = "Summarize the key takeaways from this document in three bullet points."

# Initialize the Gemini Client
# It will automatically use the GEMINI_API_KEY environment variable.
try:
    client = genai.Client()
except Exception as e:
    print(f"Error initializing Gemini client: {e}")
    print("Please ensure your GEMINI_API_KEY environment variable is set.")
    exit()

def extract_text_from_docx_url(url: str) -> str:
    """Downloads DOCX content and extracts text using python-docx."""
    print(f"1. Downloading DOCX file from: {url}")
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"Error downloading file. Check if the S3 link is public or if you need to handle AWS authentication/presigned URLs: {e}")
        return None

    # Use io.BytesIO to treat the downloaded binary content as a file
    docx_file = io.BytesIO(response.content)
    
    # Extract text from the in-memory DOCX file
    doc = Document(docx_file)
    full_text = []
    for paragraph in doc.paragraphs:
        full_text.append(paragraph.text)
        
    return '\n'.join(full_text)

def analyze_document_with_gemini():
    """Main function to handle the entire workflow."""
    extracted_text = extract_text_from_docx_url(S3_DOCX_URL)
    if not extracted_text:
        return

    # Treat the extracted text content as a file-like object for upload
    text_io = io.BytesIO(extracted_text.encode('utf-8'))
    
    uploaded_file = None
    try:
        print("2. Uploading extracted text content to Gemini Files API...")
        # Upload the text content as text/plain
        uploaded_file = client.files.upload(
            file=text_io, 
            config={
                'mime_type': 'text/plain', 
                'display_name': "S3_DOCX_Text_Content.txt"
            }
        )
        print(f"   -> Uploaded successfully. File Name: {uploaded_file.name}")

        print(f"3. Generating content with model gemini-2.5-flash...")
        # Include the uploaded file reference and the text prompt
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=[
                uploaded_file, # The file object acts as the multimodal Part
                PROMPT
            ]
        )

        print("\n" + "="*50)
        print("🤖 Gemini Response:")
        print(response.text)
        print("="*50 + "\n")

    except Exception as e:
        print(f"An error occurred during Gemini API call: {e}")

    finally:
        # Clean up: Delete the file from the Files API storage
        if uploaded_file:
            print(f"4. Deleting uploaded file: {uploaded_file.name}")
            client.files.delete(name=uploaded_file.name)
            print("   -> Cleanup complete.")

if __name__ == "__main__":
    analyze_document_with_gemini()