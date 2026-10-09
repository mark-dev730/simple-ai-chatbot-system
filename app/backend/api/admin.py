from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.backend.core.config import get_db
from app.backend.api.auth import get_current_active_user
from app.backend.database.initialized_db import User, ChatSession, ChatMessage, OllamaModel, UserLog
from app.backend.services import auth_service

router = APIRouter(prefix="/api", tags=["Admin"])


def require_admin(current_user: User = Depends(get_current_active_user)) -> User:
    """Ensure user has admin privileges"""
    if current_user.access_level < 2:  # 2 = Admin
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return current_user


@router.get("/users/count")
async def get_users_count(
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Get total user count (admin only)"""
    total = db.query(func.count(User.user_id)).scalar()
    active = db.query(func.count(User.user_id)).filter(User.is_active == True).scalar()
    
    return {
        "total": total,
        "active": active,
        "inactive": total - active
    }


@router.get("/users/list")
async def list_all_users(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Get list of all users (admin only)"""
    users = db.query(User).offset(skip).limit(limit).all()
    total = db.query(func.count(User.user_id)).scalar()
    
    # last_login derived from audit log (User has no last_login column)
    last_logins = dict(
        db.query(UserLog.user_id, func.max(UserLog.timestamp))
        .filter(UserLog.action == "login")
        .group_by(UserLog.user_id)
        .all()
    )
    
    return {
        "users": [
            {
                "user_id": u.user_id,
                "username": u.username,
                "email": u.email,
                "access_level": u.access_level,
                "is_active": u.is_active,
                "created_at": u.created_at.isoformat() if u.created_at else None,
                "last_login": last_logins[u.user_id].isoformat() if last_logins.get(u.user_id) else None,
            }
            for u in users
        ],
        "total": total
    }


@router.get("/stats")
async def get_system_stats(
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Get system statistics (admin only)"""
    
    users_total = db.query(func.count(User.user_id)).scalar()
    sessions_total = db.query(func.count(ChatSession.session_id)).scalar()
    messages_total = db.query(func.count(ChatMessage.message_id)).scalar()
    models_total = db.query(func.count(OllamaModel.model_id)).filter(
        OllamaModel.is_enabled == True
    ).scalar()
    
    return {
        "users": users_total,
        "sessions": sessions_total,
        "messages": messages_total,
        "models": models_total
    }


@router.patch("/users/{user_id}/toggle")
async def toggle_user_status(
    user_id: int,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Toggle user active status (admin only)"""
    
    user = db.query(User).filter(User.user_id == user_id).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Prevent admin from deactivating themselves
    if user.user_id == current_user.user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot deactivate your own account"
        )
    
    user.is_active = not user.is_active
    db.commit()
    db.refresh(user)
    auth_service.log_activity(
        db, current_user.user_id, "admin_toggle_user",
        f"user_id={user.user_id} is_active={user.is_active}"
    )
    
    return {
        "user_id": user.user_id,
        "username": user.username,
        "is_active": user.is_active
    }


@router.patch("/users/{user_id}/access")
async def update_user_access(
    user_id: int,
    access_level: int,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Update user access level (admin only)"""
    
    if access_level not in [0, 1, 2]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid access level. Must be 0 (User), 1 (Moderator), or 2 (Admin)"
        )
    
    user = db.query(User).filter(User.user_id == user_id).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Prevent admin from changing their own access level
    if user.user_id == current_user.user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot change your own access level"
        )
    
    user.access_level = access_level
    db.commit()
    db.refresh(user)
    auth_service.log_activity(
        db, current_user.user_id, "admin_change_access",
        f"user_id={user.user_id} access_level={user.access_level}"
    )
    
    return {
        "user_id": user.user_id,
        "username": user.username,
        "access_level": user.access_level
    }

