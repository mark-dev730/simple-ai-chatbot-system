import sys
from pathlib import Path

# Add parent directory to path to import config
sys.path.append(str(Path(__file__).parent.parent.parent))

from app.backend.core.config import engine, Base
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Boolean, Float, Sequence
from sqlalchemy.orm import relationship
from datetime import datetime

# User model
class User(Base):
    __tablename__ = 'users'

    user_id = Column(Integer, Sequence('users_seq'), primary_key=True)
    username = Column(String(50), unique=True, nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    access_level = Column(Integer, default=0)  # 0=user, 1=moderator, 2=admin
    created_at = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)

    # Relationships
    sessions = relationship("ChatSession", back_populates="user")
    logs = relationship("UserLog", back_populates="user")
    configs = relationship("ChatConfig", back_populates="user")

# Ollama Models table (NEW)
class OllamaModel(Base):
    __tablename__ = 'ollama_models'

    model_id = Column(Integer, Sequence('ollama_models_seq'), primary_key=True)
    model_name = Column(String(100), unique=True, nullable=False)  # e.g., 'llama2', 'mistral'
    display_name = Column(String(100), nullable=False)  # e.g., 'Llama 2', 'Mistral 7B'
    description = Column(Text)
    size_gb = Column(Float)  # Model size in GB
    is_available = Column(Boolean, default=True)  # Is model pulled/available
    is_enabled = Column(Boolean, default=True)  # Admin can disable models
    added_at = Column(DateTime, default=datetime.utcnow)
    last_used = Column(DateTime)

    # Relationships
    configs = relationship("ChatConfig", back_populates="model")

# Chat session model
class ChatSession(Base):
    __tablename__ = 'chat_sessions'

    session_id = Column(Integer, Sequence('chat_sessions_seq'), primary_key=True)
    user_id = Column(Integer, ForeignKey('users.user_id'), nullable=False)
    session_name = Column(String(100))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = Column(Boolean, default=True)

    # Relationships
    user = relationship("User", back_populates="sessions")
    messages = relationship("ChatMessage", back_populates="session", cascade="all, delete-orphan")

# Chat message model
class ChatMessage(Base):
    __tablename__ = 'chat_messages'

    message_id = Column(Integer, Sequence('chat_messages_seq'), primary_key=True)
    session_id = Column(Integer, ForeignKey('chat_sessions.session_id'), nullable=False)
    role = Column(String(20), nullable=False)  # 'user' or 'assistant'
    content = Column(Text, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
    token_count = Column(Integer)

    # Relationships
    session = relationship("ChatSession", back_populates="messages")

# Chat configuration model (UPDATED)
class ChatConfig(Base):
    __tablename__ = 'chat_config'

    config_id = Column(Integer, Sequence('chat_config_seq'), primary_key=True)
    user_id = Column(Integer, ForeignKey('users.user_id'), nullable=False)
    model_id = Column(Integer, ForeignKey('ollama_models.model_id'), nullable=False)  # NEW: FK to ollama_models
    temperature = Column(Float, default=0.7)  # Changed to Float (0.0-1.0)
    max_tokens = Column(Integer, default=2000)
    system_prompt = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="configs")
    model = relationship("OllamaModel", back_populates="configs")

# User logs model (for activity tracking)
class UserLog(Base):
    __tablename__ = 'user_logs'

    log_id = Column(Integer, Sequence('user_logs_seq'), primary_key=True)
    user_id = Column(Integer, ForeignKey('users.user_id'), nullable=False)
    action = Column(String(100), nullable=False)  # 'login', 'logout', 'chat_created', 'model_switched', etc.
    details = Column(Text)
    ip_address = Column(String(45))  # IPv4 or IPv6
    timestamp = Column(DateTime, default=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="logs")

def seed_default_models():
    """Add default Ollama models"""
    from sqlalchemy.orm import Session

    default_models = [
        {"model_name": "llama2", "display_name": "Llama 2", "description": "Meta's Llama 2 model", "size_gb": 3.8},
        {"model_name": "mistral", "display_name": "Mistral 7B", "description": "Mistral AI 7B model", "size_gb": 4.1},
        {"model_name": "codellama", "display_name": "Code Llama", "description": "Code-focused Llama model", "size_gb": 3.8},
        {"model_name": "phi", "display_name": "Phi-2", "description": "Microsoft's small language model", "size_gb": 1.7},
    ]

    with Session(engine) as session:
        for model_data in default_models:
            existing = session.query(OllamaModel).filter_by(model_name=model_data["model_name"]).first()
            if not existing:
                model = OllamaModel(**model_data)
                session.add(model)
        session.commit()
    print("✓ Default Ollama models seeded!")

def initialize_database():
    """Create all tables in the database"""
    try:
        print("Creating database tables...")
        Base.metadata.create_all(bind=engine)
        print("✓ All tables created successfully!")

        # Print created tables
        print("\nCreated tables:")
        for table in Base.metadata.sorted_tables:
            print(f"  - {table.name}")

        # Seed default models
        print("\nSeeding default Ollama models...")
        seed_default_models()

        return True
    except Exception as e:
        print(f"✗ Error creating tables: {e}")
        return False

def drop_all_tables():
    """Drop all tables (use with caution!)"""
    try:
        print("WARNING: Dropping all tables...")
        Base.metadata.drop_all(bind=engine)
        print("✓ All tables dropped successfully!")
        return True
    except Exception as e:
        print(f"✗ Error dropping tables: {e}")
        return False

if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "--drop":
        drop_all_tables()

    initialize_database()

