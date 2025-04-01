"""Admin screen for user management and system settings."""

import logging
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, 
    QPushButton, QLineEdit, QTableWidget, QTableWidgetItem,
    QHeaderView, QComboBox, QMessageBox, QFrame, QDialog,
    QDialogButtonBox, QFormLayout, QCheckBox, QTabWidget
)
from PySide6.QtCore import Qt

# Add parent directory to path to allow relative imports
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent.parent))

from core.auth import Permission, hash_password
from ui.base_screen import BaseScreen
from db.models import User
from db.repositories import user_repo


class AdminScreen(BaseScreen):
    """Screen for system administration."""
    
    def __init__(self, parent=None):
        super().__init__(parent, required_permission=Permission.USER_MANAGE)
        
        # Refresh users on init
        self.refresh_users()
    
    def get_title(self):
        return "Administration"
    
    def setup_ui(self):
        """Set up the UI components."""
        # Create tabs
        tabs = QTabWidget()
        
        # Users tab
        users_tab = QWidget()
        tabs.addTab(users_tab, "User Management")
        
        # User management layout
        users_layout = QVBoxLayout(users_tab)
        
        # Controls
        controls_frame = QFrame()
        controls_frame.setFrameShape(QFrame.StyledPanel)
        controls_frame.setStyleSheet("background-color: white; border-radius: 5px;")
        
        controls_layout = QHBoxLayout(controls_frame)
        
        add_user_button = QPushButton("Add New User")
        add_user_button.setStyleSheet("background-color: #28a745; color: white;")
        add_user_button.clicked.connect(self.show_add_user_dialog)
        
        refresh_button = QPushButton("Refresh")
        refresh_button.clicked.connect(self.refresh_users)
        
        controls_layout.addWidget(add_user_button)
        controls_layout.addStretch(1)
        controls_layout.addWidget(refresh_button)
        
        users_layout.addWidget(controls_frame)
        
        # Users table
        self.users_table = QTableWidget(0, 5)  # 0 rows, 5 columns
        self.users_table.setHorizontalHeaderLabels([
            "ID", "Username", "Role", "Status", "Actions"
        ])
        
        # Set column widths
        self.users_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.users_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.users_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.users_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.users_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeToContents)
        
        self.users_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.users_table.setEditTriggers(QTableWidget.NoEditTriggers)
        
        users_layout.addWidget(self.users_table)
        
        # Add tabs to main layout
        self.main_layout.addWidget(tabs)
    
    def refresh_users(self):
        """Refresh the users table."""
        users = user_repo.get_all()
        
        self.users_table.setRowCount(0)
        
        for i, user in enumerate(users):
            self.users_table.insertRow(i)
            
            # ID
            id_item = QTableWidgetItem(str(user.id))
            id_item.setFlags(id_item.flags() & ~Qt.ItemIsEditable)
            self.users_table.setItem(i, 0, id_item)
            
            # Username
            username_item = QTableWidgetItem(user.username)
            username_item.setFlags(username_item.flags() & ~Qt.ItemIsEditable)
            self.users_table.setItem(i, 1, username_item)
            
            # Role
            role_item = QTableWidgetItem(user.role.capitalize())
            role_item.setFlags(role_item.flags() & ~Qt.ItemIsEditable)
            self.users_table.setItem(i, 2, role_item)
            
            # Status
            status_text = "Active" if user.active else "Inactive"
            status_item = QTableWidgetItem(status_text)
            status_item.setFlags(status_item.flags() & ~Qt.ItemIsEditable)
            
            if not user.active:
                status_item.setBackground(Qt.red)
                status_item.setForeground(Qt.white)
            else:
                status_item.setBackground(Qt.green)
                status_item.setForeground(Qt.black)
            
            self.users_table.setItem(i, 3, status_item)
            
            # Actions - only show for non-self users (prevent self-deletion)
            actions_widget = QWidget()
            actions_layout = QHBoxLayout(actions_widget)
            actions_layout.setContentsMargins(4, 2, 4, 2)
            actions_layout.setSpacing(4)
            
            current_user = self.get_current_user()
            
            # Don't allow editing the admin user if you're not the admin
            is_modifiable = (user.id != current_user.id) or (current_user.role == 'admin')
            
            if is_modifiable:
                edit_button = QPushButton("Edit")
                edit_button.setStyleSheet("background-color: #007bff; color: white;")
                edit_button.clicked.connect(lambda checked, uid=user.id: self.show_edit_user_dialog(uid))
                actions_layout.addWidget(edit_button)
                
                if user.active:
                    status_button = QPushButton("Deactivate")
                    status_button.setStyleSheet("background-color: #dc3545; color: white;")
                else:
                    status_button = QPushButton("Activate")
                    status_button.setStyleSheet("background-color: #28a745; color: white;")
                
                status_button.clicked.connect(lambda checked, uid=user.id, active=user.active: self.toggle_user_status(uid, active))
                actions_layout.addWidget(status_button)
                
                reset_pwd_button = QPushButton("Reset Password")
                reset_pwd_button.setStyleSheet("background-color: #ffc107; color: black;")
                reset_pwd_button.clicked.connect(lambda checked, uid=user.id: self.show_reset_password_dialog(uid))
                actions_layout.addWidget(reset_pwd_button)
            
            self.users_table.setCellWidget(i, 4, actions_widget)
    
    def show_add_user_dialog(self):
        """Show dialog to add a new user."""
        dialog = QDialog(self)
        dialog.setWindowTitle("Add New User")
        dialog.setMinimumWidth(350)
        
        layout = QVBoxLayout(dialog)
        
        form_layout = QFormLayout()
        
        # Username
        username_input = QLineEdit()
        username_input.setPlaceholderText("Required")
        form_layout.addRow("Username:", username_input)
        
        # Password
        password_input = QLineEdit()
        password_input.setEchoMode(QLineEdit.Password)
        password_input.setPlaceholderText("Required")
        form_layout.addRow("Password:", password_input)
        
        # Role
        role_combo = QComboBox()
        role_combo.addItems(["Cashier", "Manager", "Admin"])
        role_combo.setCurrentIndex(0)  # Default to Cashier
        form_layout.addRow("Role:", role_combo)
        
        # Active status
        active_checkbox = QCheckBox("Active")
        active_checkbox.setChecked(True)
        form_layout.addRow("Status:", active_checkbox)
        
        layout.addLayout(form_layout)
        
        # Buttons
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(dialog.accept)
        button_box.rejected.connect(dialog.reject)
        layout.addWidget(button_box)
        
        if dialog.exec() == QDialog.Accepted:
            username = username_input.text().strip()
            password = password_input.text()
            role = role_combo.currentText().lower()
            active = active_checkbox.isChecked()
            
            # Validate
            if not username:
                self.show_error("Validation Error", "Username is required.")
                return
            
            if not password:
                self.show_error("Validation Error", "Password is required.")
                return
            
            # Check if username exists
            existing_user = user_repo.get_by_username(username)
            if existing_user:
                self.show_error("Validation Error", f"Username '{username}' already exists.")
                return
            
            # Create user
            user = User(
                username=username,
                password_hash=hash_password(password),
                role=role,
                active=active
            )
            
            success, user_id = user_repo.create(user)
            
            if success:
                self.show_info("Success", f"User '{username}' created successfully.")
                self.refresh_users()
            else:
                self.show_error("Error", "Failed to create user.")
    
    def show_edit_user_dialog(self, user_id):
        """Show dialog to edit a user."""
        user = user_repo.get_by_id(user_id)
        
        if not user:
            self.show_error("Error", "User not found.")
            return
        
        dialog = QDialog(self)
        dialog.setWindowTitle(f"Reset Password: {user.username}")
        dialog.setMinimumWidth(350)
        
        layout = QVBoxLayout(dialog)
        
        layout.addWidget(QLabel(f"Reset password for user: {user.username}"))
        
        form_layout = QFormLayout()
        
        # New password
        new_password_input = QLineEdit()
        new_password_input.setEchoMode(QLineEdit.Password)
        new_password_input.setPlaceholderText("Required")
        form_layout.addRow("New Password:", new_password_input)
        
        # Confirm password
        confirm_password_input = QLineEdit()
        confirm_password_input.setEchoMode(QLineEdit.Password)
        confirm_password_input.setPlaceholderText("Required")
        form_layout.addRow("Confirm Password:", confirm_password_input)
        
        layout.addLayout(form_layout)
        
        # Buttons
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(dialog.accept)
        button_box.rejected.connect(dialog.reject)
        layout.addWidget(button_box)
        
        if dialog.exec() == QDialog.Accepted:
            new_password = new_password_input.text()
            confirm_password = confirm_password_input.text()
            
            # Validate
            if not new_password:
                self.show_error("Validation Error", "Password is required.")
                return
            
            if new_password != confirm_password:
                self.show_error("Validation Error", "Passwords do not match.")
                return
            
            # Update password
            user.password_hash = hash_password(new_password)
            
            success = user_repo.update(user)
            
            if success:
                self.show_info("Success", f"Password for '{user.username}' reset successfully.")
            else:
                self.show_error("Error", "Failed to reset password.")
            return
        
        dialog = QDialog(self)
        dialog.setWindowTitle(f"Edit User: {user.username}")
        dialog.setMinimumWidth(350)
        
        layout = QVBoxLayout(dialog)
        
        form_layout = QFormLayout()
        
        # Username
        username_input = QLineEdit(user.username)
        username_input.setPlaceholderText("Required")
        form_layout.addRow("Username:", username_input)
        
        # Role
        role_combo = QComboBox()
        role_combo.addItems(["Cashier", "Manager", "Admin"])
        
        # Set current role
        if user.role == "admin":
            role_combo.setCurrentIndex(2)
        elif user.role == "manager":
            role_combo.setCurrentIndex(1)
        else:
            role_combo.setCurrentIndex(0)
        
        form_layout.addRow("Role:", role_combo)
        
        # Active status
        active_checkbox = QCheckBox("Active")
        active_checkbox.setChecked(user.active)
        form_layout.addRow("Status:", active_checkbox)
        
        layout.addLayout(form_layout)
        
        # Buttons
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(dialog.accept)
        button_box.rejected.connect(dialog.reject)
        layout.addWidget(button_box)
        
        if dialog.exec() == QDialog.Accepted:
            new_username = username_input.text().strip()
            new_role = role_combo.currentText().lower()
            new_active = active_checkbox.isChecked()
            
            # Validate
            if not new_username:
                self.show_error("Validation Error", "Username is required.")
                return
            
            # Check if username exists and it's not the current user
            if new_username != user.username:
                existing_user = user_repo.get_by_username(new_username)
                if existing_user:
                    self.show_error("Validation Error", f"Username '{new_username}' already exists.")
                    return
            
            # Don't allow the last admin to be demoted or deactivated
            if user.role == "admin" and (new_role != "admin" or not new_active):
                # Count active admins
                users = user_repo.get_all()
                active_admins = sum(1 for u in users if u.role == "admin" and u.active)
                
                if active_admins <= 1:
                    self.show_error(
                        "Validation Error", 
                        "Cannot change the last active admin. Create another admin first."
                    )
                    return
            
            # Update user
            user.username = new_username
            user.role = new_role
            user.active = new_active
            
            success = user_repo.update(user)
            
            if success:
                self.show_info("Success", f"User '{user.username}' updated successfully.")
                self.refresh_users()
            else:
                self.show_error("Error", "Failed to update user.")
    
    def toggle_user_status(self, user_id, current_status):
        """Toggle user active status."""
        user = user_repo.get_by_id(user_id)
        
        if not user:
            self.show_error("Error", "User not found.")
            return
        
        # Don't allow deactivating the last admin
        if user.role == "admin" and current_status:
            # Count active admins
            users = user_repo.get_all()
            active_admins = sum(1 for u in users if u.role == "admin" and u.active)
            
            if active_admins <= 1:
                self.show_error(
                    "Error", 
                    "Cannot deactivate the last active admin. Create another admin first."
                )
                return
        
        # Update status
        user.active = not current_status
        
        success = user_repo.update(user)
        
        if success:
            status = "activated" if user.active else "deactivated"
            self.show_info("Success", f"User '{user.username}' {status} successfully.")
            self.refresh_users()
        else:
            self.show_error("Error", "Failed to update user status.")
    
    def show_reset_password_dialog(self, user_id):
        """Show dialog to reset user password."""
        user = user_repo.get_by_id(user_id)
        
        if not user:
            self.show_error("Error", "User not found.")