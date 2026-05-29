"""
schemas/schemas.py
Modelos Pydantic para validación de datos de entrada y salida.

¿Por qué Pydantic?
  FastAPI lo usa para validar automáticamente el JSON que llega en el body
  y el que sale en la respuesta. Si el frontend manda un campo mal, 
  FastAPI devuelve un error 422 con descripción exacta del problema
  — sin que tú escribas ninguna validación manual.
"""

from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from datetime import datetime


# ================================================================
# AUTH
# ================================================================

class UserRegister(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=72)
    phone: Optional[str] = None
    address: Optional[str] = None


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=100)
    phone: Optional[str] = None
    address: Optional[str] = None


class UserOut(BaseModel):
    id: int
    name: str
    email: str
    role: str
    phone: Optional[str]
    address: Optional[str]
    created_at: datetime


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut


# ================================================================
# PRODUCTOS
# ================================================================

class InventoryItem(BaseModel):
    size: str
    color: str
    stock: int = Field(..., ge=0)


class InventoryOut(BaseModel):
    id: int
    size: str
    color: str
    stock: int
    sku: str


class ProductCreate(BaseModel):
    brand_id: int
    name: str = Field(..., min_length=2, max_length=150)
    description: Optional[str] = None
    price: float = Field(..., gt=0)
    image_url: Optional[str] = None
    inventory: List[InventoryItem] = []   # tallas/colores iniciales


class ProductUpdate(BaseModel):
    brand_id: Optional[int] = None
    name: Optional[str] = Field(None, min_length=2, max_length=150)
    description: Optional[str] = None
    price: Optional[float] = Field(None, gt=0)
    image_url: Optional[str] = None
    is_active: Optional[bool] = None


class ProductOut(BaseModel):
    id: int
    brand_id: int
    brand_name: str
    name: str
    slug: str
    description: Optional[str]
    price: float
    image_url: Optional[str]
    is_active: bool
    inventory: List[InventoryOut] = []


# ================================================================
# CARRITO
# ================================================================

class CartAdd(BaseModel):
    inventory_id: int
    quantity: int = Field(..., ge=1, le=10)


class CartUpdate(BaseModel):
    quantity: int = Field(..., ge=1, le=10)


class CartItemOut(BaseModel):
    id: int
    inventory_id: int
    product_id: int
    product_name: str
    brand_name: str
    image_url: Optional[str]
    size: str
    color: str
    unit_price: float
    quantity: int
    subtotal: float


class CartOut(BaseModel):
    items: List[CartItemOut]
    total: float


# ================================================================
# PEDIDOS
# ================================================================

class CheckoutRequest(BaseModel):
    shipping_name: str = Field(..., min_length=2)
    shipping_address: str = Field(..., min_length=5)
    shipping_phone: str
    notes: Optional[str] = None


class OrderStatusUpdate(BaseModel):
    status: str = Field(..., pattern="^(pending|paid|shipped|delivered|cancelled)$")


class OrderItemOut(BaseModel):
    product_name: str
    brand_name: str
    size: str
    color: str
    quantity: int
    unit_price: float
    subtotal: float


class OrderOut(BaseModel):
    id: int
    status: str
    subtotal: float
    shipping_cost: float
    total: float
    shipping_name: Optional[str]
    shipping_address: Optional[str]
    notes: Optional[str]
    created_at: datetime
    items: List[OrderItemOut] = []


# ================================================================
# REPORTES (solo admin)
# ================================================================

class SalesReportItem(BaseModel):
    product_name: str
    brand: str
    total_sold: int
    total_revenue: float


class MonthlySales(BaseModel):
    month: str
    total_orders: int
    total_revenue: float
