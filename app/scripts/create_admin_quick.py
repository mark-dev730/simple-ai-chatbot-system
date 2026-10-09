import sys
from pathlib import Path
from datetime import datetime

# Add project root to path (two levels up: scripts -> app -> root)
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from app.backend.core.config import SessionLocal
from app.backend.database.initialized_db import User
from app.backend.services.auth_service import get_password_hash

def create_admin(username, email, password):
    session = SessionLocal()
    try:
        # Check if user exists
        existing = session.query(User).filter_by(username=username).first()
        if existing:
            print(f"Deleting existing user: {username}")
            session.delete(existing)
            session.commit()

        # Create new user with bcrypt hash
        new_user = User(
            username=username,
            email=email,
            password_hash=get_password_hash(password),
            access_level=2,  # Admin
            created_at=datetime.utcnow(),
            is_active=True
        )

        session.add(new_user)
        session.commit()

        print(f"\n✓ Admin user created successfully!")
        print(f"Username: {username}")
        print(f"Email: {email}")
        print(f"Access Level: Admin (2)")
        print(f"\nYou can now login with these credentials.")

    except Exception as e:
        session.rollback()
        print(f"Error: {e}")
    finally:
        session.close()

if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Usage: python create_admin_quick.py <username> <email> <password>")
        print("\nExample: python create_admin_quick.py admin admin@example.com mypassword123")
        sys.exit(1)

    create_admin(sys.argv[1], sys.argv[2], sys.argv[3])

