from decimal import Decimal
from sqlalchemy import select, update, delete, and_, or_
from sqlalchemy.exc import IntegrityError
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

            # --- VALIDACIÓN INTELIGENTE ---
            existing = session.execute(select(Inventory).where(Inventory.nro_lote == nro_lote)).scalars().first()
            
            if existing:
                existing_qty = float(existing.quantity)
                new_qty = float(data.get("quantity") or 0)
                if existing.sku == sku and abs(existing_qty - new_qty) < 0.01:
                    return {"inventory_id": existing.id, "status": "ignored_duplicate"}
                raise ValueError(f"El Lote '{nro_lote}' ya existe con otros datos.")
            # ------------------------------

            prod = session.execute(select(Product).where(Product.sku == sku)).scalars().first()
            if not prod:
                prod = Product(sku=sku, name=name, unit=data.get("unit"), quality=data.get("quality"))
                session.add(prod)
                session.flush()

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
            
            if inv.quantity != 0:
                mv = Movement(
                    inventory_id=inv.id, product_id=prod.id, change_quantity=inv.quantity,
                    movement_type="IN", reference=f"Prod. Lote {inv.nro_lote}", notes="Producción inicial"
                )
                session.add(mv)

            session.commit()
            return {"inventory_id": inv.id, "status": "created"}

        except IntegrityError:
            session.rollback()
            return {"status": "ignored_duplicate"}
        except Exception:
            session.rollback()
            raise

# --- CAMBIO 1: FILTRO DE VISIBILIDAD ---
def list_inventory_rows(mostrar_agotados=False):
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
                Inventory.drying, Inventory.planing, Inventory.impregnated
            ).join(Product, Product.id == Inventory.product_id)
        )

        # Si NO queremos ver agotados, filtramos solo los que tienen cantidad > 0
        if not mostrar_agotados:
            stmt = stmt.where(Inventory.quantity > 0)
        
        stmt = stmt.order_by(Inventory.created_at.desc())
        
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
                "drying": r[15], "planing": r[16], "impregnated": r[17]
            })
        return result

# --- CAMBIO 2: ELIMINACIÓN LÓGICA (DAR DE BAJA) ---
def delete_inventory(inventory_id: int):
    with SessionLocal() as session:
        inv = session.get(Inventory, inventory_id)
        if inv and inv.quantity > 0:
            # En lugar de borrar, sacamos todo el stock y cambiamos estado
            qty_to_remove = inv.quantity
            
            # Registrar movimiento de salida por baja
            mv = Movement(
                inventory_id=inv.id,
                product_id=inv.product_id,
                change_quantity=-qty_to_remove,
                movement_type="OUT",
                reference="BAJA MANUAL",
                notes="Eliminación lógica desde Inventario"
            )
            session.add(mv)

            # Actualizar inventario a CERO y estado BAJA
            inv.quantity = 0
            inv.status = "BAJA" # O "AGOTADO"
            
            session.commit()
            
        elif inv and inv.quantity == 0:
            # Si ya está en 0, solo aseguramos el estado
            inv.status = "BAJA"
            session.commit()

# ... (El resto del archivo create_dispatch, update_inventory, etc. sigue igual) ...
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

def get_available_inventory():
    with SessionLocal() as session:
        stmt = (select(Inventory, Product.name).join(Product, Inventory.product_id == Product.id).where(and_(Inventory.quantity > 0, Inventory.status == 'DISPONIBLE')).order_by(Inventory.prod_date))
        results = session.execute(stmt).all()
        data = []
        for inv, p_name in results:
            inv.product_name = p_name; inv.product_type = p_name; data.append(inv)
        return data

