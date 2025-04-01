"""Inventory service for product management operations."""

import logging
from typing import List, Optional, Tuple

# Add parent directory to path to allow relative imports
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent.parent))

from db.models import Product
from db.repositories import product_repo
from core.auth import require_permission, Permission


@require_permission(Permission.INVENTORY_VIEW)
def get_all_products() -> List[Product]:
    """Get all products."""
    return product_repo.get_all()


@require_permission(Permission.INVENTORY_VIEW)
def search_products(query: str) -> List[Product]:
    """Search for products by name or barcode."""
    return product_repo.search(query)


@require_permission(Permission.INVENTORY_VIEW)
def get_product_by_id(product_id: int) -> Optional[Product]:
    """Get a product by ID."""
    return product_repo.get_by_id(product_id)


@require_permission(Permission.INVENTORY_VIEW)
def get_product_by_barcode(barcode: str) -> Optional[Product]:
    """Get a product by barcode."""
    return product_repo.get_by_barcode(barcode)


@require_permission(Permission.INVENTORY_EDIT)
def create_product(product: Product) -> Tuple[bool, Optional[int]]:
    """Create a new product."""
    # Validate product
    if not product.name:
        logging.warning("Cannot create product with empty name")
        return False, None
    
    if product.price < 0:
        logging.warning("Cannot create product with negative price")
        return False, None
    
    if product.quantity < 0:
        logging.warning("Cannot create product with negative quantity")
        return False, None
    
    # Check if barcode already exists (if provided)
    if product.barcode:
        existing = product_repo.get_by_barcode(product.barcode)
        if existing:
            logging.warning(f"Product with barcode {product.barcode} already exists")
            return False, None
    
    # Create product
    return product_repo.create(product)


@require_permission(Permission.INVENTORY_EDIT)
def update_product(product: Product) -> bool:
    """Update an existing product."""
    # Validate product
    if not product.id:
        logging.warning("Cannot update product without ID")
        return False
    
    if not product.name:
        logging.warning("Cannot update product with empty name")
        return False
    
    if product.price < 0:
        logging.warning("Cannot update product with negative price")
        return False
    
    if product.quantity < 0:
        logging.warning("Cannot update product with negative quantity")
        return False
    
    # Check if barcode already exists and belongs to another product
    if product.barcode:
        existing = product_repo.get_by_barcode(product.barcode)
        if existing and existing.id != product.id:
            logging.warning(f"Another product with barcode {product.barcode} already exists")
            return False
    
    # Update product
    return product_repo.update(product)


@require_permission(Permission.INVENTORY_EDIT)
def update_stock(product_id: int, quantity_change: int) -> bool:
    """
    Update product stock.
    Positive quantity_change increases stock, negative decreases it.
    """
    # Get current product
    product = product_repo.get_by_id(product_id)
    if not product:
        logging.warning(f"Cannot update stock: Product ID {product_id} not found")
        return False
    
    # Ensure quantity won't go negative
    if product.quantity + quantity_change < 0:
        logging.warning(f"Cannot update stock: Not enough quantity available")
        return False
    
    # Update quantity
    return product_repo.update_quantity(product_id, quantity_change)


@require_permission(Permission.INVENTORY_EDIT)
def delete_product(product_id: int) -> bool:
    """Delete a product."""
    return product_repo.delete(product_id)


@require_permission(Permission.INVENTORY_VIEW)
def get_low_stock_products(threshold: int = 10) -> List[Product]:
    """Get products with quantity below the specified threshold."""
    all_products = product_repo.get_all()
    return [p for p in all_products if p.quantity <= threshold]