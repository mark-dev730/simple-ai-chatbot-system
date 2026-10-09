import os
from pathlib import Path
from dotenv import load_dotenv
import oracledb
from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL
from sqlalchemy.orm import sessionmaker, declarative_base
# load .env path
env_path = Path(__file__).parent.parent.parent / '.env'
load_dotenv(env_path)

# db config from env vars
DB_USERNAME = os.getenv("DB_username")
DB_PASSWORD = os.getenv("DB_password")
DB_HOST = os.getenv("DB_host")
DB_PORT = os.getenv("DB_port", "1521")
DB_SERVICE_NAME = os.getenv("DB_service_name")

# Use localhost instead of 127.0.0.1 since SQL*Plus works with it
if DB_HOST == "127.0.0.1":
    DB_HOST = "localhost"

# Custom connection creator for SQLAlchemy using oracledb directly
def get_oracle_connection():
    dsn = f"{DB_HOST}:{DB_PORT}/{DB_SERVICE_NAME}"
    return oracledb.connect(user=DB_USERNAME, password=DB_PASSWORD, dsn=dsn)

#engine & sessions
engine = create_engine("oracle+oracledb://", creator=get_oracle_connection, echo=False)
SessionLocal = sessionmaker (autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

#helper function to get session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

#test connection
def test_connection():
    """Test both raw oracledb and SQLAlchemy connections"""
    print("Testing raw oracledb connection...")
    try:
        dsn = f"{DB_HOST}:{DB_PORT}/{DB_SERVICE_NAME}"
        conn = oracledb.connect(user=DB_USERNAME, password=DB_PASSWORD, dsn=dsn)
        cursor = conn.cursor()
        cursor.execute("SELECT 1 FROM dual")
        result = cursor.fetchone()
        cursor.close()
        conn.close()
        print("✓ Raw oracledb connection successful!")
    except Exception as e:
        print(f"✗ Raw connection failed: {e}")
        return False
    
    print("\nTesting SQLAlchemy engine connection...")
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1 FROM dual"))
            print("✓ SQLAlchemy connection successful!")
        return True
    except Exception as e:
        print(f"✗ SQLAlchemy connection failed: {e}")
        return False

if __name__ == "__main__":
    test_connection()

