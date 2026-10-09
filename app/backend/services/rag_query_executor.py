"""
RAG Query Executor - Automatically executes SQL queries from AI responses.
Detects SQL in AI responses, executes them, and formats results.
"""
import re
from typing import Optional, Tuple, List, Dict, Any
from app.backend.services.rag_service import rag_service
import logging

logger = logging.getLogger(__name__)


class RAGQueryExecutor:
    """Executes SQL queries detected in AI responses and formats results."""
    
    # Forbidden SQL keywords that could modify or destroy data
    FORBIDDEN_KEYWORDS = [
        'INSERT', 'UPDATE', 'DELETE', 'DROP', 'CREATE', 'ALTER', 
        'TRUNCATE', 'GRANT', 'REVOKE', 'COMMIT', 'ROLLBACK',
        'MERGE', 'REPLACE', 'RENAME', 'EXECUTE', 'EXEC', 'CALL'
    ]
    
    @staticmethod
    def validate_query_safety(sql: str) -> Tuple[bool, Optional[str]]:
        """
        Validate that SQL query is read-only (SELECT only).
        
        Returns:
            Tuple of (is_safe, error_message)
        """
        if not sql:
            return False, "Empty query"
        
        # Remove comments and normalize whitespace
        sql_normalized = re.sub(r'--.*?$', '', sql, flags=re.MULTILINE)
        sql_normalized = re.sub(r'/\*.*?\*/', '', sql_normalized, flags=re.DOTALL)
        sql_normalized = ' '.join(sql_normalized.split()).upper()
        
        # Check if query starts with SELECT (allow WITH for CTEs)
        if not (sql_normalized.startswith('SELECT') or sql_normalized.startswith('WITH')):
            return False, "Only SELECT queries are allowed"
        
        # Check for forbidden keywords
        for keyword in RAGQueryExecutor.FORBIDDEN_KEYWORDS:
            # Use word boundaries to avoid false positives (e.g., "INSERTED" column name)
            pattern = r'\b' + keyword + r'\b'
            if re.search(pattern, sql_normalized):
                return False, f"Forbidden keyword detected: {keyword}. Only SELECT queries are allowed."
        
        # Additional safety checks
        if ';' in sql_normalized:
            # Check if there are multiple statements (semicolon not at the end)
            sql_stripped = sql_normalized.rstrip(';').strip()
            if ';' in sql_stripped:
                return False, "Multiple SQL statements not allowed"
        
        return True, None
    
    @staticmethod
    def detect_sql_query(text: str) -> Optional[str]:
        """
        Detect SQL query in text.
        Looks for patterns like:
        - ```sql ... ```
        - [QUERY]...[/QUERY]
        - SELECT statements
        """
        # Try markdown code block with sql
        sql_block_pattern = r'```sql\s*(.*?)\s*```'
        match = re.search(sql_block_pattern, text, re.DOTALL | re.IGNORECASE)
        if match:
            sql = match.group(1).strip()
            # Validate and auto-fix common mistakes
            sql = RAGQueryExecutor._auto_fix_sql(sql)
            return sql
        
        # Try [QUERY] tags
        query_tag_pattern = r'\[QUERY\](.*?)\[/QUERY\]'
        match = re.search(query_tag_pattern, text, re.DOTALL | re.IGNORECASE)
        if match:
            sql = match.group(1).strip()
            sql = RAGQueryExecutor._auto_fix_sql(sql)
            return sql
        
        # Try to find SELECT statement
        select_pattern = r'(SELECT\s+.*?FROM\s+\w+.*?(?:;|$))'
        match = re.search(select_pattern, text, re.DOTALL | re.IGNORECASE)
        if match:
            query = match.group(1).strip()
            # Remove trailing punctuation if it's not a semicolon
            if query and query[-1] not in [';', ')']:
                query = query.rstrip('.')
            query = RAGQueryExecutor._auto_fix_sql(query)
            return query
        
        return None
    
    @staticmethod
    def _auto_fix_sql(sql: str) -> str:
        """
        Auto-fix common SQL mistakes for Oracle.
        
        Converts PostgreSQL syntax to Oracle syntax.
        """
        if not sql:
            return sql
        
        # Remove trailing semicolon (Oracle via SQLAlchemy doesn't like it)
        sql = sql.rstrip(';').strip()
        
        # Fix DATE_PART to SUBSTR (common mistake)
        # DATE_PART('year', column) -> SUBSTR(column, 1, 4)
        sql = re.sub(
            r"DATE_PART\s*\(\s*['\"]year['\"]\s*,\s*(\w+)\s*\)\s*=\s*(\d{4})",
            r"SUBSTR(\1, 1, 4) = '\2'",
            sql,
            flags=re.IGNORECASE
        )
        
        # DATE_PART('month', column) -> SUBSTR(column, 5, 2)
        sql = re.sub(
            r"DATE_PART\s*\(\s*['\"]month['\"]\s*,\s*(\w+)\s*\)\s*=\s*(\d{1,2})",
            lambda m: f"SUBSTR({m.group(1)}, 5, 2) = '{int(m.group(2)):02d}'",
            sql,
            flags=re.IGNORECASE
        )
        
        # Fix LIMIT to FETCH FIRST
        sql = re.sub(
            r'\bLIMIT\s+(\d+)\b',
            r'FETCH FIRST \1 ROWS ONLY',
            sql,
            flags=re.IGNORECASE
        )
        
        # Fix substring() to SUBSTR()
        sql = re.sub(
            r'\bsubstring\b',
            'SUBSTR',
            sql,
            flags=re.IGNORECASE
        )
        
        logger.info(f"Auto-fixed SQL query")
        return sql
    
    @staticmethod
    def execute_query_from_text(text: str) -> Tuple[Optional[str], Optional[List[Dict[str, Any]]]]:
        """
        Detect and execute SQL query from text.
        
        Returns:
            Tuple of (sql_query, results) or (None, None) if no query found
        """
        sql = RAGQueryExecutor.detect_sql_query(text)
        if not sql:
            return None, None
        
        # Validate query safety BEFORE execution
        is_safe, error_msg = RAGQueryExecutor.validate_query_safety(sql)
        if not is_safe:
            logger.warning(f"BLOCKED UNSAFE QUERY: {sql}")
            logger.warning(f"Reason: {error_msg}")
            # Return the SQL but with None results to indicate it was blocked
            return sql, None
        
        try:
            # Log the query being executed
            logger.info(f"EXECUTING SQL: {sql}")
            
            # Execute query
            results = rag_service.execute_query(sql)
            logger.info(f"Query returned {len(results)} results")
            
            return sql, results
        except Exception as e:
            logger.error(f"Query execution failed: {e}")
            logger.error(f"Failed SQL was: {sql}")
            return sql, None
    
    @staticmethod
    def format_query_results(results: List[Dict[str, Any]], max_rows: int = 10) -> str:
        """
        Format query results in a human-readable way.
        """
        if not results:
            return "Query returned no results."
        
        # Get column names from first result
        columns = list(results[0].keys())
        
        # Format as table
        output = ["\n**Query Results:**\n"]
        
        # Single result - format as key-value
        if len(results) == 1:
            output.append("```")
            for col in columns:
                value = results[0].get(col)
                if value is not None:
                    output.append(f"{col}: {value}")
            output.append("```")
        
        # Multiple results - format as table
        else:
            # Determine column widths
            col_widths = {}
            for col in columns:
                col_widths[col] = len(str(col))
                for row in results[:max_rows]:
                    val_len = len(str(row.get(col, '')))
                    col_widths[col] = max(col_widths[col], val_len)
            
            # Header
            output.append("```")
            header = " | ".join(str(col).ljust(col_widths[col]) for col in columns)
            output.append(header)
            output.append("-" * len(header))
            
            # Rows
            for row in results[:max_rows]:
                row_str = " | ".join(
                    str(row.get(col, '')).ljust(col_widths[col]) 
                    for col in columns
                )
                output.append(row_str)
            
            if len(results) > max_rows:
                output.append(f"\n... and {len(results) - max_rows} more rows")
            
            output.append("```")
        
        output.append(f"\n*Total: {len(results)} row(s)*")
        
        return "\n".join(output)
    
    @staticmethod
    def enhance_response_with_results(response: str) -> str:
        """
        Detect SQL in response, execute it, and add results with natural language summary.
        
        This is the main entry point for processing AI responses.
        """
        sql, results = RAGQueryExecutor.execute_query_from_text(response)
        
        if sql:
            # Check if query was blocked (sql exists but results is None)
            if results is None:
                # Query was blocked or failed - remove SQL and show error message
                response = re.sub(r'```sql.*?```', '', response, flags=re.DOTALL | re.IGNORECASE)
                response = re.sub(r'\[QUERY\].*?\[/QUERY\]', '', response, flags=re.DOTALL | re.IGNORECASE)
                response = response.strip()
                
                # Add friendly error message
                error_msg = "⚠️ I cannot execute this query for security reasons. I can only run SELECT queries to retrieve data, not modify or delete it."
                
                if response:
                    return f"{response}\n\n{error_msg}"
                else:
                    return error_msg
            
            # Query succeeded - format and show results
            if results is not None:
                # Add results to response
                formatted_results = RAGQueryExecutor.format_query_results(results)
                
                # Create natural language summary
                summary = RAGQueryExecutor.create_natural_language_summary(response, results)
                
                # Remove ALL SQL-related content from response (code blocks, [QUERY] tags, explanations)
                response = re.sub(r'```sql.*?```', '', response, flags=re.DOTALL | re.IGNORECASE)
                response = re.sub(r'\[QUERY\].*?\[/QUERY\]', '', response, flags=re.DOTALL | re.IGNORECASE)
                response = re.sub(r'Explanation:.*?(?=\n\n|\Z)', '', response, flags=re.DOTALL | re.IGNORECASE)
                response = re.sub(r'This (?:SQL )?query.*?(?=\n\n|\Z)', '', response, flags=re.DOTALL | re.IGNORECASE)
                response = re.sub(r'Here\'?s? the (?:data|query|SQL).*?(?=\n\n|\Z)', '', response, flags=re.DOTALL | re.IGNORECASE)
                
                # Clean up the remaining intro text and extra whitespace
                response = response.strip()
                if response:
                    # Keep any intro text from AI, then add summary and results
                    enhanced = f"{response}\n\n{summary}\n\n{formatted_results}"
                else:
                    # No intro text, just show summary and results
                    enhanced = f"{summary}\n\n{formatted_results}"
                
                return enhanced.strip()
        
        return response
    
    @staticmethod
    def create_natural_language_summary(
        query_text: str,
        results: List[Dict[str, Any]]
    ) -> str:
        """
        Create a natural language summary of query results.
        Analyzes the query intent and formats results accordingly.
        """
        if not results:
            return "No matching data found."
        
        query_lower = query_text.lower()
        
        # Single numeric result (COUNT, AVG, SUM, etc.)
        if len(results) == 1 and len(results[0]) == 1:
            key = list(results[0].keys())[0]
            value = results[0][key]
            
            if 'count' in key.lower():
                return f"**{value:,}** devices match your criteria."
            elif 'avg' in key.lower() or 'average' in key.lower():
                return f"The average is **{value:.2f}**."
            elif 'sum' in key.lower() or 'total' in key.lower():
                return f"The total is **{value:,}**."
            elif 'min' in key.lower():
                return f"The minimum is **{value}**."
            elif 'max' in key.lower():
                return f"The maximum is **{value}**."
            else:
                return f"Result: **{value}**"
        
        # Grouped results (likely GROUP BY query)
        if len(results) > 1 and len(results[0]) == 2:
            # Get column names
            cols = list(results[0].keys())
            name_col = cols[0]
            value_col = cols[1]
            
            # Check if it's asking for "most", "highest", "largest"
            if any(word in query_lower for word in ['most', 'highest', 'largest', 'which', 'top']):
                # Show top result prominently
                top = results[0]
                summary = f"**{top[name_col]}** has the most with **{top[value_col]:,}** devices."
                
                # Add runners-up if available
                if len(results) > 1:
                    second = results[1]
                    summary += f" Followed by **{second[name_col]}** with **{second[value_col]:,}**."
                
                if len(results) > 2:
                    third = results[2]
                    summary += f" Then **{third[name_col]}** with **{third[value_col]:,}**."
                
                return summary
            
            # Otherwise, list all results
            summary_parts = []
            for row in results[:5]:  # Top 5
                summary_parts.append(f"- **{row[name_col]}**: {row[value_col]:,}")
            
            summary = "\n".join(summary_parts)
            if len(results) > 5:
                summary += f"\n\n... and {len(results) - 5} more"
            
            return summary
        
        # Multiple column results - show as count
        return f"Found **{len(results)}** matching records."


# Global instance
rag_query_executor = RAGQueryExecutor()

