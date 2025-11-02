from pydantic import BaseModel
from typing import List, Optional

class User(BaseModel):
    name:str
    email:str
    password:str

class CourseBase(BaseModel):
    course_code: str
    title: str
    instructors: str

class Course(CourseBase):
    class Config():
        from_attributes = True

class ShowCourse(BaseModel):
    id: int
    course_code: str
    title: str
    instructors: str

    class Config():
        from_attributes = True

class ShowUser(BaseModel):
    id: int
    name: str
    email: str
    karma: int = 0
    class Config():
        from_attributes = True



class Login(BaseModel):
    username: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    email: str | None = None

class CourseMaterialBase(BaseModel):
    course_id: int
    title: str
    type: int
    description: str
    role: bool
    score: int
    file_link: str = ""  # Optional, defaults to empty string

class CourseMaterial(CourseMaterialBase):
    class Config():
        from_attributes = True

class ShowCourseMaterial(BaseModel):
    id: int
    course_id: int
    title: str
    type: int
    description: str
    role: bool
    score: int
    file_link: str
    user_id: int

    class Config():
        from_attributes = True
