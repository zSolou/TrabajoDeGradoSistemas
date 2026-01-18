# core/repo.py
from decimal import Decimal
from sqlalchemy import select, update
from sqlalchemy.orm.exc import NoResultFound
from .db import SessionLocal, create_tables
from .models import Client, User, Product, Inventory, Movement
import psycopg2
import psycopg2.extras
import os

# ---------- SQLAlchemy CRUD ----------

def create_product(sku: str, name: str, unit: str = None, quality: str = None, description: str = None):
    with SessionLocal() as session:
        prod = Product(sku=sku, name=name, unit=unit, quality=quality, description=description)
        session.add(prod)
        session.commit()
        session.refresh(prod)
        return prod
    
def create_product_with_inventory(data: dict):
    """
    data: dict con keys mínimas: sku, name, quantity
    y opcionales: unit, quality, lot_code, location,
    largo, ancho, espesor, piezas, prod_date, dispatch_date,
    drying, planing, impregnated, obs, performed_by
    """
    from datetime import datetime
    def parse_date_iso(s):
        if not s:
            return None
        # Qt ISODate: 'YYYY-MM-DD' o 'YYYY-MM-DDThh:mm:ss'
        try:
            if "T" in s:
                return datetime.fromisoformat(s)
            return datetime.strptime(s, "%Y-%m-%d")
        except Exception:
            return None

    with SessionLocal() as session:
        try:
            sku = (data.get("sku") or "").strip()
            name = (data.get("name") or data.get("product_type") or "").strip()
            if not sku:
                raise ValueError("SKU es obligatorio.")
            if not name:
                raise ValueError("Nombre/Tipo es obligatorio.")

            # Producto por SKU
            prod = session.execute(select(Product).where(Product.sku == sku)).scalars().first()
            if prod is None:
                prod = Product(
                    sku=sku,
                    name=name,
                    unit=data.get("unit"),
                    quality=data.get("quality")
                )
                session.add(prod)
                session.flush()

            # Inventario con medidas/atributos
            inv = Inventory(
                product_id=prod.id,
                lot_code=(data.get("lot_code") or "").strip(),
                location=(data.get("location") or "").strip(),
                quantity=Decimal(str(data.get("quantity") or 0)),
                largo=Decimal(str(data.get("largo"))) if data.get("largo") is not None else None,
                ancho=Decimal(str(data.get("ancho"))) if data.get("ancho") is not None else None,
                espesor=Decimal(str(data.get("espesor"))) if data.get("espesor") is not None else None,
                piezas=int(data.get("piezas")) if data.get("piezas") is not None else None,
                prod_date=parse_date_iso(data.get("prod_date")),
                dispatch_date=parse_date_iso(data.get("dispatch_date")),
                quality=data.get("quality"),
                drying=data.get("drying"),
                planing=data.get("planing"),
                impregnated=data.get("impregnated"),
                obs=data.get("obs")
            )
            session.add(inv)
            session.flush()

            # Movimiento IN (trazabilidad)
            qty = inv.quantity or Decimal("0")
            if qty != 0:
                mv = Movement(
                    inventory_id=inv.id,
                    product_id=prod.id,
                    change_quantity=qty,
                    movement_type="IN",
                    reference=data.get("reference"),
                    performed_by=data.get("performed_by"),
                    notes=data.get("obs")
                )
                session.add(mv)

            session.commit()
            return {"product_id": prod.id, "inventory_id": inv.id}
        except Exception:
            session.rollback()
            raise
        
def insert_inventory(data: dict):
    with SessionLocal() as session:
        inv = Inventory(
            product_id=data.get("product_id"),
            quantity=data.get("quantity"),
            largo=data.get("largo"),
            ancho=data.get("ancho"),
            espesor=data.get("espesor"),
            piezas=data.get("piezas"),
            prod_date=data.get("prod_date"),
            dispatch_date=data.get("dispatch_date"),
            quality=data.get("quality"),
            drying=data.get("drying"),
            planing=data.get("planing"),
            impregnated=data.get("impregnated"),
            obs=data.get("obs")
        )
        session.add(inv)
        session.commit()
        session.refresh(inv)
        return inv.id

