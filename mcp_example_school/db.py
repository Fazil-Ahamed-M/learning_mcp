import os

import pymysql
from dotenv import load_dotenv

# Load DB credentials from the .env file next to this script
load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env"))


def get_connection(use_database: bool = True) -> pymysql.connections.Connection:
    """Open a MySQL connection that returns rows as dictionaries."""
    return pymysql.connect(
        host=os.getenv("DB_HOST", "127.0.0.1"),
        port=int(os.getenv("DB_PORT", "3306")),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        database="school" if use_database else None,
        cursorclass=pymysql.cursors.DictCursor,
    )
