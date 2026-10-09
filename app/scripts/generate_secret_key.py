"""
Generate a secure SECRET_KEY for JWT authentication.
Run this script and add the output to your .env file.
"""
import secrets

def generate_secret_key():
    """Generate a cryptographically secure secret key."""
    secret_key = secrets.token_urlsafe(32)
    return secret_key

if __name__ == "__main__":
    key = generate_secret_key()
    print("=" * 60)
    print("🔐 Generated Secure SECRET_KEY")
    print("=" * 60)
    print()
    print(f"SECRET_KEY={key}")
    print()
    print("=" * 60)
    print("Copy the line above to your .env file")
    print("=" * 60)
