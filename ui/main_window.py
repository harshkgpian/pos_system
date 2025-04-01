"""Main window for the POS application."""

import logging
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QPushButton, QStackedWidget, QLabel, QFrame, QApplication
)
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QIcon, QFont

# Add parent directory to path to allow relative imports
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent))

from core.auth import get_current_session, logout, Permission
from ui.login_screen import LoginScreen
from ui.screens.sales import SalesScreen
from ui.screens.inventory import InventoryScreen
from ui.screens.admin import AdminScreen


class MainWindow(QMainWindow):
    """Main window for the POS application."""
    
    def __init__(self):
        super().__init__()
        self.setup_ui()
        
        # Start with login screen
        self.show_login_screen()
    
    def setup_ui(self):
        """Set up the main window UI."""
        # Window properties
        self.setWindowTitle("Infoware POS System")
        self.setMinimumSize(1024, 768)
        
        # Central widget
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        
        # Main layout
        self.main_layout = QHBoxLayout(self.central_widget)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)
        
        # Sidebar
        self.sidebar = QFrame()
        self.sidebar.setMaximumWidth(220)
        self.sidebar.setMinimumWidth(220)
        self.sidebar.setStyleSheet("""
            QFrame {
                background-color: #2c3e50;
                color: white;
            }
            QPushButton {
                color: white;
                border: none;
                text-align: left;
                padding: 10px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #34495e;
            }
            QPushButton:pressed {
                background-color: #1abc9c;
            }
            QPushButton:checked {
                background-color: #16a085;
                border-left: 4px solid #1abc9c;
            }
        """)
        
        # Sidebar layout
        self.sidebar_layout = QVBoxLayout(self.sidebar)
        self.sidebar_layout.setContentsMargins(0, 0, 0, 0)
        self.sidebar_layout.setSpacing(0)
        
        # App title in sidebar
        self.title_label = QLabel("Infoware POS")
        self.title_label.setAlignment(Qt.AlignCenter)
        self.title_label.setStyleSheet("""
            font-size: 18px;
            font-weight: bold;
            padding: 20px;
            background-color: #1abc9c;
        """)
        self.sidebar_layout.addWidget(self.title_label)
        
        # User info
        self.user_frame = QFrame()
        self.user_frame.setMaximumHeight(80)
        self.user_frame.setMinimumHeight(80)
        self.user_frame.setStyleSheet("background-color: #34495e;")
        
        user_layout = QVBoxLayout(self.user_frame)
        self.user_name_label = QLabel("Not logged in")
        self.user_role_label = QLabel("")
        self.user_name_label.setStyleSheet("font-size: 14px; font-weight: bold;")
        self.user_role_label.setStyleSheet("font-size: 12px;")
        
        user_layout.addWidget(self.user_name_label)
        user_layout.addWidget(self.user_role_label)
        
        self.sidebar_layout.addWidget(self.user_frame)
        
        # Navigation buttons
        self.nav_buttons = {}
        
        # Sales button
        self.nav_buttons['sales'] = QPushButton("Sales")
        self.nav_buttons['sales'].setIcon(QIcon.fromTheme("document-save"))
        self.nav_buttons['sales'].setIconSize(QSize(24, 24))
        self.nav_buttons['sales'].setCheckable(True)
        self.nav_buttons['sales'].clicked.connect(lambda: self.show_screen('sales'))
        
        # Inventory button
        self.nav_buttons['inventory'] = QPushButton("Inventory")
        self.nav_buttons['inventory'].setIcon(QIcon.fromTheme("package"))
        self.nav_buttons['inventory'].setIconSize(QSize(24, 24))
        self.nav_buttons['inventory'].setCheckable(True)
        self.nav_buttons['inventory'].clicked.connect(lambda: self.show_screen('inventory'))
        
        # Admin button
        self.nav_buttons['admin'] = QPushButton("Administration")
        self.nav_buttons['admin'].setIcon(QIcon.fromTheme("preferences-system"))
        self.nav_buttons['admin'].setIconSize(QSize(24, 24))
        self.nav_buttons['admin'].setCheckable(True)
        self.nav_buttons['admin'].clicked.connect(lambda: self.show_screen('admin'))
        
        # Logout button
        self.logout_button = QPushButton("Logout")
        self.logout_button.setIcon(QIcon.fromTheme("system-log-out"))
        self.logout_button.setIconSize(QSize(24, 24))
        self.logout_button.clicked.connect(self.handle_logout)
        
        # Add navigation buttons to sidebar
        for btn in self.nav_buttons.values():
            self.sidebar_layout.addWidget(btn)
        
        self.sidebar_layout.addStretch(1)
        self.sidebar_layout.addWidget(self.logout_button)
        
        # Add sidebar to main layout
        self.main_layout.addWidget(self.sidebar)
        
        # Content area
        self.content_area = QStackedWidget()
        self.content_area.setStyleSheet("""
            background-color: #ecf0f1;
        """)
        self.main_layout.addWidget(self.content_area)
        
        # Create login screen
        self.login_screen = LoginScreen()
        self.login_screen.login_successful.connect(self.handle_login_success)
        
        # Hide sidebar initially (will show after login)
        self.sidebar.setVisible(False)
    
    def show_login_screen(self):
        """Show the login screen."""
        # Clear content area
        while self.content_area.count() > 0:
            widget = self.content_area.widget(0)
            self.content_area.removeWidget(widget)
        
        # Hide sidebar
        self.sidebar.setVisible(False)
        
        # Add login screen directly to content area
        self.content_area.addWidget(self.login_screen)
    
    def handle_login_success(self, user):
        """Handle successful login."""
        # Update user info
        self.user_name_label.setText(user.username)
        self.user_role_label.setText(f"Role: {user.role.capitalize()}")
        
        # Show sidebar
        self.sidebar.setVisible(True)
        
        # Update button visibility based on permissions
        session = get_current_session()
        
        self.nav_buttons['sales'].setVisible(
            Permission.SALES_VIEW in session.permissions
        )
        
        self.nav_buttons['inventory'].setVisible(
            Permission.INVENTORY_VIEW in session.permissions
        )
        
        self.nav_buttons['admin'].setVisible(
            Permission.USER_MANAGE in session.permissions
        )
        
        # Show sales screen by default
        self.show_screen('sales')
    
    def handle_logout(self):
        """Handle logout button click."""
        logout()
        self.show_login_screen()
    
    def show_screen(self, screen_name):
        """Show the specified screen."""
        # Clear content area
        while self.content_area.count() > 0:
            widget = self.content_area.widget(0)
            self.content_area.removeWidget(widget)
        
        # Update button states
        for name, btn in self.nav_buttons.items():
            btn.setChecked(name == screen_name)
        
        # Create and show the requested screen
        if screen_name == 'sales':
            screen = SalesScreen(self)
        elif screen_name == 'inventory':
            screen = InventoryScreen(self)
        elif screen_name == 'admin':
            screen = AdminScreen(self)
        else:
            return
        
        self.content_area.addWidget(screen)