def create_dispatch(data: dict):
    with SessionLocal() as session:
        inv_item = session.get(Inventory, data['inventory_id'])
        if not inv_item: raise ValueError("Lote no encontrado.")
        cant = Decimal(str(data['quantity']))
        if cant > inv_item.quantity: raise ValueError(f"Stock insuficiente. Disp: {inv_item.quantity}")
        new_d = Dispatch(inventory_id=data['inventory_id'], client_id=data['client_id'], quantity=cant, date=data['date'], transport_guide=data.get('guide', ''), obs=data.get('obs', ''))
        session.add(new_d)
        inv_item.quantity -= cant
        if inv_item.quantity <= 0: inv_item.quantity=0; inv_item.status="AGOTADO"
        session.add(Movement(inventory_id=inv_item.id, product_id=inv_item.product_id, change_quantity=-cant, movement_type="OUT", reference=f"Despacho {data.get('guide')}", notes="Salida"))
        session.commit(); return new_d.id

def list_dispatches_history():
    with SessionLocal() as session:
        stmt = (select(Dispatch.id, Dispatch.date, Client.name, Product.name, Inventory.nro_lote, Inventory.sku, Dispatch.quantity, Dispatch.transport_guide, Dispatch.obs, Product.name).join(Inventory, Dispatch.inventory_id == Inventory.id).join(Product, Inventory.product_id == Product.id).join(Client, Dispatch.client_id == Client.id).order_by(Dispatch.date.desc()))
        rows = session.execute(stmt).all()
        return [{"id":r[0],"date":r[1],"client":r[2],"product":r[3],"lote":r[4] or "-","sku":r[5],"quantity":float(r[6]),"guide":r[7] or "S/G","obs":r[8] or "","type":r[9]} for r in rows]

def create_client(data):
    with SessionLocal() as s: c=Client(name=data["nombre"], document_id=data["cedula_rif"], phone=data["telefono"], email=data["email"], address=data["direccion"], is_active=True); s.add(c); s.commit(); return c.id
def list_clients(solo_activos=True):
    with SessionLocal() as s: q=select(Client).order_by(Client.name); return s.execute(q.where(Client.is_active==True) if solo_activos else q).scalars().all()
def update_client(cid, data):
    with SessionLocal() as s: c=s.get(Client, cid); 
    if c: c.name=data.get("nombre",c.name); c.document_id=data.get("cedula_rif",c.document_id); c.phone=data.get("telefono",c.phone); c.email=data.get("email",c.email); c.address=data.get("direccion",c.address); s.commit()
def toggle_client_active(cid, active):
    with SessionLocal() as s: c=s.get(Client, cid); 
    if c: c.is_active=active; s.commit()
def create_measure(data):
    with SessionLocal() as s: m=PredefinedMeasure(product_type=data["product_type"], name=data["name"], largo=data["largo"], ancho=data["ancho"], espesor=data["espesor"], is_active=True); s.add(m); s.commit(); return m
def get_measures_by_type(ptype):
    with SessionLocal() as s: return s.execute(select(PredefinedMeasure).where(and_(PredefinedMeasure.product_type==ptype, PredefinedMeasure.is_active==True))).scalars().all()
def delete_measure(mid):
    with SessionLocal() as s: m=s.get(PredefinedMeasure, mid); 
    if m: m.is_active=False; s.commit()
def authenticate_user_plain(u, p):
    with SessionLocal() as s: us=s.execute(select(User).where(User.username==u)).scalars().first(); 
    return {"id":us.id,"username":us.username,"role":us.role} if us and us.active and us.password_hash==p else None
def delete_inventory_logical(iid): # Alias
    delete_inventory(iid)
# ... (Todo lo anterior en repo.py se mantiene igual) ...

# ---------- NUEVAS FUNCIONES PARA REPORTES AVANZADOS ----------

def report_production_period(start_date, end_date):
    """Retorna todo lo producido (ingresado) en un rango de fechas."""
    with SessionLocal() as s:
        stmt = (
            select(Inventory, Product.name)
            .join(Product, Inventory.product_id == Product.id)
            .where(and_(
                Inventory.prod_date >= start_date,
                Inventory.prod_date <= end_date
            ))
            .order_by(Inventory.prod_date)
        )
        results = s.execute(stmt).all()
        data = []
        for inv, pname in results:
            data.append({
                "fecha": inv.prod_date,
                "lote": inv.nro_lote,
                "producto": pname,
                "cantidad": float(inv.quantity), # Stock actual
                "piezas_iniciales": inv.piezas or 0, # Lo que se produjo originalmente
                "status": inv.status
            })
        return data

