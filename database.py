"""Create the SQLAlchemy engine and session factory."""
from sqlalchemy import create_engine, event
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from config import settings


class Base(DeclarativeBase):
    pass


if settings.database_url.startswith("sqlite"):
    connect_args = {"check_same_thread": False}
elif settings.database_ssl_ca:
    # Hosted MySQL providers can use this CA file to verify encrypted connections.
    connect_args = {"ssl": {"ca": settings.database_ssl_ca}}
else:
    connect_args = {}
engine = create_engine(settings.database_url, connect_args=connect_args, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

if settings.database_url.startswith("sqlite"):
    @event.listens_for(engine, "connect")
    def enable_sqlite_foreign_keys(connection, _record):
        """Make SQLite apply the same foreign-key delete rules as MySQL."""
        cursor = connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()
