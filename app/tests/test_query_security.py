"""
Test script for RAG query security validation.
Tests that only SELECT queries are allowed.
"""
import sys
import os
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# Add project root to path (two levels up: tests -> app -> root)
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from app.backend.services.rag_query_executor import rag_query_executor

def test_query_security():
    """Test various SQL queries to ensure only SELECT is allowed."""
    
    test_cases = [
        # Safe queries (should pass)
        ("SELECT * FROM conv_test_pivot_queue_sim", True, "Simple SELECT"),
        ("SELECT COUNT(*) FROM conv_test_pivot_queue_sim WHERE outcome = 'PLACED'", True, "SELECT with WHERE"),
        ("SELECT AVG(p1_yield) as avg_yield FROM conv_test_pivot_queue_sim", True, "SELECT with aggregate"),
        ("WITH cte AS (SELECT * FROM conv_test_pivot_queue_sim) SELECT * FROM cte", True, "CTE query"),
        
        # Unsafe queries (should fail)
        ("DELETE FROM conv_test_pivot_queue_sim WHERE outcome = 'PLACED'", False, "DELETE"),
        ("UPDATE conv_test_pivot_queue_sim SET outcome = 'MOVED' WHERE device_id = 123", False, "UPDATE"),
        ("INSERT INTO conv_test_pivot_queue_sim (device_id) VALUES (999)", False, "INSERT"),
        ("DROP TABLE conv_test_pivot_queue_sim", False, "DROP TABLE"),
        ("TRUNCATE TABLE conv_test_pivot_queue_sim", False, "TRUNCATE"),
        ("CREATE TABLE test_table (id NUMBER)", False, "CREATE TABLE"),
        ("ALTER TABLE conv_test_pivot_queue_sim ADD COLUMN test VARCHAR2(100)", False, "ALTER TABLE"),
        ("GRANT SELECT ON conv_test_pivot_queue_sim TO public", False, "GRANT"),
        ("SELECT * FROM conv_test_pivot_queue_sim; DELETE FROM conv_test_pivot_queue_sim", False, "Multiple statements"),
        ("MERGE INTO conv_test_pivot_queue_sim", False, "MERGE"),
        ("EXECUTE IMMEDIATE 'DROP TABLE conv_test_pivot_queue_sim'", False, "EXECUTE"),
    ]
    
    print("=" * 70)
    print("RAG QUERY SECURITY VALIDATION TESTS")
    print("=" * 70)
    print()
    
    passed = 0
    failed = 0
    
    for sql, should_pass, description in test_cases:
        is_safe, error_msg = rag_query_executor.validate_query_safety(sql)
        
        # Check if result matches expectation
        test_passed = (is_safe == should_pass)
        
        status = "✓ PASS" if test_passed else "✗ FAIL"
        color = "\033[92m" if test_passed else "\033[91m"
        reset = "\033[0m"
        
        print(f"{color}{status}{reset} | {description}")
        print(f"  SQL: {sql[:80]}{'...' if len(sql) > 80 else ''}")
        print(f"  Expected: {'ALLOW' if should_pass else 'BLOCK'}")
        print(f"  Result: {'ALLOWED' if is_safe else 'BLOCKED'}")
        
        if not is_safe:
            print(f"  Reason: {error_msg}")
        
        print()
        
        if test_passed:
            passed += 1
        else:
            failed += 1
    
    print("=" * 70)
    print(f"Results: {passed} passed, {failed} failed out of {len(test_cases)} tests")
    print("=" * 70)
    
    return failed == 0


if __name__ == "__main__":
    success = test_query_security()
    sys.exit(0 if success else 1)