def report_dispatches_detailed(start_date, end_date, client_id=None):
    """
    Reporte de: Qué salió, de qué lote y a qué cliente.
    """
    with SessionLocal() as s:
        stmt = (
            select(
                Dispatch.date,
                Dispatch.transport_guide,
                Client.name,
                Product.name,
                Inventory.nro_lote,
                Dispatch.quantity,
                Dispatch.obs
            )
            .join(Inventory, Dispatch.inventory_id == Inventory.id)
            .join(Product, Inventory.product_id == Product.id)
            .join(Client, Dispatch.client_id == Client.id)
            .where(and_(Dispatch.date >= start_date, Dispatch.date <= end_date))
        )
        
        if client_id:
            stmt = stmt.where(Dispatch.client_id == client_id)
            
        stmt = stmt.order_by(Dispatch.date.desc())
        
        results = s.execute(stmt).all()
        return [{
            "fecha": r[0], "guia": r[1], "cliente": r[2],
            "producto": r[3], "lote": r[4], "cantidad": float(r[5]), "obs": r[6]
        } for r in results]

def report_by_lot_range(start_lote: int, end_lote: int):
    """
    Busca lotes en un rango numérico específico.
    NOTA: Esto asume que los lotes son numéricos.
    """
    with SessionLocal() as s:
        # Traemos todo y filtramos en Python para evitar problemas de cast en SQL con strings sucios
        stmt = (
            select(Inventory, Product.name)
            .join(Product, Inventory.product_id == Product.id)
        )
        results = s.execute(stmt).all()
        
        data = []
        for inv, pname in results:
            try:
                # Intentamos convertir el lote a entero
                lote_num = int(inv.nro_lote)
                if start_lote <= lote_num <= end_lote:
                    data.append({
                        "lote": inv.nro_lote,
                        "producto": pname,
                        "fecha_prod": inv.prod_date,
                        "stock_actual": float(inv.quantity),
                        "estado": inv.status
                    })
            except ValueError:
                continue # Ignoramos lotes no numéricos (ej: "A-1")
                
        # Ordenamos por número de lote
        data.sort(key=lambda x: int(x["lote"]))
        return data
    
def report_production_period(start_date, end_date, product_name=None):
    """
    Retorna todo lo producido (ingresado) en un rango de fechas.
    Opcional: Filtrar por nombre de producto.
    """
    with SessionLocal() as s:
        stmt = (
            select(Inventory, Product.name)
            .join(Product, Inventory.product_id == Product.id)
            .where(and_(
                Inventory.prod_date >= start_date,
                Inventory.prod_date <= end_date
            ))
        )
        
        if product_name:
            # Filtro insensible a mayúsculas/minúsculas parcial
            stmt = stmt.where(Product.name.ilike(f"%{product_name}%"))
            
        stmt = stmt.order_by(Inventory.prod_date)
        
        results = s.execute(stmt).all()
        data = []
        for inv, pname in results:
            data.append({
                "fecha": inv.prod_date,
                "lote": inv.nro_lote,
                "producto": pname,
                "cantidad": float(inv.quantity),
                "piezas_iniciales": inv.piezas or 0,
                "status": inv.status
            })
        return data

