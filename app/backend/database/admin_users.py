import sys
from pathlib import Path
import getpass
from datetime import datetime

sys.path.append(str(Path(__file__).parent.parent.parent))

from app.backend.core.config import SessionLocal
from app.backend.database.initialized_db import User
from app.backend.services.auth_service import get_password_hash
from sqlalchemy.exc import IntegrityError

ACCESS_LEVELS = {
    0: "User",
    1: "Moderator",
    2: "Admin"
}

def create_admin_user():
    """Interactive CLI to create a user"""
    print("\n" + "=" * 50)
    print("CREATE USER")
    print("=" * 50)

    while True:
        username = input("\nUsername: ").strip()
        if len(username) < 3:
            print("Username must be at least 3 characters")
            continue
        break

    while True:
        email = input("Email: ").strip()
        if "@" not in email or "." not in email:
            print("Invalid email format")
            continue
        break

    while True:
        password = getpass.getpass("Password: ")
        if len(password) < 6:
            print("Password must be at least 6 characters")
            continue

        confirm_password = getpass.getpass("Confirm password: ")
        if password != confirm_password:
            print("Passwords do not match")
            continue
        break

    print("\nAccess levels:")
    print("0 = User")
    print("1 = Moderator")
    print("2 = Admin")

    while True:
        access_level_input = input("Access level (0-2) [0]: ").strip()
        if not access_level_input:
            access_level = 0
            break

        try:
            access_level = int(access_level_input)
            if access_level not in [0, 1, 2]:
                print("Invalid access level. Use 0, 1, or 2")
                continue
            break
        except ValueError:
            print("Invalid input. Use 0, 1, or 2")

    session = SessionLocal()
    try:
        new_user = User(
            username=username,
            email=email,
            password_hash=get_password_hash(password),
            access_level=access_level,
            created_at=datetime.utcnow(),
            is_active=True
        )

        session.add(new_user)
        session.commit()

        print(f"\nUser created: {username} (ID: {new_user.user_id})")
        print(f"Access level: {ACCESS_LEVELS[access_level]}")

        return True

    except IntegrityError as e:
        session.rollback()
        error_msg = str(e.orig)
        if "unique constraint" in error_msg.lower():
            print("\nError: Username or email already exists")
        else:
            print(f"\nIntegrity Error: {error_msg}")
        return False
    except Exception as e:
        session.rollback()
        print(f"\nError: {e}")
        return False
    finally:
        session.close()

def list_users():
    """List all users"""
    session = SessionLocal()
    try:
        users = session.query(User).all()

        if not users:
            print("\nNo users found")
            return

        print("\n" + "=" * 90)
        print(f"{'ID':<5} {'Username':<20} {'Email':<30} {'Access':<12} {'Active':<8}")
        print("=" * 90)

        for user in users:
            access = ACCESS_LEVELS.get(user.access_level, "Unknown")
            print(f"{user.user_id:<5} {user.username:<20} {user.email:<30} "
                  f"{access:<12} "
                  f"{'Yes' if user.is_active else 'No':<8}")

        print("=" * 90)
        print(f"Total: {len(users)}")

    except Exception as e:
        print(f"Error: {e}")
    finally:
        session.close()

def delete_user():
    """Delete a user"""
    username = input("\nUsername to delete: ").strip()
    confirm = input(f"Delete '{username}'? (yes/no): ").strip().lower()

    if confirm != 'yes':
        print("Cancelled")
        return

    session = SessionLocal()
    try:
        user = session.query(User).filter_by(username=username).first()

        if not user:
            print(f"User '{username}' not found")
            return

        session.delete(user)
        session.commit()
        print(f"User '{username}' deleted")

    except Exception as e:
        session.rollback()
        print(f"Error: {e}")
    finally:
        session.close()

def change_access_level():
    """Change user access level"""
    username = input("\nUsername: ").strip()

    session = SessionLocal()
    try:
        user = session.query(User).filter_by(username=username).first()

        if not user:
            print(f"User '{username}' not found")
            return

        print(f"\nCurrent access level: {ACCESS_LEVELS[user.access_level]}")
        print("\n0 = User")
        print("1 = Moderator")
        print("2 = Admin")

        while True:
            new_level_input = input("New access level (0-2): ").strip()
            try:
                new_level = int(new_level_input)
                if new_level not in [0, 1, 2]:
                    print("Invalid access level")
                    continue
                break
            except ValueError:
                print("Invalid input")

        user.access_level = new_level
        session.commit()

        print(f"'{username}' access level changed to {ACCESS_LEVELS[new_level]}")

    except Exception as e:
        session.rollback()
        print(f"Error: {e}")
    finally:
        session.close()

def main_menu():
    """Main menu"""
    while True:
        print("\n" + "=" * 50)
        print("USER MANAGEMENT")
        print("=" * 50)
        print("1. Create user")
        print("2. List users")
        print("3. Delete user")
        print("4. Change access level")
        print("5. Exit")

        choice = input("\nOption: ").strip()

        if choice == '1':
            create_admin_user()
        elif choice == '2':
            list_users()
        elif choice == '3':
            delete_user()
        elif choice == '4':
            change_access_level()
        elif choice == '5':
            break
        else:
            print("Invalid option")

if __name__ == "__main__":
    try:
        main_menu()
    except KeyboardInterrupt:
        print("\n\nExiting")
    except Exception as e:
        print(f"\nFatal error: {e}")

