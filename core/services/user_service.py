# Change from:
# from ...db.repositories.user_repo import UserRepository

# To:
from db.repositories.user_repo import UserRepository
from db.models import User
from core.auth import Auth

class UserService:
    """Service class for user management operations"""
    
    def __init__(self):
        self.user_repo = UserRepository()
    
    def authenticate(self, username, password):
        """Authenticate a user with username and password
        
        Args:
            username (str): Username
            password (str): Plain text password
            
        Returns:
            dict: User data if authentication successful, None otherwise
        """
        user = self.user_repo.get_by_username(username)
        if not user:
            return None
        
        # Check if user is active
        if not user.active:
            return None
        
        # Verify password
        if not Auth.verify_password(user.password_hash, password):
            return None
        
        # Update last login
        self.user_repo.update_last_login(user.id)
        
        # Return user data (excluding password)
        user_data = user.to_dict()
        user_data.pop('password_hash', None)
        return user_data
    
    def get_all_users(self):
        """Get all users
        
        Returns:
            list: List of users (without password hashes)
        """
        users = self.user_repo.get_all()
        # Remove password hashes
        for user in users:
            user.password_hash = None
        return users
    
    def get_user_by_id(self, user_id):
        """Get a user by ID
        
        Args:
            user_id (int): User ID
            
        Returns:
            User: User object without password hash, or None if not found
        """
        user = self.user_repo.get_by_id(user_id)
        if user:
            user.password_hash = None
        return user
    
    def create_user(self, user_data):
        """Create a new user
        
        Args:
            user_data (dict): User data including username, password, role, etc.
            
        Returns:
            User: Created user without password hash, or None if failed
        """
        # Check if username already exists
        existing_user = self.user_repo.get_by_username(user_data.get('username'))
        if existing_user:
            raise ValueError(f"Username '{user_data.get('username')}' already exists")
        
        # Hash password
        password_hash = Auth.hash_password(user_data.get('password'))
        
        # Create user object
        user = User(
            username=user_data.get('username'),
            password_hash=password_hash,
            role=user_data.get('role'),
            full_name=user_data.get('full_name'),
            active=user_data.get('active', True)
        )
        
        # Save to database
        created_user = self.user_repo.create(user)
        
        # Remove password hash before returning
        created_user.password_hash = None
        return created_user
    
    def update_user(self, user_id, user_data):
        """Update an existing user
        
        Args:
            user_id (int): ID of the user to update
            user_data (dict): Updated user data
            
        Returns:
            User: Updated user without password hash, or None if not found
        """
        existing_user = self.user_repo.get_by_id(user_id)
        if not existing_user:
            return None
        
        # Check username uniqueness if changing
        if 'username' in user_data and user_data['username'] != existing_user.username:
            username_check = self.user_repo.get_by_username(user_data['username'])
            if username_check and username_check.id != user_id:
                raise ValueError(f"Username '{user_data['username']}' already exists")
            existing_user.username = user_data['username']
        
        # Update fields
        if 'role' in user_data:
            existing_user.role = user_data['role']
        if 'full_name' in user_data:
            existing_user.full_name = user_data['full_name']
        if 'active' in user_data:
            existing_user.active = user_data['active']
        
        # Update in database
        updated_user = self.user_repo.update(existing_user)
        
        # Update password if provided
        if 'password' in user_data and user_data['password']:
            password_hash = Auth.hash_password(user_data['password'])
            self.user_repo.update_password(user_id, password_hash)
        
        # Remove password hash before returning
        updated_user.password_hash = None
        return updated_user
    
    def delete_user(self, user_id):
        """Delete a user
        
        Args:
            user_id (int): ID of the user to delete
            
        Returns:
            bool: True if successful, False otherwise
        """
        existing_user = self.user_repo.get_by_id(user_id)
        if not existing_user:
            return False
        
        try:
            self.user_repo.delete(user_id)
            return True
        except Exception as e:
            print(f"Error deleting user: {e}")
            return False