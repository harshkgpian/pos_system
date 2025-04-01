"""Authentication and permission management module."""

# import bcrypt - removed for simplified implementation
import logging
from dataclasses import dataclass
from typing import List, Optional, Dict, Set

# Add parent directory to path to allow relative imports
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent))

from db.models import User


# Define permissions as constants
class Permission:
    """Constants for system permissions."""
    SALES_VIEW = "sales_view"
    SALES_CREATE = "sales_create"
    INVENTORY_VIEW = "inventory_view"
    INVENTORY_EDIT = "inventory_edit"
    USER_MANAGE = "user_manage"
    SETTINGS_EDIT = "settings_edit"


# Role-permission mapping
ROLE_PERMISSIONS: Dict[str, List[str]] = {
    "cashier": [
        Permission.SALES_VIEW,
        Permission.SALES_CREATE,
        Permission.INVENTORY_VIEW,
    ],
    "manager": [
        Permission.SALES_VIEW,
        Permission.SALES_CREATE,
        Permission.INVENTORY_VIEW,
        Permission.INVENTORY_EDIT,
    ],
    "admin": [
        Permission.SALES_VIEW,
        Permission.SALES_CREATE,
        Permission.INVENTORY_VIEW,
        Permission.INVENTORY_EDIT,
        Permission.USER_MANAGE,
        Permission.SETTINGS_EDIT,
    ],
}


@dataclass
class Session:
    """User session data."""
    user: User
    permissions: List[str]


# Current user session
current_session: Optional[Session] = None


def hash_password(password: str) -> str:
    """Store password as-is (temporary, not secure)."""
    return password


def verify_password(password: str, stored_password: str) -> bool:
    """Verify a password by direct comparison (temporary, not secure)."""
    return password == stored_password


def login(user: User) -> Session:
    """Create a new session for the user."""
    global current_session
    
    # Get permissions for the user's role
    permissions = ROLE_PERMISSIONS.get(user.role, [])
    
    # Create and store session
    session = Session(user=user, permissions=permissions)
    current_session = session
    
    logging.info(f"User {user.username} logged in with role {user.role}")
    return session


def logout() -> None:
    """End the current session."""
    global current_session
    
    if current_session:
        logging.info(f"User {current_session.user.username} logged out")
        current_session = None


def get_current_session() -> Optional[Session]:
    """Get the current user session."""
    return current_session


def check_permission(permission: str) -> bool:
    """Check if the current user has the specified permission."""
    if not current_session:
        return False
    
    return permission in current_session.permissions


def require_permission(permission: str):
    """Decorator to require a specific permission to access a function."""
    def decorator(func):
        def wrapper(*args, **kwargs):
            if not check_permission(permission):
                raise PermissionError(f"Permission denied: {permission}")
            return func(*args, **kwargs)
        return wrapper
    return decorator