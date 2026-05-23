"""
routers/products.py
Catálogo de productos — público y admin.

GET  /products              → lista paginada con filtros (público)
GET  /products/{id}         → detalle de un producto (público)
POST /products              → crear producto (admin)
PUT  /products/{id}         → editar producto (admin)
DELETE /products/{id}       → desactivar producto (admin)
GET  /products/{id}/inventory → ver tallas/stock (público)
PUT  /products/{id}/inventory → actualizar stock (admin)
POST /products/import-api   → importar desde DummyJSON (admin)
"""

import re
import httpx
from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional
from mysql.connector.connection import MySQLConnection

from core.database import get_db
from core.security import require_admin
from schemas.schemas import ProductCreate, ProductUpdate, ProductOut, InventoryItem

router = APIRouter(prefix="/products", tags=["Productos"])


def slugify(text: str) -> str:
    """Convierte 'Nike Air Max 270' en 'nike-air-max-270'"""
    text = text.lower().strip()
    text = re.sub(r'[áàä]', 'a', text)
    text = re.sub(r'[éèë]', 'e', text)
    text = re.sub(r'[íìï]', 'i', text)
    text = re.sub(r'[óòö]', 'o', text)
    text = re.sub(r'[úùü]', 'u', text)
    text = re.sub(r'[^a-z0-9\s-]', '', text)
    return re.sub(r'[\s]+', '-', text)


def get_product_with_inventory(cursor, product_id: int) -> Optional[dict]:
    """Helper: obtiene un producto con su inventario completo"""
    cursor.execute(
        """SELECT p.*, b.name AS brand_name
           FROM products p
           JOIN brands b ON b.id = p.brand_id
           WHERE p.id = %s""",
        (product_id,),
    )
    product = cursor.fetchone()
    if not product:
        return None

    cursor.execute(
        "SELECT id, size, color, stock, sku FROM inventory WHERE product_id = %s",
        (product_id,),
    )
    product["inventory"] = cursor.fetchall()
    return product


