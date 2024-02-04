from datetime import datetime
from typing import Any

from sqlalchemy import Engine, JSON, func
from sqlalchemy import event
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


@event.listens_for(Engine, 'connect')
def set_sqlite_pragma(dbapi_connection, _):
    cursor = dbapi_connection.cursor()
    cursor.execute('PRAGMA foreign_keys=ON')
    cursor.close()


class Base(DeclarativeBase):
    __abstract__ = True
    __table_args__ = {'extend_existing': True}
    type_annotation_map = {dict[str, Any]: JSON}

    id: Mapped[int] = mapped_column(primary_key=True)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow, server_default=func.now())
