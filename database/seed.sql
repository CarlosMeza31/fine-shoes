-- ============================================================
--  FINE SHOES — Datos de prueba (seed)
--  Ejecutar DESPUÉS de schema.sql
-- ============================================================

USE fine_shoes;

-- ------------------------------------------------------------
-- Marcas
-- ------------------------------------------------------------
INSERT INTO brands (name, slug) VALUES
  ('Nike',          'nike'),
  ('Adidas',        'adidas'),
  ('New Balance',   'new-balance'),
  ('Puma',          'puma'),
  ('Vans',          'vans'),
  ('Jordan',        'jordan');

-- ------------------------------------------------------------
-- Usuario admin (password: Admin1234!)
-- Hash generado con bcrypt rounds=12
-- Para generar tu propio hash: python -c "import bcrypt; print(bcrypt.hashpw(b'Admin1234!', bcrypt.gensalt(12)).decode())"
-- ------------------------------------------------------------
INSERT INTO users (name, email, password, role) VALUES
  ('Admin Fine Shoes', 'admin@fineshoes.com',
   '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewrpE1VRZ.7k8Y6K',
   'admin'),
  ('Juan Pérez',       'juan@ejemplo.com',
   '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewrpE1VRZ.7k8Y6K',
   'customer');

-- ------------------------------------------------------------
-- Productos de ejemplo
-- (Las imágenes vienen de la API externa DummyJSON)
-- ------------------------------------------------------------
INSERT INTO products (brand_id, name, slug, description, price, image_url) VALUES
(1, 'Nike Air Max 270',      'nike-air-max-270',
 'Zapatilla lifestyle con unidad Air Max en el talón. Comodidad todo el día.',
 2899.00, 'https://dummyjson.com/image/400x300/nike'),

(1, 'Nike React Infinity',   'nike-react-infinity',
 'Diseñada para reducir lesiones. Foam React para amortiguación responsiva.',
 3199.00, 'https://dummyjson.com/image/400x300/nike2'),

(2, 'Adidas Ultraboost 23',  'adidas-ultraboost-23',
 'Tecnología Boost para máxima energía. Parte superior Primeknit.',
 3499.00, 'https://dummyjson.com/image/400x300/adidas'),

(2, 'Adidas Stan Smith',     'adidas-stan-smith',
 'Ícono del tenis convertido en clásico streetwear. Cuero y suela gum.',
 1899.00, 'https://dummyjson.com/image/400x300/adidas2'),

(3, 'New Balance 574',       'new-balance-574',
 'El modelo retro más vendido de la marca. Estilo y soporte excepcionales.',
 2299.00, 'https://dummyjson.com/image/400x300/nb'),

(4, 'Puma Suede Classic',    'puma-suede-classic',
 'Un ícono del deporte desde 1968. Gamuza premium y suela de goma.',
 1599.00, 'https://dummyjson.com/image/400x300/puma'),

(5, 'Vans Old Skool',        'vans-old-skool',
 'La firma waffle sole y la franja lateral. El skate clásico que nunca pasa.',
 1499.00, 'https://dummyjson.com/image/400x300/vans'),

(6, 'Air Jordan 1 Retro',    'air-jordan-1-retro',
 'El original de 1985 reinterpretado. Cuero premium y amortiguación Air.',
 4299.00, 'https://dummyjson.com/image/400x300/jordan');

-- ------------------------------------------------------------
-- Inventario (tallas y colores por producto)
-- ------------------------------------------------------------
INSERT INTO inventory (product_id, size, color, stock) VALUES
-- Nike Air Max 270
(1,'40','Negro',10),(1,'41','Negro',8),(1,'42','Negro',5),(1,'43','Negro',7),
(1,'40','Blanco',12),(1,'41','Blanco',9),(1,'42','Blanco',6),
-- Nike React Infinity
(2,'39','Azul',8),(2,'40','Azul',10),(2,'41','Azul',7),(2,'42','Azul',5),
-- Adidas Ultraboost 23
(3,'40','Blanco',15),(3,'41','Blanco',12),(3,'42','Blanco',8),(3,'43','Blanco',6),
(3,'40','Negro',10),(3,'41','Negro',9),
-- Adidas Stan Smith
(4,'38','Blanco',20),(4,'39','Blanco',18),(4,'40','Blanco',15),(4,'41','Blanco',12),(4,'42','Blanco',10),
-- New Balance 574
(5,'40','Gris',8),(5,'41','Gris',10),(5,'42','Gris',7),(5,'43','Gris',5),
(5,'40','Navy',6),(5,'41','Navy',8),
-- Puma Suede Classic
(6,'39','Negro',12),(6,'40','Negro',10),(6,'41','Negro',8),(6,'42','Negro',6),
(6,'40','Azul marino',7),(6,'41','Azul marino',5),
-- Vans Old Skool
(7,'38','Negro/Blanco',15),(7,'39','Negro/Blanco',12),(7,'40','Negro/Blanco',10),
(7,'41','Negro/Blanco',8),(7,'42','Negro/Blanco',6),
(7,'40','Rojo',5),(7,'41','Rojo',4),
-- Air Jordan 1 Retro
(8,'40','Rojo/Negro',5),(8,'41','Rojo/Negro',4),(8,'42','Rojo/Negro',3),(8,'43','Rojo/Negro',2),
(8,'40','Royal Blue',4),(8,'41','Royal Blue',3);
