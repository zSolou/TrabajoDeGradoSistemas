from decimal import Decimal
from sqlalchemy import select, update, delete, and_
from sqlalchemy.orm.exc import NoResultFound
from .db import SessionLocal, create_tables
from .models import Client, PredefinedMeasure, User, Product, Inventory, Movement, Dispatch
import psycopg2
import psycopg2.extras
from datetime import datetime, date

# ---------- HERRAMIENTAS ----------
def _parse_date(s):
    if not s: return None
    try:
        if isinstance(s, (date, datetime)): return s if isinstance(s, date) else s.date()
        if isinstance(s, str):
            return datetime.fromisoformat(s.split("T")[0]).date()
        return None
    except: return None

# ---------- INVENTARIO Y PRODUCTOS ----------
def create_product_with_inventory(data: dict):
    with SessionLocal() as session:
        try:
            sku = (data.get("sku") or "").strip()
            name = (data.get("name") or data.get("product_type") or "").strip()
            nro_lote = (data.get("nro_lote") or "").strip()
            
            if not sku or not name: raise ValueError("SKU y Nombre obligatorios.")
            if not nro_lote: raise ValueError("El Número de Lote es obligatorio.")

            # --- CORRECCIÓN: IDEMPOTENCIA (Si existe, no hacer nada y devolver éxito) ---
            lote_existe = session.execute(
                select(Inventory).where(Inventory.nro_lote == nro_lote)
            ).scalars().first()
            
            if lote_existe:
                # En lugar de error, retornamos el ID existente.
                # El frontend pensará que se guardó correctamente (que es verdad).
                # Esto elimina el mensaje de error por doble clic.
                return {"inventory_id": lote_existe.id}
            # --------------------------------------------------------------------------

            # 1. Buscar o Crear Producto en Catálogo
            prod = session.execute(select(Product).where(Product.sku == sku)).scalars().first()
            if not prod:
                prod = Product(sku=sku, name=name, unit=data.get("unit"), quality=data.get("quality"))
                session.add(prod)
                session.flush()

            # 2. Crear Registro de Inventario
            inv = Inventory(
                product_id=prod.id,
                sku=sku,
                nro_lote=nro_lote,
                quantity=Decimal(str(data.get("quantity") or 0)),
                largo=Decimal(str(data.get("largo"))) if data.get("largo") else None,
                ancho=Decimal(str(data.get("ancho"))) if data.get("ancho") else None,
                espesor=Decimal(str(data.get("espesor"))) if data.get("espesor") else None,
                piezas=int(data.get("piezas")) if data.get("piezas") else None,
                prod_date=_parse_date(data.get("prod_date")),
                quality=data.get("quality"),
                drying=data.get("drying"),
                planing=data.get("planing"),
                impregnated=data.get("impregnated"),
                obs=data.get("obs"),
                status="DISPONIBLE"
            )
            session.add(inv)
            session.flush()
            
            # 3. Registrar Movimiento Inicial
            if inv.quantity != 0:
                mv = Movement(
                    inventory_id=inv.id,
                    product_id=prod.id,
                    change_quantity=inv.quantity,
                    movement_type="IN",
                    reference=f"Prod. Lote {inv.nro_lote}",
                    notes="Producción inicial"
                )
                session.add(mv)

            session.commit()
            return {"inventory_id": inv.id}
        except:
            session.rollback()
            raise

def list_inventory_rows():
    with SessionLocal() as session:
        stmt = (
            select(
                Inventory.id, Inventory.sku, Inventory.nro_lote, 
                Product.name,
                Inventory.quantity, Product.unit,
                Inventory.largo, Inventory.ancho, Inventory.espesor,
                Inventory.piezas, Inventory.quality, Inventory.prod_date,
                Inventory.status, Inventory.obs, 
                Product.name,
                Inventory.drying,
                Inventory.planing,
                Inventory.impregnated
            ).join(Product, Product.id == Inventory.product_id)
            .order_by(Inventory.created_at.desc())
        )
        rows = session.execute(stmt).all()
        result = []
        for r in rows:
            result.append({
                "id": r[0], "sku": r[1], "nro_lote": r[2] or "---",
                "product_name": r[3], "quantity": float(r[4] or 0), "unit": r[5],
                "largo": float(r[6] or 0), "ancho": float(r[7] or 0), "espesor": float(r[8] or 0),
                "piezas": int(r[9] or 0), "quality": r[10], "prod_date": r[11],
                "status": r[12], "obs": r[13], 
                "product_type": r[14],
                "drying": r[15],
                "planing": r[16],
                "impregnated": r[17]
            })
        return result

def update_inventory(data: dict):
    with SessionLocal() as session:
        inv = session.get(Inventory, data["id"])
        if not inv: raise ValueError("No encontrado")
        inv.nro_lote = data.get("nro_lote")
        inv.quantity = data.get("quantity")
        inv.largo = data.get("largo")
        inv.ancho = data.get("ancho")
        inv.espesor = data.get("espesor")
        inv.piezas = data.get("piezas")
        inv.prod_date = _parse_date(data.get("prod_date"))
        inv.quality = data.get("quality")
        inv.obs = data.get("obs")
        session.commit()

