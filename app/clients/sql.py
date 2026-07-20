import pyodbc
from app.config import settings

def get_db_connection():
    conn = pyodbc.connect(settings.sql_connection_string)
    return conn
