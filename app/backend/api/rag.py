"""
RAG (Retrieval-Augmented Generation) API endpoints.
Provides endpoints for querying manufacturing data with semantic understanding.
"""
from fastapi import APIRouter, HTTPException, Depends
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from app.backend.services.rag_service import rag_service
from app.backend.api.auth import get_current_user
from app.backend.schemas.auth import UserResponse
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/rag", tags=["RAG"])


# Request/Response Models
class SchemaContextRequest(BaseModel):
    table_name: Optional[str] = Field(None, description="Optional specific table name")


class SchemaContextResponse(BaseModel):
    context: str = Field(..., description="Formatted schema context for LLM")


class SearchRequest(BaseModel):
    table_name: str = Field(..., description="Table to search")
    search_term: Optional[str] = Field(None, description="Text search term")
    filters: Optional[Dict[str, Any]] = Field(None, description="Column filters")
    limit: int = Field(10, ge=1, le=100, description="Maximum results")


class SearchResponse(BaseModel):
    results: List[Dict[str, Any]] = Field(..., description="Query results")
    count: int = Field(..., description="Number of results returned")
    formatted: str = Field(..., description="LLM-formatted results")


class ExecuteQueryRequest(BaseModel):
    sql: str = Field(..., description="SQL query to execute")
    params: Optional[Dict[str, Any]] = Field(None, description="Query parameters")


class ExecuteQueryResponse(BaseModel):
    results: List[Dict[str, Any]] = Field(..., description="Query results")
    count: int = Field(..., description="Number of results")


class StatisticsResponse(BaseModel):
    table_name: str
    statistics: Dict[str, Any]


# Endpoints
@router.get("/schema", response_model=SchemaContextResponse)
async def get_schema_context(
    table_name: Optional[str] = None,
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Get formatted schema context for LLM prompt injection.
    
    This endpoint provides comprehensive information about database tables,
    including column descriptions, business meanings, and common query patterns.
    """
    try:
        context = rag_service.get_schema_context(table_name)
        return SchemaContextResponse(context=context)
    except Exception as e:
        logger.error(f"Error getting schema context: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/search", response_model=SearchResponse)
async def search_data(
    request: SearchRequest,
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Search table data with optional text search and filters.
    
    Example:
    ```json
    {
      "table_name": "conv_test_pivot_queue_sim",
      "search_term": "low yield",
      "filters": {"outcome": "PLACED"},
      "limit": 10
    }
    ```
    """
    try:
        results = rag_service.search_data(
            table_name=request.table_name,
            search_term=request.search_term,
            filters=request.filters,
            limit=request.limit
        )
        
        formatted = rag_service.format_results_for_llm(results, max_rows=5)
        
        return SearchResponse(
            results=results,
            count=len(results),
            formatted=formatted
        )
    except Exception as e:
        logger.error(f"Error searching data: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/query", response_model=ExecuteQueryResponse)
async def execute_query(
    request: ExecuteQueryRequest,
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Execute a custom SQL query.
    
    ⚠️ Use with caution - only SELECT queries are recommended.
    
    Example:
    ```json
    {
      "sql": "SELECT * FROM conv_test_pivot_queue_sim WHERE p1_yield < :threshold FETCH FIRST 5 ROWS ONLY",
      "params": {"threshold": 85}
    }
    ```
    """
    try:
        # Basic SQL injection protection - only allow SELECT
        if not request.sql.strip().upper().startswith("SELECT"):
            raise HTTPException(
                status_code=400,
                detail="Only SELECT queries are allowed"
            )
        
        results = rag_service.execute_query(request.sql, request.params)
        
        return ExecuteQueryResponse(
            results=results,
            count=len(results)
        )
    except Exception as e:
        logger.error(f"Error executing query: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/statistics/{table_name}", response_model=StatisticsResponse)
async def get_statistics(
    table_name: str,
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Get statistical summary of a table.
    
    Returns row counts and statistics for aggregatable columns (averages, min, max, stddev).
    """
    try:
        stats = rag_service.get_statistics(table_name)
        
        return StatisticsResponse(
            table_name=table_name,
            statistics=stats
        )
    except Exception as e:
        logger.error(f"Error getting statistics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tables", response_model=Dict[str, Any])
async def list_tables(
    current_user: UserResponse = Depends(get_current_user)
):
    """
    List all available tables in the metadata.
    
    Returns table names, descriptions, and row counts.
    """
    try:
        if not rag_service.metadata:
            return {"tables": {}}
        
        tables_info = {}
        for table_name, table_data in rag_service.metadata.get("tables", {}).items():
            tables_info[table_name] = {
                "description": table_data.get("description"),
                "row_count": table_data.get("row_count"),
                "primary_key": table_data.get("primary_key"),
                "column_count": len(table_data.get("columns", {}))
            }
        
        return {"tables": tables_info}
    except Exception as e:
        logger.error(f"Error listing tables: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/columns/{table_name}", response_model=Dict[str, Any])
async def get_columns(
    table_name: str,
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Get column information for a specific table.
    
    Returns column names, types, descriptions, and metadata.
    """
    try:
        table_info = rag_service.get_table_info(table_name)
        
        if not table_info:
            raise HTTPException(status_code=404, detail=f"Table '{table_name}' not found")
        
        return {
            "table_name": table_name,
            "columns": table_info.get("columns", {}),
            "searchable_columns": rag_service.get_searchable_columns(table_name),
            "aggregatable_columns": rag_service.get_aggregatable_columns(table_name)
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting columns: {e}")
        raise HTTPException(status_code=500, detail=str(e))

