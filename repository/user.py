from fastapi import Depends, status, HTTPException
from sqlalchemy.orm import Session

import schemas
import database
import models
import hashing

def create_user(request: schemas.User, db:Session):
    new_user = models.User(name = request.name, email = request.email, password = hashing.Hash.bcrypt(request.password))
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

def get_user(id: int, db: Session):
    user = db.query(models.User).filter(models.User.id == id).first()

    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"User with id {id} not found")
    
    return user

def add_karma(user_id: int, points: int, db: Session):
    """Add karma points to a user"""
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"User with id {user_id} not found")
    
    # Get karma value, handling case where column might not exist
    try:
        current_karma = getattr(user, 'karma', None)
        if current_karma is None:
            current_karma = 0
            user.karma = 0
        
        user.karma = current_karma + points
        db.commit()
        db.refresh(user)
        return user
    except Exception as e:
        # If karma column doesn't exist, rollback and log error
        db.rollback()
        print(f"Error updating karma (column might not exist): {e}")
        # Re-run migrations and try again
        from migrations import add_karma_column_if_not_exists
        add_karma_column_if_not_exists()
        # Retry
        user = db.query(models.User).filter(models.User.id == user_id).first()
        user.karma = (getattr(user, 'karma', 0) or 0) + points
        db.commit()
        db.refresh(user)
        return user