def report_dispatches_detailed(start_date, end_date, client_id=None, product_name=None):
    """
    Reporte de salidas con filtros de Cliente y Producto.
    """
    with SessionLocal() as s:
        stmt = (
            select(
                Dispatch.date,
                Dispatch.transport_guide,
                Client.name,
                Product.name,
                Inventory.nro_lote,
                Dispatch.quantity,
                Dispatch.obs
            )
            .join(Inventory, Dispatch.inventory_id == Inventory.id)
            .join(Product, Inventory.product_id == Product.id)
            .join(Client, Dispatch.client_id == Client.id)
            .where(and_(Dispatch.date >= start_date, Dispatch.date <= end_date))
        )
        
        if client_id:
            stmt = stmt.where(Dispatch.client_id == client_id)
            
        if product_name:
            stmt = stmt.where(Product.name.ilike(f"%{product_name}%"))
            
        stmt = stmt.order_by(Dispatch.date.desc())
        
        results = s.execute(stmt).all()
        return [{
            "fecha": r[0], "guia": r[1], "cliente": r[2],
            "producto": r[3], "lote": r[4], "cantidad": float(r[5]), "obs": r[6]
        } for r in results]

def report_by_lot_range(start_lote: int, end_lote: int):
    # (Esta función se mantiene igual que antes)
    with SessionLocal() as s:
        stmt = (
            select(Inventory, Product.name)
            .join(Product, Inventory.product_id == Product.id)
        )
        results = s.execute(stmt).all()
        data = []
        for inv, pname in results:
            try:
                lote_num = int(inv.nro_lote)
                if start_lote <= lote_num <= end_lote:
                    data.append({
                        "lote": inv.nro_lote,
                        "producto": pname,
                        "fecha_prod": inv.prod_date,
                        "stock_actual": float(inv.quantity),
                        "estado": inv.status
                    })
            except ValueError: continue
        data.sort(key=lambda x: int(x["lote"]))
        return data
    
    # ---------- REPORTES AVANZADOS ----------

def report_production_period(start_date, end_date, product_name=None):
    with SessionLocal() as s:
        stmt = (
            select(Inventory, Product.name)
            .join(Product, Inventory.product_id == Product.id)
            .where(and_(Inventory.prod_date >= start_date, Inventory.prod_date <= end_date))
        )
        if product_name: stmt = stmt.where(Product.name.ilike(f"%{product_name}%"))
        stmt = stmt.order_by(Inventory.prod_date)
        results = s.execute(stmt).all()
        data = []
        for inv, pname in results:
            data.append({
                "fecha": inv.prod_date, "lote": inv.nro_lote, "producto": pname,
                "cantidad": float(inv.quantity), "piezas_iniciales": inv.piezas or 0, "status": inv.status
            })
        return data

def report_dispatches_detailed(start_date, end_date, client_id=None, product_name=None):
    with SessionLocal() as s:
        stmt = (
            select(Dispatch.date, Dispatch.transport_guide, Client.name, Product.name, Inventory.nro_lote, Dispatch.quantity, Dispatch.obs)
            .join(Inventory, Dispatch.inventory_id == Inventory.id)
            .join(Product, Inventory.product_id == Product.id)
            .join(Client, Dispatch.client_id == Client.id)
            .where(and_(Dispatch.date >= start_date, Dispatch.date <= end_date))
        )
        if client_id: stmt = stmt.where(Dispatch.client_id == client_id)
        if product_name: stmt = stmt.where(Product.name.ilike(f"%{product_name}%"))
        stmt = stmt.order_by(Dispatch.date.desc())
        results = s.execute(stmt).all()
        return [{"fecha": r[0], "guia": r[1], "cliente": r[2], "producto": r[3], "lote": r[4], "cantidad": float(r[5]), "obs": r[6]} for r in results]

# --- CAMBIO: AHORA ACEPTA UN FILTRO PARA BAJAS ---
def report_by_lot_range(start_lote: int, end_lote: int, incluir_bajas: bool = False):
    with SessionLocal() as s:
        stmt = select(Inventory, Product.name).join(Product, Inventory.product_id == Product.id)
        results = s.execute(stmt).all()
        data = []
        for inv, pname in results:
            try:
                lote_num = int(inv.nro_lote)
                if start_lote <= lote_num <= end_lote:
                    # FILTRO DE BAJAS
                    if not incluir_bajas and (inv.quantity <= 0 or inv.status == "BAJA"):
                        continue
                    
                    data.append({
                        "lote": inv.nro_lote, "producto": pname, "fecha_prod": inv.prod_date,
                        "stock_actual": float(inv.quantity), "estado": inv.status
                    })
            except ValueError: continue
        data.sort(key=lambda x: int(x["lote"]))
        return data
    
