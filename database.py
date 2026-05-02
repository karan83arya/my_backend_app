import psycopg2

def get_connection():
    try:
        conn = psycopg2.connect(
            dbname="smartedueranew",
            user="postgres",
            password="Karan87%",
            host="localhost",
            port="5432"
        )
        return conn
    except Exception as e:
        print("Database connection failed:", e)
        raise