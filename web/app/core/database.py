from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import QueuePool
from sqlalchemy.orm import sessionmaker
 
import sqlalchemy as sa

Base = declarative_base()

def get_db(nombre_file): 
    connection_string = (
        r"DRIVER={Microsoft Access Driver (*.mdb, *.accdb)};"
        rf"DBQ=C:\Users\Aaron\Documents\{nombre_file}.accdb;"
        r"pool_pre_ping=True;"
        r"ExtendedAnsiSQL=1;"
    )

    connection_url = sa.engine.URL.create( 
            "access+pyodbc",
            query={"odbc_connect": connection_string}
    )

    engine = sa.create_engine(connection_url, poolclass=QueuePool )
    SessionLocal = sessionmaker(autocommit=False, autoflush=True, bind=engine)

    db = SessionLocal()

    try:
        yield db
    finally: 
        db.close()
        

def get_db_sql(): 
    # Crear el motor de conexión (engine)
    DATABASE_URL = "postgresql+psycopg2://postgres:Escalera1!@localhost/postgres"

    engine = sa.create_engine(DATABASE_URL, poolclass=QueuePool)

    # Crear un sessionmaker vinculado al engine
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    # Función para obtener una sesión
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()