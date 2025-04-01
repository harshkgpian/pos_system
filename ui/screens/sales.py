"""Sales screen for processing transactions."""

import logging
from datetime import datetime
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, 
    QPushButton, QLineEdit, QTableWidget, QTableWidgetItem,
    QHeaderView, QComboBox, QMessageBox, QFrame, QDialog,
    QDialogButtonBox, QFormLayout, QDoubleSpinBox, QSpinBox
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QFont

# Add parent directory to path to allow relative imports
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent.parent))

from core.auth import Permission
from ui.base_screen import BaseScreen
from db.models import Sale, SaleItem, Product
from core.services import sales_service, inventory_service


class SalesScreen(BaseScreen):
    """Screen for processing sales transactions."""
    
    def __init__(self, parent=None):
        super().__init__(parent, required_permission=Permission.SALES_VIEW)
        
        # Current sale
        self.current_sale = Sale(user_id=self.get_current_user().id)
    
    def get_title(self):
        return "Sales"
    
    def setup_ui(self):
        """Set up the UI components."""
        # Main layout is already created in BaseScreen
        
        # Top section - search and add products
        self.create_top_section()
        
        # Middle section - cart/items table
        self.create_cart_section()
        
        # Bottom section - totals and payment
        self.create_payment_section()
        
        # Scan input gets focus
        self.search_input.setFocus()
    
    def create_top_section(self):
        """Create the top section with search and product info."""
        top_frame = QFrame()
        top_frame.setFrameShape(QFrame.StyledPanel)
        top_frame.setStyleSheet("background-color: white; border-radius: 5px;")
        
        top_layout = QGridLayout(top_frame)
        
        # Search/scan input
        search_label = QLabel("Scan Barcode or Search:")
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Scan barcode or search product...")
        self.search_input.setMinimumHeight(40)
        self.search_input.returnPressed.connect(self.handle_search)
        
        search_button = QPushButton("Search")
        search_button.setMinimumHeight(40)
        search_button.clicked.connect(self.handle_search)
        
        # Product info (hidden until product is selected)
        self.product_info_frame = QFrame()
        self.product_info_frame.setVisible(False)
        self.product_info_frame.setStyleSheet("background-color: #f8f9fa; padding: 10px; border-radius: 5px;")
        
        product_info_layout = QGridLayout(self.product_info_frame)
        
        self.product_name_label = QLabel("Product Name")
        self.product_name_label.setStyleSheet("font-size: 16px; font-weight: bold;")
        
        self.product_price_label = QLabel("$0.00")
        self.product_price_label.setStyleSheet("font-size: 16px;")
        
        self.product_stock_label = QLabel("In Stock: 0")
        
        self.quantity_input = QSpinBox()
        self.quantity_input.setMinimum(1)
        self.quantity_input.setMaximum(999)
        self.quantity_input.setValue(1)
        self.quantity_input.setMinimumHeight(30)
        
        add_to_cart_button = QPushButton("Add to Cart")
        add_to_cart_button.setStyleSheet("background-color: #28a745; color: white;")
        add_to_cart_button.setMinimumHeight(30)
        add_to_cart_button.clicked.connect(self.add_to_cart)
        
        # Layout for product info
        product_info_layout.addWidget(self.product_name_label, 0, 0, 1, 2)
        product_info_layout.addWidget(QLabel("Price:"), 1, 0)
        product_info_layout.addWidget(self.product_price_label, 1, 1)
        product_info_layout.addWidget(self.product_stock_label, 2, 0)
        product_info_layout.addWidget(QLabel("Quantity:"), 3, 0)
        product_info_layout.addWidget(self.quantity_input, 3, 1)
        product_info_layout.addWidget(add_to_cart_button, 4, 0, 1, 2)
        
        # Add all to top layout
        top_layout.addWidget(search_label, 0, 0)
        top_layout.addWidget(self.search_input, 0, 1)
        top_layout.addWidget(search_button, 0, 2)
        top_layout.addWidget(self.product_info_frame, 1, 0, 1, 3)
        
        self.main_layout.addWidget(top_frame)
    
    def create_cart_section(self):
        """Create the cart/items table section."""
        cart_frame = QFrame()
        cart_frame.setFrameShape(QFrame.StyledPanel)
        cart_frame.setStyleSheet("background-color: white; border-radius: 5px;")
        
        cart_layout = QVBoxLayout(cart_frame)
        
        # Cart title
        cart_title = QLabel("Current Sale")
        cart_title.setStyleSheet("font-size: 16px; font-weight: bold;")
        cart_layout.addWidget(cart_title)
        
        # Cart table
        self.cart_table = QTableWidget(0, 5)  # 0 rows, 5 columns
        self.cart_table.setHorizontalHeaderLabels(["Product", "Price", "Quantity", "Total", "Actions"])
        self.cart_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.cart_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.cart_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.cart_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.cart_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeToContents)
        self.cart_table.setSelectionBehavior(QTableWidget.SelectRows)
        
        cart_layout.addWidget(self.cart_table)
        
        # Add to main layout
        self.main_layout.addWidget(cart_frame)
    
    def create_payment_section(self):
        """Create the payment section with totals and checkout."""
        payment_frame = QFrame()
        payment_frame.setFrameShape(QFrame.StyledPanel)
        payment_frame.setStyleSheet("background-color: white; border-radius: 5px;")
        payment_frame.setMaximumHeight(150)
        
        payment_layout = QHBoxLayout(payment_frame)
        
        # Left side - totals
        totals_layout = QFormLayout()
        
        self.subtotal_label = QLabel("$0.00")
        self.subtotal_label.setStyleSheet("font-size: 16px;")
        
        self.total_label = QLabel("$0.00")
        self.total_label.setStyleSheet("font-size: 24px; font-weight: bold; color: #28a745;")
        
        totals_layout.addRow("Subtotal:", self.subtotal_label)
        totals_layout.addRow("Total:", self.total_label)
        
        # Right side - payment buttons
        payment_buttons_layout = QVBoxLayout()
        
        # Payment method
        payment_method_layout = QHBoxLayout()
        payment_method_layout.addWidget(QLabel("Payment Method:"))
        
        self.payment_method = QComboBox()
        self.payment_method.addItems(["Cash", "Card"])
        payment_method_layout.addWidget(self.payment_method)
        
        payment_buttons_layout.addLayout(payment_method_layout)
        
        # Action buttons
        action_buttons_layout = QHBoxLayout()
        
        cancel_sale_button = QPushButton("Cancel Sale")
        cancel_sale_button.setStyleSheet("background-color: #dc3545; color: white;")
        cancel_sale_button.clicked.connect(self.cancel_sale)
        
        self.checkout_button = QPushButton("Complete Sale")
        self.checkout_button.setStyleSheet("background-color: #28a745; color: white; font-size: 16px;")
        self.checkout_button.setMinimumHeight(50)
        self.checkout_button.clicked.connect(self.complete_sale)
        self.checkout_button.setEnabled(False)  # Disabled until items are added
        
        action_buttons_layout.addWidget(cancel_sale_button)
        action_buttons_layout.addWidget(self.checkout_button)
        
        payment_buttons_layout.addLayout(action_buttons_layout)
        
        # Add to payment layout
        payment_layout.addLayout(totals_layout, 1)
        payment_layout.addLayout(payment_buttons_layout, 2)
        
        # Add to main layout
        self.main_layout.addWidget(payment_frame)
    
    def handle_search(self):
        """Handle product search by barcode or keyword."""
        search_term = self.search_input.text().strip()
        
        if not search_term:
            return
        
        # Try to find by barcode first
        product = inventory_service.get_product_by_barcode(search_term)
        
        # If not found, search by name
        if not product:
            products = inventory_service.search_products(search_term)
            
            if not products:
                self.show_error("Product not found", "No products match your search.")
                return
            
            if len(products) == 1:
                # If only one product found, use it
                product = products[0]
            else:
                # If multiple products, show selection dialog
                product = self.show_product_selection_dialog(products)
        
        if product:
            self.display_product(product)
    
    def display_product(self, product):
        """Display product information in the UI."""
        self.current_product = product
        
        # Update product info display
        self.product_name_label.setText(product.name)
        self.product_price_label.setText(f"${product.price:.2f}")
        self.product_stock_label.setText(f"In Stock: {product.quantity}")
        
        # Reset quantity input
        self.quantity_input.setValue(1)
        self.quantity_input.setMaximum(product.quantity)
        
        # Show product info
        self.product_info_frame.setVisible(True)
        
        # Clear search input
        self.search_input.clear()
    
    def add_to_cart(self):
        """Add the current product to the cart."""
        if not hasattr(self, 'current_product'):
            return
        
        quantity = self.quantity_input.value()
        
        if quantity <= 0:
            self.show_error("Invalid quantity", "Quantity must be greater than zero.")
            return
        
        if quantity > self.current_product.quantity:
            self.show_error("Insufficient stock", f"Only {self.current_product.quantity} available.")
            return
        
        # Add to current sale
        result = sales_service.add_product_to_sale(
            self.current_sale,
            self.current_product.id,
            quantity
        )
        
        if not result:
            self.show_error("Error", "Could not add product to sale.")
            return
        
        # Update cart display
        self.update_cart_display()
        
        # Hide product info
        self.product_info_frame.setVisible(False)
        
        # Focus search input again
        self.search_input.setFocus()
    
    def update_cart_display(self):
        """Update the cart table display."""
        # Clear table
        self.cart_table.setRowCount(0)
        
        # Populate table with items
        for i, item in enumerate(self.current_sale.items):
            self.cart_table.insertRow(i)
            
            # Product name
            name_item = QTableWidgetItem(item.product_name)
            name_item.setFlags(name_item.flags() & ~Qt.ItemIsEditable)  # Make read-only
            self.cart_table.setItem(i, 0, name_item)
            
            # Price
            price_item = QTableWidgetItem(f"${item.unit_price:.2f}")
            price_item.setFlags(price_item.flags() & ~Qt.ItemIsEditable)
            self.cart_table.setItem(i, 1, price_item)
            
            # Quantity
            qty_item = QTableWidgetItem(str(item.quantity))
            qty_item.setFlags(qty_item.flags() & ~Qt.ItemIsEditable)
            self.cart_table.setItem(i, 2, qty_item)
            
            # Total
            total_item = QTableWidgetItem(f"${item.total_price:.2f}")
            total_item.setFlags(total_item.flags() & ~Qt.ItemIsEditable)
            self.cart_table.setItem(i, 3, total_item)
            
            # Actions - delete button
            delete_button = QPushButton("Remove")
            delete_button.setStyleSheet("background-color: #dc3545; color: white;")
            delete_button.clicked.connect(lambda checked, idx=i: self.remove_item(idx))
            
            self.cart_table.setCellWidget(i, 4, delete_button)
        
        # Update totals
        self.update_totals()
        
        # Enable/disable checkout button
        self.checkout_button.setEnabled(len(self.current_sale.items) > 0)
    
    def remove_item(self, index):
        """Remove an item from the cart."""
        if 0 <= index < len(self.current_sale.items):
            item = self.current_sale.items[index]
            self.current_sale.items.pop(index)
            self.update_cart_display()
    
    def update_totals(self):
        """Update the totals display."""
        # Calculate subtotal
        subtotal = self.current_sale.calculate_total()
        
        # Update labels
        self.subtotal_label.setText(f"${subtotal:.2f}")
        self.total_label.setText(f"${subtotal:.2f}")
    
    def cancel_sale(self):
        """Cancel the current sale."""
        if not self.current_sale.items:
            return
        
        confirm = self.show_question(
            "Cancel Sale",
            "Are you sure you want to cancel this sale?"
        )
        
        if confirm:
            self.current_sale = Sale(user_id=self.get_current_user().id)
            self.update_cart_display()
            self.product_info_frame.setVisible(False)
    
    def complete_sale(self):
        """Complete the current sale."""
        if not self.current_sale.items:
            return
        
        # Set payment method
        self.current_sale.payment_method = self.payment_method.currentText().lower()
        
        # Save sale to database
        success, sale_id = sales_service.create_sale(self.current_sale)
        
        if not success:
            self.show_error("Error", "Failed to process sale. Please try again.")
            return
        
        # Show receipt
        self.show_receipt(sale_id)
        
        # Start new sale
        self.current_sale = Sale(user_id=self.get_current_user().id)
        self.update_cart_display()
        self.product_info_frame.setVisible(False)
        self.search_input.setFocus()
    
    def show_receipt(self, sale_id):
        """Show a receipt dialog."""
        receipt_dialog = QDialog(self)
        receipt_dialog.setWindowTitle("Sale Complete")
        receipt_dialog.setMinimumWidth(400)
        
        layout = QVBoxLayout(receipt_dialog)
        
        # Success message
        success_label = QLabel("Sale Completed Successfully!")
        success_label.setStyleSheet("font-size: 16pt; color: #28a745; font-weight: bold;")
        success_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(success_label)
        
        # Sale ID
        id_label = QLabel(f"Sale ID: {sale_id}")
        id_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(id_label)
        
        # Amount
        amount_label = QLabel(f"Total Amount: ${self.current_sale.total_amount:.2f}")
        amount_label.setStyleSheet("font-size: 14pt;")
        amount_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(amount_label)
        
        # Payment method
        payment_label = QLabel(f"Payment Method: {self.current_sale.payment_method.upper()}")
        payment_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(payment_label)
        
        # OK button
        button_box = QDialogButtonBox(QDialogButtonBox.Ok)
        button_box.accepted.connect(receipt_dialog.accept)
        layout.addWidget(button_box)
        
        receipt_dialog.exec()
    
    def show_product_selection_dialog(self, products):
        """Show a dialog to select from multiple products."""
        dialog = QDialog(self)
        dialog.setWindowTitle("Select Product")
        dialog.setMinimumWidth(400)
        
        layout = QVBoxLayout(dialog)
        
        layout.addWidget(QLabel("Multiple products found. Please select one:"))
        
        # Create buttons for each product
        selected_product = None
        
        for product in products:
            button = QPushButton(f"{product.name} - ${product.price:.2f}")
            button.clicked.connect(lambda checked, p=product: select_product(p))
            layout.addWidget(button)
        
        def select_product(product):
            nonlocal selected_product
            selected_product = product
            dialog.accept()
        
        # Cancel button
        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(dialog.reject)
        layout.addWidget(cancel_button)
        
        dialog.exec()
        return selected_product