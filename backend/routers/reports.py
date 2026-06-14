"""
routers/reports.py
Reportes para el panel de administración.

GET /reports/sales-by-product  → productos más vendidos
GET /reports/sales-by-month    → ventas por mes
GET /reports/low-stock         → productos con poco inventario
GET /reports/summary           → resumen general (dashboard)
"""

from fastapi import APIRouter, Depends, Query
from mysql.connector.connection import MySQLConnection

from core.database import get_db
from core.security import require_admin

router = APIRouter(prefix="/reports", tags=["Reportes"])


@router.get("/sales-by-product")
def sales_by_product(
    limit: int = Query(10, ge=1, le=50),
    _: dict = Depends(require_admin),
    db: MySQLConnection = Depends(get_db),
):
    """Top productos por unidades vendidas"""
    cursor = db.cursor(dictionary=True)
    cursor.execute(
        """SELECT
             p.id            AS product_id,
             p.name          AS product_name,
             b.name          AS brand,
             SUM(oi.quantity)          AS total_sold,
             SUM(oi.quantity * oi.unit_price) AS total_revenue
           FROM order_items oi
           JOIN products p ON p.id = oi.product_id
           JOIN brands   b ON b.id = p.brand_id
           JOIN orders   o ON o.id = oi.order_id
           WHERE o.status NOT IN ('cancelled')
           GROUP BY p.id, p.name, b.name
           ORDER BY total_sold DESC
           LIMIT %s""",
        (limit,)
    )
    rows = cursor.fetchall()
    # Convertir Decimal a float/int para serialización JSON correcta
    for row in rows:
        row["total_sold"]    = int(row["total_sold"])    if row["total_sold"]    is not None else 0
        row["total_revenue"] = float(row["total_revenue"]) if row["total_revenue"] is not None else 0.0
    return rows


@router.get("/sales-by-month")
def sales_by_month(
    _: dict = Depends(require_admin),
    db: MySQLConnection = Depends(get_db),
):
    """Ventas totales agrupadas por mes"""
    cursor = db.cursor(dictionary=True)
    cursor.execute(
        """SELECT
             DATE_FORMAT(created_at, '%Y-%m') AS month,
             COUNT(*)                          AS total_orders,
             SUM(total)                        AS total_revenue
           FROM orders
           WHERE status NOT IN ('cancelled')
           GROUP BY month
           ORDER BY month DESC
           LIMIT 24"""
    )
    rows = cursor.fetchall()
    # Convertir Decimal a float/int para serialización JSON correcta
    for row in rows:
        row["total_orders"]  = int(row["total_orders"])    if row["total_orders"]  is not None else 0
        row["total_revenue"] = float(row["total_revenue"]) if row["total_revenue"] is not None else 0.0
    return rows


@router.get("/low-stock")
def low_stock(
    threshold: int = Query(5, ge=0, description="Cantidad mínima de stock"),
    _: dict = Depends(require_admin),
    db: MySQLConnection = Depends(get_db),
):
    """Variantes con stock igual o menor al umbral"""
    cursor = db.cursor(dictionary=True)
    cursor.execute(
        """SELECT p.name AS product_name, b.name AS brand,
                  inv.size, inv.color, inv.stock, inv.sku
           FROM inventory inv
           JOIN products p ON p.id = inv.product_id
           JOIN brands b   ON b.id = p.brand_id
           WHERE inv.stock <= %s AND p.is_active = TRUE
           ORDER BY inv.stock ASC""",
        (threshold,),
    )
    return cursor.fetchall()


@router.get("/summary")
def dashboard_summary(
    _: dict = Depends(require_admin),
    db: MySQLConnection = Depends(get_db),
):
    """Tarjetas del dashboard: totales rápidos"""
    cursor = db.cursor(dictionary=True)

    cursor.execute("SELECT COUNT(*) AS total FROM users WHERE role='customer'")
    total_customers = cursor.fetchone()["total"]

    cursor.execute("SELECT COUNT(*) AS total FROM orders WHERE status != 'cancelled'")
    total_orders = cursor.fetchone()["total"]

    cursor.execute("SELECT COALESCE(SUM(total), 0) AS revenue FROM orders WHERE status != 'cancelled'")
    total_revenue = cursor.fetchone()["revenue"]

    cursor.execute("SELECT COUNT(*) AS total FROM products WHERE is_active = TRUE")
    total_products = cursor.fetchone()["total"]

    cursor.execute(
        "SELECT COUNT(*) AS total FROM orders WHERE status = 'pending'"
    )
    pending_orders = cursor.fetchone()["total"]

    return {
        "total_customers": total_customers,
        "total_orders": total_orders,
        "total_revenue": float(total_revenue),
        "total_products": total_products,
        "pending_orders": pending_orders,
    }
