-- ============================================================
--  FINE SHOES — Schema de base de datos
--  MySQL 8.0+
--  Ejecutar en orden, las FK dependen de las tablas anteriores
-- ============================================================

CREATE DATABASE IF NOT EXISTS fine_shoes
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

USE fine_shoes;

-- ------------------------------------------------------------
-- 1. USUARIOS
--    role: 'customer' o 'admin'
-- ------------------------------------------------------------
CREATE TABLE users (
  id          INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  name        VARCHAR(100)        NOT NULL,
  email       VARCHAR(150)        NOT NULL UNIQUE,
  password    VARCHAR(255)        NOT NULL,          -- bcrypt hash
  role        ENUM('customer','admin') NOT NULL DEFAULT 'customer',
  phone       VARCHAR(20),
  address     VARCHAR(255),
  created_at  TIMESTAMP           NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at  TIMESTAMP           NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- ------------------------------------------------------------
-- 2. MARCAS
-- ------------------------------------------------------------
CREATE TABLE brands (
  id    INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  name  VARCHAR(80) NOT NULL UNIQUE,
  slug  VARCHAR(80) NOT NULL UNIQUE   -- "nike", "adidas" — para filtros URL
);

-- ------------------------------------------------------------
-- 3. PRODUCTOS
-- ------------------------------------------------------------
CREATE TABLE products (
  id           INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  brand_id     INT UNSIGNED        NOT NULL,
  name         VARCHAR(150)        NOT NULL,
  slug         VARCHAR(150)        NOT NULL UNIQUE,
  description  TEXT,
  price        DECIMAL(10,2)       NOT NULL,
  image_url    VARCHAR(500),
  is_active    BOOLEAN             NOT NULL DEFAULT TRUE,
  created_at   TIMESTAMP           NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at   TIMESTAMP           NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

  FOREIGN KEY (brand_id) REFERENCES brands(id) ON DELETE RESTRICT,
  INDEX idx_brand (brand_id),
  FULLTEXT INDEX idx_search (name, description)   -- para búsqueda por texto
);

-- ------------------------------------------------------------
-- 4. INVENTARIO (producto + talla + color)
--    Un producto puede tener varias combinaciones talla/color
-- ------------------------------------------------------------
CREATE TABLE inventory (
  id          INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  product_id  INT UNSIGNED  NOT NULL,
  size        VARCHAR(10)   NOT NULL,   -- "40", "41", "42" ...
  color       VARCHAR(50)   NOT NULL,   -- "Negro", "Blanco", "Rojo"
  stock       INT UNSIGNED  NOT NULL DEFAULT 0,
  sku         VARCHAR(100)  GENERATED ALWAYS AS (
                CONCAT('SKU-', product_id, '-', size, '-', REPLACE(color,' ','_'))
              ) STORED UNIQUE,

  FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE,
  INDEX idx_product (product_id)
);

-- ------------------------------------------------------------
-- 5. IMÁGENES ADICIONALES DE PRODUCTO
-- ------------------------------------------------------------
CREATE TABLE product_images (
  id          INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  product_id  INT UNSIGNED  NOT NULL,
  url         VARCHAR(500)  NOT NULL,
  sort_order  TINYINT       NOT NULL DEFAULT 0,

  FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE
);

-- ------------------------------------------------------------
-- 6. PEDIDOS
--    status: pending → paid → shipped → delivered → cancelled
-- ------------------------------------------------------------
CREATE TABLE orders (
  id              INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  user_id         INT UNSIGNED        NOT NULL,
  status          ENUM('pending','paid','shipped','delivered','cancelled')
                  NOT NULL DEFAULT 'pending',
  subtotal        DECIMAL(10,2)       NOT NULL,
  shipping_cost   DECIMAL(10,2)       NOT NULL DEFAULT 0.00,
  total           DECIMAL(10,2)       NOT NULL,
  -- dirección de envío (copiada en el momento del pedido)
  shipping_name    VARCHAR(100),
  shipping_address VARCHAR(255),
  shipping_phone   VARCHAR(20),
  notes           TEXT,
  created_at      TIMESTAMP           NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at      TIMESTAMP           NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

  FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE RESTRICT,
  INDEX idx_user (user_id),
  INDEX idx_status (status),
  INDEX idx_created (created_at)
);

-- ------------------------------------------------------------
-- 7. ITEMS DEL PEDIDO
-- ------------------------------------------------------------
CREATE TABLE order_items (
  id            INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  order_id      INT UNSIGNED  NOT NULL,
  inventory_id  INT UNSIGNED  NOT NULL,             -- talla+color específica
  product_id    INT UNSIGNED  NOT NULL,             -- redundante pero útil para reportes
  quantity      SMALLINT UNSIGNED NOT NULL,
  unit_price    DECIMAL(10,2) NOT NULL,             -- precio al momento de comprar
  subtotal      DECIMAL(10,2) GENERATED ALWAYS AS (quantity * unit_price) STORED,

  FOREIGN KEY (order_id)     REFERENCES orders(id)    ON DELETE CASCADE,
  FOREIGN KEY (inventory_id) REFERENCES inventory(id) ON DELETE RESTRICT,
  FOREIGN KEY (product_id)   REFERENCES products(id)  ON DELETE RESTRICT
);

-- ------------------------------------------------------------
-- 8. CARRITO (persistido en BD para multi-dispositivo)
-- ------------------------------------------------------------
CREATE TABLE cart_items (
  id            INT UNSIGNED  AUTO_INCREMENT PRIMARY KEY,
  user_id       INT UNSIGNED  NOT NULL,
  inventory_id  INT UNSIGNED  NOT NULL,
  quantity      SMALLINT UNSIGNED NOT NULL DEFAULT 1,
  added_at      TIMESTAMP     NOT NULL DEFAULT CURRENT_TIMESTAMP,

  UNIQUE KEY uq_user_item (user_id, inventory_id),   -- un usuario no repite el mismo item
  FOREIGN KEY (user_id)      REFERENCES users(id)     ON DELETE CASCADE,
  FOREIGN KEY (inventory_id) REFERENCES inventory(id) ON DELETE CASCADE
);

-- ============================================================
--  VISTAS ÚTILES (facilitan los reportes del admin)
-- ============================================================

-- Resumen de ventas por producto
CREATE OR REPLACE VIEW v_sales_by_product AS
SELECT
  p.id            AS product_id,
  p.name          AS product_name,
  b.name          AS brand,
  SUM(oi.quantity)     AS total_sold,
  SUM(oi.subtotal)     AS total_revenue
FROM order_items oi
JOIN products p   ON p.id = oi.product_id
JOIN brands   b   ON b.id = p.brand_id
JOIN orders   o   ON o.id = oi.order_id
WHERE o.status NOT IN ('cancelled')
GROUP BY p.id, p.name, b.name
ORDER BY total_sold DESC;

-- Resumen de ventas por mes
CREATE OR REPLACE VIEW v_sales_by_month AS
SELECT
  DATE_FORMAT(created_at, '%Y-%m') AS month,
  COUNT(*)                          AS total_orders,
  SUM(total)                        AS total_revenue
FROM orders
WHERE status NOT IN ('cancelled')
GROUP BY month
ORDER BY month DESC;
