from database import Base
from sqlalchemy import Column, Integer, String, Boolean, ForeignKey

class Course(Base):
    __tablename__ = 'courses'

    id = Column(Integer, primary_key=True, index=True)
    course_code = Column(String, unique=True, index=True)
    title = Column(String)
    instructors = Column(String)  # Storing as comma-separated string or JSON

class User(Base):
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    email = Column(String)
    password = Column(String)

class CourseMaterial(Base):
    __tablename__ = 'course_materials'

    id = Column(Integer, primary_key=True, index=True)
    course_id = Column(Integer, ForeignKey("courses.id"), index=True)
    title = Column(String)
    type = Column(Integer)  # Type of material (assignment, exam, lecture, etc.)
    description = Column(String)
    role = Column(Boolean)  # Role/permission flag
    score = Column(Integer)
    file_link = Column(String)  # Link to file (for future S3 integration)
    user_id = Column(Integer, ForeignKey("users.id"), index=True)  # User who created/submitted this material