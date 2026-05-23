"""
core/database.py
Maneja la conexión a MySQL.

Por qué un pool de conexiones:
  Abrir una conexión nueva en cada request es lento (100-300 ms).
  Un pool mantiene N conexiones abiertas y las presta a cada request,
  devolviéndolas al terminar. Mucho más eficiente.
"""

import mysql.connector
from mysql.connector import pooling
from core.config import settings

# El pool se crea UNA SOLA VEZ cuando arranca el servidor
connection_pool = pooling.MySQLConnectionPool(
    pool_name="fine_shoes_pool",
    pool_size=5,                  # 5 conexiones simultáneas máximo
    pool_reset_session=True,
    host=settings.DB_HOST,
    port=settings.DB_PORT,
    database=settings.DB_NAME,
    user=settings.DB_USER,
    password=settings.DB_PASSWORD,
    charset="utf8mb4",
    collation="utf8mb4_unicode_ci",
)


def get_db():
    """
    Generador que FastAPI usa como dependencia (Depends).
    Cada vez que una ruta lo pide, entrega una conexión del pool.
    El bloque finally garantiza que la conexión se devuelva al pool
    aunque ocurra un error — así no se agotan las conexiones.

    Uso en una ruta:
        @router.get("/algo")
        def mi_ruta(db = Depends(get_db)):
            cursor = db.cursor(dictionary=True)
            ...
    """
    conn = connection_pool.get_connection()
    try:
        yield conn
    finally:
        conn.close()   # devuelve al pool, no cierra realmente
