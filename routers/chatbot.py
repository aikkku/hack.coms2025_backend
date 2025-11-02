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
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        
        docx_file = io.BytesIO(response.content)
        doc = Document(docx_file)
        full_text = []
        for paragraph in doc.paragraphs:
            full_text.append(paragraph.text)
        
        return '\n'.join(full_text)
    except Exception as e:
        print(f"Error extracting text from {url}: {e}")
        return None


def extract_text_from_url(url: str) -> Optional[str]:
    """Extract text from various file types. Currently supports DOCX."""
    if url.endswith('.docx'):
        return extract_text_from_docx_url(url)
    # Add support for other file types (PDF, TXT, etc.) here
    return None


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
    
    for material_id in request.material_ids:
        material_obj = material.show(material_id, None, db)
        
        # Verify material belongs to the course
        if material_obj.course_id != request.course_id:
            continue
        
        # Extract text from file if available
        if material_obj.file_link:
            text = extract_text_from_url(material_obj.file_link)
            if text:
                materials_text.append(f"Material: {material_obj.title}\n{text}")
                materials_used.append(material_id)
        
        # Also include material metadata
        if material_obj.description:
            metadata = f"Material: {material_obj.title}\nDescription: {material_obj.description}"
            if metadata not in materials_text:
                materials_text.append(metadata)
                if material_id not in materials_used:
                    materials_used.append(material_id)
    
    if not materials_text:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No valid materials with extractable content found"
        )
    
    # Prepare context for Gemini
    context = "\n\n".join(materials_text)
    prompt = f"""You are a helpful course assistant. Use the following course materials as context to answer the user's question.

Course Materials Context:
{context}

User Question: {request.message}

Please provide a helpful answer based on the materials provided."""
    
    try:
        # Upload materials as text to Gemini Files API if they're large
        # For now, we'll send directly as text in the prompt
        response = gemini_client.models.generate_content(
            model='gemini-2.5-flash',
            contents=[prompt]
        )
        
        return ChatResponse(
            response=response.text,
            materials_used=materials_used
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error communicating with Gemini AI: {str(e)}"
        )

