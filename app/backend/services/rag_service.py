"""
RAG (Retrieval-Augmented Generation) service for intelligent database querying.
Uses semantic metadata to understand schema and generate SQL queries dynamically.
"""
import yaml
import os
from typing import List, Dict, Any, Optional
from pathlib import Path
from sqlalchemy import text
from app.backend.core.config import engine
import logging

logger = logging.getLogger(__name__)


class RAGService:
    def __init__(self):
        self.metadata = None
        self.load_metadata()
    
    def load_metadata(self):
        """Load schema metadata from YAML file."""
        metadata_path = Path(__file__).parent.parent / "rag" / "schema_metadata.yaml"
        
        try:
            with open(metadata_path, 'r') as f:
                self.metadata = yaml.safe_load(f)
            logger.info(f"✓ Loaded schema metadata from {metadata_path}")
        except Exception as e:
            logger.error(f"✗ Failed to load schema metadata: {e}")
            self.metadata = {"tables": {}, "query_patterns": {}, "business_glossary": {}}
    
    def get_schema_context(self, table_name: Optional[str] = None) -> str:
        """
        Get formatted schema context for LLM prompt injection.
        
        Args:
            table_name: Optional specific table to describe. If None, describes all tables.
            
        Returns:
            Formatted string describing database schema
        """
        if not self.metadata:
            return "No schema metadata available."
        
        context_parts = ["=== DATABASE SCHEMA INFORMATION ===\n"]
        
        # Add business glossary
        if self.metadata.get("business_glossary"):
            context_parts.append("## Business Terms:")
            for term, definition in self.metadata["business_glossary"].items():
                context_parts.append(f"- {term}: {definition}")
            context_parts.append("")
        
        # Add table information
        tables = self.metadata.get("tables", {})
        if table_name:
            tables = {table_name: tables.get(table_name)} if table_name in tables else {}
        
        for tbl_name, tbl_info in tables.items():
            context_parts.append(f"## Table: {tbl_name}")
            context_parts.append(f"Description: {tbl_info.get('description', 'N/A')}")
            
            if tbl_info.get("business_context"):
                context_parts.append(f"\nBusiness Context:\n{tbl_info['business_context']}")
            
            context_parts.append(f"\nRow Count: ~{tbl_info.get('row_count', 'unknown')} rows")
            context_parts.append(f"Primary Key: {tbl_info.get('primary_key', 'N/A')}")
            
            # Add columns
            context_parts.append("\nColumns:")
            for col_name, col_info in tbl_info.get("columns", {}).items():
                col_desc = col_info.get("description", "")
                col_type = col_info.get("type", "unknown")
                context_parts.append(f"  - {col_name} ({col_type}): {col_desc}")
                
                if col_info.get("business_meaning"):
                    context_parts.append(f"    → {col_info['business_meaning']}")
                
                if col_info.get("common_values"):
                    context_parts.append(f"    Common values: {', '.join(col_info['common_values'])}")
            
            # Add common queries
            if tbl_info.get("common_queries"):
                context_parts.append("\nCommon Questions:")
                for query in tbl_info["common_queries"]:
                    context_parts.append(f"  - {query}")
            
            context_parts.append("")
        
        # Add query patterns
        if self.metadata.get("query_patterns"):
            context_parts.append("## Query Patterns:")
            for pattern_name, pattern_info in self.metadata["query_patterns"].items():
                context_parts.append(f"- {pattern_name}: {pattern_info.get('description', '')}")
                if pattern_info.get("examples"):
                    context_parts.append(f"  Examples: {', '.join(pattern_info['examples'][:3])}")
            context_parts.append("")
        
        context_parts.append("=== END SCHEMA INFORMATION ===")
        
        return "\n".join(context_parts)
    
    def get_table_info(self, table_name: str) -> Optional[Dict[str, Any]]:
        """Get metadata for a specific table."""
        if not self.metadata:
            return None
        return self.metadata.get("tables", {}).get(table_name)
    
    def get_searchable_columns(self, table_name: str) -> List[str]:
        """Get list of searchable column names for a table."""
        table_info = self.get_table_info(table_name)
        if not table_info:
            return []
        
        searchable = []
        for col_name, col_info in table_info.get("columns", {}).items():
            if col_info.get("searchable", False):
                searchable.append(col_name)
        
        return searchable
    
    def get_aggregatable_columns(self, table_name: str) -> List[str]:
        """Get list of columns suitable for aggregation."""
        table_info = self.get_table_info(table_name)
        if not table_info:
            return []
        
        aggregatable = []
        for col_name, col_info in table_info.get("columns", {}).items():
            if col_info.get("aggregatable", False):
                aggregatable.append(col_name)
        
        return aggregatable
    
    @staticmethod
    def _get_key(row_dict: Dict[str, Any], key: str) -> str:
        """
        Get key from dictionary, handling Oracle's uppercase column names.
        Returns the actual key that exists in the dictionary.
        """
        if key in row_dict:
            return key
        elif key.upper() in row_dict:
            return key.upper()
        elif key.lower() in row_dict:
            return key.lower()
        raise KeyError(f"Key '{key}' not found in result (tried {key}, {key.upper()}, {key.lower()})")
    
    def execute_query(self, sql: str, params: Optional[Dict] = None) -> List[Dict[str, Any]]:
        """
        Execute a SQL query and return results.
        
        Args:
            sql: SQL query string
            params: Optional parameters for parameterized queries
            
        Returns:
            List of result rows as dictionaries
        """
        try:
            with engine.connect() as conn:
                if params:
                    result = conn.execute(text(sql), params)
                else:
                    result = conn.execute(text(sql))
                
                columns = result.keys()
                rows = []
                
                for row in result:
                    rows.append(dict(zip(columns, row)))
                
                return rows
        except Exception as e:
            logger.error(f"Query execution error: {e}")
            raise
    
    def search_data(
        self,
        table_name: str,
        search_term: Optional[str] = None,
        filters: Optional[Dict[str, Any]] = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Search table data with optional filters.
        
        Args:
            table_name: Name of table to search
            search_term: Optional text to search in searchable columns
            filters: Optional column filters (e.g., {"outcome": "PASS"})
            limit: Maximum number of results
            
        Returns:
            List of matching rows
        """
        # Build query
        query_parts = [f"SELECT * FROM {table_name} WHERE 1=1"]
        params = {}
        
        # Add text search across searchable columns
        if search_term:
            searchable_cols = self.get_searchable_columns(table_name)
            if searchable_cols:
                search_conditions = []
                for col in searchable_cols:
                    search_conditions.append(f"UPPER({col}) LIKE :search_term")
                
                query_parts.append(f"AND ({' OR '.join(search_conditions)})")
                params["search_term"] = f"%{search_term.upper()}%"
        
        # Add specific filters
        if filters:
            for col, value in filters.items():
                param_name = f"filter_{col}"
                query_parts.append(f"AND {col} = :{param_name}")
                params[param_name] = value
        
        query_parts.append(f"FETCH FIRST {limit} ROWS ONLY")
        
        sql = " ".join(query_parts)
        
        return self.execute_query(sql, params)
    
    def get_statistics(self, table_name: str) -> Dict[str, Any]:
        """
        Get statistical summary of a table.
        
        Args:
            table_name: Name of table
            
        Returns:
            Dictionary with statistics
        """
        stats = {}
        
        # Total count
        result = self.execute_query(f"SELECT COUNT(*) as cnt FROM {table_name}")
        cnt_key = self._get_key(result[0], "cnt")
        stats["total_rows"] = result[0][cnt_key] if result else 0
        
        # Get aggregatable columns and calculate stats
        aggregatable_cols = self.get_aggregatable_columns(table_name)
        
        if aggregatable_cols:
            for col in aggregatable_cols:
                col_upper = col.upper()
                sql = f"""
                    SELECT 
                        AVG({col}) as avg_val,
                        MIN({col}) as min_val,
                        MAX({col}) as max_val,
                        STDDEV({col}) as stddev_val
                    FROM {table_name}
                    WHERE {col} IS NOT NULL
                """
                result = self.execute_query(sql)
                if result and result[0]:
                    row = result[0]
                    avg_key = self._get_key(row, "avg_val")
                    min_key = self._get_key(row, "min_val")
                    max_key = self._get_key(row, "max_val")
                    stddev_key = self._get_key(row, "stddev_val")
                    
                    stats[col] = {
                        "average": float(row[avg_key]) if row[avg_key] else None,
                        "min": float(row[min_key]) if row[min_key] else None,
                        "max": float(row[max_key]) if row[max_key] else None,
                        "stddev": float(row[stddev_key]) if row[stddev_key] else None
                    }
        
        return stats
    
    def format_results_for_llm(self, results: List[Dict[str, Any]], max_rows: int = 5) -> str:
        """
        Format query results for LLM consumption.
        
        Args:
            results: Query results
            max_rows: Maximum rows to include in formatted output
            
        Returns:
            Formatted string representation
        """
        if not results:
            return "No results found."
        
        output = [f"Found {len(results)} results (showing first {min(len(results), max_rows)}):\n"]
        
        for i, row in enumerate(results[:max_rows]):
            output.append(f"Result {i+1}:")
            for key, value in row.items():
                output.append(f"  {key}: {value}")
            output.append("")
        
        if len(results) > max_rows:
            output.append(f"... and {len(results) - max_rows} more results")
        
        return "\n".join(output)


# Global RAG service instance
rag_service = RAGService()

