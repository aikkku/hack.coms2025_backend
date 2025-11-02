"""
Chatbot router for Gemini AI integration
Handles chat requests with course materials as context
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional
import os
import io
import requests
from docx import Document
from pypdf import PdfReader
from google import genai
from dotenv import load_dotenv

import database
import oauth2
import models
from repository import material

load_dotenv()

router = APIRouter(
    tags=['Chatbot'],
    prefix="/chatbot"
)

# Initialize Gemini client
try:
    gemini_client = genai.Client()
except Exception as e:
    print(f"Warning: Could not initialize Gemini client: {e}")
    gemini_client = None


class ChatRequest(BaseModel):
    course_id: int
    material_ids: List[int]  # List of material IDs to include in context
    message: str


class ChatResponse(BaseModel):
    response: str
    materials_used: List[int]


def extract_text_from_docx_url(url: str) -> Optional[str]:
    """Downloads DOCX content and extracts text using python-docx."""
    try:
        print(f"Attempting to download DOCX from: {url}")
        response = requests.get(url, timeout=30, stream=True)
        response.raise_for_status()
        
        print(f"Downloaded {len(response.content)} bytes")
        docx_file = io.BytesIO(response.content)
        doc = Document(docx_file)
        full_text = []
        for paragraph in doc.paragraphs:
            if paragraph.text.strip():  # Only add non-empty paragraphs
                full_text.append(paragraph.text)
        
        extracted = '\n'.join(full_text)
        print(f"Extracted {len(extracted)} characters from DOCX")
        return extracted
    except requests.exceptions.RequestException as e:
        print(f"Error downloading file from {url}: {e}")
        print(f"Response status: {getattr(e.response, 'status_code', 'N/A')}")
        return None
    except Exception as e:
        print(f"Error extracting text from DOCX {url}: {e}")
        import traceback
        traceback.print_exc()
        return None


def extract_text_from_txt_url(url: str) -> Optional[str]:
    """Downloads plain text file."""
    try:
        print(f"Attempting to download TXT from: {url}")
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        
        # Try to decode as UTF-8, fallback to latin-1
        try:
            text = response.content.decode('utf-8')
        except UnicodeDecodeError:
            text = response.content.decode('latin-1')
        
        print(f"Extracted {len(text)} characters from TXT")
        return text
    except Exception as e:
        print(f"Error extracting text from TXT {url}: {e}")
        return None


def extract_text_from_pdf_url(url: str) -> Optional[str]:
    """Downloads PDF content and extracts text using pypdf."""
    try:
        print(f"Attempting to download PDF from: {url}")
        response = requests.get(url, timeout=30, stream=True)
        response.raise_for_status()
        
        print(f"Downloaded {len(response.content)} bytes")
        pdf_file = io.BytesIO(response.content)
        
        # Use PdfReader to extract text from PDF
        pdf_reader = PdfReader(pdf_file)
        
        full_text = []
        total_pages = len(pdf_reader.pages)
        print(f"PDF has {total_pages} pages")
        
        for page_num, page in enumerate(pdf_reader.pages, start=1):
            try:
                page_text = page.extract_text()
                if page_text.strip():  # Only add non-empty pages
                    full_text.append(page_text)
                    print(f"Extracted text from page {page_num}/{total_pages}")
            except Exception as e:
                print(f"Warning: Could not extract text from page {page_num}: {e}")
                continue
        
        extracted = '\n\n'.join(full_text)
        print(f"Extracted {len(extracted)} characters from PDF ({total_pages} pages)")
        
        if not extracted.strip():
            print("⚠️ PDF appears to be empty or contains only images/scanned content")
            return None
        
        return extracted
        
    except requests.exceptions.RequestException as e:
        print(f"Error downloading PDF file from {url}: {e}")
        print(f"Response status: {getattr(e.response, 'status_code', 'N/A')}")
        return None
    except Exception as e:
        print(f"Error extracting text from PDF {url}: {e}")
        import traceback
        traceback.print_exc()
        return None


def extract_text_from_url(url: str) -> Optional[str]:
    """
    Extract text from various file types.
    Supports: DOCX, TXT, PDF
    """
    if not url or not url.strip():
        return None
    
    # Normalize URL - remove query parameters for extension check
    url_lower = url.lower().split('?')[0]
    
    # Try to detect file type from URL extension
    if url_lower.endswith('.docx'):
        return extract_text_from_docx_url(url)
    elif url_lower.endswith('.txt') or url_lower.endswith('.text'):
        return extract_text_from_txt_url(url)
    elif url_lower.endswith('.pdf'):
        return extract_text_from_pdf_url(url)
    else:
        # Try to detect from Content-Type header
        try:
            print(f"Attempting to detect file type for: {url}")
            head_response = requests.head(url, timeout=10, allow_redirects=True)
            content_type = head_response.headers.get('Content-Type', '').lower()
            
            if 'wordprocessingml' in content_type or 'msword' in content_type or url_lower.endswith('.docx'):
                return extract_text_from_docx_url(url)
            elif 'text/plain' in content_type or url_lower.endswith('.txt'):
                return extract_text_from_txt_url(url)
            elif 'application/pdf' in content_type or 'pdf' in content_type or url_lower.endswith('.pdf'):
                return extract_text_from_pdf_url(url)
            else:
                print(f"Unsupported content type: {content_type} for URL: {url}")
                return None
        except Exception as e:
            print(f"Error detecting file type for {url}: {e}")
            # Fallback: try PDF first, then DOCX
            if url_lower.endswith('.pdf'):
                return extract_text_from_pdf_url(url)
            else:
                return extract_text_from_docx_url(url)


@router.post('/chat', response_model=ChatResponse)
def chat_with_materials(
    request: ChatRequest,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(oauth2.get_current_user)
):
    """
    Chat with Gemini AI using selected course materials as context.
    
    - **course_id**: ID of the course
    - **material_ids**: List of material IDs to include in context
    - **message**: User's message/question
    """
    if not gemini_client:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Gemini AI service is not available"
        )
    
    # Verify course exists
    course = db.query(models.Course).filter(models.Course.id == request.course_id).first()
    if not course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Course with id {request.course_id} not found"
        )
    
    # Get materials
    materials_text = []
    materials_used = []
    uploaded_files = []  # Track files uploaded to Gemini for cleanup
    
    for material_id in request.material_ids:
        try:
            material_obj = material.show(material_id, None, db)
            
            # Verify material belongs to the course
            if material_obj.course_id != request.course_id:
                print(f"Material {material_id} does not belong to course {request.course_id}")
                continue
            
            # Extract text from file if available
            if material_obj.file_link:
                print(f"Processing material {material_id}: {material_obj.title}")
                print(f"File link: {material_obj.file_link}")
                
                # Extract text from file
                extracted_text = extract_text_from_url(material_obj.file_link)
                
                if extracted_text and extracted_text.strip():
                    # Use Gemini Files API for better handling of large files
                    try:
                        # Upload extracted text to Gemini Files API
                        text_bytes = extracted_text.encode('utf-8')
                        text_io = io.BytesIO(text_bytes)
                        
                        uploaded_file = gemini_client.files.upload(
                            file=text_io,
                            config={
                                'mime_type': 'text/plain',
                                'display_name': f"{material_obj.title}_{material_id}.txt"
                            }
                        )
                        uploaded_files.append(uploaded_file)
                        
                        # Store reference for use in prompt
                        materials_text.append({
                            'type': 'file',
                            'file': uploaded_file,
                            'title': material_obj.title,
                            'material_id': material_id
                        })
                        materials_used.append(material_id)
                        print(f"✅ Successfully uploaded material {material_id} to Gemini Files API")
                    except Exception as e:
                        print(f"Error uploading to Gemini Files API, falling back to text: {e}")
                        # Fallback: use text directly
                        materials_text.append({
                            'type': 'text',
                            'content': f"Material: {material_obj.title}\n{extracted_text[:5000]}",  # Limit to avoid token limits
                            'material_id': material_id
                        })
                        materials_used.append(material_id)
                else:
                    print(f"⚠️ Could not extract text from file: {material_obj.file_link}")
            
            # Always include material metadata (title and description)
            if material_obj.description:
                metadata = f"Material: {material_obj.title}\nDescription: {material_obj.description}"
                # Check if we already have this material in our list
                material_exists = any(m.get('material_id') == material_id for m in materials_text if isinstance(m, dict))
                if not material_exists:
                    materials_text.append({
                        'type': 'text',
                        'content': metadata,
                        'material_id': material_id
                    })
                    if material_id not in materials_used:
                        materials_used.append(material_id)
        except Exception as e:
            print(f"Error processing material {material_id}: {e}")
            import traceback
            traceback.print_exc()
            continue
    
    if not materials_text:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No valid materials with extractable content found. Make sure materials have file links and files are accessible."
        )
    
    try:
        # Prepare contents for Gemini API
        # Mix of uploaded files and text content
        contents = []
        
        # Add uploaded files (from Gemini Files API) and text metadata
        for mat in materials_text:
            if mat['type'] == 'file':
                # File uploaded to Gemini Files API
                contents.append(mat['file'])
                # Add a text part describing the file
                contents.append(f"Material: {mat['title']}\n")
            elif mat['type'] == 'text':
                # Regular text content
                contents.append(mat['content'])
        
        # Add the user's question
        contents.append(f"\n\nUser Question: {request.message}\n\nPlease provide a helpful answer based on the course materials provided above.")
        
        print(f"Sending {len(contents)} content parts to Gemini (including {len(uploaded_files)} files)")
        
        # Generate response using Gemini
        response = gemini_client.models.generate_content(
            model='gemini-2.5-flash',
            contents=contents
        )
        
        result = ChatResponse(
            response=response.text,
            materials_used=materials_used
        )
        
        return result
    
    except Exception as e:
        print(f"Error communicating with Gemini AI: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error communicating with Gemini AI: {str(e)}"
        )
    
    finally:
        # Cleanup: Delete uploaded files from Gemini Files API
        for uploaded_file in uploaded_files:
            try:
                print(f"Cleaning up uploaded file: {uploaded_file.name}")
                gemini_client.files.delete(name=uploaded_file.name)
            except Exception as e:
                print(f"Error deleting file {uploaded_file.name}: {e}")