def report_production_period(start_date, end_date, product_name=None, quality=None):
    """
    Reporte de producción con filtro de CALIDAD agregado.
    """
    with SessionLocal() as s:
        stmt = (
            select(Inventory, Product.name)
            .join(Product, Inventory.product_id == Product.id)
            .where(and_(Inventory.prod_date >= start_date, Inventory.prod_date <= end_date))
        )
        
        if product_name: 
            stmt = stmt.where(Product.name.ilike(f"%{product_name}%"))
            
        # --- NUEVO FILTRO: CALIDAD ---
        if quality and quality != "Todas":
            stmt = stmt.where(Inventory.quality == quality)
        # -----------------------------

        stmt = stmt.order_by(Inventory.prod_date)
        results = s.execute(stmt).all()
        
        data = []
        for inv, pname in results:
            data.append({
                "fecha": inv.prod_date, "lote": inv.nro_lote, "producto": pname,
                "cantidad": float(inv.quantity), "piezas_iniciales": inv.piezas or 0, 
                "status": inv.status, "quality": inv.quality
            })
        return data

def report_dispatches_detailed(start_date, end_date, client_id=None, product_name=None, guide=None):
    """
    Reporte de despachos con filtro de GUÍA agregado.
    """
    with SessionLocal() as s:
        stmt = (
            select(
                Dispatch.date, Dispatch.transport_guide, Client.name, 
                Product.name, Inventory.nro_lote, Dispatch.quantity, Dispatch.obs
            )
            .join(Inventory, Dispatch.inventory_id == Inventory.id)
            .join(Product, Inventory.product_id == Product.id)
            .join(Client, Dispatch.client_id == Client.id)
            .where(and_(Dispatch.date >= start_date, Dispatch.date <= end_date))
        )
        
        if client_id: stmt = stmt.where(Dispatch.client_id == client_id)
        if product_name: stmt = stmt.where(Product.name.ilike(f"%{product_name}%"))
        
        # --- NUEVO FILTRO: GUÍA ---
        if guide:
            stmt = stmt.where(Dispatch.transport_guide.ilike(f"%{guide}%"))
        # --------------------------

        stmt = stmt.order_by(Dispatch.date.desc())
        results = s.execute(stmt).all()
        return [{
            "fecha": r[0], "guia": r[1], "cliente": r[2], 
            "producto": r[3], "lote": r[4], "cantidad": float(r[5]), "obs": r[6]
        } for r in results]

def report_by_lot_range(start_lote: int, end_lote: int, incluir_bajas: bool = False, product_name=None):
    """
    Búsqueda por lotes con filtro de TIPO DE PRODUCTO agregado.
    """
    with SessionLocal() as s:
        stmt = select(Inventory, Product.name).join(Product, Inventory.product_id == Product.id)
        
        # --- NUEVO FILTRO: PRODUCTO (Pre-filtrado SQL para eficiencia) ---
        if product_name:
            stmt = stmt.where(Product.name.ilike(f"%{product_name}%"))
        # -----------------------------------------------------------------

        results = s.execute(stmt).all()
        data = []
        for inv, pname in results:
            try:
                lote_num = int(inv.nro_lote)
                if start_lote <= lote_num <= end_lote:
                    if not incluir_bajas and (inv.quantity <= 0 or inv.status == "BAJA"):
                        continue
                    
                    data.append({
                        "lote": inv.nro_lote, "producto": pname, "fecha_prod": inv.prod_date,
                        "stock_actual": float(inv.quantity), "estado": inv.status
                    })
            except ValueError: continue
        data.sort(key=lambda x: int(x["lote"]))
        return data