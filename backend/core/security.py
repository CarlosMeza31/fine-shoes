"""
core/security.py
Todo lo relacionado con contraseñas y tokens JWT.

¿Qué es JWT?
  JSON Web Token — es una cadena firmada digitalmente que contiene datos
  (como el user_id y rol). El servidor la genera al hacer login y el
  cliente la envía en cada request en el header: Authorization: Bearer <token>
  El servidor verifica la firma sin consultar la BD → muy rápido.
"""

from datetime import datetime, timedelta, timezone
from typing import Optional

from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi import Depends

from core.config import settings

# CryptContext maneja el hash de contraseñas con bcrypt
# bcrypt aplica un "work factor" (rounds) que hace el hash lento a propósito
# — así aunque roben la BD, crackear cada password tarda mucho
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# HTTPBearer extrae el token del header "Authorization: Bearer <token>"
bearer_scheme = HTTPBearer()


def hash_password(plain: str) -> str:
    """Convierte 'MiPassword123' en '$2b$12$...' (hash bcrypt)"""
    return pwd_context.hash(plain)


def verify_password(plain: str, hashed: str) -> bool:
    """Verifica si el password ingresado coincide con el hash guardado"""
    return pwd_context.verify(plain, hashed)


def create_access_token(user_id: int, role: str) -> str:
    """
    Genera un JWT con el user_id y rol dentro.
    Expira según JWT_EXPIRE_MINUTES del .env (default: 24h).
    """
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.JWT_EXPIRE_MINUTES)
    payload = {
        "sub": str(user_id),   # "subject" — estándar JWT
        "role": role,
        "exp": expire,
    }
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


def decode_token(token: str) -> dict:
    """
    Decodifica y valida un JWT.
    Lanza excepción si el token es inválido o expiró.
    """
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
        return payload
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido o expirado",
            headers={"WWW-Authenticate": "Bearer"},
        )


# ----------------------------------------------------------------
# Dependencias de FastAPI — se usan con Depends() en las rutas
# ----------------------------------------------------------------

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme)) -> dict:
    """
    Dependencia que extrae y valida el token de cualquier ruta protegida.
    Retorna el payload del token: {"sub": "1", "role": "customer"}

    Uso:
        @router.get("/perfil")
        def mi_perfil(user = Depends(get_current_user)):
            return {"user_id": user["sub"]}
    """
    return decode_token(credentials.credentials)


def require_admin(user: dict = Depends(get_current_user)) -> dict:
    """
    Dependencia que además verifica que el usuario sea administrador.
    Úsala en rutas del panel admin.

    Uso:
        @router.delete("/products/{id}")
        def eliminar(id: int, user = Depends(require_admin)):
            ...
    """
    if user.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acceso restringido a administradores",
        )
    return user
