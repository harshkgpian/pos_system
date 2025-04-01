"""Database connection and initialization module."""

import os
import logging
import mysql.connector
from mysql.connector import pooling
from pathlib import Path

# Add parent directory to path to allow relative imports
import sys
sys.path.append(str(Path(__file__).resolve().parent.parent))

from config import get_config

# Get database configuration
config = get_config()
db_config = config['db']

# Connection pool
connection_pool = None


def initialize_database():
    """
    Initialize the database - create it if it doesn't exist,
    and run the schema.sql script to set up tables.
    """
    try:
        # First connect without specifying database to create it if needed
        conn = mysql.connector.connect(
            host=db_config['host'],
            port=db_config['port'],
            user=db_config['user'],
            password=db_config['password']
        )
        
        cursor = conn.cursor()
        
        # Create database if it doesn't exist
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {db_config['database']}")
        cursor.execute(f"USE {db_config['database']}")
        
        # Execute schema.sql to create tables
        schema_path = Path(__file__).resolve().parent / 'schema.sql'
        
        if schema_path.exists():
            with open(schema_path, 'r') as f:
                schema_sql = f.read()
            
            # Split by semicolon to execute multiple statements
            for statement in schema_sql.split(';'):
                if statement.strip():
                    cursor.execute(statement)
            
            conn.commit()
            logging.info("Database schema initialized successfully.")
        else:
            logging.warning("Schema file not found. Database structure might be incomplete.")
        
        cursor.close()
        conn.close()
    
    except Exception as e:
        logging.error(f"Error initializing database: {e}")
        raise


def create_pool():
    """Create a connection pool for database access."""
    global connection_pool
    
    if connection_pool is None:
        try:
            connection_pool = pooling.MySQLConnectionPool(
                pool_name="pos_pool",
                pool_size=5,
                **db_config
            )
            logging.info("Database connection pool created successfully.")
        except Exception as e:
            logging.error(f"Error creating connection pool: {e}")
            raise


def get_connection():
    """Get a connection from the pool."""
    if connection_pool is None:
        create_pool()
    
    try:
        return connection_pool.get_connection()
    except Exception as e:
        logging.error(f"Error getting connection from pool: {e}")
        raise


def init():
    """Initialize the database module."""
    initialize_database()
    create_pool()