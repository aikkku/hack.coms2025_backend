from fastapi import APIRouter, Depends, status, Response, Query
from typing import List, Optional
from sqlalchemy.orm import Session

import schemas
import database
import oauth2
from repository import course

router = APIRouter(
    tags=['Courses'],
    prefix="/course"
)


#POST
@router.post('/', status_code=status.HTTP_201_CREATED, response_model=schemas.ShowCourse)
def create(request:schemas.Course, db:Session = Depends(database.get_db), current_user: schemas.User = Depends(oauth2.get_current_user)):
    return course.create(request, db)

#GET
@router.get('/', response_model=List[schemas.ShowCourse])
def get_courses(
    search: Optional[str] = Query(None, description="Search courses by code, title, or instructors"),
    db: Session = Depends(database.get_db), 
    current_user: schemas.User = Depends(oauth2.get_current_user)
):
    """
    Get all courses or search courses.
    
    - If 'search' query parameter is provided: returns courses matching the search term
    - If no 'search' parameter: returns all courses
    """
    if search:
        return course.search(search, db)
    return course.all(db)

#SEARCH (alternative endpoint)
@router.get('/search', response_model=List[schemas.ShowCourse])
def search_courses(
    q: str = Query(..., description="Search query for course code, title, or instructors"),
    db: Session = Depends(database.get_db),
    current_user: schemas.User = Depends(oauth2.get_current_user)
):
    """
    Search courses by course code, title, or instructors.
    Returns all courses that match the search query in any of these fields.
    """
    return course.search(q, db)

@router.get('/{id}', status_code=200, response_model=schemas.ShowCourse)
def show(id:int, response: Response, db: Session = Depends(database.get_db), current_user: schemas.User = Depends(oauth2.get_current_user)):
    return course.show(id, response, db)

#DELETE
@router.delete('/{id}', status_code=status.HTTP_204_NO_CONTENT)
def destroy(id:int, db: Session = Depends(database.get_db), current_user: schemas.User = Depends(oauth2.get_current_user)):
    return course.destroy(id, db)

#PUT
@router.put('/{id}', status_code=status.HTTP_202_ACCEPTED, response_model=schemas.ShowCourse)
def update(id:int, request: schemas.Course, db:Session = Depends(database.get_db), current_user: schemas.User = Depends(oauth2.get_current_user)):
    return course.update(id, request, db)


