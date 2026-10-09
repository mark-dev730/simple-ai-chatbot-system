import sys
from pathlib import Path

# Add project root to path (two levels up: scripts -> app -> root)
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from app.backend.core.config import SessionLocal
from sqlalchemy import inspect, text

session = SessionLocal()
try:
    inspector = inspect(session.bind)
    
    table_name = 'conv_test_pivot_queue_sim'
    cols = inspector.get_columns(table_name)
    
    print(f"Table: {table_name}")
    print("=" * 80)
    print(f"{'Column Name':<30} {'Type':<20} {'Nullable':<10}")
    print("-" * 80)
    
    for col in cols:
        nullable = "NULL" if col.get('nullable', True) else "NOT NULL"
        print(f"{col['name']:<30} {str(col['type']):<20} {nullable:<10}")
    
    # Get row count
    count = session.execute(text(f"SELECT COUNT(*) FROM {table_name}")).scalar()
    print("-" * 80)
    print(f"Total rows: {count}")
    
    # Show sample data
    if count > 0:
        print("\nSample data (first 3 rows):")
        print("=" * 80)
        result = session.execute(text(f"SELECT * FROM {table_name} WHERE ROWNUM <= 3"))
        rows = result.fetchall()
        
        for i, row in enumerate(rows, 1):
            print(f"\nRow {i}:")
            for col, val in zip(cols, row):
                print(f"  {col['name']}: {val}")
    
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
finally:
    session.close()