# ----------------------------------------------------------------
# GET /products — con filtros y paginación
# ----------------------------------------------------------------
@router.get("/")
def list_products(
    brand: Optional[str] = Query(None, description="Slug de marca: nike, adidas..."),
    size:  Optional[str] = Query(None, description="Talla: 40, 41..."),
    color: Optional[str] = Query(None, description="Color"),
    q:     Optional[str] = Query(None, description="Búsqueda por nombre"),
    min_price: Optional[float] = Query(None, ge=0),
    max_price: Optional[float] = Query(None, ge=0),
    page:  int = Query(1, ge=1),
    limit: int = Query(12, ge=1, le=50),
    db: MySQLConnection = Depends(get_db),
):
    cursor = db.cursor(dictionary=True)
    offset = (page - 1) * limit

    # Construimos el WHERE dinámicamente según los filtros recibidos
    # Usar %s siempre — NUNCA f-string con datos del usuario (SQL injection)
    conditions = ["p.is_active = TRUE"]
    params: list = []

    if brand:
        conditions.append("b.slug = %s");  params.append(brand)
    if size:
        conditions.append("EXISTS (SELECT 1 FROM inventory i WHERE i.product_id = p.id AND i.size = %s AND i.stock > 0)")
        params.append(size)
    if color:
        conditions.append("EXISTS (SELECT 1 FROM inventory i WHERE i.product_id = p.id AND i.color = %s AND i.stock > 0)")
        params.append(color)
    if q:
        conditions.append("MATCH(p.name, p.description) AGAINST(%s IN BOOLEAN MODE)")
        params.append(f"{q}*")
    if min_price is not None:
        conditions.append("p.price >= %s"); params.append(min_price)
    if max_price is not None:
        conditions.append("p.price <= %s"); params.append(max_price)

    where = " AND ".join(conditions)

    # Total para paginación
    cursor.execute(
        f"SELECT COUNT(*) AS total FROM products p JOIN brands b ON b.id = p.brand_id WHERE {where}",
        params,
    )
    total = cursor.fetchone()["total"]

    # Productos de esta página
    cursor.execute(
        f"""SELECT p.*, b.name AS brand_name
            FROM products p
            JOIN brands b ON b.id = p.brand_id
            WHERE {where}
            ORDER BY p.created_at DESC
            LIMIT %s OFFSET %s""",
        [*params, limit, offset],
    )
    products = cursor.fetchall()

    return {
        "products": products,
        "pagination": {"total": total, "page": page, "limit": limit, "pages": -(-total // limit)},
    }


# ----------------------------------------------------------------
# GET /products/{id}
# ----------------------------------------------------------------
@router.get("/{product_id}")
def get_product(product_id: int, db: MySQLConnection = Depends(get_db)):
    cursor = db.cursor(dictionary=True)
    product = get_product_with_inventory(cursor, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    return product


# ----------------------------------------------------------------
# POST /products — admin
# ----------------------------------------------------------------
@router.post("/", status_code=201)
def create_product(
    data: ProductCreate,
    _: dict = Depends(require_admin),
    db: MySQLConnection = Depends(get_db),
):
    cursor = db.cursor(dictionary=True)

    slug = slugify(data.name)
    # Garantizar slug único agregando sufijo si ya existe
    cursor.execute("SELECT id FROM products WHERE slug = %s", (slug,))
    if cursor.fetchone():
        slug = f"{slug}-{data.brand_id}"

    cursor.execute(
        """INSERT INTO products (brand_id, name, slug, description, price, image_url)
           VALUES (%s, %s, %s, %s, %s, %s)""",
        (data.brand_id, data.name, slug, data.description, data.price, data.image_url),
    )
    db.commit()
    product_id = cursor.lastrowid

    # Insertar inventario inicial si se proporcionó
    for item in data.inventory:
        cursor.execute(
            "INSERT INTO inventory (product_id, size, color, stock) VALUES (%s, %s, %s, %s)",
            (product_id, item.size, item.color, item.stock),
        )
    db.commit()

    return get_product_with_inventory(cursor, product_id)


# ----------------------------------------------------------------
# PUT /products/{id} — admin
# ----------------------------------------------------------------
@router.put("/{product_id}")
def update_product(
    product_id: int,
    data: ProductUpdate,
    _: dict = Depends(require_admin),
    db: MySQLConnection = Depends(get_db),
):
    cursor = db.cursor(dictionary=True)

    fields, values = [], []
    if data.brand_id is not None:
        fields.append("brand_id = %s"); values.append(data.brand_id)
    if data.name is not None:
        fields.append("name = %s"); values.append(data.name)
        fields.append("slug = %s"); values.append(slugify(data.name))
    if data.description is not None:
        fields.append("description = %s"); values.append(data.description)
    if data.price is not None:
        fields.append("price = %s"); values.append(data.price)
    if data.image_url is not None:
        fields.append("image_url = %s"); values.append(data.image_url)
    if data.is_active is not None:
        fields.append("is_active = %s"); values.append(data.is_active)

    if not fields:
        raise HTTPException(status_code=400, detail="Sin campos para actualizar")

    values.append(product_id)
    cursor.execute(f"UPDATE products SET {', '.join(fields)} WHERE id = %s", values)
    db.commit()

    return get_product_with_inventory(cursor, product_id)


# ----------------------------------------------------------------
# DELETE /products/{id} — soft delete (is_active = false)
# ----------------------------------------------------------------
@router.delete("/{product_id}", status_code=204)
def delete_product(
    product_id: int,
    _: dict = Depends(require_admin),
    db: MySQLConnection = Depends(get_db),
):
    cursor = db.cursor()
    cursor.execute("UPDATE products SET is_active = FALSE WHERE id = %s", (product_id,))
    db.commit()
    if cursor.rowcount == 0:
        raise HTTPException(status_code=404, detail="Producto no encontrado")


# ----------------------------------------------------------------
# PUT /products/{id}/inventory — actualizar stock de una variante
# ----------------------------------------------------------------
@router.put("/{product_id}/inventory/{inventory_id}")
def update_inventory(
    product_id: int,
    inventory_id: int,
    data: InventoryItem,
    _: dict = Depends(require_admin),
    db: MySQLConnection = Depends(get_db),
):
    cursor = db.cursor()
    cursor.execute(
        "UPDATE inventory SET size=%s, color=%s, stock=%s WHERE id=%s AND product_id=%s",
        (data.size, data.color, data.stock, inventory_id, product_id),
    )
    db.commit()
    if cursor.rowcount == 0:
        raise HTTPException(status_code=404, detail="Variante no encontrada")
    return {"message": "Inventario actualizado"}


# ----------------------------------------------------------------
# POST /products/import-api — importar desde DummyJSON (API externa)
# Este endpoint cumple el requisito de "conectar a una API externa"
# ----------------------------------------------------------------
@router.post("/import-api", status_code=201)
def import_from_api(
    _: dict = Depends(require_admin),
    db: MySQLConnection = Depends(get_db),
):
    """
    Consume la API pública DummyJSON para obtener productos reales
    con nombre, descripción, precio e imagen.
    Mapea los que sean de categoría 'mens-shoes' o 'womens-shoes'.
    """
    # Petición HTTP a la API externa
    response = httpx.get("https://dummyjson.com/products/category/mens-shoes", timeout=10)
    if response.status_code != 200:
        raise HTTPException(status_code=502, detail="Error al contactar la API externa")

    external_products = response.json().get("products", [])
    cursor = db.cursor(dictionary=True)

    # Buscar o crear una marca genérica para productos importados
    cursor.execute("SELECT id FROM brands WHERE slug = 'imported'")
    brand = cursor.fetchone()
    if not brand:
        cursor.execute("INSERT INTO brands (name, slug) VALUES ('Importado', 'imported')")
        db.commit()
        brand_id = cursor.lastrowid
    else:
        brand_id = brand["id"]

    imported = 0
    for p in external_products:
        slug = slugify(p["title"])
        cursor.execute("SELECT id FROM products WHERE slug = %s", (slug,))
        if cursor.fetchone():
            continue  # Ya existe, omitir

        cursor.execute(
            """INSERT INTO products (brand_id, name, slug, description, price, image_url)
               VALUES (%s, %s, %s, %s, %s, %s)""",
            (brand_id, p["title"], slug, p["description"], p["price"], p.get("thumbnail")),
        )
        db.commit()
        product_id = cursor.lastrowid

        # Crear inventario básico
        for size in ["40", "41", "42", "43"]:
            cursor.execute(
                "INSERT INTO inventory (product_id, size, color, stock) VALUES (%s, %s, %s, %s)",
                (product_id, size, "Negro", 10),
            )
        db.commit()
        imported += 1

    return {"message": f"{imported} productos importados correctamente"}