def list_inventory_rows():
    with SessionLocal() as session:
        stmt = (
            select(
                Inventory.id,
                Product.sku,
                Product.name,
                Inventory.quantity,
                Product.unit,
                Inventory.largo,
                Inventory.ancho,
                Inventory.espesor,
                Inventory.piezas,
                Inventory.prod_date,
                Inventory.dispatch_date,
                Inventory.quality,
                Inventory.drying,
                Inventory.planing,
                Inventory.impregnated,
                Inventory.obs
            ).join(Product, Product.id == Inventory.product_id)
            .order_by(Product.name)
        )
        rows = session.execute(stmt).all()
        def to_date_str(dt):
            if not dt:
                return ""
            # DateTime → solo fecha
            return dt.date().isoformat() if hasattr(dt, "date") else dt.isoformat()

        result = []
        for r in rows:
            result.append({
                "id": int(r[0]),
                "sku": r[1],
                "product_type": r[2],
                "quantity": float(r[3]) if r[3] is not None else 0.0,
                "unit": r[4] or "",
                "largo": float(r[5]) if r[5] is not None else 0.0,
                "ancho": float(r[6]) if r[6] is not None else 0.0,
                "espesor": float(r[7]) if r[7] is not None else 0.0,
                "piezas": int(r[8]) if r[8] is not None else 0,
                "prod_date": to_date_str(r[9]),
                "dispatch_date": to_date_str(r[10]),
                "quality": r[11] or "",
                "drying": r[12] or "",
                "planing": r[13] or "",
                "impregnated": r[14] or "",
                "obs": r[15] or ""
            })
        return result

def update_inventory(data: dict):
    with SessionLocal() as session:
        inv = session.get(Inventory, data["id"])
        if not inv:
            raise ValueError("Registro de inventario no encontrado")

        inv.quantity = data.get("quantity")
        inv.largo = data.get("largo")
        inv.ancho = data.get("ancho")
        inv.espesor = data.get("espesor")
        inv.piezas = data.get("piezas")
        inv.prod_date = data.get("prod_date")
        inv.dispatch_date = data.get("dispatch_date")
        inv.quality = data.get("quality")
        inv.drying = data.get("drying")
        inv.planing = data.get("planing")
        inv.impregnated = data.get("impregnated")
        inv.obs = data.get("obs")

        session.commit()    

def get_product_by_sku(sku: str):
    with SessionLocal() as session:
        stmt = select(Product).where(Product.sku == sku)
        return session.execute(stmt).scalars().first()

def list_products():
    with SessionLocal() as session:
        stmt = select(Product).order_by(Product.name)
        return session.execute(stmt).scalars().all()

def get_inventory_by_product(product_id: int):
    with SessionLocal() as session:
        stmt = select(Inventory).where(Inventory.product_id == product_id)
        return session.execute(stmt).scalars().all()

def register_movement(product_id: int, change_qty: Decimal, movement_type: str, inventory_id: int = None, performed_by: int = None, reference: str = None, notes: str = None):
    """
    Registra un movimiento y actualiza inventory.quantity dentro de una transacción.
    Si inventory_id es None, intenta usar la primera fila de inventory para el producto.
    """
    with SessionLocal() as session:
        # obtener o crear inventario objetivo
        inv = None
        if inventory_id:
            inv = session.get(Inventory, inventory_id)
            if inv is None:
                raise ValueError("Inventory id no encontrado")
        else:
            inv = session.execute(select(Inventory).where(Inventory.product_id == product_id).limit(1)).scalars().first()
            if inv is None:
                # crear registro de inventario vacío si no existe
                inv = Inventory(product_id=product_id, quantity=0)
                session.add(inv)
                session.flush()  # para obtener id

        # insertar movimiento
        mv = Movement(
            inventory_id=inv.id,
            product_id=product_id,
            change_quantity=change_qty,
            movement_type=movement_type,
            reference=reference,
            performed_by=performed_by,
            notes=notes
        )
        session.add(mv)

        # actualizar cantidad
        new_qty = (inv.quantity or 0) + Decimal(change_qty)
        if new_qty < 0:
            raise ValueError("Stock insuficiente para esta operación")
        inv.quantity = new_qty

        session.commit()
        session.refresh(mv)
        return mv
    
