-- astillados_db
-- Tipos enumerados (crea si no existen)
DO $$ BEGIN
    CREATE TYPE role_enum AS ENUM ('admin','user','viewer');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

DO $$ BEGIN
    CREATE TYPE movement_type_enum AS ENUM ('IN','OUT','ADJUSTMENT','TRANSFER');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

-- Tablas principales (usar SERIAL/INTEGER para ids)
CREATE TABLE users (
  id SERIAL PRIMARY KEY,
  username TEXT UNIQUE NOT NULL,
  password_hash TEXT NOT NULL,
  full_name TEXT,
  role role_enum NOT NULL DEFAULT 'user',
  email TEXT,
  active BOOLEAN NOT NULL DEFAULT true,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ
);

CREATE TABLE clients (
  id SERIAL PRIMARY KEY,
  name TEXT NOT NULL,
  document_id TEXT,
  phone TEXT,
  email TEXT,
  address TEXT,
  notes TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ
);

CREATE TABLE products (
  id SERIAL PRIMARY KEY,
  sku TEXT UNIQUE,
  name TEXT NOT NULL,
  description TEXT,
  unit TEXT,                -- ejemplo: m3, pieza
  quality TEXT,
  is_active BOOLEAN NOT NULL DEFAULT true,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ
);

-- inventory: stock por producto / lote / ubicación
CREATE TABLE inventory (
  id SERIAL PRIMARY KEY,
  product_id INTEGER NOT NULL REFERENCES products(id) ON DELETE CASCADE,
  lot_code TEXT,
  location TEXT,
  quantity NUMERIC(18,6) NOT NULL DEFAULT 0,  -- precisión para m3
  unit_cost NUMERIC(18,4),
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ
);

-- movements: historial de cambios (auditable)
CREATE TABLE movements (
  id SERIAL PRIMARY KEY,
  inventory_id INTEGER REFERENCES inventory(id) ON DELETE SET NULL,
  product_id INTEGER NOT NULL REFERENCES products(id) ON DELETE CASCADE,
  change_quantity NUMERIC(18,6) NOT NULL,   -- + entrada, - salida
  movement_type movement_type_enum NOT NULL,
  reference TEXT,
  performed_by INTEGER REFERENCES users(id) ON DELETE SET NULL,
  performed_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  notes TEXT
);

CREATE TABLE settings (
  key TEXT PRIMARY KEY,
  value TEXT,
  description TEXT
);

CREATE TABLE audit_logs (
  id SERIAL PRIMARY KEY,
  actor_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
  action TEXT NOT NULL,
  object_type TEXT,
  object_id TEXT,
  occurred_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  details JSONB
);

-- Índices recomendados
CREATE INDEX idx_products_name ON products (lower(name));
CREATE INDEX idx_inventory_product ON inventory (product_id);
CREATE INDEX idx_movements_product_time ON movements (product_id, performed_at DESC);
CREATE INDEX idx_users_username ON users (lower(username));
