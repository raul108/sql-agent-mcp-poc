"""
SQL Safety Validator

Enforces read-only operations and blocks dangerous SQL commands.
Critical for POC safety requirements - prevents accidental data modifications.

Blocked Operations:
- DROP (tables, databases, schemas)
- DELETE (remove data)
- ALTER (modify structure)
- TRUNCATE (remove all data)
- UPDATE (modify data)
- INSERT (add data)
- MERGE (upsert data)
- CREATE (create objects)

Only SELECT queries are allowed.
"""

import re
from typing import Tuple, List


class SQLValidator:
    """
    Validates SQL queries for safety before execution.
    
    Implements read-only enforcement by blocking all data modification
    and schema alteration commands.
    """
    
    # Dangerous SQL keywords that modify data or schema
    DANGEROUS_KEYWORDS = [
        'DROP',
        'DELETE',
        'TRUNCATE',
        'UPDATE',
        'INSERT',
        'MERGE',
        'ALTER',
        'CREATE',
        'REPLACE',
        'GRANT',
        'REVOKE',
    ]
    
    # Dangerous SQL patterns (regex)
    DANGEROUS_PATTERNS = [
        r'\bDROP\s+(TABLE|DATABASE|SCHEMA|VIEW|INDEX)',
        r'\bDELETE\s+FROM\b',
        r'\bTRUNCATE\s+TABLE\b',
        r'\bUPDATE\s+\w+\s+SET\b',
        r'\bINSERT\s+INTO\b',
        r'\bMERGE\s+INTO\b',
        r'\bALTER\s+(TABLE|DATABASE|SCHEMA)',
        r'\bCREATE\s+(TABLE|DATABASE|SCHEMA|VIEW|INDEX)',
        r'\bREPLACE\s+INTO\b',
        r'\bGRANT\s+',
        r'\bREVOKE\s+',
    ]
    
    def __init__(self):
        """Initialize the SQL validator."""
        pass
    
    def validate(self, sql: str) -> Tuple[bool, str, List[str]]:
        """
        Validate SQL query for safety.
        
        Args:
            sql: SQL query string to validate
            
        Returns:
            Tuple containing:
                - is_valid (bool): True if query is safe, False otherwise
                - message (str): Validation message
                - violations (list): List of detected violations
        
        Example:
            >>> validator = SQLValidator()
            >>> is_valid, msg, violations = validator.validate("SELECT * FROM CUSTOMER")
            >>> print(is_valid)  # True
            
            >>> is_valid, msg, violations = validator.validate("DROP TABLE CUSTOMER")
            >>> print(is_valid)  # False
            >>> print(violations)  # ['DROP']
        """
        if not sql or not sql.strip():
            return False, "Empty SQL query", []
        
        # Normalize SQL for checking (uppercase, remove extra spaces)
        sql_normalized = ' '.join(sql.upper().split())
        
        violations = []
        
        # Check for dangerous keywords
        for keyword in self.DANGEROUS_KEYWORDS:
            if re.search(r'\b' + keyword + r'\b', sql_normalized):
                violations.append(keyword)
        
        # Check for dangerous patterns
        for pattern in self.DANGEROUS_PATTERNS:
            if re.search(pattern, sql_normalized, re.IGNORECASE):
                match = re.search(pattern, sql_normalized, re.IGNORECASE)
                if match and match.group(0) not in violations:
                    violations.append(match.group(0))
        
        # Determine if valid
        if violations:
            violation_list = ', '.join(violations)
            message = f"❌ BLOCKED: Query contains dangerous operations: {violation_list}"
            return False, message, violations
        
        # Additional check: ensure query starts with SELECT (or WITH for CTEs)
        first_word = sql_normalized.split()[0] if sql_normalized else ""
        if first_word not in ['SELECT', 'WITH', 'SHOW', 'DESCRIBE', 'DESC', 'EXPLAIN']:
            return False, f"❌ BLOCKED: Only SELECT queries are allowed. Found: {first_word}", [first_word]
        
        return True, "✓ Query is safe to execute", []
    
    def is_read_only(self, sql: str) -> bool:
        """
        Quick check if SQL is read-only.
        
        Args:
            sql: SQL query string
            
        Returns:
            bool: True if query is read-only, False otherwise
        """
        is_valid, _, _ = self.validate(sql)
        return is_valid
    
    def get_violation_report(self, sql: str) -> str:
        """
        Get detailed violation report for a SQL query.
        
        Args:
            sql: SQL query string
            
        Returns:
            str: Formatted violation report
        """
        is_valid, message, violations = self.validate(sql)
        
        if is_valid:
            return f"✓ SAFE: {message}"
        
        report = [
            "=" * 60,
            "SQL SAFETY VIOLATION DETECTED",
            "=" * 60,
            f"Query: {sql[:100]}{'...' if len(sql) > 100 else ''}",
            f"\nViolations Found: {len(violations)}",
        ]
        
        for i, violation in enumerate(violations, 1):
            report.append(f"  {i}. {violation}")
        
        report.extend([
            f"\nReason: {message}",
            "\n⚠️  Only SELECT queries are allowed for safety.",
            "=" * 60,
        ])
        
        return '\n'.join(report)
