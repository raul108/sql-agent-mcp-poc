"""
Configuration Management Module

Loads all configuration from environment variables (.env file).
No YAML files required - purely environment-based for security and simplicity.

Schema discovery is automatic from Snowflake INFORMATION_SCHEMA.
"""

import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class Config:
    """
    Centralized configuration manager for the SQL Agent.
    
    Loads all settings from environment variables for security.
    Schema is auto-discovered from Snowflake at runtime.
    """
    
    def __init__(self):
        """Initialize configuration from environment variables."""
        pass
    
    def get_snowflake_config(self):
        """
        Get Snowflake connection parameters from environment variables.
        
        Required environment variables:
            SNOWFLAKE_ACCOUNT - Account identifier
            SNOWFLAKE_USER - Username
            SNOWFLAKE_PASSWORD - Password
            SNOWFLAKE_DATABASE - Database name
            SNOWFLAKE_SCHEMA - Schema name
            SNOWFLAKE_WAREHOUSE - Warehouse name
            SNOWFLAKE_ROLE - User role
        
        Returns:
            dict: Snowflake connection configuration
        """
        required_vars = [
            'SNOWFLAKE_ACCOUNT', 'SNOWFLAKE_USER', 'SNOWFLAKE_PASSWORD',
            'SNOWFLAKE_DATABASE', 'SNOWFLAKE_SCHEMA', 'SNOWFLAKE_WAREHOUSE', 'SNOWFLAKE_ROLE'
        ]
        
        # Check if all required variables are set
        missing = [var for var in required_vars if not os.getenv(var)]
        if missing:
            raise ValueError(f"Missing required environment variables: {', '.join(missing)}")
        
        return {
            'account': os.getenv('SNOWFLAKE_ACCOUNT'),
            'user': os.getenv('SNOWFLAKE_USER'),
            'password': os.getenv('SNOWFLAKE_PASSWORD'),
            'database': os.getenv('SNOWFLAKE_DATABASE'),
            'schema': os.getenv('SNOWFLAKE_SCHEMA'),
            'warehouse': os.getenv('SNOWFLAKE_WAREHOUSE'),
            'role': os.getenv('SNOWFLAKE_ROLE')
        }
    
    def get_openai_config(self):
        """
        Get OpenAI API configuration from environment variables.
        
        Required environment variables:
            OPENAI_API_KEY - API key for authentication
            OPENAI_MODEL - Model to use (optional, defaults to gpt-4)
        
        Returns:
            dict: OpenAI configuration
        """
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            raise ValueError("Missing required environment variable: OPENAI_API_KEY")
        
        return {
            'api_key': api_key,
            'model': os.getenv('OPENAI_MODEL', 'gpt-4')
        }
