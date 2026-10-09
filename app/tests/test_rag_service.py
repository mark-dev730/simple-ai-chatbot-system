"""
Test script to demonstrate RAG service capabilities.
Shows how the chatbot can understand and query manufacturing data.
"""
import sys
import os
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# Add project root to path (two levels up: tests -> app -> root)
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from app.backend.services.rag_service import rag_service

def test_schema_context():
    """Test getting schema context for LLM."""
    print("=" * 60)
    print("TEST 1: Schema Context Generation")
    print("=" * 60)
    
    # Get full schema context
    context = rag_service.get_schema_context()
    print(context)
    print()


def test_table_queries():
    """Test direct table queries."""
    print("=" * 60)
    print("TEST 2: Direct Table Queries")
    print("=" * 60)
    
    # Test 1: Get statistics
    print("\n1. Table Statistics:")
    print("-" * 40)
    stats = rag_service.get_statistics("conv_test_pivot_queue_sim")
    for key, value in stats.items():
        print(f"{key}: {value}")
    
    # Test 2: Search for specific data
    print("\n2. Search for devices with low yield:")
    print("-" * 40)
    results = rag_service.execute_query("""
        SELECT wbdevice, p1_yield, p2_yield, p3_yield, outcome
        FROM conv_test_pivot_queue_sim
        WHERE p1_yield < 80
        FETCH FIRST 5 ROWS ONLY
    """)
    
    for row in results:
        print(f"Device: {row.get('WBDEVICE') or row.get('wbdevice')}, "
              f"P1 Yield: {row.get('P1_YIELD') or row.get('p1_yield')}, "
              f"P2: {row.get('P2_YIELD') or row.get('p2_yield')}, "
              f"P3: {row.get('P3_YIELD') or row.get('p3_yield')}, "
              f"Outcome: {row.get('OUTCOME') or row.get('outcome')}")
    
    # Test 3: Search with filters
    print("\n3. Search with text filters:")
    print("-" * 40)
    results = rag_service.search_data(
        "conv_test_pivot_queue_sim",
        search_term="FAIL",
        limit=3
    )
    
    formatted = rag_service.format_results_for_llm(results, max_rows=3)
    print(formatted)
    
    # Test 4: Aggregation query
    print("\n4. Aggregate by outcome:")
    print("-" * 40)
    results = rag_service.execute_query("""
        SELECT outcome, COUNT(*) as count, AVG(p1_yield) as avg_yield
        FROM conv_test_pivot_queue_sim
        GROUP BY outcome
        ORDER BY count DESC
    """)
    
    for row in results:
        avg_yield = row.get('AVG_YIELD') or row.get('avg_yield')
        outcome = row.get('OUTCOME') or row.get('outcome')
        count = row.get('COUNT') or row.get('count')
        yield_str = f"{avg_yield:.2f}" if avg_yield else "N/A"
        print(f"Outcome: {outcome}, Count: {count}, Avg P1 Yield: {yield_str}")
    
    print()


def test_searchable_columns():
    """Test getting searchable columns."""
    print("=" * 60)
    print("TEST 3: Searchable Columns")
    print("=" * 60)
    
    searchable = rag_service.get_searchable_columns("conv_test_pivot_queue_sim")
    print(f"Searchable columns: {', '.join(searchable)}")
    
    aggregatable = rag_service.get_aggregatable_columns("conv_test_pivot_queue_sim")
    print(f"Aggregatable columns: {', '.join(aggregatable)}")
    print()


def simulate_chatbot_query():
    """Simulate how the chatbot would use RAG."""
    print("=" * 60)
    print("TEST 4: Simulated Chatbot Interaction")
    print("=" * 60)
    
    print("\nUser Question: 'Show me devices with low yield that failed'")
    print("\nStep 1: Chatbot gets schema context")
    print("-" * 40)
    context = rag_service.get_schema_context("conv_test_pivot_queue_sim")
    print(context[:500] + "...\n")
    
    print("Step 2: Chatbot uses context to generate SQL")
    print("-" * 40)
    sql = """
        SELECT wbdevice, mkt_part_num, p1_yield, p2_yield, p3_yield, outcome, remarks
        FROM conv_test_pivot_queue_sim
        WHERE outcome = 'FAIL' AND p1_yield < 85
        FETCH FIRST 5 ROWS ONLY
    """
    print(f"Generated SQL:\n{sql}")
    
    print("\nStep 3: Execute query and format results")
    print("-" * 40)
    results = rag_service.execute_query(sql)
    formatted = rag_service.format_results_for_llm(results, max_rows=5)
    print(formatted)
    
    print("\nStep 4: Chatbot generates natural language response")
    print("-" * 40)
    print(f"Found {len(results)} devices with low yield that failed.")
    print("These devices had yields below 85% in phase 1 testing and did not pass final inspection.")
    print()


def main():
    """Run all tests."""
    test_schema_context()
    test_table_queries()
    test_searchable_columns()
    simulate_chatbot_query()
    
    print("=" * 60)
    print("✓ All RAG service tests complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()

