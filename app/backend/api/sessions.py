from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime

from app.backend.core.config import get_db
from app.backend.api.auth import get_current_active_user
from app.backend.database.initialized_db import User, ChatSession, ChatMessage
from app.backend.services import auth_service
from app.backend.schemas.session import SessionCreate, SessionUpdate, SessionResponse, SessionListResponse

router = APIRouter(prefix="/api/sessions", tags=["Chat Sessions"])


@router.post("", response_model=SessionResponse, status_code=status.HTTP_201_CREATED)
async def create_session(
    session_data: SessionCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Create a new chat session"""
    
    session_name = session_data.session_name
    if not session_name:
        session_name = f"Chat {datetime.now().strftime('%Y-%m-%d %H:%M')}"
    
    new_session = ChatSession(
        user_id=current_user.user_id,
        session_name=session_name,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
        is_active=True
    )
    
    db.add(new_session)
    db.commit()
    db.refresh(new_session)
    auth_service.log_activity(db, current_user.user_id, "chat_created", f"session_id={new_session.session_id}")
    
    # Add message count
    response = SessionResponse.from_orm(new_session)
    response.message_count = 0
    
    return response


@router.get("", response_model=SessionListResponse)
async def list_sessions(
    skip: int = 0,
    limit: int = 50,
    active_only: bool = True,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get list of user's chat sessions"""
    
    query = db.query(ChatSession).filter(ChatSession.user_id == current_user.user_id)
    
    if active_only:
        query = query.filter(ChatSession.is_active == True)
    
    # Get total count
    total = query.count()
    
    # Get sessions with pagination
    sessions = query.order_by(ChatSession.updated_at.desc()).offset(skip).limit(limit).all()
    
    # Add message counts
    session_responses = []
    for session in sessions:
        msg_count = db.query(func.count(ChatMessage.message_id)).filter(
            ChatMessage.session_id == session.session_id
        ).scalar()
        
        response = SessionResponse.from_orm(session)
        response.message_count = msg_count
        session_responses.append(response)
    
    return SessionListResponse(sessions=session_responses, total=total)


@router.get("/{session_id}", response_model=SessionResponse)
async def get_session(
    session_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get a specific chat session"""
    
    session = db.query(ChatSession).filter(
        ChatSession.session_id == session_id,
        ChatSession.user_id == current_user.user_id
    ).first()
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )
    
    # Add message count
    msg_count = db.query(func.count(ChatMessage.message_id)).filter(
        ChatMessage.session_id == session.session_id
    ).scalar()
    
    response = SessionResponse.from_orm(session)
    response.message_count = msg_count
    
    return response


@router.put("/{session_id}", response_model=SessionResponse)
async def update_session(
    session_id: int,
    session_data: SessionUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Update a chat session"""
    
    session = db.query(ChatSession).filter(
        ChatSession.session_id == session_id,
        ChatSession.user_id == current_user.user_id
    ).first()
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )
    
    # Update fields
    if session_data.session_name is not None:
        session.session_name = session_data.session_name
    
    if session_data.is_active is not None:
        session.is_active = session_data.is_active
    
    session.updated_at = datetime.utcnow()
    
    db.commit()
    db.refresh(session)
    
    # Add message count
    msg_count = db.query(func.count(ChatMessage.message_id)).filter(
        ChatMessage.session_id == session.session_id
    ).scalar()
    
    response = SessionResponse.from_orm(session)
    response.message_count = msg_count
    
    return response


@router.delete("/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_session(
    session_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Delete a chat session (soft delete by setting is_active=False)"""
    
    session = db.query(ChatSession).filter(
        ChatSession.session_id == session_id,
        ChatSession.user_id == current_user.user_id
    ).first()
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )
    
    # Soft delete
    session.is_active = False
    session.updated_at = datetime.utcnow()
    
    db.commit()
    
    return None


@router.delete("/{session_id}/permanent", status_code=status.HTTP_204_NO_CONTENT)
async def delete_session_permanent(
    session_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Permanently delete a chat session and all its messages"""
    
    session = db.query(ChatSession).filter(
        ChatSession.session_id == session_id,
        ChatSession.user_id == current_user.user_id
    ).first()
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )
    
    # Delete associated messages first (cascade should handle this, but being explicit)
    db.query(ChatMessage).filter(ChatMessage.session_id == session_id).delete()
    
    # Delete session
    db.delete(session)
    db.commit()
    
    return None

