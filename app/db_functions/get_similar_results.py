# import psycopg2
# from psycopg2.extensions import register_adapter, AsIs
# import numpy as np

# def adapt_vector(vec):
#     return AsIs(f"'{np.array(vec).tolist()}'")


# def search_similar_summaries(query_embedding, top_k=10):
#     conn = psycopg2.connect(
#         dbname="ragdb",
#         user="postgres",
#         password="postgres",
#         host="localhost",
#         port=5432
#     )
#     cur = conn.cursor()
#     cur.execute("""
#         SELECT link, summary
#         FROM posts
#         ORDER BY embedding <-> %s
#         LIMIT %s
#     """, (adapt_vector(query_embedding), top_k))
#     results = cur.fetchall()
#     cur.close()
#     conn.close()

#     return [{"link": r[0], "summary": r[1]} for r in results]

import psycopg2
from psycopg2.extensions import register_adapter, AsIs
import numpy as np

def adapt_vector(vec):
    """Convert numpy vector into SQL array string for pgvector."""
    return AsIs(f"'{np.array(vec).tolist()}'")

def search_similar_summaries(query_text, query_embedding, top_k=10):
    conn = psycopg2.connect(
        dbname="ragdb",
        user="postgres",
        password="postgres",
        host="localhost",
        port=5432
    )
    cur = conn.cursor()

    # Hybrid search: combine semantic similarity (embedding) and FTS relevance
    cur.execute("""
        SELECT link, summary,
               -- embedding similarity (smaller distance = better, so invert it)
               (1 - (embedding <-> %s)) AS semantic_score,
               -- text similarity (Postgres full-text search)
               ts_rank_cd(to_tsvector('english', summary), plainto_tsquery(%s)) AS lexical_score,
               -- weighted hybrid score
               (0.7 * (1 - (embedding <-> %s)) +
                0.3 * ts_rank_cd(to_tsvector('english', summary), plainto_tsquery(%s))) AS hybrid_score
        FROM posts
        WHERE summary @@ plainto_tsquery(%s)  -- ensures at least some keyword overlap
        ORDER BY hybrid_score DESC
        LIMIT %s
    """, (adapt_vector(query_embedding), query_text,
          adapt_vector(query_embedding), query_text,
          query_text, top_k))

    results = cur.fetchall()
    cur.close()
    conn.close()

    return [
        {"link": r[0], "summary": r[1], "semantic": r[2], "lexical": r[3], "score": r[4]}
        for r in results
    ]
