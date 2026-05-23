"""
routers/cart.py
Carrito de compras persistido en base de datos.

GET    /cart         → ver mi carrito
POST   /cart         → agregar item
PUT    /cart/{id}    → cambiar cantidad
DELETE /cart/{id}    → eliminar item
DELETE /cart         → vaciar todo
"""

from fastapi import APIRouter, Depends, HTTPException
from mysql.connector.connection import MySQLConnection

from core.database import get_db
from core.security import get_current_user
from schemas.schemas import CartAdd, CartUpdate, CartOut

router = APIRouter(prefix="/cart", tags=["Carrito"])


def build_cart(cursor, user_id: int) -> dict:
    """Construye el carrito completo con subtotales"""
    cursor.execute(
        """SELECT ci.id, ci.inventory_id, ci.quantity,
                  p.id AS product_id, p.name AS product_name, p.image_url,
                  p.price AS unit_price,
                  b.name AS brand_name,
                  inv.size, inv.color
           FROM cart_items ci
           JOIN inventory inv ON inv.id = ci.inventory_id
           JOIN products p    ON p.id  = inv.product_id
           JOIN brands b      ON b.id  = p.brand_id
           WHERE ci.user_id = %s""",
        (user_id,),
    )
    items = cursor.fetchall()
    for item in items:
        item["subtotal"] = round(item["unit_price"] * item["quantity"], 2)

    total = round(sum(i["subtotal"] for i in items), 2)
    return {"items": items, "total": total}


@router.get("/")
def get_cart(user=Depends(get_current_user), db: MySQLConnection = Depends(get_db)):
    cursor = db.cursor(dictionary=True)
    return build_cart(cursor, int(user["sub"]))


@router.post("/", status_code=201)
def add_to_cart(
    data: CartAdd,
    user=Depends(get_current_user),
    db: MySQLConnection = Depends(get_db),
):
    user_id = int(user["sub"])
    cursor = db.cursor(dictionary=True)

    # Verificar que haya stock suficiente
    cursor.execute(
        "SELECT stock FROM inventory WHERE id = %s", (data.inventory_id,)
    )
    inv = cursor.fetchone()
    if not inv:
        raise HTTPException(status_code=404, detail="Variante no encontrada")
    if inv["stock"] < data.quantity:
        raise HTTPException(status_code=400, detail=f"Stock insuficiente (disponible: {inv['stock']})")

    # INSERT OR UPDATE — si ya está en el carrito, sumar cantidad
    cursor.execute(
        """INSERT INTO cart_items (user_id, inventory_id, quantity)
           VALUES (%s, %s, %s)
           ON DUPLICATE KEY UPDATE quantity = quantity + VALUES(quantity)""",
        (user_id, data.inventory_id, data.quantity),
    )
    db.commit()
    return build_cart(cursor, user_id)


@router.put("/{item_id}")
def update_cart_item(
    item_id: int,
    data: CartUpdate,
    user=Depends(get_current_user),
    db: MySQLConnection = Depends(get_db),
):
    user_id = int(user["sub"])
    cursor = db.cursor()
    cursor.execute(
        "UPDATE cart_items SET quantity = %s WHERE id = %s AND user_id = %s",
        (data.quantity, item_id, user_id),
    )
    db.commit()
    if cursor.rowcount == 0:
        raise HTTPException(status_code=404, detail="Item no encontrado en tu carrito")

    cursor2 = db.cursor(dictionary=True)
    return build_cart(cursor2, user_id)


@router.delete("/{item_id}", status_code=200)
def remove_cart_item(
    item_id: int,
    user=Depends(get_current_user),
    db: MySQLConnection = Depends(get_db),
):
    user_id = int(user["sub"])
    cursor = db.cursor()
    cursor.execute("DELETE FROM cart_items WHERE id = %s AND user_id = %s", (item_id, user_id))
    db.commit()

    cursor2 = db.cursor(dictionary=True)
    return build_cart(cursor2, user_id)


@router.delete("/", status_code=200)
def clear_cart(user=Depends(get_current_user), db: MySQLConnection = Depends(get_db)):
    cursor = db.cursor()
    cursor.execute("DELETE FROM cart_items WHERE user_id = %s", (int(user["sub"]),))
    db.commit()
    return {"items": [], "total": 0}
