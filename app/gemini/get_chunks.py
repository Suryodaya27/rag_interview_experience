from transformers import AutoTokenizer

# bge-m3 is based on a MiniLM-like encoder
tokenizer = AutoTokenizer.from_pretrained("BAAI/bge-m3")

def chunk_text_by_tokens(text, max_tokens=1024):
    sentences = text.split(". ")
    chunks, current = [], ""

    for sentence in sentences:
        tentative = current + sentence + ". "
        token_len = len(tokenizer.encode(tentative, truncation=False))
        if token_len <= max_tokens:
            current = tentative
        else:
            if current:
                chunks.append(current.strip())
            current = sentence + ". "

    if current:
        chunks.append(current.strip())

    return chunks
