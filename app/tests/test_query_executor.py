"""
Test script for RAG query executor.
Tests SQL detection and execution.
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


def test_sql_detection():
    """Test SQL detection in various formats."""
    print("=" * 60)
    print("TEST 1: SQL Detection")
    print("=" * 60)
    
    test_cases = [
        # Markdown code block
        ("Let me check:\n```sql\nSELECT COUNT(*) FROM table\n```\nThis counts rows.",
         "SELECT COUNT(*) FROM table"),
        
        # Inline SELECT
        ("The query is: SELECT * FROM users WHERE id = 1;",
         "SELECT * FROM users WHERE id = 1;"),
        
        # Multi-line
        ("Here's the query:\n```sql\nSELECT COUNT(*) as count\nFROM conv_test_pivot_queue_sim\nWHERE outcome = 'DE_COMMIT'\n```",
         "SELECT COUNT(*) as count\nFROM conv_test_pivot_queue_sim\nWHERE outcome = 'DE_COMMIT'"),
    ]
    
    for text, expected in test_cases:
        result = rag_query_executor.detect_sql_query(text)
        status = "✓" if result and expected.lower() in result.lower() else "✗"
        print(f"\n{status} Test case:")
        print(f"  Input: {text[:50]}...")
        print(f"  Detected: {result[:50] if result else 'None'}...")


def test_query_execution():
    """Test actual query execution."""
    print("\n" + "=" * 60)
    print("TEST 2: Query Execution")
    print("=" * 60)
    
    test_queries = [
        "Let me check:\n```sql\nSELECT COUNT(*) as total FROM conv_test_pivot_queue_sim\n```",
        "Here's the count:\n```sql\nSELECT outcome, COUNT(*) as count FROM conv_test_pivot_queue_sim GROUP BY outcome ORDER BY count DESC FETCH FIRST 3 ROWS ONLY\n```",
    ]
    
    for query_text in test_queries:
        print(f"\nExecuting query from text...")
        sql, results = rag_query_executor.execute_query_from_text(query_text)
        
        if sql:
            print(f"✓ Detected SQL: {sql[:60]}...")
            if results is not None:
                print(f"✓ Got {len(results)} results")
                if results:
                    print(f"  First result: {results[0]}")
            else:
                print("✗ Query execution failed")
        else:
            print("✗ No SQL detected")


def test_result_formatting():
    """Test result formatting."""
    print("\n" + "=" * 60)
    print("TEST 3: Result Formatting")
    print("=" * 60)
    
    # Single result
    single_result = [{"COUNT": 5444}]
    formatted = rag_query_executor.format_query_results(single_result)
    print("\nSingle result:")
    print(formatted)
    
    # Multiple results
    multiple_results = [
        {"OUTCOME": "PLACED", "COUNT": 4185},
        {"OUTCOME": "DE_COMMIT", "COUNT": 1143},
        {"OUTCOME": "MOVED", "COUNT": 98}
    ]
    formatted = rag_query_executor.format_query_results(multiple_results)
    print("\nMultiple results:")
    print(formatted)


def test_full_enhancement():
    """Test full response enhancement."""
    print("\n" + "=" * 60)
    print("TEST 4: Full Response Enhancement")
    print("=" * 60)
    
    ai_response = """Let me check the database for DE_COMMIT devices:

```sql
SELECT COUNT(*) as count FROM conv_test_pivot_queue_sim WHERE outcome = 'DE_COMMIT'
```

This query counts all devices with DE_COMMIT outcome."""
    
    print("\nOriginal response:")
    print(ai_response)
    
    enhanced = rag_query_executor.enhance_response_with_results(ai_response)
    
    print("\n" + "-" * 60)
    print("Enhanced response:")
    print(enhanced)


def main():
    """Run all tests."""
    test_sql_detection()
    test_query_execution()
    test_result_formatting()
    test_full_enhancement()
    
    print("\n" + "=" * 60)
    print("✓ All tests complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()

