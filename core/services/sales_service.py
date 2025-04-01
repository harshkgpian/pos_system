"""Sales service for managing sales operations."""

import logging
from datetime import datetime, timedelta
from typing import List, Optional, Tuple, Dict

# Add parent directory to path to allow relative imports
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent.parent))

from db.models import Sale, SaleItem, Product
from db.repositories import sales_repo, product_repo
from core.auth import require_permission, Permission, get_current_session


@require_permission(Permission.SALES_CREATE)
def create_sale(sale: Sale) -> Tuple[bool, Optional[int]]:
    """Create a new sale with its items."""
    # Validate sale
    if not sale.items:
        logging.warning("Cannot create sale without items")
        return False, None
    
    # Get current user
    session = get_current_session()
    if not session:
        logging.warning("Cannot create sale: No active user session")
        return False, None
    
    sale.user_id = session.user.id
    
    # Calculate total amount
    sale.calculate_total()
    
    # Validate each item
    for item in sale.items:
        # Get product to ensure it exists and has enough stock
        product = product_repo.get_by_id(item.product_id)
        
        if not product:
            logging.warning(f"Product ID {item.product_id} not found")
            return False, None
        
        if product.quantity < item.quantity:
            logging.warning(f"Not enough stock for product {product.name}")
            return False, None
        
        # Set product name for the sale item (not stored in DB, but useful)
        item.product_name = product.name
    
    # Create sale
    return sales_repo.create_sale_with_items(sale)


@require_permission(Permission.SALES_VIEW)
def get_sale_by_id(sale_id: int) -> Optional[Sale]:
    """Get a sale by its ID, including all sale items."""
    return sales_repo.get_by_id(sale_id)


@require_permission(Permission.SALES_VIEW)
def get_recent_sales(limit: int = 10) -> List[Sale]:
    """Get recent sales with pagination."""
    return sales_repo.get_all(limit=limit, offset=0)


@require_permission(Permission.SALES_VIEW)
def get_sales_by_date_range(start_date, end_date) -> List[Sale]:
    """Get sales within a date range."""
    return sales_repo.get_sales_by_date_range(start_date, end_date)


@require_permission(Permission.SALES_VIEW)
def get_sales_summary(days: int = 30) -> Dict:
    """Get sales summary for the last X days."""
    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=days)
    
    return sales_repo.get_sales_summary(start_date, end_date)


@require_permission(Permission.SALES_VIEW)
def get_daily_sales(start_date, end_date) -> Dict:
    """Get daily sales totals within a date range."""
    try:
        conn = product_repo.get_connection()
        cursor = conn.cursor(dictionary=True)
        
        query = """
            SELECT 
                DATE(created_at) as sale_date,
                COUNT(*) as sale_count,
                SUM(total_amount) as total_amount
            FROM sales 
            WHERE DATE(created_at) BETWEEN %s AND %s
            GROUP BY DATE(created_at)
            ORDER BY sale_date
        """
        
        cursor.execute(query, (start_date, end_date))
        results = cursor.fetchall()
        
        daily_sales = {}
        for result in results:
            date_str = result['sale_date'].strftime('%Y-%m-%d')
            daily_sales[date_str] = {
                'count': result['sale_count'],
                'total': float(result['total_amount'])
            }
        
        cursor.close()
        conn.close()
        
        return daily_sales
        
    except Exception as e:
        logging.error(f"Error getting daily sales: {e}")
        return {}


@require_permission(Permission.SALES_CREATE)
def add_product_to_sale(sale: Sale, product_id: int, quantity: int = 1) -> bool:
    """Add a product to a sale."""
    # Get product
    product = product_repo.get_by_id(product_id)
    if not product:
        logging.warning(f"Product ID {product_id} not found")
        return False
    
    if product.quantity < quantity:
        logging.warning(f"Not enough stock for product {product.name}")
        return False
    
    # Check if product is already in the sale
    for item in sale.items:
        if item.product_id == product_id:
            # Update quantity
            item.quantity += quantity
            return True
    
    # Add new item
    sale.items.append(SaleItem(
        product_id=product_id,
        product_name=product.name,
        quantity=quantity,
        unit_price=product.price
    ))
    
    return True


@require_permission(Permission.SALES_CREATE)
def remove_product_from_sale(sale: Sale, product_id: int, quantity: int = None) -> bool:
    """
    Remove a product from a sale.
    If quantity is None, remove the entire item.
    If quantity is specified, reduce the item quantity by that amount.
    """
    for i, item in enumerate(sale.items):
        if item.product_id == product_id:
            if quantity is None or item.quantity <= quantity:
                # Remove entire item
                sale.items.pop(i)
            else:
                # Reduce quantity
                item.quantity -= quantity
            return True
    
    return False