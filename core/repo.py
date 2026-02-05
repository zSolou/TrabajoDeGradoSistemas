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

# ---------- HERRAMIENTAS CRUD ----------

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

# ---------- INVENTARIO Y PRODUCTOS ----------

def create_product_with_inventory(data: dict):
    """
    Crea el producto (si no existe) y registra el Lote en inventario.
    Ahora guarda 'nro_lote' y omite 'dispatch_date'.
    """
    with SessionLocal() as session:
        try:
            sku = (data.get("sku") or "").strip()
            name = (data.get("name") or data.get("product_type") or "").strip()
            
            if not sku: raise ValueError("SKU es obligatorio.")
            if not name: raise ValueError("Nombre/Tipo es obligatorio.")

            # 1. Buscar o Crear Producto en Catálogo (Tabla products)
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

            # 2. Crear Registro de Inventario (Lote)
            inv = Inventory(
                product_id=prod.id,
                sku=sku,                      # SKU redundante para búsqueda rápida
                nro_lote=data.get("nro_lote"), # <--- NUEVO: Lote Físico
                quantity=Decimal(str(data.get("quantity") or 0)),
                largo=Decimal(str(data.get("largo"))) if data.get("largo") else None,
                ancho=Decimal(str(data.get("ancho"))) if data.get("ancho") else None,
                espesor=Decimal(str(data.get("espesor"))) if data.get("espesor") else None,
                piezas=int(data.get("piezas")) if data.get("piezas") else None,
                prod_date=_parse_date(data.get("prod_date")),
                # dispatch_date REMOVIDO
                quality=data.get("quality"),
                drying=data.get("drying"),
                planing=data.get("planing"),
                impregnated=data.get("impregnated"),
                obs=data.get("obs"),
                status="DISPONIBLE"
            )
            session.add(inv)
            session.flush()

            # 3. Registrar Movimiento Inicial (IN)
            qty = inv.quantity or Decimal("0")
            if qty != 0:
                mv = Movement(
                    inventory_id=inv.id,
                    product_id=prod.id,
                    change_quantity=qty,
                    movement_type="IN",
                    reference=f"Prod. Lote {inv.nro_lote}",
                    performed_by=data.get("performed_by"),
                    notes="Producción inicial"
                )
                session.add(mv)

            session.commit()
            return {"inventory_id": inv.id, "product_id": prod.id}
        except Exception:
            session.rollback()
            raise

def list_inventory_rows():
    """
    Lista el inventario mostrando LOTE en lugar de fecha despacho.
    """
    with SessionLocal() as session:
        stmt = (
            select(
                Inventory.id,         # 0
                Inventory.sku,        # 1
                Inventory.nro_lote,   # 2 (Nuevo)
                Product.name,         # 3
                Inventory.quantity,   # 4
                Product.unit,         # 5
                Inventory.largo,      # 6
                Inventory.ancho,      # 7
                Inventory.espesor,    # 8
                Inventory.piezas,     # 9
                Inventory.quality,    # 10
                Inventory.prod_date,  # 11
                Inventory.status,     # 12
                Inventory.obs         # 13
            ).join(Product, Product.id == Inventory.product_id)
            .order_by(Inventory.created_at.desc())
        )
        rows = session.execute(stmt).all()
        
        result = []
        for r in rows:
            result.append({
                "id": r[0],
                "sku": r[1],
                "nro_lote": r[2] or "---",
                "product_type": r[3],
                "quantity": float(r[4] or 0),
                "unit": r[5] or "",
                "largo": float(r[6] or 0),
                "ancho": float(r[7] or 0),
                "espesor": float(r[8] or 0),
                "piezas": int(r[9] or 0),
                "quality": r[10] or "",
                "prod_date": r[11],
                "status": r[12] or "DISPONIBLE",
                "obs": r[13] or ""
            })
        return result

def update_inventory(data: dict):
    """
    Actualiza datos del lote (corregir medidas, lote mal escrito, etc).
    """
    with SessionLocal() as session:
        inv = session.get(Inventory, data["id"])
        if not inv:
            raise ValueError("Registro no encontrado")

        inv.nro_lote = data.get("nro_lote")
        inv.quantity = data.get("quantity")
        inv.largo = data.get("largo")
        inv.ancho = data.get("ancho")
        inv.espesor = data.get("espesor")
        inv.piezas = data.get("piezas")
        inv.prod_date = _parse_date(data.get("prod_date"))
        inv.quality = data.get("quality")
        inv.obs = data.get("obs")
        # No actualizamos status aquí para no romper lógica de agotado

        session.commit()

