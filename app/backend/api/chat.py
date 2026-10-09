from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from datetime import datetime, timezone
from typing import AsyncGenerator

from app.backend.core.config import get_db
from app.backend.api.auth import get_current_active_user
from app.backend.database.initialized_db import User, ChatSession, ChatMessage, ChatConfig, OllamaModel
from app.backend.schemas.chat import (
    MessageCreate, MessageResponse, ChatHistoryResponse,
    ChatRequest, ModelInfo, ModelListResponse
)
from app.backend.services.ollama_service import ollama_service
from app.backend.services.rag_service import rag_service
from app.backend.services.rag_query_executor import rag_query_executor
from app.backend.services.clarification_service import clarification_service

router = APIRouter(prefix="/api/chat", tags=["Chat"])


def get_user_config(db: Session, user_id: int, model_name: str):
    """Get or create user chat configuration"""
    config = db.query(ChatConfig).filter(ChatConfig.user_id == user_id).first()
    
    if not config:
        # Get default model
        model = db.query(OllamaModel).filter(OllamaModel.model_name == model_name).first()
        if not model:
            model = db.query(OllamaModel).filter(OllamaModel.is_enabled == True).first()
        
        if model:
            config = ChatConfig(
                user_id=user_id,
                model_id=model.model_id,
                temperature=0.7,
                max_tokens=2000
            )
            db.add(config)
            db.commit()
            db.refresh(config)
    
    return config


