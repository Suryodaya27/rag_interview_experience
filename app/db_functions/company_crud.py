# app/company_utils.py

import psycopg2
from datetime import datetime

conn = psycopg2.connect(
        dbname="ragdb",
        user="postgres",
        password="postgres",
        host="localhost",
        port=5432
    )

def get_connection():
    return conn

def list_companies():
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT name, created_at FROM companies ORDER BY created_at DESC;")
            return cur.fetchall()

def add_company(name: str):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("INSERT INTO companies (name) VALUES (%s) ON CONFLICT (name) DO NOTHING;", (name,))
            conn.commit()

