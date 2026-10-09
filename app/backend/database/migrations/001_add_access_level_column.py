import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent.parent.parent))

from app.backend.core.config import engine
from sqlalchemy import text

def upgrade():
    """Add access_level column to users table"""
    print("Running migration: Add access_level column")

    with engine.connect() as conn:
        try:
            # Check if column exists
            result = conn.execute(text("""
                SELECT COUNT(*)
                FROM user_tab_columns
                WHERE table_name = 'USERS'
                AND column_name = 'ACCESS_LEVEL'
            """))

            exists = result.scalar() > 0

            if exists:
                print("Column ACCESS_LEVEL already exists. Skipping.")
                return

            # Add column: 0=user, 1=moderator, 2=admin
            conn.execute(text("""
                ALTER TABLE users
                ADD access_level NUMBER(1) DEFAULT 0 NOT NULL
            """))

            # Add check constraint
            conn.execute(text("""
                ALTER TABLE users
                ADD CONSTRAINT chk_access_level
                CHECK (access_level IN (0, 1, 2))
            """))

            conn.commit()
            print("Successfully added ACCESS_LEVEL column")
            print("Access levels: 0=User, 1=Moderator, 2=Admin")

        except Exception as e:
            conn.rollback()
            print(f"Error: {e}")
            raise

def downgrade():
    """Remove access_level column from users table"""
    print("Rolling back migration: Remove access_level column")

    with engine.connect() as conn:
        try:
            conn.execute(text("ALTER TABLE users DROP CONSTRAINT chk_access_level"))
            conn.execute(text("ALTER TABLE users DROP COLUMN access_level"))
            conn.commit()
            print("Successfully removed ACCESS_LEVEL column")

        except Exception as e:
            conn.rollback()
            print(f"Error: {e}")
            raise

if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "down":
        downgrade()
    else:
        upgrade()

