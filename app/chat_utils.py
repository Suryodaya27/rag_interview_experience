from app.gemini import gemini_functions as gemini
from app.db_functions import get_similar_results
from app import main

def get_contextual_answer(user_query: str, debug: bool = False):
    embedding = gemini.create_embeddings(user_query)
    chunks = get_similar_results.search_similar_summaries(embedding, top_k=5)
    answer = gemini.generate_answer_with_context(user_query, chunks)
    # Format debug info nicely
    if debug:
        debug_info = "\n\n---\n\n".join(
            [f"🔗 [{chunk['link']}]({chunk['link']})\n\n{chunk['summary']}" for chunk in chunks]
        )
    else:
        debug_info = None
    return answer, debug_info



def scrape_and_add_company(name: str):
    return main.scrape_and_add_company(name)
