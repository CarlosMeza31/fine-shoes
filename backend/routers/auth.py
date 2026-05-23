"""
routers/auth.py
Endpoints de autenticación: registro, login, perfil.

Flujo completo:
  POST /auth/register → crea usuario → devuelve token
  POST /auth/login    → verifica credenciales → devuelve token
  GET  /auth/me       → devuelve datos del usuario logueado
  PUT  /auth/me       → edita nombre/teléfono/dirección
"""

from fastapi import APIRouter, Depends, HTTPException, status
from mysql.connector.connection import MySQLConnection

from core.database import get_db
from core.security import hash_password, verify_password, create_access_token, get_current_user
from schemas.schemas import UserRegister, UserLogin, UserUpdate, UserOut, TokenOut

router = APIRouter(prefix="/auth", tags=["Autenticación"])


# ----------------------------------------------------------------
# POST /auth/register
# ----------------------------------------------------------------
@router.post("/register", response_model=TokenOut, status_code=201)
def register(data: UserRegister, db: MySQLConnection = Depends(get_db)):
    cursor = db.cursor(dictionary=True)

    # 1. Verificar que el email no esté en uso
    cursor.execute("SELECT id FROM users WHERE email = %s", (data.email,))
    if cursor.fetchone():
        raise HTTPException(status_code=400, detail="El email ya está registrado")

    # 2. Hashear el password — NUNCA guardar el texto plano
    hashed = hash_password(data.password)

    # 3. Insertar usuario
    cursor.execute(
        """INSERT INTO users (name, email, password, phone, address)
           VALUES (%s, %s, %s, %s, %s)""",
        (data.name, data.email, hashed, data.phone, data.address),
    )
    db.commit()
    new_id = cursor.lastrowid

    # 4. Obtener el usuario recién creado para devolverlo
    cursor.execute("SELECT * FROM users WHERE id = %s", (new_id,))
    user = cursor.fetchone()

    token = create_access_token(user["id"], user["role"])
    return {"access_token": token, "user": user}


# ----------------------------------------------------------------
# POST /auth/login
# ----------------------------------------------------------------
@router.post("/login", response_model=TokenOut)
def login(data: UserLogin, db: MySQLConnection = Depends(get_db)):
    cursor = db.cursor(dictionary=True)

    cursor.execute("SELECT * FROM users WHERE email = %s", (data.email,))
    user = cursor.fetchone()

    # Usamos el mismo mensaje para email y password incorrectos
    # — así no revelamos si el email existe o no (seguridad)
    if not user or not verify_password(data.password, user["password"]):
        raise HTTPException(status_code=401, detail="Credenciales incorrectas")

    token = create_access_token(user["id"], user["role"])
    return {"access_token": token, "user": user}


# ----------------------------------------------------------------
# GET /auth/me — requiere token
# ----------------------------------------------------------------
@router.get("/me", response_model=UserOut)
def get_profile(
    current_user: dict = Depends(get_current_user),
    db: MySQLConnection = Depends(get_db),
):
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT * FROM users WHERE id = %s", (int(current_user["sub"]),))
    user = cursor.fetchone()

    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return user


# ----------------------------------------------------------------
# PUT /auth/me — editar perfil
# ----------------------------------------------------------------
@router.put("/me", response_model=UserOut)
def update_profile(
    data: UserUpdate,
    current_user: dict = Depends(get_current_user),
    db: MySQLConnection = Depends(get_db),
):
    user_id = int(current_user["sub"])
    cursor = db.cursor(dictionary=True)

    # Solo actualizar los campos que llegaron (no None)
    fields, values = [], []
    if data.name is not None:
        fields.append("name = %s"); values.append(data.name)
    if data.phone is not None:
        fields.append("phone = %s"); values.append(data.phone)
    if data.address is not None:
        fields.append("address = %s"); values.append(data.address)

    if not fields:
        raise HTTPException(status_code=400, detail="No se enviaron campos para actualizar")

    values.append(user_id)
    cursor.execute(f"UPDATE users SET {', '.join(fields)} WHERE id = %s", values)
    db.commit()

    cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))
    return cursor.fetchone()
