from sqlalchemy import event
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine


class DatabaseConnector:
    def __init__(self, url: str, echo: bool = False) -> None:
        self.engine = create_async_engine(url=url, echo=echo, connect_args={"timeout": 30}, pool_pre_ping=True)

        if self.engine.dialect.name == "sqlite":

            def _set_sqlite_pragmas(dbapi_connection, connection_record):
                cursor = dbapi_connection.cursor()
                cursor.execute("PRAGMA journal_mode=WAL")
                cursor.execute("PRAGMA synchronous=NORMAL")
                cursor.close()

            event.listen(self.engine.sync_engine, "connect", _set_sqlite_pragmas)

        self.session_factory = async_sessionmaker(
            bind=self.engine, expire_on_commit=False, autocommit=False, autoflush=False,
        )
