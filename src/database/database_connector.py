from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.engine.url import make_url


class DatabaseConnector:
    def __init__(self, url: str, echo: bool = False) -> None:
        url_obj = make_url(url)
        connect_args = {}
        if url_obj.get_backend_name() == "postgresql":
            connect_args = {"server_settings": {"timezone": "UTC"}}
        self.engine = create_async_engine(url=url, echo=echo, connect_args=connect_args, pool_pre_ping=True)

        self.session_factory = async_sessionmaker(
            bind=self.engine,
            expire_on_commit=False,
            autocommit=False,
            autoflush=False,
        )
