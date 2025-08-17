# app/agentic_rag.py
import json
import re
from typing import Dict, Any, List, Tuple, Optional

from app.llm import llm_functions as llm
from app.db_functions import get_similar_results
from app.chat_utils import get_contextual_answer  # if you want to reuse it
from app.chat_utils import scrape_and_add_company  # your wrapper around main.scrape_and_add_company


def _extract_json(text: str) -> Dict[str, Any]:
    """
    Robustly extract a JSON object from an LLM response that *should* be JSON.
    """
    try:
        return json.loads(text)
    except Exception:
        # Try to pull the first {...} block
        m = re.search(r"\{.*\}", text, flags=re.DOTALL)
        if m:
            try:
                return json.loads(m.group(0))
            except Exception:
                pass
    # As a last resort, try a simple key sniff
    lowered = text.lower()
    if "refine" in lowered:
        return {"status": "refine", "new_query": ""}
    if "good" in lowered:
        return {"status": "good", "new_query": ""}
    return {"status": "fail", "new_query": ""}


async def _retrieve_and_answer(query: str, top_k: int = 6) -> Tuple[str, List[Dict[str, str]]]:
    """
    One retrieval + answer pass, using your same building blocks.
    Returns (answer_text, chunks_used).
    """
    embedding = await llm.create_embeddings(query)
    chunks = get_similar_results.search_similar_summaries(embedding, top_k=top_k)
    answer = llm.generate_answer_with_context(query, chunks)
    return answer, chunks


async def _judge_answer(user_query: str, answer: str, chunks: List[Dict[str, str]]) -> Dict[str, Any]:
    """
    Ask your LLM to judge whether the current answer is good enough or needs refinement.
    We call your same llm.generate_answer_with_context with an instruction-only prompt (no context needed).
    """
    # Give the model a tiny view of sources (titles/links) to judge relevance
    sources_preview = "\n".join(
        [f"- {c.get('link','')}: {c.get('summary','')[:160]}..." for c in (chunks[:3] if chunks else [])]
    )

    judge_prompt = f"""
You are a strict evaluator for a RAG system.

User query: {user_query}

Current answer:
\"\"\"{answer}\"\"\"

Context sources (preview):
{sources_preview or "(no sources retrieved)"}

Decide:
- "good"  => answer directly addresses the user_query using the sources.
- "refine"=> we should reformulate the search query (give a better query).
- "fail"  => we cannot answer with confidence (no relevant sources).

Respond ONLY in strict JSON with keys:
{{
  "status": "good" | "refine" | "fail",
  "new_query": "a refined search query if status == 'refine', else empty string",
  "reason": "brief reason"
}}
"""
    raw = llm.generate_answer_with_context(judge_prompt, [])  # no context needed
    return _extract_json(raw)


async def agentic_rag(
    user_query: str,
    *,
    company: Optional[str] = None,
    max_loops: int = 3,
    top_k: int = 6,
    min_hits: int = 2,
    allow_scrape: bool = True
) -> Tuple[str, Dict[str, Any]]:
    """
    Agentic RAG loop:
      - iteratively retrieve → answer → judge
      - optionally refine query and retry
      - optional scrape fallback if nothing useful found (requires `company`)
    Returns (final_answer, debug_dict)
    """
    debug: Dict[str, Any] = {"attempts": []}
    query = user_query
    best_answer = ""
    best_chunks: List[Dict[str, str]] = []

    for attempt in range(1, max_loops + 1):
        answer, chunks = await _retrieve_and_answer(query, top_k=top_k)

        debug["attempts"].append({
            "attempt": attempt,
            "query": query,
            "num_chunks": len(chunks),
            "first_links": [c.get("link", "") for c in chunks[:3]],
            "answer_preview": answer[:300]
        })

        # If we retrieved very little, consider scrape fallback (once)
        if len(chunks) < min_hits and allow_scrape and company and attempt == 1:
            try:
                scrape_and_add_company(company)  # populate DB
                # Re-run retrieval with same query after scrape
                answer, chunks = await _retrieve_and_answer(query, top_k=top_k)
                debug["attempts"][-1]["post_scrape_num_chunks"] = len(chunks)
            except Exception as e:
                debug["attempts"][-1]["scrape_error"] = str(e)

        # keep the best-so-far based on chunk count as a simple heuristic
        if len(chunks) > len(best_chunks):
            best_chunks = chunks
            best_answer = answer

        decision = await _judge_answer(user_query, answer, chunks)
        debug["attempts"][-1]["judge"] = decision

        status = decision.get("status", "fail")
        if status == "good":
            debug["final"] = {"status": "good", "attempt": attempt}
            return answer, debug
        elif status == "refine":
            new_q = (decision.get("new_query") or "").strip()
            # Safety: if model didn't give a new query, try a simple heuristic rewrite
            query = new_q if new_q else f"{user_query} (use exact company/role keywords, synonyms, abbreviations)"
            continue
        else:  # "fail"
            # only retry if we still have loops left; otherwise bail with best effort
            if attempt < max_loops:
                # try a mild expansion
                query = f"{user_query} (expand acronyms, include synonyms, use interview terminology)"
                continue
            break

    # best-effort fallback
    if best_answer:
        debug["final"] = {"status": "best_effort", "attempts": len(debug["attempts"])}
        return best_answer, debug

    debug["final"] = {"status": "no_answer", "attempts": len(debug["attempts"])}
    return "I couldn't find a reliable answer in the current knowledge base.", debug
