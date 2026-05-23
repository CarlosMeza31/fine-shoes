"""
routers/orders.py
Pedidos — checkout simulado y gestión.

POST /orders/checkout          → convertir carrito en pedido
GET  /orders/my                → mis pedidos (cliente)
GET  /orders/{id}              → detalle de un pedido
GET  /orders                   → todos los pedidos (admin)
PUT  /orders/{id}/status       → actualizar estado (admin)
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from mysql.connector.connection import MySQLConnection
from typing import Optional

from core.database import get_db
from core.security import get_current_user, require_admin
from schemas.schemas import CheckoutRequest, OrderStatusUpdate

router = APIRouter(prefix="/orders", tags=["Pedidos"])


def get_order_detail(cursor, order_id: int) -> dict:
    """Obtiene un pedido con todos sus items"""
    cursor.execute("SELECT * FROM orders WHERE id = %s", (order_id,))
    order = cursor.fetchone()
    if not order:
        return None

    cursor.execute(
        """SELECT p.name AS product_name, b.name AS brand_name,
                  inv.size, inv.color,
                  oi.quantity, oi.unit_price, oi.subtotal
           FROM order_items oi
           JOIN inventory inv ON inv.id = oi.inventory_id
           JOIN products p    ON p.id  = oi.product_id
           JOIN brands b      ON b.id  = p.brand_id
           WHERE oi.order_id = %s""",
        (order_id,),
    )
    order["items"] = cursor.fetchall()
    return order


# ----------------------------------------------------------------
# POST /orders/checkout — convierte el carrito en pedido
# ----------------------------------------------------------------
@router.post("/checkout", status_code=201)
def checkout(
    data: CheckoutRequest,
    user=Depends(get_current_user),
    db: MySQLConnection = Depends(get_db),
):
    user_id = int(user["sub"])
    cursor = db.cursor(dictionary=True)

    # 1. Obtener items del carrito
    cursor.execute(
        """SELECT ci.inventory_id, ci.quantity, p.price,
                  inv.stock, p.id AS product_id
           FROM cart_items ci
           JOIN inventory inv ON inv.id = ci.inventory_id
           JOIN products p    ON p.id  = inv.product_id
           WHERE ci.user_id = %s""",
        (user_id,),
    )
    cart = cursor.fetchall()

    if not cart:
        raise HTTPException(status_code=400, detail="El carrito está vacío")

    # 2. Verificar stock de cada item
    for item in cart:
        if item["stock"] < item["quantity"]:
            raise HTTPException(
                status_code=400,
                detail=f"Stock insuficiente para inventory_id {item['inventory_id']}",
            )

    # 3. Calcular totales
    subtotal = sum(float(i["price"]) * i["quantity"] for i in cart)
    shipping = 0.00
    total = subtotal + shipping

    # 4. Crear el pedido
    cursor.execute(
        """INSERT INTO orders
           (user_id, subtotal, shipping_cost, total,
            shipping_name, shipping_address, shipping_phone, notes)
           VALUES (%s, %s, %s, %s, %s, %s, %s, %s)""",
        (user_id, subtotal, shipping, total,
         data.shipping_name, data.shipping_address, data.shipping_phone, data.notes),
    )
    db.commit()
    order_id = cursor.lastrowid

    # 5. Insertar items del pedido y descontar stock
    for item in cart:
        cursor.execute(
            """INSERT INTO order_items (order_id, inventory_id, product_id, quantity, unit_price)
               VALUES (%s, %s, %s, %s, %s)""",
            (order_id, item["inventory_id"], item["product_id"], item["quantity"], item["price"]),
        )
        cursor.execute(
            "UPDATE inventory SET stock = stock - %s WHERE id = %s",
            (item["quantity"], item["inventory_id"]),
        )

    # 6. Vaciar el carrito
    cursor.execute("DELETE FROM cart_items WHERE user_id = %s", (user_id,))
    db.commit()

    return get_order_detail(cursor, order_id)


# ----------------------------------------------------------------
# GET /orders/my — pedidos del cliente logueado
# ----------------------------------------------------------------
@router.get("/my")
def my_orders(user=Depends(get_current_user), db: MySQLConnection = Depends(get_db)):
    cursor = db.cursor(dictionary=True)
    cursor.execute(
        "SELECT * FROM orders WHERE user_id = %s ORDER BY created_at DESC",
        (int(user["sub"]),),
    )
    orders = cursor.fetchall()
    for order in orders:
        cursor.execute(
            """SELECT p.name AS product_name, oi.quantity, oi.unit_price, oi.subtotal
               FROM order_items oi
               JOIN products p ON p.id = oi.product_id
               WHERE oi.order_id = %s""",
            (order["id"],),
        )
        order["items"] = cursor.fetchall()
    return orders


# ----------------------------------------------------------------
# GET /orders/{id} — detalle de un pedido
# ----------------------------------------------------------------
@router.get("/{order_id}")
def get_order(order_id: int, user=Depends(get_current_user), db: MySQLConnection = Depends(get_db)):
    cursor = db.cursor(dictionary=True)
    order = get_order_detail(cursor, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Pedido no encontrado")

    # El cliente solo puede ver sus propios pedidos
    if user["role"] != "admin" and order["user_id"] != int(user["sub"]):
        raise HTTPException(status_code=403, detail="Sin acceso a este pedido")

    return order


# ----------------------------------------------------------------
# GET /orders — todos los pedidos (admin)
# ----------------------------------------------------------------
@router.get("/")
def list_all_orders(
    status: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    _: dict = Depends(require_admin),
    db: MySQLConnection = Depends(get_db),
):
    cursor = db.cursor(dictionary=True)
    offset = (page - 1) * limit

    where = "WHERE o.status = %s" if status else ""
    params = [status] if status else []

    cursor.execute(
        f"""SELECT o.*, u.name AS customer_name, u.email AS customer_email
            FROM orders o
            JOIN users u ON u.id = o.user_id
            {where}
            ORDER BY o.created_at DESC
            LIMIT %s OFFSET %s""",
        [*params, limit, offset],
    )
    return cursor.fetchall()


# ----------------------------------------------------------------
# PUT /orders/{id}/status — admin actualiza estado del pedido
# ----------------------------------------------------------------
@router.put("/{order_id}/status")
def update_order_status(
    order_id: int,
    data: OrderStatusUpdate,
    _: dict = Depends(require_admin),
    db: MySQLConnection = Depends(get_db),
):
    cursor = db.cursor()
    cursor.execute(
        "UPDATE orders SET status = %s WHERE id = %s",
        (data.status, order_id),
    )
    db.commit()
    if cursor.rowcount == 0:
        raise HTTPException(status_code=404, detail="Pedido no encontrado")
    return {"message": f"Estado actualizado a '{data.status}'"}
