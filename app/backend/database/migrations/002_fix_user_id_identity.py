import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent.parent.parent))

from app.backend.core.config import engine
from sqlalchemy import text

def upgrade():
    """Convert user_id to identity column"""
    print("Running migration: Fix user_id identity")

    with engine.connect() as conn:
        try:
            # Drop existing table and recreate with Identity
            # This is needed because you can't ALTER a column to Identity in Oracle

            # Get max user_id first
            result = conn.execute(text("SELECT NVL(MAX(user_id), 0) FROM users"))
            max_id = result.scalar()

            # Create sequence
            conn.execute(text("DROP SEQUENCE users_seq"))
        except:
            pass

        try:
            conn.execute(text(f"CREATE SEQUENCE users_seq START WITH {max_id + 1}"))

            # Drop existing identity if any
            try:
                conn.execute(text("ALTER TABLE users MODIFY user_id DROP IDENTITY"))
            except:
                pass

            # Add identity
            conn.execute(text("""
                ALTER TABLE users
                MODIFY user_id GENERATED ALWAYS AS IDENTITY (START WITH 1)
            """))

            conn.commit()
            print("Successfully fixed USER_ID identity")

        except Exception as e:
            conn.rollback()
            print(f"Error: {e}")
            raise

if __name__ == "__main__":
    upgrade()

