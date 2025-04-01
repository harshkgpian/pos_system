"""Login screen for user authentication."""

import logging
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
    QPushButton, QFormLayout, QFrame
)
from PySide6.QtCore import Qt, Signal

# Add parent directory to path to allow relative imports
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent))

from db.repositories import user_repo
from core.auth import verify_password, login


class LoginScreen(QWidget):
    """Login screen for user authentication."""
    
    # Signal to emit when login is successful
    login_successful = Signal(object)  # Pass user object
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.setup_ui()
    
    def setup_ui(self):
        """Set up the login screen UI."""
        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        # Create a centered frame for the login form
        form_frame = QFrame(self)
        form_frame.setFrameShape(QFrame.StyledPanel)
        form_frame.setStyleSheet("""
            QFrame {
                background-color: white;
                border-radius: 10px;
                border: 1px solid #ddd;
            }
        """)
        form_frame.setMaximumWidth(400)
        form_frame.setMaximumHeight(300)
        
        # Add the frame to the main layout with centering
        main_layout.addStretch(1)
        main_layout.addWidget(form_frame, 0, Qt.AlignCenter)
        main_layout.addStretch(1)
        
        # Form layout inside the frame
        form_layout = QVBoxLayout(form_frame)
        form_layout.setContentsMargins(30, 30, 30, 30)
        form_layout.setSpacing(15)
        
        # Title
        title_label = QLabel("Infoware POS Login")
        title_label.setStyleSheet("font-size: 18pt; font-weight: bold; color: #333;")
        title_label.setAlignment(Qt.AlignCenter)
        form_layout.addWidget(title_label)
        
        # Form fields
        fields_layout = QFormLayout()
        fields_layout.setSpacing(10)
        
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Enter username")
        self.username_input.setMinimumHeight(35)
        fields_layout.addRow("Username:", self.username_input)
        
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Enter password")
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.setMinimumHeight(35)
        fields_layout.addRow("Password:", self.password_input)
        
        form_layout.addLayout(fields_layout)
        
        # Login button
        self.login_button = QPushButton("Login")
        self.login_button.setMinimumHeight(40)
        self.login_button.setStyleSheet("""
            QPushButton {
                background-color: #0078D7;
                color: white;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #0063B1;
            }
            QPushButton:pressed {
                background-color: #004E8C;
            }
        """)
        self.login_button.clicked.connect(self.handle_login)
        form_layout.addWidget(self.login_button)
        
        # Error message label
        self.error_label = QLabel("")
        self.error_label.setStyleSheet("color: red;")
        self.error_label.setAlignment(Qt.AlignCenter)
        self.error_label.setVisible(False)
        form_layout.addWidget(self.error_label)
        
        # Connect enter key to login
        self.username_input.returnPressed.connect(self.password_input.setFocus)
        self.password_input.returnPressed.connect(self.handle_login)
    
    def handle_login(self):
        """Handle the login button click."""
        username = self.username_input.text().strip()
        password = self.password_input.text()
        
        if not username or not password:
            self.show_error("Please enter both username and password.")
            return
        
        # Get user from database
        user = user_repo.get_by_username(username)
        
        if not user:
            self.show_error("Invalid username or password.")
            return
        
        if not user.active:
            self.show_error("This account is disabled.")
            return
        
        # Verify password
        if not verify_password(password, user.password_hash):
            self.show_error("Invalid username or password.")
            return
        
        # Create session
        session = login(user)
        logging.info(f"User logged in: {username}")
        
        # Emit signal for successful login
        self.login_successful.emit(user)
        
        # Clear inputs
        self.username_input.clear()
        self.password_input.clear()
        self.error_label.setVisible(False)
    
    def show_error(self, message):
        """Show an error message on the login form."""
        self.error_label.setText(message)
        self.error_label.setVisible(True)