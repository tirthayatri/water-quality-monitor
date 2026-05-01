import os
from sqlalchemy import event
from sqlalchemy.engine import Engine
import sqlite3

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

# 每次 SQLite 连接建立时，自动启用外键约束
@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    if isinstance(dbapi_connection, sqlite3.Connection):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-key-123'
    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(BASE_DIR, 'instance', 'water.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False