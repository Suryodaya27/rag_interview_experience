# ollama_filter.py
import time
import ollama
import re
import aiohttp
import asyncio
import re
from asyncio import Semaphore
import requests
import numpy as np

def normalize(vec):
    norm = np.linalg.norm(vec)
    return [v / norm for v in vec] if norm else vec


async def is_relevant(link, company_name, role, session, sem):
    time.sleep(1)  # Simulate delay for relevance check
    title = link["title"]

    prompt = f"""You are a helpful assistant. Your task is to determine whether the following job interview post title is directly relevant to the company and the user's role.
Answer only with "YES" or "NO".

Title: {title}
Company: {company_name}
Role: {role}"""

    async with sem:
        print(f"🔍 Checking relevance for: {title}")
        try:
            async with session.post(
                "http://localhost:11434/api/generate",
                json={"model": "llama3.2:1b", "prompt": prompt, "stream": False},
                timeout=30
            ) as resp:
                data = await resp.json()
                content = data["response"]
                result = re.sub(r"<think>.*?</think>", "", content, flags=re.IGNORECASE | re.DOTALL).strip().upper()
                return link if result == "YES" else None
        except Exception as e:
            print(f"❌ Error for title: {title} -> {e}")
            return None

async def async_filter_links(links, company_name, role, max_results=15):
    filtered_links = []
    sem = Semaphore(1)  # limit 1 concurrent requests
    async with aiohttp.ClientSession() as session:
        tasks = [
            is_relevant(link, company_name, role, session, sem)
            for link in links
        ]
        for future in asyncio.as_completed(tasks):
            result = await future
            if result:
                filtered_links.append(result)
                print(len(filtered_links), "relevant links found so far.")
                if len(filtered_links) >= max_results:
                    print("🔍 Reached limit of 10 relevant links.")
                    break
    return filtered_links


def filter_links(links, company_name, role):
    counter = 0
    filtered_links = []

    for link in links:
        title = link['title']
        prompt = f"""You are a helpful assistant. Your task is to determine whether the following job interview post title is directly relevant to the company and the user's role.
        Answer only with "YES" or "NO".

        Title: {title}
        Company: {company_name}
        Role: {role}
        """
        print(f"🔍 Checking relevance for: {title}")
        response = ollama.chat(
            model='llama3.2:1b',
            messages=[{"role": "user", "content": prompt}]
        )
        result = response['message']['content'].strip().upper()
        result = re.sub(r"<think>.*?</think>", "", result, flags=re.IGNORECASE | re.DOTALL).strip()
        if result == "YES":
            filtered_links.append(link)
            counter += 1

        if counter >= 10:
            print("🔍 Reached limit of 10 relevant links.")
            break

    return filtered_links


def summarize_content(content):
    time.sleep(1)  # Simulate delay for summarization
    prompt = f"""You are a helpful assistant. Your task is to summarize the following job interview post content in a concise manner.
    Provide a summary that captures the key points and insights.

    Content: {content}
    """
    print("📝 Summarizing content...")
    response = ollama.chat(
        model='llama3.2:1b',
        messages=[{"role": "user", "content": prompt}]
    )
    summary = response['message']['content'].strip()
    summary = re.sub(r"<think>.*?</think>", "", summary, flags=re.IGNORECASE | re.DOTALL).strip()
    return summary



def create_embeddings(content):
    time.sleep(1)  # Simulate delay for embedding creation
    response = ollama.embeddings(
        model='bge-m3:latest',
        prompt=content
    )
    embedding = response['embedding']
    return embedding


def generate_answer_with_context(query, context_chunks, model="gemma3:4b"):
    context_text = "\n\n".join([chunk["summary"] for chunk in context_chunks])

    prompt = f"""
        You are a helpful assistant. Use the context below to answer the user's question.

        Only return an answer if the context contains **directly relevant information** to the user's query.  
        If the user is asking for a **specific role** (e.g., SDE1, SDE2, E5), **only include summaries matching that role**.  
        If no relevant summaries are found for the role, return a polite response saying no matching information is available.

        CONTEXT:
        {context_text}

        QUESTION:
        {query}

        ANSWER:"""

    res = requests.post("http://localhost:11434/api/generate", json={
        "model": model,
        "prompt": prompt,
        "stream": False
    })
    result = res.json()["response"]
    return result