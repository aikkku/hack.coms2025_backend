from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

import schemas
import database
import oauth2
import models
from repository import user

router = APIRouter(
    tags=['Users'],
    prefix="/user"
)

@router.post('/', response_model=schemas.ShowUser)
def create_user(request: schemas.User, db:Session = Depends(database.get_db)):
    return user.create_user(request, db)

@router.get('/{id}', response_model=schemas.ShowUser)
def get_user(id: int, db: Session = Depends(database.get_db)):
    return user.get_user(id, db)

@router.get('/me/current', response_model=schemas.ShowUser)
def get_current_user_info(
    current_user: models.User = Depends(oauth2.get_current_user),
    db: Session = Depends(database.get_db)
):
    """Get current authenticated user information including karma"""
    try:
        # Get karma, defaulting to 0 if column doesn't exist or is None
        karma_value = getattr(current_user, 'karma', None)
        if karma_value is None:
            karma_value = 0
            # Try to initialize karma for existing users
            try:
                current_user.karma = 0
                db.commit()
                db.refresh(current_user)
            except Exception:
                # If karma column doesn't exist, just return 0
                db.rollback()
                pass
        
        return {
            "id": current_user.id,
            "name": current_user.name,
            "email": current_user.email,
            "karma": karma_value
        }
    except Exception as e:
        # Fallback if anything goes wrong
        return {
            "id": current_user.id,
            "name": current_user.name,
            "email": current_user.email,
            "karma": 0
        }
