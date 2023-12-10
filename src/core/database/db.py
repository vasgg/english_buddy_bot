from core.config import settings
from core.database.database_connector import DatabaseConnector

# todo: move from global scope
# could open connection from init, which is bad
db = DatabaseConnector(url=settings.aiosqlite_db_url, echo=settings.db_echo)
