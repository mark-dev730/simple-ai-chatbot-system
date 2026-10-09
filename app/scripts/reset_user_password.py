import sys
from pathlib import Path

# Add project root to path (two levels up: scripts -> app -> root)
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from app.backend.core.config import SessionLocal
from app.backend.database.initialized_db import User
from app.backend.services.auth_service import get_password_hash

def reset_password(username, new_password):
    session = SessionLocal()
    try:
        user = session.query(User).filter_by(username=username).first()
        
        if not user:
            print(f"❌ User '{username}' not found")
            return False
        
        print(f"Found user: {username} ({user.email})")
        print(f"Old hash: {user.password_hash[:40]}...")
        
        # Update password with bcrypt hash
        user.password_hash = get_password_hash(new_password)
        session.commit()
        
        print(f"New hash: {user.password_hash[:40]}...")
        print(f"\n✓ Password reset successfully for '{username}'")
        print(f"  New password: {new_password}")
        print(f"\nYou can now login with these credentials.")
        
        return True
        
    except Exception as e:
        session.rollback()
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        session.close()

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python reset_user_password.py <username> <new_password>")
        print("\nExample: python reset_user_password.py admin newpassword123")
        sys.exit(1)
    
    print("=" * 60)
    print("PASSWORD RESET")
    print("=" * 60)
    reset_password(sys.argv[1], sys.argv[2])

