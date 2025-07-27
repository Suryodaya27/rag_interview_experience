import psycopg2

def insert_post(link, summary, embedding):
    conn = psycopg2.connect(
        dbname="ragdb",
        user="postgres",
        password="postgres",
        host="localhost",
        port=5432
    )
    cur = conn.cursor()
    try:
        cur.execute("""
            INSERT INTO posts (link, summary, embedding)
            VALUES (%s, %s, %s)
            ON CONFLICT (link) DO NOTHING;
        """, (link, summary, embedding))
        conn.commit()
    except Exception as e:
        print(f"❌ Failed to insert: {e}")
    finally:
        cur.close()
        conn.close()