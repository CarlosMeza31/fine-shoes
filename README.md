# Fine Shoes 👟
Tienda en línea de sneakers — Proyecto Final Programación Web

## Stack tecnológico
| Capa | Tecnología |
|------|-----------|
| Frontend | HTML5 + CSS3 + JS (ES Modules) |
| Backend / API | Python 3.11 + FastAPI |
| Base de datos | MySQL 8.0 |
| Autenticación | JWT (python-jose + bcrypt) |
| API externa | DummyJSON (productos de ejemplo) |
| Gráficas | Chart.js 4 |

---

## Estructura del proyecto
```
fine-shoes/
├── database/
│   ├── schema.sql        ← Crear tablas (ejecutar primero)
│   └── seed.sql          ← Datos de prueba
├── backend/
│   ├── app.py            ← Servidor FastAPI
│   ├── core/             ← Config, BD, Seguridad
│   ├── routers/          ← auth, products, cart, orders, reports
│   ├── schemas/          ← Modelos Pydantic
│   ├── requirements.txt
│   └── .env.example
└── frontend/
    ├── index.html        ← Catálogo
    ├── login.html
    ├── register.html
    ├── product.html      ← Detalle de producto
    ├── cart.html
    ├── checkout.html
    ├── orders.html       ← Mis pedidos
    ├── admin/
    │   ├── dashboard.html
    │   ├── products.html
    │   ├── orders.html
    │   └── reports.html
    ├── css/styles.css
    └── js/api.js         ← Cliente centralizado de la API
```

---

## Instalación paso a paso

### 1. Base de datos (MySQL)
```sql
-- Conéctate a MySQL y ejecuta en orden:
source fine-shoes/database/schema.sql
source fine-shoes/database/seed.sql
```
Esto crea la base `fine_shoes` con 8 tablas, marcas, productos y un usuario admin.

### 2. Backend (FastAPI)
```bash
cd fine-shoes/backend

# Crear entorno virtual (recomendado)
python -m venv venv
source venv/bin/activate          # Mac/Linux
venv\Scripts\activate             # Windows

# Instalar dependencias
pip install -r requirements.txt

# Configurar variables de entorno
cp .env.example .env
# Edita .env con tu usuario/contraseña de MySQL

# Instalar pydantic-settings (necesario para leer .env)
pip install pydantic-settings

# Iniciar el servidor
uvicorn app:app --reload
```
El servidor queda en: **http://localhost:8000**
Documentación interactiva: **http://localhost:8000/docs**

### 3. Frontend
Abre la carpeta `frontend/` con la extensión **Live Server** de VS Code.
- Click derecho en `index.html` → "Open with Live Server"
- La URL será: **http://localhost:5500**

Asegúrate de que `FRONTEND_URL=http://localhost:5500` en tu `.env`.

---

## Credenciales de prueba
| Rol | Email | Password |
|-----|-------|----------|
| Admin | admin@fineshoes.com | Admin1234! |
| Cliente | juan@ejemplo.com | Admin1234! |

---

## Endpoints de la API

### Auth
| Método | Ruta | Descripción |
|--------|------|-------------|
| POST | /auth/register | Registro de usuario |
| POST | /auth/login | Inicio de sesión |
| GET | /auth/me | Perfil del usuario logueado |
| PUT | /auth/me | Editar perfil |

### Productos (público)
| Método | Ruta | Descripción |
|--------|------|-------------|
| GET | /products/ | Lista con filtros (brand, size, color, q, price) |
| GET | /products/{id} | Detalle con inventario |

### Productos (admin)
| Método | Ruta | Descripción |
|--------|------|-------------|
| POST | /products/ | Crear producto |
| PUT | /products/{id} | Editar producto |
| DELETE | /products/{id} | Desactivar producto |
| PUT | /products/{id}/inventory/{iid} | Actualizar stock |
| POST | /products/import-api | **Importar de DummyJSON** |

### Carrito (autenticado)
| Método | Ruta | Descripción |
|--------|------|-------------|
| GET | /cart/ | Ver carrito |
| POST | /cart/ | Agregar item |
| PUT | /cart/{id} | Cambiar cantidad |
| DELETE | /cart/{id} | Eliminar item |
| DELETE | /cart/ | Vaciar carrito |

### Pedidos
| Método | Ruta | Descripción |
|--------|------|-------------|
| POST | /orders/checkout | Crear pedido desde el carrito |
| GET | /orders/my | Mis pedidos |
| GET | /orders/ | Todos los pedidos (admin) |
| PUT | /orders/{id}/status | Actualizar estado (admin) |

### Reportes (admin)
| Método | Ruta | Descripción |
|--------|------|-------------|
| GET | /reports/summary | Totales del dashboard |
| GET | /reports/sales-by-product | Top productos vendidos |
| GET | /reports/sales-by-month | Ventas por mes |
| GET | /reports/low-stock | Variantes con stock bajo |

---

## Roles del sistema
- **customer** — puede navegar, comprar y ver sus pedidos
- **admin** — puede además crear/editar productos, gestionar inventario, ver todos los pedidos y reportes

Los roles se controlan con JWT. El token incluye `role` en su payload.
FastAPI verifica el rol en cada endpoint protegido usando `Depends(require_admin)`.

---

## API externa integrada
Se consume **DummyJSON** (`https://dummyjson.com/products/category/mens-shoes`)  
Endpoint en el admin: `POST /products/import-api`  
Importa productos con nombre, descripción, precio e imagen desde la API pública.
