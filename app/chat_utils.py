from app.llm import llm_functions as llm
from app.db_functions import get_similar_results
from app import main

async def get_contextual_answer(user_query: str, debug: bool = False):
    embedding = await llm.create_embeddings(user_query)
    chunks = get_similar_results.search_similar_summaries(embedding, top_k=6)
    print(f"🔍 Found {len(chunks)} relevant chunks for the query.")
    answer = llm.generate_answer_with_context(user_query, chunks)
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