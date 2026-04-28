import os
import psycopg2

def get_connection():
    try:
        conn = psycopg2.connect(
            os.getenv("Database_Url"),
            sslmode="require"
        )
        return conn
    except Exception as e:
        print("Database connection failed:", e)
        raise