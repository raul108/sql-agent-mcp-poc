"""
Snowflake Database Tools

Provides utilities for interacting with Snowflake database:
1. SQL query execution
2. Auto-discovery of schema from INFORMATION_SCHEMA
3. Connection management
4. Schema caching for performance
"""

import snowflake.connector
from src.config import Config
from typing import Optional


class SnowflakeSQLTool:
    """
    Tool for executing SQL queries on Snowflake.
    
    Handles connection management, query execution, and automatic schema discovery.
    Schema information is cached to avoid repeated queries to INFORMATION_SCHEMA.
    """
    
    def __init__(self, config: Config):
        """Initialize the Snowflake tool."""
        self.config = config
        self.sf_config = config.get_snowflake_config()
        self._schema_cache: Optional[str] = None
    
    def _get_connection(self):
        """Create and return a Snowflake connection."""
        return snowflake.connector.connect(**self.sf_config)
    
    def execute_query(self, query: str) -> str:
        """Execute SQL query and return formatted results."""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute(query)
            
            results = cursor.fetchall()
            columns = [desc[0] for desc in cursor.description] if cursor.description else []
            
            cursor.close()
            conn.close()
            
            if not results:
                return "Query executed successfully. No results returned."
            
            formatted_results = [dict(zip(columns, row)) for row in results[:10]]
            
            if len(results) > 10:
                return f"Results (showing 10 of {len(results)} rows):\n{formatted_results}\n\nNote: Showing first 10 rows."
            
            return f"Results ({len(results)} rows):\n{formatted_results}"
            
        except Exception as e:
            return f"Error executing query: {str(e)}"
    
    def _discover_schema_from_snowflake(self) -> str:
        """Auto-discover schema from Snowflake INFORMATION_SCHEMA."""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            database = self.sf_config["database"]
            schema = self.sf_config["schema"]
            
            cursor.execute(f"""
                SELECT TABLE_NAME
                FROM {database}.INFORMATION_SCHEMA.TABLES
                WHERE TABLE_SCHEMA = '{schema}'
                AND TABLE_TYPE = 'BASE TABLE'
                ORDER BY TABLE_NAME
            """)
            
            tables = [row[0] for row in cursor.fetchall()]
            
            if not tables:
                cursor.close()
                conn.close()
                return f"No tables found in {database}.{schema}"
            
            schema_info = f"Database: {database}\nSchema: {schema}\n"
            schema_info += f"Tables ({len(tables)}):\n\n"
            
            for table_name in tables:
                cursor.execute(f"""
                    SELECT 
                        COLUMN_NAME,
                        DATA_TYPE,
                        IS_NULLABLE,
                        COLUMN_DEFAULT
                    FROM {database}.INFORMATION_SCHEMA.COLUMNS
                    WHERE TABLE_SCHEMA = '{schema}'
                    AND TABLE_NAME = '{table_name}'
                    ORDER BY ORDINAL_POSITION
                """)
                
                columns = cursor.fetchall()
                
                schema_info += f"Table: {table_name} ({len(columns)} columns)\n"
                schema_info += "Columns:\n"
                
                for col_name, data_type, is_nullable, default_val in columns:
                    nullable = " [NULL]" if is_nullable == "YES" else " [NOT NULL]"
                    schema_info += f"  - {col_name}: {data_type}{nullable}\n"
                
                schema_info += "\n"
            
            cursor.close()
            conn.close()
            
            return schema_info
            
        except Exception as e:
            return f"Error discovering schema: {str(e)}"
    
    def get_schema_info(self, use_cache: bool = True) -> str:
        """Get database schema information with optional caching."""
        if use_cache and self._schema_cache is not None:
            return self._schema_cache
        
        schema_info = self._discover_schema_from_snowflake()
        self._schema_cache = schema_info
        
        return schema_info
    
    def clear_schema_cache(self):
        """Clear the cached schema information to force re-discovery."""
        self._schema_cache = None
