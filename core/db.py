# db.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from screens.inventario import InventarioScreen
from .models import Base

import core.repo as repo

# Ajusta esta URL con tus credenciales y base
DATABASE_URL = "postgresql+psycopg2://postgres@localhost:5432/astillados_db"

engine = create_engine(DATABASE_URL, future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

def create_tables():
    """Crear tablas definidas en models.Base (solo en desarrollo/inicialización)."""
    Base.metadata.create_all(bind=engine)