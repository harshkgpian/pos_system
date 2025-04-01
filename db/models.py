"""Database models representing the application entities."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional


@dataclass
class User:
    """User model representing a system user."""
    id: Optional[int] = None
    username: str = ""
    password_hash: str = ""
    role: str = ""
    active: bool = True
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class Product:
    """Product model representing inventory items."""
    id: Optional[int] = None
    barcode: Optional[str] = None
    name: str = ""
    price: float = 0.0
    quantity: int = 0
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: Optional[datetime] = None


@dataclass
class SaleItem:
    """Sale item model representing a line in a sale."""
    id: Optional[int] = None
    sale_id: Optional[int] = None
    product_id: int = 0
    product_name: str = ""  # For convenience, not stored in DB
    quantity: int = 0
    unit_price: float = 0.0
    
    @property
    def total_price(self) -> float:
        """Calculate the total price for this item."""
        return self.quantity * self.unit_price


@dataclass
class Sale:
    """Sale model representing a complete transaction."""
    id: Optional[int] = None
    user_id: int = 0
    total_amount: float = 0.0
    payment_method: str = "cash"
    created_at: datetime = field(default_factory=datetime.now)
    items: List[SaleItem] = field(default_factory=list)
    
    def calculate_total(self) -> float:
        """Calculate the total amount based on all items."""
        self.total_amount = sum(item.total_price for item in self.items)
        return self.total_amount