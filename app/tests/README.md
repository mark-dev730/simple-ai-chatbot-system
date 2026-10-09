# Test Scripts

These scripts test various system functionalities. Run them periodically to ensure system integrity.

## Available Tests

### RAG Functionality Tests

**`test_rag_service.py`**
- Tests RAG service functionality
- Validates schema context retrieval
- Checks query execution

```powershell
python app/tests/test_rag_service.py
```

**`test_query_executor.py`**
- Tests SQL query execution from text
- Validates query detection and formatting
- Tests result summarization

```powershell
python app/tests/test_query_executor.py
```

### Security Tests

**`test_query_security.py`** ⚠️ CRITICAL
- Validates that only SELECT queries are allowed
- Tests blocking of destructive operations (INSERT, UPDATE, DELETE, DROP, etc.)
- Ensures SQL injection prevention

```powershell
python app/tests/test_query_security.py
```

**Run this test after any changes to query validation logic!**

## Running All Tests

```powershell
# Run all tests
Get-ChildItem app\tests\test_*.py | ForEach-Object { python $_.FullName }
```

## Test Results

All tests should pass with exit code 0. If any test fails, investigate before deploying to production.