@router.post("/send", response_model=MessageResponse)
async def send_message(
    message_data: MessageCreate,
    session_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Send a message and get AI response (non-streaming)"""
    
    # Verify session belongs to user
    session = db.query(ChatSession).filter(
        ChatSession.session_id == session_id,
        ChatSession.user_id == current_user.user_id,
        ChatSession.is_active == True
    ).first()
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found or inactive"
        )
    
    # Get user config
    model_name = message_data.model_name or "gemma2:2b"
    config = get_user_config(db, current_user.user_id, model_name)
    
    # Save user message
    user_message = ChatMessage(
        session_id=session_id,
        role="user",
        content=message_data.content,
        timestamp=datetime.now(timezone.utc)
    )
    db.add(user_message)
    db.commit()
    
    # Update session name with first user message (if it's still the default name)
    if session.session_name.startswith("Chat 20"):  # Default name pattern
        # Count user messages in this session
        user_message_count = db.query(ChatMessage).filter(
            ChatMessage.session_id == session_id,
            ChatMessage.role == "user"
        ).count()
        
        # If this is the first user message, use it as the session name
        if user_message_count == 1:
            # Truncate to 50 characters for display
            session_name = message_data.content[:50]
            if len(message_data.content) > 50:
                session_name += "..."
            session.session_name = session_name
            db.commit()
    
    # Get conversation history
    messages = db.query(ChatMessage).filter(
        ChatMessage.session_id == session_id
    ).order_by(ChatMessage.timestamp.asc()).all()
    
    # Build conversation for Ollama
    conversation = []
    for msg in messages[-10:]:  # Last 10 messages for context
        conversation.append({
            "role": msg.role,
            "content": msg.content
        })
    
    # Inject RAG context if enabled
    if message_data.enable_rag:
        try:
            # Get schema context
            schema_context = rag_service.get_schema_context(message_data.rag_table)
            
            # Inject as system message at the beginning
            rag_system_message = f"""You are a helpful assistant that answers questions about manufacturing data.

{schema_context}

CRITICAL RULES:
1. If a question is AMBIGUOUS or UNCLEAR, ask for clarification with options
2. When asking for clarification, use this EXACT format:
   [CLARIFICATION]
   {{
     "question": "What specifically do you need?",
     "options": ["Option 1", "Option 2", "Option 3"]
   }}
   [/CLARIFICATION]
3. If question is clear, write SQL query in [QUERY] tags (users won't see this - it executes automatically)
4. NEVER show SQL code blocks to users - they only see the results

WHEN TO ASK FOR CLARIFICATION:
- User says "November" but doesn't specify origin_month vs current_month
- User says "devices" without specifying outcome status
- User asks for "best" without defining criteria
- Column names are ambiguous (e.g., "yield" could be p1_yield, p2_yield, or p3_yield)
- Time period is unclear (this month? next month? specific month?)

CLARIFICATION FORMAT EXAMPLES:

Example 1 - Ambiguous month:
User: "Show me devices for November"
You: [CLARIFICATION]
{{
  "question": "Which November data do you want to see?",
  "options": ["Originally planned for November (origin_month)", "Currently scheduled for November (current_month)", "Both - show me all November devices"]
}}
[/CLARIFICATION]

Example 2 - Ambiguous outcome:
User: "How many devices for November?"
You: [CLARIFICATION]
{{
  "question": "Which devices should I count?",
  "options": ["All devices", "Only PLACED devices", "Only DE_COMMIT devices", "Exclude DE_COMMIT devices"]
}}
[/CLARIFICATION]

Example 3 - Unclear yield:
User: "Show low yield devices"
You: [CLARIFICATION]
{{
  "question": "Which yield phase and what threshold?",
  "options": ["Phase 1 yield below 95%", "Phase 2 yield below 95%", "Phase 3 yield below 95%", "Any phase below 95%"]
}}
[/CLARIFICATION]

IF QUESTION IS CLEAR:
Write a brief intro, then SQL in [QUERY] tags:

Here's the data you requested:

[QUERY]
SELECT COUNT(*) as count FROM conv_test_pivot_queue_sim WHERE current_month = '202611'
[/QUERY]

DO NOT use ```sql code blocks. DO NOT explain the SQL. Users only see the results.

QUERY SYNTAX (when question is clear):
- **SECURITY: Only SELECT queries are allowed. No INSERT, UPDATE, DELETE, DROP, etc.**
- For "current" or "actual" month → Use current_month = 'YYYYMM'
- For "originally planned" → Use origin_month = 'YYYYMM'
- **DEFAULT: Use current_month unless specified**
- Use SUBSTR(current_month, 1, 4) for year filtering
- Use FETCH FIRST n ROWS ONLY to limit results
- outcome values: 'PLACED', 'DE_COMMIT', 'MOVED', 'PUSHED_BACK', 'PULLED_IN'
- NO SEMICOLONS at the end of queries
- Only read data, never modify or delete

EXAMPLES OF CLEAR QUESTIONS (no clarification needed):
- "How many devices currently scheduled for November 2026?" → current_month = '202611'
- "Show DE_COMMIT devices" → WHERE outcome = 'DE_COMMIT'
- "What's the average P1 yield?" → SELECT AVG(p1_yield)
"""
            
            # Insert system message at beginning of conversation
            conversation.insert(0, {
                "role": "system",
                "content": rag_system_message
            })
        except Exception as e:
            print(f"RAG context injection error: {e}")
            # Continue without RAG if there's an error
    
    # Get AI response
    system_prompt = config.system_prompt if config else None
    
    try:
        ai_response = await ollama_service.chat(
            model=model_name,
            messages=conversation,
            temperature=config.temperature if config else 0.7,
            max_tokens=config.max_tokens if config else 2000
        )
        
        # Check if AI is asking for clarification
        clarification_data = None
        if message_data.enable_rag:
            clarification_data = clarification_service.detect_clarification(ai_response)
            
            if clarification_data:
                # AI is asking for clarification - clean up response
                ai_response = clarification_service.remove_clarification_tags(ai_response)
                ai_response = clarification_service.format_clarification_response(clarification_data)
            else:
                # No clarification needed - execute query
                ai_response = rag_query_executor.enhance_response_with_results(ai_response)
            
    except Exception as e:
        ai_response = f"Error: {str(e)}"
        clarification_data = None
    
    # Save AI response
    assistant_message = ChatMessage(
        session_id=session_id,
        role="assistant",
        content=ai_response,
        timestamp=datetime.now(timezone.utc)
    )
    db.add(assistant_message)
    
    # Update session timestamp
    session.updated_at = datetime.utcnow()
    
    db.commit()
    db.refresh(assistant_message)
    
    # Build response with clarification if present
    response_data = {
        "message_id": assistant_message.message_id,
        "session_id": assistant_message.session_id,
        "role": assistant_message.role,
        "content": assistant_message.content,
        "timestamp": assistant_message.timestamp,
        "token_count": assistant_message.token_count
    }
    
    if clarification_data:
        response_data["clarification"] = clarification_data
    
    return response_data


@router.post("/send/stream")
async def send_message_stream(
    message_data: MessageCreate,
    session_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Send a message and get AI response (streaming)"""
    
    # Verify session
    session = db.query(ChatSession).filter(
        ChatSession.session_id == session_id,
        ChatSession.user_id == current_user.user_id,
        ChatSession.is_active == True
    ).first()
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found or inactive"
        )
    
    # Get user config
    model_name = message_data.model_name or "gemma2:2b"
    config = get_user_config(db, current_user.user_id, model_name)
    
    # Save user message
    user_message = ChatMessage(
        session_id=session_id,
        role="user",
        content=message_data.content,
        timestamp=datetime.now(timezone.utc)
    )
    db.add(user_message)
    db.commit()
    
    # Update session name with first user message (if it's still the default name)
    if session.session_name.startswith("Chat 20"):  # Default name pattern
        # Count user messages in this session
        user_message_count = db.query(ChatMessage).filter(
            ChatMessage.session_id == session_id,
            ChatMessage.role == "user"
        ).count()
        
        # If this is the first user message, use it as the session name
        if user_message_count == 1:
            # Truncate to 50 characters for display
            session_name = message_data.content[:50]
            if len(message_data.content) > 50:
                session_name += "..."
            session.session_name = session_name
            db.commit()
    
    # Get conversation history
    messages = db.query(ChatMessage).filter(
        ChatMessage.session_id == session_id
    ).order_by(ChatMessage.timestamp.asc()).all()
    
    conversation = []
    for msg in messages[-10:]:
        conversation.append({
            "role": msg.role,
            "content": msg.content
        })
    
    # Inject RAG context if enabled
    if message_data.enable_rag:
        try:
            schema_context = rag_service.get_schema_context(message_data.rag_table)
            
            rag_system_message = f"""You are a database assistant with DIRECT ACCESS to manufacturing data.

{schema_context}

CRITICAL INSTRUCTIONS:
1. When users ask data questions, write SQL queries to get the answer
2. Put your SQL query in a code block: ```sql ... ```
3. After the SQL, briefly explain what you're checking
4. Do NOT just describe what query to run - ACTUALLY WRITE THE SQL
5. The system will automatically execute your SQL and show results

Examples:

User: "How many devices have outcome DE_COMMIT?"
You: "Let me check the database:
```sql
SELECT COUNT(*) as count FROM conv_test_pivot_queue_sim WHERE outcome = 'DE_COMMIT'
```
This counts all devices with DE_COMMIT outcome."

User: "What's the average P1 yield?"
You: "Let me get that for you:
```sql
SELECT AVG(p1_yield) as avg_yield FROM conv_test_pivot_queue_sim
```
This calculates the average P1 yield across all devices."

REMEMBER: Always include executable SQL in ```sql blocks. The system will run it automatically!
"""
            
            conversation.insert(0, {
                "role": "system",
                "content": rag_system_message
            })
        except Exception as e:
            print(f"RAG context injection error: {e}")
    
    async def stream_response() -> AsyncGenerator[str, None]:
        """Stream AI response"""
        full_response = ""
        
        try:
            async for chunk in ollama_service.chat_stream(
                model=model_name,
                messages=conversation,
                temperature=config.temperature if config else 0.7,
                max_tokens=config.max_tokens if config else 2000
            ):
                full_response += chunk
                yield chunk
        except Exception as e:
            error_msg = f"Error: {str(e)}"
            full_response = error_msg
            yield error_msg
        
        # If RAG is enabled, detect and execute queries, then stream the results
        if message_data.enable_rag and full_response:
            sql, results = rag_query_executor.execute_query_from_text(full_response)
            if sql and results is not None:
                # Stream the query results
                formatted_results = rag_query_executor.format_query_results(results)
                yield f"\n\n{formatted_results}"
                full_response += f"\n\n{formatted_results}"
        
        # Save complete response to database
        assistant_message = ChatMessage(
            session_id=session_id,
            role="assistant",
            content=full_response,
            timestamp=datetime.now(timezone.utc)
        )
        db.add(assistant_message)
        
        # Update session
        session.updated_at = datetime.utcnow()
        db.commit()
    
    return StreamingResponse(stream_response(), media_type="text/plain")


@router.get("/history/{session_id}", response_model=ChatHistoryResponse)
async def get_chat_history(
    session_id: int,
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get chat history for a session"""
    
    # Verify session
    session = db.query(ChatSession).filter(
        ChatSession.session_id == session_id,
        ChatSession.user_id == current_user.user_id
    ).first()
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )
    
    # Get messages
    query = db.query(ChatMessage).filter(ChatMessage.session_id == session_id)
    total = query.count()
    
    messages = query.order_by(ChatMessage.timestamp.asc()).offset(skip).limit(limit).all()
    
    return ChatHistoryResponse(
        session_id=session_id,
        messages=messages,
        total=total
    )


@router.delete("/message/{message_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_message(
    message_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Delete a specific message"""
    
    # Get message and verify ownership
    message = db.query(ChatMessage).join(ChatSession).filter(
        ChatMessage.message_id == message_id,
        ChatSession.user_id == current_user.user_id
    ).first()
    
    if not message:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Message not found"
        )
    
    db.delete(message)
    db.commit()
    
    return None


@router.get("/models", response_model=ModelListResponse)
async def list_available_models(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get list of available Ollama models from database"""
    
    models = db.query(OllamaModel).filter(
        OllamaModel.is_enabled == True,
        OllamaModel.is_available == True
    ).all()
    
    model_list = [
        ModelInfo(
            name=m.model_name,
            size=int(m.size_gb * 1024 * 1024 * 1024) if m.size_gb else None,
            modified_at=m.added_at.isoformat() if m.added_at else None
        )
        for m in models
    ]
    
    return ModelListResponse(models=model_list, total=len(model_list))


@router.get("/models/ollama")
async def list_ollama_models(current_user: User = Depends(get_current_active_user)):
    """Get list of models directly from Ollama"""
    
    models = await ollama_service.list_models()
    
    return {
        "models": models,
        "total": len(models)
    }


@router.get("/ollama/status")
async def check_ollama_status(current_user: User = Depends(get_current_active_user)):
    """Check if Ollama is running"""
    
    is_connected = await ollama_service.check_connection()
    
    return {
        "connected": is_connected,
        "url": ollama_service.base_url
    }