def delete_inventory(inventory_id: int):
    with SessionLocal() as session:
        inv = session.get(Inventory, inventory_id)
        if inv:
            session.delete(inv)
            session.commit()

# ---------- DESPACHOS Y SALIDAS ----------

def get_available_inventory():
    with SessionLocal() as session:
        stmt = (
            select(Inventory, Product.name)
            .join(Product, Inventory.product_id == Product.id)
            .where(and_(Inventory.quantity > 0, Inventory.status == 'DISPONIBLE'))
            .order_by(Inventory.prod_date)
        )
        results = session.execute(stmt).all()
        data = []
        for inv, p_name in results:
            inv.product_name = p_name 
            inv.product_type = p_name 
            data.append(inv)
        return data

def create_dispatch(data: dict):
    with SessionLocal() as session:
        inv_item = session.get(Inventory, data['inventory_id'])
        if not inv_item: raise ValueError("Lote no encontrado.")
        
        cant_despacho = Decimal(str(data['quantity']))
        if cant_despacho > inv_item.quantity:
            raise ValueError(f"Stock insuficiente. Disp: {inv_item.quantity}")
            
        new_dispatch = Dispatch(
            inventory_id=data['inventory_id'],
            client_id=data['client_id'],
            quantity=cant_despacho,
            date=data['date'],
            transport_guide=data.get('guide', ''),
            obs=data.get('obs', '')
        )
        session.add(new_dispatch)
        
        inv_item.quantity -= cant_despacho
        if inv_item.quantity <= Decimal("0.001"):
            inv_item.quantity = 0
            inv_item.status = "AGOTADO"
            
        mv = Movement(
            inventory_id=inv_item.id, product_id=inv_item.product_id,
            change_quantity=-cant_despacho, movement_type="OUT",
            reference=f"Despacho {data.get('guide')}", notes="Salida"
        )
        session.add(mv)
        session.commit()
        return new_dispatch.id

def list_dispatches_history():
    with SessionLocal() as session:
        stmt = (
            select(
                Dispatch.id, Dispatch.date, Client.name, Product.name,
                Inventory.nro_lote, Inventory.sku, Dispatch.quantity,
                Dispatch.transport_guide, Dispatch.obs, Product.name
            )
            .join(Inventory, Dispatch.inventory_id == Inventory.id)
            .join(Product, Inventory.product_id == Product.id)
            .join(Client, Dispatch.client_id == Client.id)
            .order_by(Dispatch.date.desc())
        )
        rows = session.execute(stmt).all()
        result = []
        for r in rows:
            result.append({
                "id": r[0], "date": r[1], "client": r[2], "product": r[3],
                "lote": r[4] or "---", "sku": r[5], "quantity": float(r[6]),
                "guide": r[7] or "S/G", "obs": r[8] or "", "type": r[9]
            })
        return result

# ---------- CLIENTES / MEDIDAS / USUARIOS ----------
def create_client(data):
    with SessionLocal() as s:
        c = Client(name=data["nombre"], document_id=data["cedula_rif"], phone=data["telefono"], email=data["email"], address=data["direccion"], is_active=True)
        s.add(c); s.commit(); return c.id

def list_clients(solo_activos=True):
    with SessionLocal() as s:
        stmt = select(Client).order_by(Client.name)
        if solo_activos: stmt = stmt.where(Client.is_active == True)
        return s.execute(stmt).scalars().all()

def update_client(cid, data):
    with SessionLocal() as s:
        c = s.get(Client, cid)
        if c: 
            c.name = data.get("nombre", c.name)
            c.document_id = data.get("cedula_rif", c.document_id)
            c.phone = data.get("telefono", c.phone)
            c.email = data.get("email", c.email)
            c.address = data.get("direccion", c.address)
            s.commit()

def toggle_client_active(cid, active):
    with SessionLocal() as s:
        c = s.get(Client, cid); 
        if c: c.is_active = active; s.commit()

def create_measure(data):
    with SessionLocal() as s:
        m = PredefinedMeasure(product_type=data["product_type"], name=data["name"], largo=data["largo"], ancho=data["ancho"], espesor=data["espesor"], is_active=True)
        s.add(m); s.commit(); return m

def get_measures_by_type(ptype):
    with SessionLocal() as session:
        stmt = select(PredefinedMeasure).where(and_(PredefinedMeasure.product_type == ptype, PredefinedMeasure.is_active == True))
        return session.execute(stmt).scalars().all()

def delete_measure(mid):
    with SessionLocal() as session:
        m = session.get(PredefinedMeasure, mid)
        if m:
            m.is_active = False 
            session.commit()

def authenticate_user_plain(u, p):
    with SessionLocal() as s:
        user = s.execute(select(User).where(User.username == u)).scalars().first()
        if user and user.active and user.password_hash == p: return {"id": user.id, "username": user.username, "role": user.role}
        return None