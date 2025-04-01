"""Base screen class for all UI screens."""

from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QMessageBox
from PySide6.QtCore import Qt

# Add parent directory to path to allow relative imports
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent))

from core.auth import get_current_session, check_permission


class BaseScreen(QWidget):
    """Base class for all application screens."""
    
    def __init__(self, parent=None, required_permission=None):
        """
        Initialize the base screen.
        
        Args:
            parent: The parent widget
            required_permission: Permission required to access this screen
        """
        super().__init__(parent)
        self.parent = parent
        self.required_permission = required_permission
        
        # Check permissions
        if self.required_permission and not check_permission(self.required_permission):
            self.show_error("Permission Denied", 
                           "You don't have permission to access this screen.")
            # Return to previous screen or logout
            if parent and hasattr(parent, 'show_login_screen'):
                parent.show_login_screen()
            return
        
        # Set up the base layout
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(10, 10, 10, 10)
        self.main_layout.setSpacing(10)
        
        # Header label
        self.header_label = QLabel(self.get_title())
        self.header_label.setAlignment(Qt.AlignCenter)
        self.header_label.setStyleSheet("font-size: 18pt; margin-bottom: 10px;")
        self.main_layout.addWidget(self.header_label)
        
        # Initialize UI components
        self.setup_ui()
    
    def setup_ui(self):
        """Set up the UI components. To be implemented by subclasses."""
        pass
    
    def get_title(self):
        """Get the screen title. To be implemented by subclasses."""
        return "POS System"
    
    def get_current_user(self):
        """Get the current logged-in user."""
        session = get_current_session()
        if session:
            return session.user
        return None
    
    def has_permission(self, permission):
        """Check if the current user has a specific permission."""
        return check_permission(permission)
    
    def show_error(self, title, message):
        """Show an error message dialog."""
        QMessageBox.critical(self, title, message)
    
    def show_info(self, title, message):
        """Show an information message dialog."""
        QMessageBox.information(self, title, message)
    
    def show_warning(self, title, message):
        """Show a warning message dialog."""
        QMessageBox.warning(self, title, message)
    
    def show_question(self, title, message):
        """
        Show a yes/no question dialog.
        Returns True if the user clicked Yes, False otherwise.
        """
        reply = QMessageBox.question(
            self, title, message,
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        return reply == QMessageBox.Yes