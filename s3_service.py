import boto3
from botocore.exceptions import ClientError
import os
from typing import Optional
import uuid
from fastapi import UploadFile, HTTPException, status
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# AWS S3 Configuration - Load from environment variables
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
AWS_REGION = os.getenv("AWS_REGION", "us-east-1")
S3_BUCKET_NAME = os.getenv("S3_BUCKET_NAME")

# Initialize S3 client
s3_client = boto3.client(
    's3',
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
    region_name=AWS_REGION
)

def upload_file_to_s3(file: UploadFile, material_id: int, course_id: int) -> str:
    """
    Upload a file to S3 and return the public URL
    
    Args:
        file: FastAPI UploadFile object
        material_id: ID of the course material
        course_id: ID of the course
    
    Returns:
        str: Public URL of the uploaded file
    
    Raises:
        HTTPException: If AWS credentials are not configured or upload fails
    """
    # Validate AWS configuration
    if not AWS_ACCESS_KEY_ID or not AWS_SECRET_ACCESS_KEY or not S3_BUCKET_NAME:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="AWS S3 configuration is missing. Please set AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, and S3_BUCKET_NAME environment variables."
        )
    
    try:
        # Generate unique filename: course_id/material_id/original_filename-uuid.ext
        file_extension = os.path.splitext(file.filename)[1] if file.filename else ""
        unique_filename = f"{uuid.uuid4()}{file_extension}"
        s3_key = f"courses/{course_id}/materials/{material_id}/{unique_filename}"
        
        # Read file content
        file_content = file.file.read()
        
        # Upload to S3
        s3_client.put_object(
            Bucket=S3_BUCKET_NAME,
            Key=s3_key,
            Body=file_content,
            ContentType=file.content_type or "application/octet-stream"
        )
        
        # Generate public URL
        file_url = f"https://{S3_BUCKET_NAME}.s3.{AWS_REGION}.amazonaws.com/{s3_key}"
        
        return file_url
    
    except ClientError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upload file to S3: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unexpected error during file upload: {str(e)}"
        )

