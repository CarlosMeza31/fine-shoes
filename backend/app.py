"""
app.py — Punto de entrada del servidor FastAPI

Para correr el servidor:
  cd backend
  pip install -r requirements.txt
  cp .env.example .env        # edita el .env con tus datos
  uvicorn app:app --reload    # --reload reinicia al guardar cambios

Documentación automática generada por FastAPI:
  http://localhost:8000/docs       ← Swagger UI (puedes probar los endpoints aquí)
  http://localhost:8000/redoc      ← ReDoc (más legible)
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from core.config import settings
from routers import auth, products, cart, orders, reports

# ------------------------------------------------------------
# Crear la aplicación
# ------------------------------------------------------------
app = FastAPI(
    title="Fine Shoes API",
    description="API REST para la tienda de sneakers Fine Shoes",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# ------------------------------------------------------------
# CORS — permite que el frontend (otro origen) llame a la API
#
# ¿Qué es CORS?
#   El navegador bloquea peticiones JS de dominio A hacia dominio B
#   por seguridad. Este middleware le dice al navegador:
#   "sí está bien que http://localhost:5500 llame a esta API".
#   En producción, cambia allow_origins a tu dominio real.
# ------------------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,     # necesario para enviar cookies/headers de auth
    allow_methods=["*"],        # GET, POST, PUT, DELETE...
    allow_headers=["*"],        # Authorization, Content-Type...
)

# ------------------------------------------------------------
# Registrar todos los routers (grupos de endpoints)
# ------------------------------------------------------------
app.include_router(auth.router)
app.include_router(products.router)
app.include_router(cart.router)
app.include_router(orders.router)
app.include_router(reports.router)

# Brands (simple, no necesita router propio)
from fastapi import Depends
from core.database import get_db
from mysql.connector.connection import MySQLConnection

@app.get("/brands", tags=["Marcas"])
def get_brands(db: MySQLConnection = Depends(get_db)):
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT * FROM brands ORDER BY name")
    return cursor.fetchall()


# ------------------------------------------------------------
# Health check — útil para verificar que el servidor está vivo
# ------------------------------------------------------------
@app.get("/", tags=["Health"])
def root():
    return {"status": "ok", "message": "Fine Shoes API corriendo 🚀"}