def delete_inventory(inventory_id: int):
    with SessionLocal() as session:
        inv = session.get(Inventory, inventory_id)
        if not inv:
            raise ValueError("Registro de inventario no encontrado")
        session.delete(inv)
        session.commit()
        
        # ----Clientes----#
        
def create_client(data: dict):
        with SessionLocal() as session:
            client = Client(
            name=data.get("nombre"),
            document_id=data.get("cedula_rif"),
            phone=data.get("telefono"),
            email=data.get("email"),
            address=data.get("direccion"),
        )
        session.add(client)
        session.commit()
        session.refresh(client)
        return client.id

def list_clients():
        with SessionLocal() as session:
            return session.query(Client).order_by(Client.name).all()

def update_client(client_id: int, data: dict):
            with SessionLocal() as session:
                client = session.get(Client, client_id)
                if not client:
                    raise ValueError("Cliente no encontrado")
                client.name = data.get("nombre", client.name)
                client.document_id = data.get("cedula_rif", client.document_id)
                client.phone = data.get("telefono", client.phone)
                client.email = data.get("email", client.email)
                client.address = data.get("direccion", client.address)
                session.commit()

def delete_client(client_id: int):
            with SessionLocal() as session:
                client = session.get(Client, client_id)
                if client:
                    session.delete(client)
                    session.commit()


# ---------- psycopg2 helper (ejecuciones crudas) ----------
def get_psycopg2_conn():
    # lee la URL desde la variable de entorno DATABASE_URL_PG o usa la de SQLAlchemy sin el driver prefix
    url = os.getenv("postgresql+psycopg2://postgres@localhost:5432/astillados_db")  # ejemplo: postgresql://user:pass@host:port/db
    if not url:
        raise RuntimeError("Define DATABASE_URL_PG en variables de entorno para usar psycopg2 helper")
    return psycopg2.connect(url, cursor_factory=psycopg2.extras.RealDictCursor)

def execute_raw(sql: str, params: tuple = None):
    """Ejecuta SQL crudo y devuelve filas (lista de dicts)."""
    conn = get_psycopg2_conn()
    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute(sql, params)
                if cur.description:
                    return cur.fetchall()
                return []
    finally:
        conn.close()

# ---------- Autenticación sencilla (texto plano) ----------
def create_user_plain(username: str, password: str, full_name: str = None,
                      role: str = "user", email: str = None, active: bool = True):
    """
    Crea un usuario con contraseña en texto plano (solo para sistemas pequeños).
    """
    username = username.strip()
    with SessionLocal() as session:
        existing = session.execute(select(User).where(User.username == username)).scalars().first()
        if existing:
            raise ValueError("El username ya existe")
        user = User(username=username, password_hash=password, full_name=full_name,
                    role=role, email=email, active=active)
        session.add(user)
        session.commit()
        session.refresh(user)
        return user.id

def authenticate_user_plain(username: str, password: str):
    """
    Autentica comparando directamente la contraseña con lo almacenado en la BD.
    Devuelve dict con id, username, role si credenciales válidas, o None.
    """
    with SessionLocal() as session:
        user = session.execute(select(User).where(User.username == username)).scalars().first()
        if not user or not user.active:
            return None
        if user.password_hash == password:
            return {"id": user.id, "username": user.username, "role": user.role}
        return None

# ---------- inicialización (solo si se ejecuta directamente) ----------
if __name__ == "__main__":
    create_tables()
    print("Tablas creadas (si no existían).")
