# core/repo.py
from decimal import Decimal
from sqlalchemy import select, update, delete, and_
from sqlalchemy.orm.exc import NoResultFound
from .db import SessionLocal, create_tables
from .models import Client, PredefinedMeasure, User, Product, Inventory, Movement, Dispatch
import psycopg2
import psycopg2.extras
import os
from datetime import datetime, date

# ---------- SQLAlchemy CRUD ----------
def create_product(sku: str, name: str, unit: str = None, quality: str = None, description: str = None):
    with SessionLocal() as session:
        prod = Product(sku=sku, name=name, unit=unit, quality=quality, description=description)
        session.add(prod)
        session.commit()
        session.refresh(prod)
        return prod

def _parse_date(s):
    if not s:
        return None
    try:
        if isinstance(s, date) and not isinstance(s, datetime):
            return s
        if isinstance(s, datetime):
            return s.date()
        if isinstance(s, str):
            if "T" in s:
                dt = datetime.fromisoformat(s)
            else:
                dt = datetime.strptime(s, "%Y-%m-%d")
            return dt.date()
        return None
    except Exception:
        return None

def create_product_with_inventory(data: dict):
    """
    data: dict con keys mínimas: sku, name, quantity
    y opcionales: unit, quality, largo, ancho, espesor, piezas, prod_date, dispatch_date,
    drying, planing, impregnated, obs, performed_by
    """
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

            # Inventario (sin lot_code/location)
            inv = Inventory(
                product_id=prod.id,
                quantity=Decimal(str(data.get("quantity") or 0)),
                largo=Decimal(str(data.get("largo"))) if data.get("largo") is not None else None,
                ancho=Decimal(str(data.get("ancho"))) if data.get("ancho") is not None else None,
                espesor=Decimal(str(data.get("espesor"))) if data.get("espesor") is not None else None,
                piezas=int(data.get("piezas")) if data.get("piezas") is not None else None,
                prod_date=_parse_date(data.get("prod_date")),
                dispatch_date=_parse_date(data.get("dispatch_date")),
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
            return {"inventory_id": inv.id, "product_id": prod.id}
        except Exception:
            session.rollback()
            raise

def insert_inventory(data: dict):
    with SessionLocal() as session:
        inv = Inventory(
            product_id=data.get("product_id"),
            quantity=Decimal(str(data.get("quantity") or 0)),
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

# ---------- list/inventory ----------
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
                "prod_date": r[9],
                "dispatch_date": r[10],
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
    with SessionLocal() as session:
        inv = None
        if inventory_id:
            inv = session.get(Inventory, inventory_id)
            if inv is None:
                raise ValueError("Inventory id no encontrado")
        else:
            inv = session.execute(select(Inventory).where(Inventory.product_id == product_id).limit(1)).scalars().first()
            if inv is None:
                inv = Inventory(product_id=product_id, quantity=0)
                session.add(inv)
                session.flush()

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
        
# ---------- CLIENTES ----------
def create_client(data: dict):
    with SessionLocal() as session:
        client = Client(
            name=data.get("nombre"),
            document_id=data.get("cedula_rif"),
            phone=data.get("telefono"),
            email=data.get("email"),
            address=data.get("direccion"),
            is_active=True # Por defecto activo
        )
        session.add(client)
        session.commit()
        session.refresh(client)
        return client.id

def list_clients(solo_activos=True):
    """
    Si solo_activos=True, trae solo los visibles. 
    Si False, trae todos (para poder reactivar).
    """
    with SessionLocal() as session:
        stmt = select(Client)
        if solo_activos:
            stmt = stmt.where(Client.is_active == True)
        stmt = stmt.order_by(Client.name)
        return session.execute(stmt).scalars().all()

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
        
        # Si envían el estado activo/inactivo, lo actualizamos
        if "is_active" in data:
            client.is_active = data["is_active"]
            
        session.commit()

def toggle_client_active(client_id: int, active: bool):
    """Activa o desactiva un cliente sin borrarlo."""
    with SessionLocal() as session:
        client = session.get(Client, client_id)
        if client:
            client.is_active = active
            session.commit()

# ---------- MEDIDAS PREDEFINIDAS ----------
def create_measure(data: dict):
    with SessionLocal() as session:
        measure = PredefinedMeasure(
            product_type=data.get("product_type"),
            name=data.get("name"),
            largo=data.get("largo"),
            ancho=data.get("ancho"),
            espesor=data.get("espesor")
        )
        session.add(measure)
        session.commit()
        session.refresh(measure)
        return measure

def get_measures_by_type(p_type: str):
    with SessionLocal() as session:
        # Filtramos por el tipo de producto actual
        stmt = select(PredefinedMeasure).where(PredefinedMeasure.product_type == p_type)
        return session.execute(stmt).scalars().all()

def delete_measure(measure_id: int):
    with SessionLocal() as session:
        measure = session.get(PredefinedMeasure, measure_id)
        if measure:
            session.delete(measure)
            session.commit()

# ---------- psycopg2 helper (ejecuciones crudas) ----------
def get_psycopg2_conn():
    url = os.getenv("DATABASE_URL_PG")  # Use env var to keep it flexible
    if not url:
        url = "postgresql://postgres@localhost:5432/astillados_db"
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

# ---------- Autenticación sencillo (texto plano) ----------
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
    Autentica comparando directamente la contraseña con la almacenada en la BD.
    Devuelve dict con id, username, role si credenciales válidas, o None.
    """
    with SessionLocal() as session:
        user = session.execute(select(User).where(User.username == username)).scalars().first()
        if not user or not user.active:
            return None
        if user.password_hash == password:
            return {"id": user.id, "username": user.username, "role": user.role}
        return None

# ---------- DESPACHOS Y LÓGICA DE SALIDA ----------

def get_available_inventory():
    """
    Retorna lotes de inventario que tienen stock > 0 y están DISPONIBLES.
    Incluye datos del producto padre para mostrar el nombre real.
    """
    with SessionLocal() as session:
        # Hacemos join con Product para tener el nombre descriptivo
        stmt = (
            select(Inventory, Product.name)
            .join(Product, Inventory.product_id == Product.id)
            .where(
                and_(Inventory.quantity > 0, Inventory.status == 'DISPONIBLE')
            )
            .order_by(Inventory.prod_date)
        )
        
        results = session.execute(stmt).all()
        # Combinamos el objeto Inventory con el nombre del producto
        data = []
        for inv, prod_name in results:
            # Inyectamos el nombre del producto en el objeto inventory temporalmente para la UI
            inv.product_name = prod_name 
            data.append(inv)
        return data

def create_dispatch(data: dict):
    """
    1. Crea registro en dispatches.
    2. Resta cantidad en inventory.
    3. Actualiza status si llega a 0.
    """
    with SessionLocal() as session:
        # 1. Obtener el lote de inventario
        inv_item = session.get(Inventory, data['inventory_id'])
        if not inv_item:
            raise ValueError("Lote de inventario no encontrado.")
        
        cant_despacho = Decimal(str(data['quantity']))
        cant_actual = inv_item.quantity
        
        if cant_despacho > cant_actual:
            raise ValueError(f"Stock insuficiente en este lote. Disponible: {cant_actual}")
            
        # 2. Crear registro de despacho
        new_dispatch = Dispatch(
            inventory_id=data['inventory_id'],
            client_id=data['client_id'],
            quantity=cant_despacho,
            date=data['date'],
            transport_guide=data.get('guide', ''),
            obs=data.get('obs', '')
        )
        session.add(new_dispatch)
        
        # 3. Actualizar Inventario (Restar)
        inv_item.quantity = cant_actual - cant_despacho
        
        # 4. Verificar si se agotó (tolerancia pequeña por decimales)
        if inv_item.quantity <= Decimal("0.001"):
            inv_item.quantity = 0
            inv_item.status = "AGOTADO"
            
        # Opcional: Registrar movimiento de salida en 'movements' para auditoría doble
        mv = Movement(
            inventory_id=inv_item.id,
            product_id=inv_item.product_id,
            change_quantity=-cant_despacho, # Negativo porque sale
            movement_type="OUT",
            reference=f"Despacho Guía {data.get('guide')}",
            notes="Salida por venta/despacho"
        )
        session.add(mv)
            
        session.commit()
        return new_dispatch.id

# ---------- inicialización (solo si se ejecuta directamente) ----------
if __name__ == "__main__":
    create_tables()
    print("Tablas creadas (si no existían).")