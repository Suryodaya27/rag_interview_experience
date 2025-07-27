import psycopg2
from psycopg2.extensions import register_adapter, AsIs
import numpy as np

def adapt_vector(vec):
    return AsIs(f"'{np.array(vec).tolist()}'")


def search_similar_summaries(query_embedding, top_k=10):
    conn = psycopg2.connect(
        dbname="ragdb",
        user="postgres",
        password="postgres",
        host="localhost",
        port=5432
    )
    cur = conn.cursor()
    cur.execute("""
        SELECT link, summary
        FROM posts
        ORDER BY embedding <-> %s
        LIMIT %s
    """, (adapt_vector(query_embedding), top_k))
    results = cur.fetchall()
    cur.close()
    conn.close()

    return [{"link": r[0], "summary": r[1]} for r in results]