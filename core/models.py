# core/models.py
from sqlalchemy import (
    Column, Integer, String, Text, Boolean, Date, DateTime, Numeric, ForeignKey, JSON
)
from datetime import datetime
from sqlalchemy.sql import func
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    username = Column(String, unique=True, nullable=False)
    password_hash = Column(Text, nullable=False)
    full_name = Column(String)
    role = Column(String, nullable=False, default="user")
    email = Column(String)
    active = Column(Boolean, default=True)

class Client(Base):
    __tablename__ = "clients"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(Text, nullable=False)
    document_id = Column(Text)
    phone = Column(Text)
    email = Column(Text)
    address = Column(Text)
    # --- NUEVA LÍNEA ---
    is_active = Column(Boolean, default=True) 
    # -------------------
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), onupdate=datetime.utcnow)

class Product(Base):
    __tablename__ = "products"
    id = Column(Integer, primary_key=True)
    sku = Column(String, unique=True)
    name = Column(String, nullable=False)
    description = Column(Text)
    unit = Column(String)   # e.g., m3, pieza
    quality = Column(String)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class Inventory(Base):
    __tablename__ = "inventory"
    id = Column(Integer, primary_key=True)
    product_id = Column(Integer, ForeignKey("products.id", ondelete="CASCADE"), nullable=False)
    # Eliminadas: lot_code y location
    quantity = Column(Numeric(18,6), nullable=False, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Atributos de medida y producción
    largo = Column(Numeric(10,2))
    ancho = Column(Numeric(10,2))
    espesor = Column(Numeric(10,2))
    piezas = Column(Integer)

    prod_date = Column(Date)      # Fecha de producción (Date)
    dispatch_date = Column(Date)  # Fecha de despacho (Date)

    quality = Column(String)
    drying = Column(String)
    planing = Column(String)
    impregnated = Column(String)
    obs = Column(Text)

    product = relationship("Product", backref="inventory_items")

class Movement(Base):
    __tablename__ = "movements"
    id = Column(Integer, primary_key=True)
    inventory_id = Column(Integer, ForeignKey("inventory.id", ondelete="SET NULL"))
    product_id = Column(Integer, ForeignKey("products.id", ondelete="CASCADE"), nullable=False)
    change_quantity = Column(Numeric(18,6), nullable=False)  # + entrada, - salida
    movement_type = Column(String, nullable=False)  # IN, OUT, ADJUSTMENT, TRANSFER
    reference = Column(Text)
    performed_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"))
    performed_at = Column(DateTime(timezone=True), server_default=func.now())
    notes = Column(Text)

class Setting(Base):
    __tablename__ = "settings"
    key = Column(String, primary_key=True)
    value = Column(Text)
    description = Column(Text)

class AuditLog(Base):
    __tablename__ = "audit_logs"
    id = Column(Integer, primary_key=True)
    actor_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"))
    action = Column(Text, nullable=False)
    object_type = Column(String)
    object_id = Column(String)
    occurred_at = Column(DateTime(timezone=True), server_default=func.now())
    details = Column(JSON)
    
# EN core/models.py

# ... (Tus otras clases Product, Inventory, etc.)

class PredefinedMeasure(Base):
    __tablename__ = "predefined_measures"

    id = Column(Integer, primary_key=True, index=True)
    product_type = Column(Text, nullable=False)
    name = Column(Text)
    largo = Column(Numeric(10, 2))
    ancho = Column(Numeric(10, 2))
    espesor = Column(Numeric(10, 2))