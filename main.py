"""Main entry point for the POS application."""

import sys
import logging
import os
from pathlib import Path
from PySide6.QtWidgets import QApplication

# Create logs directory if it doesn't exist
log_dir = Path(__file__).resolve().parent / 'logs'
log_dir.mkdir(exist_ok=True)

# Ensure db directory has the schema.sql file
db_dir = Path(__file__).resolve().parent / 'db'
schema_path = db_dir / 'schema.sql'

if not schema_path.exists():
    print("Schema file not found, creating it...")
    schema_content = """-- Create database if it doesn't exist
CREATE DATABASE IF NOT EXISTS pos_db;
USE pos_db;

-- Users table
CREATE TABLE IF NOT EXISTS users (
    id INT PRIMARY KEY AUTO_INCREMENT,
    username VARCHAR(50) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role ENUM('admin', 'manager', 'cashier') NOT NULL,
    active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Products table
CREATE TABLE IF NOT EXISTS products (
    id INT PRIMARY KEY AUTO_INCREMENT,
    barcode VARCHAR(50) UNIQUE,
    name VARCHAR(100) NOT NULL,
    price DECIMAL(10,2) NOT NULL,
    quantity INT NOT NULL DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NULL ON UPDATE CURRENT_TIMESTAMP
);

-- Sales table
CREATE TABLE IF NOT EXISTS sales (
    id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT NOT NULL,
    total_amount DECIMAL(10,2) NOT NULL,
    payment_method ENUM('cash', 'card') NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- Sale items table
CREATE TABLE IF NOT EXISTS sale_items (
    id INT PRIMARY KEY AUTO_INCREMENT,
    sale_id INT NOT NULL,
    product_id INT NOT NULL,
    quantity INT NOT NULL,
    unit_price DECIMAL(10,2) NOT NULL,
    FOREIGN KEY (sale_id) REFERENCES sales(id) ON DELETE CASCADE,
    FOREIGN KEY (product_id) REFERENCES products(id)
);

-- Insert default admin user (password: admin123) - storing password directly for simplicity
INSERT INTO users (username, password_hash, role)
SELECT 'admin', 'admin123', 'admin'
WHERE NOT EXISTS (SELECT 1 FROM users WHERE username = 'admin');
"""
    with open(schema_path, 'w') as f:
        f.write(schema_content)
    print(f"Created schema file at {schema_path}")

from config import setup_logging
from db.connection import init as init_db
from ui.main_window import MainWindow


def main():
    """Main application entry point."""
    # Set up logging
    setup_logging()
    
    # Initialize database
    try:
        init_db()
    except Exception as e:
        logging.critical(f"Failed to initialize database: {e}")
        print(f"Error: Failed to initialize database: {e}")
        return 1
    
    # Create Qt application
    app = QApplication(sys.argv)
    app.setApplicationName("Infoware POS")
    
    # Create and show main window
    window = MainWindow()
    window.show()
    
    # Run application event loop
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())