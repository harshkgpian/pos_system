"""Inventory screen for managing products."""

import logging
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, 
    QPushButton, QLineEdit, QTableWidget, QTableWidgetItem,
    QHeaderView, QMessageBox, QFrame, QDialog, QDoubleSpinBox,
    QDialogButtonBox, QFormLayout, QSpinBox
)
from PySide6.QtCore import Qt

# Add parent directory to path to allow relative imports
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent.parent))

from core.auth import Permission
from ui.base_screen import BaseScreen
from db.models import Product
from core.services import inventory_service


class InventoryScreen(BaseScreen):
    """Screen for managing inventory."""
    
    def __init__(self, parent=None):
        super().__init__(parent, required_permission=Permission.INVENTORY_VIEW)
        
        # Refresh products on init
        self.refresh_products()
    
    def get_title(self):
        return "Inventory Management"
    
    def setup_ui(self):
        """Set up the inventory screen UI."""
        # Main layout is already created in BaseScreen
        
        # Top section - search and controls
        self.create_top_section()
        
        # Products table
        self.create_products_table()
    
    def create_top_section(self):
        """Create the top section with search and controls."""
        top_frame = QFrame()
        top_frame.setFrameShape(QFrame.StyledPanel)
        top_frame.setStyleSheet("background-color: white; border-radius: 5px;")
        
        top_layout = QHBoxLayout(top_frame)
        
        # Search box
        search_layout = QHBoxLayout()
        search_layout.addWidget(QLabel("Search:"))
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search by name or barcode...")
        self.search_input.setMinimumWidth(300)
        self.search_input.returnPressed.connect(self.search_products)
        search_layout.addWidget(self.search_input)
        
        search_button = QPushButton("Search")
        search_button.clicked.connect(self.search_products)
        search_layout.addWidget(search_button)
        
        reset_button = QPushButton("Reset")
        reset_button.clicked.connect(self.refresh_products)
        search_layout.addWidget(reset_button)
        
        top_layout.addLayout(search_layout)
        
        top_layout.addStretch(1)
        
        # Add new product button (only visible for users with edit permission)
        if self.has_permission(Permission.INVENTORY_EDIT):
            add_product_button = QPushButton("Add New Product")
            add_product_button.setStyleSheet("background-color: #28a745; color: white;")
            add_product_button.clicked.connect(self.show_add_product_dialog)
            top_layout.addWidget(add_product_button)
        
        self.main_layout.addWidget(top_frame)
    
    def create_products_table(self):
        """Create the products table."""
        self.products_table = QTableWidget(0, 6)  # 0 rows, 6 columns
        self.products_table.setHorizontalHeaderLabels([
            "ID", "Barcode", "Name", "Price", "Quantity", "Actions"
        ])
        
        # Set column widths
        self.products_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.products_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.products_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.products_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.products_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeToContents)
        self.products_table.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeToContents)
        
        self.products_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.products_table.setEditTriggers(QTableWidget.NoEditTriggers)
        
        self.main_layout.addWidget(self.products_table)
    
    def refresh_products(self):
        """Refresh the products table with all products."""
        self.search_input.clear()
        products = inventory_service.get_all_products()
        self.display_products(products)
    
    def search_products(self):
        """Search for products and update the table."""
        search_term = self.search_input.text().strip()
        
        if not search_term:
            self.refresh_products()
            return
        
        products = inventory_service.search_products(search_term)
        self.display_products(products)
    
    def display_products(self, products):
        """Display products in the table."""
        self.products_table.setRowCount(0)
        
        for i, product in enumerate(products):
            self.products_table.insertRow(i)
            
            # ID
            id_item = QTableWidgetItem(str(product.id))
            id_item.setFlags(id_item.flags() & ~Qt.ItemIsEditable)
            self.products_table.setItem(i, 0, id_item)
            
            # Barcode
            barcode_item = QTableWidgetItem(product.barcode if product.barcode else "")
            barcode_item.setFlags(barcode_item.flags() & ~Qt.ItemIsEditable)
            self.products_table.setItem(i, 1, barcode_item)
            
            # Name
            name_item = QTableWidgetItem(product.name)
            name_item.setFlags(name_item.flags() & ~Qt.ItemIsEditable)
            self.products_table.setItem(i, 2, name_item)
            
            # Price
            price_item = QTableWidgetItem(f"${product.price:.2f}")
            price_item.setFlags(price_item.flags() & ~Qt.ItemIsEditable)
            self.products_table.setItem(i, 3, price_item)
            
            # Quantity
            qty_item = QTableWidgetItem(str(product.quantity))
            qty_item.setFlags(qty_item.flags() & ~Qt.ItemIsEditable)
            
            # Highlight low stock
            if product.quantity <= 10:
                qty_item.setBackground(Qt.red)
                qty_item.setForeground(Qt.white)
            
            self.products_table.setItem(i, 4, qty_item)
            
            # Actions
            actions_widget = QWidget()
            actions_layout = QHBoxLayout(actions_widget)
            actions_layout.setContentsMargins(4, 2, 4, 2)
            actions_layout.setSpacing(4)
            
            # Edit button
            if self.has_permission(Permission.INVENTORY_EDIT):
                edit_button = QPushButton("Edit")
                edit_button.setStyleSheet("background-color: #007bff; color: white;")
                edit_button.clicked.connect(lambda checked, pid=product.id: self.show_edit_product_dialog(pid))
                actions_layout.addWidget(edit_button)
                
                # Stock button
                stock_button = QPushButton("Stock")
                stock_button.setStyleSheet("background-color: #17a2b8; color: white;")
                stock_button.clicked.connect(lambda checked, pid=product.id: self.show_update_stock_dialog(pid))
                actions_layout.addWidget(stock_button)
                
                # Delete button
                delete_button = QPushButton("Delete")
                delete_button.setStyleSheet("background-color: #dc3545; color: white;")
                delete_button.clicked.connect(lambda checked, pid=product.id: self.confirm_delete_product(pid))
                actions_layout.addWidget(delete_button)
            
            self.products_table.setCellWidget(i, 5, actions_widget)
    
    def show_add_product_dialog(self):
        """Show dialog to add a new product."""
        if not self.has_permission(Permission.INVENTORY_EDIT):
            return
        
        dialog = QDialog(self)
        dialog.setWindowTitle("Add New Product")
        dialog.setMinimumWidth(400)
        
        layout = QVBoxLayout(dialog)
        
        form_layout = QFormLayout()
        
        # Barcode
        barcode_input = QLineEdit()
        form_layout.addRow("Barcode:", barcode_input)
        
        # Name
        name_input = QLineEdit()
        name_input.setPlaceholderText("Required")
        form_layout.addRow("Name:", name_input)
        
        # Price
        price_input = QDoubleSpinBox()
        price_input.setMinimum(0)
        price_input.setMaximum(99999.99)
        price_input.setDecimals(2)
        price_input.setValue(0)
        price_input.setPrefix("$")
        form_layout.addRow("Price:", price_input)
        
        # Quantity
        qty_input = QSpinBox()
        qty_input.setMinimum(0)
        qty_input.setMaximum(999999)
        qty_input.setValue(0)
        form_layout.addRow("Quantity:", qty_input)
        
        layout.addLayout(form_layout)
        
        # Buttons
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(dialog.accept)
        button_box.rejected.connect(dialog.reject)
        layout.addWidget(button_box)
        
        if dialog.exec() == QDialog.Accepted:
            # Create new product
            product = Product(
                barcode=barcode_input.text().strip() or None,
                name=name_input.text().strip(),
                price=price_input.value(),
                quantity=qty_input.value()
            )
            
            if not product.name:
                self.show_error("Validation Error", "Product name is required.")
                return
            
            success, product_id = inventory_service.create_product(product)
            
            if success:
                self.show_info("Success", f"Product '{product.name}' created successfully.")
                self.refresh_products()
            else:
                self.show_error("Error", "Failed to create product. Please try again.")
    
    def show_edit_product_dialog(self, product_id):
        """Show dialog to edit a product."""
        if not self.has_permission(Permission.INVENTORY_EDIT):
            return
        
        product = inventory_service.get_product_by_id(product_id)
        
        if not product:
            self.show_error("Error", "Product not found.")
            return
        
        dialog = QDialog(self)
        dialog.setWindowTitle(f"Edit Product: {product.name}")
        dialog.setMinimumWidth(400)
        
        layout = QVBoxLayout(dialog)
        
        form_layout = QFormLayout()
        
        # Barcode
        barcode_input = QLineEdit(product.barcode if product.barcode else "")
        form_layout.addRow("Barcode:", barcode_input)
        
        # Name
        name_input = QLineEdit(product.name)
        name_input.setPlaceholderText("Required")
        form_layout.addRow("Name:", name_input)
        
        # Price
        price_input = QDoubleSpinBox()
        price_input.setMinimum(0)
        price_input.setMaximum(99999.99)
        price_input.setDecimals(2)
        price_input.setValue(product.price)
        price_input.setPrefix("$")
        form_layout.addRow("Price:", price_input)
        
        # Quantity
        qty_input = QSpinBox()
        qty_input.setMinimum(0)
        qty_input.setMaximum(999999)
        qty_input.setValue(product.quantity)
        form_layout.addRow("Quantity:", qty_input)
        
        layout.addLayout(form_layout)
        
        # Buttons
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(dialog.accept)
        button_box.rejected.connect(dialog.reject)
        layout.addWidget(button_box)
        
        if dialog.exec() == QDialog.Accepted:
            # Update product
            product.barcode = barcode_input.text().strip() or None
            product.name = name_input.text().strip()
            product.price = price_input.value()
            product.quantity = qty_input.value()
            
            if not product.name:
                self.show_error("Validation Error", "Product name is required.")
                return
            
            success = inventory_service.update_product(product)
            
            if success:
                self.show_info("Success", f"Product '{product.name}' updated successfully.")
                self.refresh_products()
            else:
                self.show_error("Error", "Failed to update product. Please try again.")
    
    def show_update_stock_dialog(self, product_id):
        """Show dialog to update product stock."""
        if not self.has_permission(Permission.INVENTORY_EDIT):
            return
        
        product = inventory_service.get_product_by_id(product_id)
        
        if not product:
            self.show_error("Error", "Product not found.")
            return
        
        dialog = QDialog(self)
        dialog.setWindowTitle(f"Update Stock: {product.name}")
        dialog.setMinimumWidth(350)
        
        layout = QVBoxLayout(dialog)
        
        # Current stock
        layout.addWidget(QLabel(f"Current Stock: {product.quantity}"))
        
        # Add/remove layout
        form_layout = QFormLayout()
        
        qty_input = QSpinBox()
        qty_input.setMinimum(1)
        qty_input.setMaximum(9999)
        qty_input.setValue(1)
        form_layout.addRow("Quantity:", qty_input)
        
        layout.addLayout(form_layout)
        
        # Buttons
        buttons_layout = QHBoxLayout()
        
        add_button = QPushButton("Add Stock")
        add_button.setStyleSheet("background-color: #28a745; color: white;")
        add_button.clicked.connect(lambda: update_stock(True))
        
        remove_button = QPushButton("Remove Stock")
        remove_button.setStyleSheet("background-color: #dc3545; color: white;")
        remove_button.clicked.connect(lambda: update_stock(False))
        
        buttons_layout.addWidget(add_button)
        buttons_layout.addWidget(remove_button)
        
        layout.addLayout(buttons_layout)
        
        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(dialog.reject)
        layout.addWidget(cancel_button)
        
        def update_stock(is_add):
            quantity = qty_input.value()
            
            if is_add:
                # Add stock
                change = quantity
            else:
                # Remove stock (negative change)
                change = -quantity
                
                # Check if removing more than available
                if abs(change) > product.quantity:
                    self.show_error(
                        "Insufficient Stock", 
                        f"Cannot remove {quantity} items. Only {product.quantity} in stock."
                    )
                    return
            
            success = inventory_service.update_stock(product_id, change)
            
            if success:
                action = "added to" if is_add else "removed from"
                self.show_info(
                    "Stock Updated",
                    f"{quantity} items {action} {product.name}"
                )
                dialog.accept()
                self.refresh_products()
            else:
                self.show_error("Error", "Failed to update stock.")
        
        dialog.exec()
    
    def confirm_delete_product(self, product_id):
        """Confirm and delete a product."""
        if not self.has_permission(Permission.INVENTORY_EDIT):
            return
        
        product = inventory_service.get_product_by_id(product_id)
        
        if not product:
            self.show_error("Error", "Product not found.")
            return
        
        confirm = self.show_question(
            "Confirm Delete",
            f"Are you sure you want to delete '{product.name}'?\nThis action cannot be undone."
        )
        
        if confirm:
            success = inventory_service.delete_product(product_id)
            
            if success:
                self.show_info("Success", f"Product '{product.name}' deleted successfully.")
                self.refresh_products()
            else:
                self.show_error("Error", "Failed to delete product. It may be referenced by sales.")