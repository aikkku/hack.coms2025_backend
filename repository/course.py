from sqlalchemy.orm import Session
from fastapi import Response, status, HTTPException
from sqlalchemy import or_

import schemas
import models

def all(db: Session):
    courses = db.query(models.Course).all()
    return courses

def search(query: str, db: Session):
    """
    Search courses by course_code, title, or instructors.
    Returns courses that match any of these fields (case-insensitive partial match).
    """
    search_term = f"%{query}%"
    courses = db.query(models.Course).filter(
        or_(
            models.Course.course_code.ilike(search_term),
            models.Course.title.ilike(search_term),
            models.Course.instructors.ilike(search_term)
        )
    ).all()
    return courses 

def show(id:int, response: Response, db: Session):
    course = db.query(models.Course).filter(models.Course.id == id).first()
    if not course:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Course with the id {id} is not available")
    return course 

def create(request:schemas.Course, db:Session):
    # Check if course_code already exists
    existing_course = db.query(models.Course).filter(models.Course.course_code == request.course_code).first()
    if existing_course:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Course with code {request.course_code} already exists")
    
    new_course = models.Course(
        course_code=request.course_code,
        title=request.title,
        instructors=request.instructors
    )
    db.add(new_course)
    db.commit()
    db.refresh(new_course)
    return new_course

def destroy(id:int, db: Session):
    course = db.query(models.Course).filter(models.Course.id == id)
    if not course.first():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Course with id {id} not found")
    course.delete(synchronize_session=False)
    db.commit()
    return {'done'}

def update(id:int, request: schemas.Course, db:Session):
    course = db.query(models.Course).filter(models.Course.id == id).first()
    if not course:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Course with id {id} not found")
    
    # Check if course_code is being changed and if it conflicts with another course
    if request.course_code != course.course_code:
        existing_course = db.query(models.Course).filter(models.Course.course_code == request.course_code).first()
        if existing_course:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Course with code {request.course_code} already exists")
    
    course.course_code = request.course_code
    course.title = request.title
    course.instructors = request.instructors
    db.commit()
    db.refresh(course)
    return course

# def 


