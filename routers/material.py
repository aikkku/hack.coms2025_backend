from fastapi import APIRouter, Depends, status, Response, UploadFile, File
from typing import List
from sqlalchemy.orm import Session

import schemas
import database
import oauth2
import models
from repository import material
from s3_service import upload_file_to_s3

router = APIRouter(
    tags=['Course Materials'],
    prefix="/material"
)

#POST
@router.post('/', status_code=status.HTTP_201_CREATED, response_model=schemas.ShowCourseMaterial)
def create(
    request: schemas.CourseMaterial, 
    db: Session = Depends(database.get_db), 
    current_user: models.User = Depends(oauth2.get_current_user)
):
    """Create a new course material. user_id is automatically set from the current authenticated user."""
    return material.create(request, current_user.id, db)

#GET
@router.get('/', response_model=List[schemas.ShowCourseMaterial])
def all(db: Session = Depends(database.get_db), current_user: models.User = Depends(oauth2.get_current_user)):
    """Get all course materials"""
    return material.all(db)

@router.get('/course/{course_id}', response_model=List[schemas.ShowCourseMaterial])
def get_by_course(
    course_id: int,
    db: Session = Depends(database.get_db), 
    current_user: models.User = Depends(oauth2.get_current_user)
):
    """Get all materials for a specific course"""
    return material.get_by_course(course_id, db)

@router.get('/{id}', status_code=200, response_model=schemas.ShowCourseMaterial)
def show(
    id: int, 
    response: Response, 
    db: Session = Depends(database.get_db), 
    current_user: models.User = Depends(oauth2.get_current_user)
):
    """Get a specific course material by ID"""
    return material.show(id, response, db)

#DELETE
@router.delete('/{id}', status_code=status.HTTP_204_NO_CONTENT)
def destroy(
    id: int, 
    db: Session = Depends(database.get_db), 
    current_user: models.User = Depends(oauth2.get_current_user)
):
    """Delete a course material"""
    return material.destroy(id, db)

#PUT
@router.put('/{id}', status_code=status.HTTP_202_ACCEPTED, response_model=schemas.ShowCourseMaterial)
def update(
    id: int, 
    request: schemas.CourseMaterial, 
    db: Session = Depends(database.get_db), 
    current_user: models.User = Depends(oauth2.get_current_user)
):
    """Update a course material"""
    return material.update(id, request, db)

#FILE UPLOAD
@router.post('/{material_id}/upload', status_code=status.HTTP_200_OK, response_model=schemas.ShowCourseMaterial)
def upload_file(
    material_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(oauth2.get_current_user)
):
    """
    Upload a file to AWS S3 and update the material's file_link.
    
    - **material_id**: ID of the course material to update
    - **file**: The file to upload (multipart/form-data)
    
    Returns the updated material with the S3 file URL.
    """
    # Get the material to verify it exists and get course_id
    material_obj = material.show(material_id, Response(), db)
    
    # Upload file to S3
    file_url = upload_file_to_s3(file, material_id, material_obj.course_id)
    
    # Update the material's file_link
    updated_material = material.update_file_link(material_id, file_url, db)
    
    return updated_material

