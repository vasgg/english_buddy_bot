from config import settings
from database.database_connector import DatabaseConnector

# todo: move from global scope
# could open connection from init, which is bad
db = DatabaseConnector(url=settings.aiosqlite_db_url, echo=settings.db_echo)
