import sys
from pathlib import Path

# Add project root to path (two levels up: scripts -> app -> root)
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from app.backend.core.config import SessionLocal
from app.backend.database.initialized_db import OllamaModel
from app.backend.services.ollama_service import ollama_service
import asyncio
from datetime import datetime

async def sync_models():
    """Sync Ollama models with database"""
    session = SessionLocal()
    try:
        # Get models from Ollama
        models = await ollama_service.list_models()
        
        print(f"\nFound {len(models)} models in Ollama:")
        
        for model_data in models:
            model_name = model_data.get("name")
            size_bytes = model_data.get("size", 0)
            size_gb = size_bytes / (1024 ** 3) if size_bytes else 0
            
            print(f"  - {model_name} ({size_gb:.2f} GB)")
            
            # Check if exists in DB
            existing = session.query(OllamaModel).filter_by(model_name=model_name).first()
            
            if existing:
                # Update
                existing.size_gb = size_gb
                existing.is_available = True
                existing.is_enabled = True
                print(f"    Updated in database")
            else:
                # Create new
                new_model = OllamaModel(
                    model_name=model_name,
                    display_name=model_name.split(':')[0].title(),
                    size_gb=size_gb,
                    is_enabled=True,
                    is_available=True,
                    added_at=datetime.utcnow()
                )
                session.add(new_model)
                print(f"    Added to database")
        
        # Mark models not in Ollama as unavailable
        all_db_models = session.query(OllamaModel).all()
        ollama_names = [m.get("name") for m in models]
        
        for db_model in all_db_models:
            if db_model.model_name not in ollama_names:
                db_model.is_available = False
                print(f"  - {db_model.model_name} marked as unavailable")
        
        session.commit()
        print(f"\n✓ Database synchronized with Ollama models")
        
    except Exception as e:
        session.rollback()
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        session.close()

if __name__ == "__main__":
    asyncio.run(sync_models())

