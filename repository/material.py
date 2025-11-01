from sqlalchemy.orm import Session
from fastapi import Response, status, HTTPException

import schemas
import models

def all(db: Session):
    materials = db.query(models.CourseMaterial).all()
    return materials

def get_by_course(course_id: int, db: Session):
    """Get all materials for a specific course"""
    materials = db.query(models.CourseMaterial).filter(models.CourseMaterial.course_id == course_id).all()
    return materials

def show(id: int, response: Response, db: Session):
    material = db.query(models.CourseMaterial).filter(models.CourseMaterial.id == id).first()
    if not material:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Material with the id {id} is not available")
    return material

def create(request: schemas.CourseMaterial, user_id: int, db: Session):
    # Verify that the course exists
    course = db.query(models.Course).filter(models.Course.id == request.course_id).first()
    if not course:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Course with id {request.course_id} not found")
    
    new_material = models.CourseMaterial(
        course_id=request.course_id,
        title=request.title,
        type=request.type,
        description=request.description,
        role=request.role,
        score=request.score,
        file_link=request.file_link,
        user_id=user_id
    )
    db.add(new_material)
    db.commit()
    db.refresh(new_material)
    return new_material

def destroy(id: int, db: Session):
    material = db.query(models.CourseMaterial).filter(models.CourseMaterial.id == id)
    if not material.first():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Material with id {id} not found")
    material.delete(synchronize_session=False)
    db.commit()
    return {'done'}

def update(id: int, request: schemas.CourseMaterial, db: Session):
    material = db.query(models.CourseMaterial).filter(models.CourseMaterial.id == id).first()
    if not material:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Material with id {id} not found")
    
    # Verify that the course exists if course_id is being changed
    if request.course_id != material.course_id:
        course = db.query(models.Course).filter(models.Course.id == request.course_id).first()
        if not course:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Course with id {request.course_id} not found")
    
    material.course_id = request.course_id
    material.title = request.title
    material.type = request.type
    material.description = request.description
    material.role = request.role
    material.score = request.score
    material.file_link = request.file_link
    db.commit()
    db.refresh(material)
    return material

def update_file_link(id: int, file_link: str, db: Session):
    """Update only the file_link of a material"""
    material = db.query(models.CourseMaterial).filter(models.CourseMaterial.id == id).first()
    if not material:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Material with id {id} not found")
    
    material.file_link = file_link
    db.commit()
    db.refresh(material)
    return material

