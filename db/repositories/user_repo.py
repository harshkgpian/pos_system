"""User repository for database operations related to users."""

import logging
from typing import List, Optional, Tuple

# Add parent directory to path to allow relative imports
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent.parent))

from db.connection import get_connection
from db.models import User


def get_by_id(user_id: int) -> Optional[User]:
    """Get a user by ID."""
    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        
        query = "SELECT * FROM users WHERE id = %s"
        cursor.execute(query, (user_id,))
        
        result = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if result:
            return User(
                id=result['id'],
                username=result['username'],
                password_hash=result['password_hash'],
                role=result['role'],
                active=result['active'],
                created_at=result['created_at']
            )
        return None
        
    except Exception as e:
        logging.error(f"Error getting user by ID: {e}")
        return None


def get_by_username(username: str) -> Optional[User]:
    """Get a user by username."""
    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        
        query = "SELECT * FROM users WHERE username = %s"
        cursor.execute(query, (username,))
        
        result = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if result:
            return User(
                id=result['id'],
                username=result['username'],
                password_hash=result['password_hash'],
                role=result['role'],
                active=result['active'],
                created_at=result['created_at']
            )
        return None
        
    except Exception as e:
        logging.error(f"Error getting user by username: {e}")
        return None


def get_all() -> List[User]:
    """Get all users."""
    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        
        query = "SELECT * FROM users ORDER BY username"
        cursor.execute(query)
        
        results = cursor.fetchall()
        cursor.close()
        conn.close()
        
        users = []
        for result in results:
            users.append(User(
                id=result['id'],
                username=result['username'],
                password_hash=result['password_hash'],
                role=result['role'],
                active=result['active'],
                created_at=result['created_at']
            ))
        
        return users
        
    except Exception as e:
        logging.error(f"Error getting all users: {e}")
        return []


def create(user: User) -> Tuple[bool, Optional[int]]:
    """
    Create a new user.
    Returns a tuple of (success, user_id).
    """
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        query = """
            INSERT INTO users (username, password_hash, role, active)
            VALUES (%s, %s, %s, %s)
        """
        
        cursor.execute(query, (
            user.username,
            user.password_hash,
            user.role,
            user.active
        ))
        
        conn.commit()
        user_id = cursor.lastrowid
        
        cursor.close()
        conn.close()
        
        logging.info(f"Created user: {user.username} with ID {user_id}")
        return True, user_id
        
    except Exception as e:
        logging.error(f"Error creating user: {e}")
        return False, None


def update(user: User) -> bool:
    """Update an existing user."""
    try:
        if not user.id:
            logging.error("Cannot update user without ID")
            return False
        
        conn = get_connection()
        cursor = conn.cursor()
        
        query = """
            UPDATE users 
            SET username = %s, password_hash = %s, role = %s, active = %s
            WHERE id = %s
        """
        
        cursor.execute(query, (
            user.username,
            user.password_hash,
            user.role,
            user.active,
            user.id
        ))
        
        conn.commit()
        affected_rows = cursor.rowcount
        
        cursor.close()
        conn.close()
        
        if affected_rows > 0:
            logging.info(f"Updated user ID {user.id}")
            return True
        else:
            logging.warning(f"No user found with ID {user.id} to update")
            return False
        
    except Exception as e:
        logging.error(f"Error updating user: {e}")
        return False


def delete(user_id: int) -> bool:
    """Delete a user by ID."""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        query = "DELETE FROM users WHERE id = %s"
        cursor.execute(query, (user_id,))
        
        conn.commit()
        affected_rows = cursor.rowcount
        
        cursor.close()
        conn.close()
        
        if affected_rows > 0:
            logging.info(f"Deleted user ID {user_id}")
            return True
        else:
            logging.warning(f"No user found with ID {user_id} to delete")
            return False
        
    except Exception as e:
        logging.error(f"Error deleting user: {e}")
        return False