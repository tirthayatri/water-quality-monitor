import os
import warnings
from sqlalchemy import event
from sqlalchemy.engine import Engine
import sqlite3

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    if isinstance(dbapi_connection, sqlite3.Connection):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

def _get_secret_key():
    key = os.environ.get('SECRET_KEY')
    if not key:
        warnings.warn(
            "SECRET_KEY 未在环境变量中设置，当前使用不安全的默认值，请勿在生产环境中运行",
            stacklevel=1
        )
        return 'dev-key-123'
    return key

class Config:
    SECRET_KEY = _get_secret_key()
    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(BASE_DIR, 'instance', 'water.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False