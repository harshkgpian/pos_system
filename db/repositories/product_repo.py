"""Product repository for database operations related to products."""

import logging
from datetime import datetime
from typing import List, Optional, Tuple

# Add parent directory to path to allow relative imports
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent.parent))

from db.connection import get_connection
from db.models import Product


def get_by_id(product_id: int) -> Optional[Product]:
    """Get a product by ID."""
    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        
        query = "SELECT * FROM products WHERE id = %s"
        cursor.execute(query, (product_id,))
        
        result = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if result:
            return Product(
                id=result['id'],
                barcode=result['barcode'],
                name=result['name'],
                price=float(result['price']),
                quantity=result['quantity'],
                created_at=result['created_at'],
                updated_at=result['updated_at']
            )
        return None
        
    except Exception as e:
        logging.error(f"Error getting product by ID: {e}")
        return None


def get_by_barcode(barcode: str) -> Optional[Product]:
    """Get a product by barcode."""
    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        
        query = "SELECT * FROM products WHERE barcode = %s"
        cursor.execute(query, (barcode,))
        
        result = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if result:
            return Product(
                id=result['id'],
                barcode=result['barcode'],
                name=result['name'],
                price=float(result['price']),
                quantity=result['quantity'],
                created_at=result['created_at'],
                updated_at=result['updated_at']
            )
        return None
        
    except Exception as e:
        logging.error(f"Error getting product by barcode: {e}")
        return None


def get_all() -> List[Product]:
    """Get all products."""
    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        
        query = "SELECT * FROM products ORDER BY name"
        cursor.execute(query)
        
        results = cursor.fetchall()
        cursor.close()
        conn.close()
        
        products = []
        for result in results:
            products.append(Product(
                id=result['id'],
                barcode=result['barcode'],
                name=result['name'],
                price=float(result['price']),
                quantity=result['quantity'],
                created_at=result['created_at'],
                updated_at=result['updated_at']
            ))
        
        return products
        
    except Exception as e:
        logging.error(f"Error getting all products: {e}")
        return []


def search(query: str) -> List[Product]:
    """Search for products by name or barcode."""
    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        
        search_param = f"%{query}%"
        query_sql = """
            SELECT * FROM products 
            WHERE name LIKE %s OR barcode LIKE %s
            ORDER BY name
        """
        
        cursor.execute(query_sql, (search_param, search_param))
        
        results = cursor.fetchall()
        cursor.close()
        conn.close()
        
        products = []
        for result in results:
            products.append(Product(
                id=result['id'],
                barcode=result['barcode'],
                name=result['name'],
                price=float(result['price']),
                quantity=result['quantity'],
                created_at=result['created_at'],
                updated_at=result['updated_at']
            ))
        
        return products
        
    except Exception as e:
        logging.error(f"Error searching products: {e}")
        return []


def create(product: Product) -> Tuple[bool, Optional[int]]:
    """
    Create a new product.
    Returns a tuple of (success, product_id).
    """
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        query = """
            INSERT INTO products (barcode, name, price, quantity)
            VALUES (%s, %s, %s, %s)
        """
        
        cursor.execute(query, (
            product.barcode,
            product.name,
            product.price,
            product.quantity
        ))
        
        conn.commit()
        product_id = cursor.lastrowid
        
        cursor.close()
        conn.close()
        
        logging.info(f"Created product: {product.name} with ID {product_id}")
        return True, product_id
        
    except Exception as e:
        logging.error(f"Error creating product: {e}")
        return False, None


def update(product: Product) -> bool:
    """Update an existing product."""
    try:
        if not product.id:
            logging.error("Cannot update product without ID")
            return False
        
        conn = get_connection()
        cursor = conn.cursor()
        
        query = """
            UPDATE products 
            SET barcode = %s, name = %s, price = %s, quantity = %s
            WHERE id = %s
        """
        
        cursor.execute(query, (
            product.barcode,
            product.name,
            product.price,
            product.quantity,
            product.id
        ))
        
        conn.commit()
        affected_rows = cursor.rowcount
        
        cursor.close()
        conn.close()
        
        if affected_rows > 0:
            logging.info(f"Updated product ID {product.id}")
            return True
        else:
            logging.warning(f"No product found with ID {product.id} to update")
            return False
        
    except Exception as e:
        logging.error(f"Error updating product: {e}")
        return False


def update_quantity(product_id: int, quantity_change: int) -> bool:
    """
    Update product quantity by adding the quantity_change value.
    For sales, quantity_change should be negative.
    """
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        # Get current quantity to ensure it doesn't go below zero
        check_query = "SELECT quantity FROM products WHERE id = %s"
        cursor.execute(check_query, (product_id,))
        result = cursor.fetchone()
        
        if not result:
            logging.warning(f"No product found with ID {product_id}")
            cursor.close()
            conn.close()
            return False
        
        current_quantity = result[0]
        new_quantity = current_quantity + quantity_change
        
        if new_quantity < 0:
            logging.warning(f"Cannot update product {product_id} to negative quantity")
            cursor.close()
            conn.close()
            return False
        
        # Update the quantity
        query = """
            UPDATE products 
            SET quantity = %s
            WHERE id = %s
        """
        
        cursor.execute(query, (new_quantity, product_id))
        
        conn.commit()
        affected_rows = cursor.rowcount
        
        cursor.close()
        conn.close()
        
        if affected_rows > 0:
            logging.info(f"Updated product ID {product_id} quantity by {quantity_change}")
            return True
        else:
            return False
        
    except Exception as e:
        logging.error(f"Error updating product quantity: {e}")
        return False


def delete(product_id: int) -> bool:
    """Delete a product by ID."""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        query = "DELETE FROM products WHERE id = %s"
        cursor.execute(query, (product_id,))
        
        conn.commit()
        affected_rows = cursor.rowcount
        
        cursor.close()
        conn.close()
        
        if affected_rows > 0:
            logging.info(f"Deleted product ID {product_id}")
            return True
        else:
            logging.warning(f"No product found with ID {product_id} to delete")
            return False
        
    except Exception as e:
        logging.error(f"Error deleting product: {e}")
        return False