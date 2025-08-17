# app/agentic_rag.py
import json
import re
from typing import Dict, Any, List, Tuple

from app.llm import llm_functions as llm
from app.db_functions import get_similar_results


# ---------- Utilities ----------

def _extract_json(text: str) -> Dict[str, Any]:
    """
    Robustly extract JSON from LLM output.
    """
    try:
        return json.loads(text)
    except Exception:
        m = re.search(r"\{.*\}", text, flags=re.DOTALL)
        if m:
            try:
                return json.loads(m.group(0))
            except Exception:
                pass
    lowered = text.lower()
    if "refine" in lowered:
        return {"status": "refine", "new_query": "", "reason": "Heuristic refine"}
    if "good" in lowered:
        return {"status": "good", "new_query": "", "reason": "Heuristic good"}
    return {"status": "fail", "new_query": "", "reason": "Heuristic fail"}


def _maybe_extract_company(query: str) -> str:
    """
    Very light heuristic: if user mentions a company (one or two capitalized words),
    we pass that along as a constraint in prompts. This is intentionally permissive.
    """
    # matches like: "Google", "American Express", "Morgan Stanley"
    m = re.search(r"\b([A-Z][a-z]+(?:\s[A-Z][a-z]+)?)\b", query)
    return m.group(1) if m else ""


def _build_answer_prompt(user_query: str, chunks: List[Dict[str, str]]) -> str:
    """
    Builds a professional, broad answer prompt with company constraint if present.
    """
    company = _maybe_extract_company(user_query)

    constraint = (
        f"- If the question references a company, constrain the answer strictly to **{company}**. "
        "Do not generalize to other companies.\n"
        if company
        else "- If NO specific company is referenced, do not invent one. Answer generally.\n"
    )

    return f"""
You are a senior technical interview assistant helping candidates prepare using a Retrieval-Augmented system.

Follow these requirements:
- Be accurate, clear, and **professionally comprehensive** (cover typical variations, caveats, and best practices).
- Use only the provided context; if the context is thin, say what is missing and proceed with careful, well-signposted best-effort guidance.
- Prefer concise structure: a short answer first, then supporting details or steps.
- Where helpful, provide bullet points, checklists, or stepwise strategies.
{constraint}
- If the user asks for a specific role (e.g., “SDE 2 at X”), tailor the guidance to that role only; otherwise, say that the query is too broad to answer specifically.
- Do not include implementation details of this system; focus on the user’s needs.
- Do not output JSON. Produce a natural, polished response.

User question:
\"\"\"{user_query}\"\"\"

You will also receive retrieved context chunks separately. Use them to ground your answer.
If the chunks disagree, explain the discrepancy briefly and choose the most reasonable interpretation.
"""


async def _retrieve_and_answer(query: str, top_k: int = 6) -> Tuple[str, List[Dict[str, str]]]:
    """
    One retrieval + answer pass.
    - Hybrid retrieval (your db layer handles using both query text and embeddings)
    - Compose a strong answer prompt and call the LLM
    """
    embedding = await llm.create_embeddings(query)
    chunks = get_similar_results.search_similar_summaries(query, embedding, top_k=top_k)

    prompt = _build_answer_prompt(query, chunks)
    answer = llm.generate_answer_with_context(prompt, chunks)
    return answer, chunks


async def _judge_answer(user_query: str, answer: str, chunks: List[Dict[str, str]]) -> Dict[str, Any]:
    """
    Judge answer quality and decide: good / refine / fail
    """
    sources_preview = "\n".join(
        [f"- {c.get('link','')}: {c.get('summary','')[:200]}..." for c in (chunks[:3] if chunks else [])]
    )
    company = _maybe_extract_company(user_query)
    company_clause = (
        f"- The user appears to reference the company **{company}**. "
        "If the answer drifts away from this company, prefer 'refine' and propose a tighter query.\n"
        if company else
        "- If no company is referenced, ensure the answer does not invent one.\n"
    )

    judge_prompt = f"""
You are a professional evaluator for an agentic RAG system.
Your job is to judge whether the current answer is sufficient, needs query refinement, or fails.

User Query:
{user_query}

Current Answer:
\"\"\"{answer}\"\"\"

Retrieved Context (preview):
{sources_preview or "(no sources retrieved)"}

Evaluation Criteria:
- Directness: Does the answer directly and fully address the user query?
- Faithfulness: Is the answer grounded in the retrieved context (and clearly notes any gaps)?
- Professionalism: Is the tone clear, structured, and helpful (short answer then details)?
- Specificity: If a company is referenced, the answer must stay focused on that company.
{company_clause}
- Coverage: Are key aspects (e.g., interview stages, role-specific expectations, typical questions) covered when relevant?

Decision Rules:
- "good": Comprehensive, grounded, professional; satisfies the constraints.
- "refine": Partially helpful or not well grounded; propose a better search query.
- "fail": Cannot answer reliably, even with refinement.

Respond ONLY in strict JSON:
{{
  "status": "good" | "refine" | "fail",
  "new_query": "refined query if status == 'refine', else empty string",
  "reason": "1-2 sentence explanation"
}}
"""
    raw = llm.generate_answer_with_context(judge_prompt, [])
    return _extract_json(raw)


# ---------- Public API ----------

async def agentic_rag(
    user_query: str,
    *,
    max_loops: int = 3,
    top_k: int = 6
) -> Tuple[str, Dict[str, Any]]:
    """
    Agentic RAG loop:
      1) retrieve → answer
      2) judge
      3) optionally refine the query and retry
    Stops when status is "good" or loop limit reached.
    Returns (final_answer, debug_dict).
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
            "answer_preview": answer[:400]
        })

        # Track best so far by amount of grounding
        if len(chunks) > len(best_chunks):
            best_chunks = chunks
            best_answer = answer

        decision = await _judge_answer(user_query, answer, chunks)
        debug["attempts"][-1]["judge"] = decision

        status = decision.get("status", "fail")
        if status == "good":
            debug["final"] = {"status": "good", "attempt": attempt}
            return answer, debug

        if status == "refine":
            new_q = (decision.get("new_query") or "").strip()
            # If judge did not supply a new query, create a more targeted refinement:
            if not new_q:
                company = _maybe_extract_company(user_query)
                company_hint = f" company:{company}" if company else ""
                new_q = (
                    f"{user_query}{company_hint} interview experience interview process onsite rounds behavioral system design DSA coding"
                )
            query = new_q
            continue

        # status == "fail"
        if attempt < max_loops:
            company = _maybe_extract_company(user_query)
            company_hint = f" company:{company}" if company else ""
            query = f"{user_query}{company_hint} interview experience role responsibilities questions preparation tips"
            continue
        break

    # Fallback: return best effort
    if best_answer:
        debug["final"] = {"status": "best_effort", "attempts": len(debug['attempts'])}
        return best_answer, debug

    debug["final"] = {"status": "no_answer", "attempts": len(debug['attempts'])}
    return "I couldn't find a reliable answer in the knowledge base.", debug
