"""Sales repository for database operations related to sales and sale items."""

import logging
from typing import List, Optional, Tuple, Dict

# Add parent directory to path to allow relative imports
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent.parent))

from db.connection import get_connection
from db.models import Sale, SaleItem


def get_by_id(sale_id: int) -> Optional[Sale]:
    """Get a sale and its items by ID."""
    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        
        # Get sale
        query = "SELECT * FROM sales WHERE id = %s"
        cursor.execute(query, (sale_id,))
        sale_result = cursor.fetchone()
        
        if not sale_result:
            cursor.close()
            conn.close()
            return None
        
        # Create Sale object
        sale = Sale(
            id=sale_result['id'],
            user_id=sale_result['user_id'],
            total_amount=float(sale_result['total_amount']),
            payment_method=sale_result['payment_method'],
            created_at=sale_result['created_at']
        )
        
        # Get sale items
        items_query = """
            SELECT si.*, p.name as product_name 
            FROM sale_items si
            JOIN products p ON si.product_id = p.id
            WHERE si.sale_id = %s
        """
        
        cursor.execute(items_query, (sale_id,))
        items_results = cursor.fetchall()
        
        # Add items to sale
        for item_result in items_results:
            sale_item = SaleItem(
                id=item_result['id'],
                sale_id=item_result['sale_id'],
                product_id=item_result['product_id'],
                product_name=item_result['product_name'],
                quantity=item_result['quantity'],
                unit_price=float(item_result['unit_price'])
            )
            sale.items.append(sale_item)
        
        cursor.close()
        conn.close()
        
        return sale
        
    except Exception as e:
        logging.error(f"Error getting sale by ID: {e}")
        return None


def get_all(limit: int = 100, offset: int = 0) -> List[Sale]:
    """Get all sales with pagination."""
    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        
        query = """
            SELECT * FROM sales 
            ORDER BY created_at DESC
            LIMIT %s OFFSET %s
        """
        
        cursor.execute(query, (limit, offset))
        results = cursor.fetchall()
        
        sales = []
        for result in results:
            sale = Sale(
                id=result['id'],
                user_id=result['user_id'],
                total_amount=float(result['total_amount']),
                payment_method=result['payment_method'],
                created_at=result['created_at']
            )
            sales.append(sale)
        
        cursor.close()
        conn.close()
        
        return sales
        
    except Exception as e:
        logging.error(f"Error getting all sales: {e}")
        return []


def create_sale_with_items(sale: Sale) -> Tuple[bool, Optional[int]]:
    """
    Create a new sale with its items.
    Returns a tuple of (success, sale_id).
    """
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        # Start transaction
        conn.start_transaction()
        
        # Insert sale
        sale_query = """
            INSERT INTO sales (user_id, total_amount, payment_method)
            VALUES (%s, %s, %s)
        """
        
        cursor.execute(sale_query, (
            sale.user_id,
            sale.total_amount,
            sale.payment_method
        ))
        
        sale_id = cursor.lastrowid
        
        # Insert items
        items_query = """
            INSERT INTO sale_items (sale_id, product_id, quantity, unit_price)
            VALUES (%s, %s, %s, %s)
        """
        
        for item in sale.items:
            cursor.execute(items_query, (
                sale_id,
                item.product_id,
                item.quantity,
                item.unit_price
            ))
            
            # Update product quantity
            update_query = """
                UPDATE products
                SET quantity = quantity - %s
                WHERE id = %s
            """
            cursor.execute(update_query, (item.quantity, item.product_id))
        
        # Commit transaction
        conn.commit()
        
        cursor.close()
        conn.close()
        
        logging.info(f"Created sale ID {sale_id} with {len(sale.items)} items")
        return True, sale_id
        
    except Exception as e:
        # Rollback on error
        if 'conn' in locals() and conn.is_connected():
            conn.rollback()
            cursor.close()
            conn.close()
        
        logging.error(f"Error creating sale: {e}")
        return False, None


def get_sales_by_date_range(start_date, end_date) -> List[Sale]:
    """Get sales within a date range."""
    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        
        query = """
            SELECT * FROM sales 
            WHERE DATE(created_at) BETWEEN %s AND %s
            ORDER BY created_at DESC
        """
        
        cursor.execute(query, (start_date, end_date))
        results = cursor.fetchall()
        
        sales = []
        for result in results:
            sale = Sale(
                id=result['id'],
                user_id=result['user_id'],
                total_amount=float(result['total_amount']),
                payment_method=result['payment_method'],
                created_at=result['created_at']
            )
            sales.append(sale)
        
        cursor.close()
        conn.close()
        
        return sales
        
    except Exception as e:
        logging.error(f"Error getting sales by date range: {e}")
        return []


def get_sales_summary(start_date, end_date) -> Dict:
    """Get summary of sales within a date range."""
    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        
        # Get total sales and revenue
        summary_query = """
            SELECT 
                COUNT(*) as total_sales,
                SUM(total_amount) as total_revenue,
                AVG(total_amount) as average_sale
            FROM sales 
            WHERE DATE(created_at) BETWEEN %s AND %s
        """
        
        cursor.execute(summary_query, (start_date, end_date))
        summary = cursor.fetchone()
        
        # Get payment method breakdown
        payment_query = """
            SELECT 
                payment_method,
                COUNT(*) as count,
                SUM(total_amount) as total
            FROM sales 
            WHERE DATE(created_at) BETWEEN %s AND %s
            GROUP BY payment_method
        """
        
        cursor.execute(payment_query, (start_date, end_date))
        payment_results = cursor.fetchall()
        
        payment_methods = {}
        for result in payment_results:
            payment_methods[result['payment_method']] = {
                'count': result['count'],
                'total': float(result['total'])
            }
        
        # Get top products
        products_query = """
            SELECT 
                p.id,
                p.name,
                SUM(si.quantity) as total_quantity,
                SUM(si.quantity * si.unit_price) as total_revenue
            FROM sale_items si
            JOIN products p ON si.product_id = p.id
            JOIN sales s ON si.sale_id = s.id
            WHERE DATE(s.created_at) BETWEEN %s AND %s
            GROUP BY p.id, p.name
            ORDER BY total_revenue DESC
            LIMIT 5
        """
        
        cursor.execute(products_query, (start_date, end_date))
        top_products = cursor.fetchall()
        
        # Combine all data
        result = {
            'total_sales': summary['total_sales'] if summary['total_sales'] else 0,
            'total_revenue': float(summary['total_revenue']) if summary['total_revenue'] else 0,
            'average_sale': float(summary['average_sale']) if summary['average_sale'] else 0,
            'payment_methods': payment_methods,
            'top_products': top_products
        }
        
        cursor.close()
        conn.close()
        
        return result
        
    except Exception as e:
        logging.error(f"Error getting sales summary: {e}")
        return {
            'total_sales': 0,
            'total_revenue': 0,
            'average_sale': 0,
            'payment_methods': {},
            'top_products': []
        }