def delete_inventory(inventory_id: int):
    with SessionLocal() as session:
        inv = session.get(Inventory, inventory_id)
        if not inv: raise ValueError("No encontrado")
        session.delete(inv)
        session.commit()

# ---------- DESPACHOS Y SALIDAS (NUEVO) ----------

def get_available_inventory():
    """
    Retorna lotes disponibles (Stock > 0) para despachar.
    """
    with SessionLocal() as session:
        # Join para obtener el nombre del producto
        stmt = (
            select(Inventory, Product.name)
            .join(Product, Inventory.product_id == Product.id)
            .where(and_(Inventory.quantity > 0, Inventory.status == 'DISPONIBLE'))
            .order_by(Inventory.prod_date)
        )
        results = session.execute(stmt).all()
        
        data = []
        for inv, prod_name in results:
            inv.product_name = prod_name # Atributo temporal para UI
            data.append(inv)
        return data

def create_dispatch(data: dict):
    """
    Registra salida en 'dispatches' y descuenta de 'inventory'.
    """
    with SessionLocal() as session:
        # 1. Obtener Lote
        inv_item = session.get(Inventory, data['inventory_id'])
        if not inv_item:
            raise ValueError("Lote no encontrado.")
        
        cant_despacho = Decimal(str(data['quantity']))
        cant_actual = inv_item.quantity
        
        if cant_despacho > cant_actual:
            raise ValueError(f"Stock insuficiente. Disponible: {cant_actual}")
            
        # 2. Crear Despacho
        new_dispatch = Dispatch(
            inventory_id=data['inventory_id'],
            client_id=data['client_id'],
            quantity=cant_despacho,
            date=data['date'],
            transport_guide=data.get('guide', ''),
            obs=data.get('obs', '')
        )
        session.add(new_dispatch)
        
        # 3. Restar Inventario
        inv_item.quantity = cant_actual - cant_despacho
        
        # 4. Verificar Agotado
        if inv_item.quantity <= Decimal("0.001"):
            inv_item.quantity = 0
            inv_item.status = "AGOTADO"
            
        # 5. Registrar Movimiento (Auditoría)
        mv = Movement(
            inventory_id=inv_item.id,
            product_id=inv_item.product_id,
            change_quantity=-cant_despacho,
            movement_type="OUT",
            reference=f"Despacho {data.get('guide')}",
            performed_by=None, # Puedes pasar el user_id si lo tienes
            notes="Salida por Despacho"
        )
        session.add(mv)
            
        session.commit()
        return new_dispatch.id

# ---------- CLIENTES ----------
def create_client(data: dict):
    with SessionLocal() as session:
        client = Client(
            name=data.get("nombre"),
            document_id=data.get("cedula_rif"),
            phone=data.get("telefono"),
            email=data.get("email"),
            address=data.get("direccion"),
            is_active=True
        )
        session.add(client)
        session.commit()
        return client.id

def list_clients(solo_activos=True):
    with SessionLocal() as session:
        stmt = select(Client)
        if solo_activos:
            stmt = stmt.where(Client.is_active == True)
        stmt = stmt.order_by(Client.name)
        return session.execute(stmt).scalars().all()

def update_client(client_id: int, data: dict):
    with SessionLocal() as session:
        client = session.get(Client, client_id)
        if not client: raise ValueError("Cliente no encontrado")
        
        client.name = data.get("nombre", client.name)
        client.document_id = data.get("cedula_rif", client.document_id)
        client.phone = data.get("telefono", client.phone)
        client.email = data.get("email", client.email)
        client.address = data.get("direccion", client.address)
        if "is_active" in data:
            client.is_active = data["is_active"]
        session.commit()

def toggle_client_active(client_id: int, active: bool):
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
        return measure

def get_measures_by_type(p_type: str):
    with SessionLocal() as session:
        stmt = select(PredefinedMeasure).where(PredefinedMeasure.product_type == p_type)
        return session.execute(stmt).scalars().all()

def delete_measure(measure_id: int):
    with SessionLocal() as session:
        measure = session.get(PredefinedMeasure, measure_id)
        if measure:
            session.delete(measure)
            session.commit()

# ---------- USUARIOS ----------
def authenticate_user_plain(username: str, password: str):
    with SessionLocal() as session:
        user = session.execute(select(User).where(User.username == username)).scalars().first()
        if not user or not user.active: return None
        if user.password_hash == password:
            return {"id": user.id, "username": user.username, "role": user.role}
        return None