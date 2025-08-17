import sys
import os
import time
from datetime import datetime
import streamlit as st

# # 👇 Adds the root (leetcode_scraper/) to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from app import main
import asyncio
import app.db_functions.company_crud as company_utils
import app.chat_utils as chat_utils
import app.agentic_rag as agentic_rag

# 🖼️ Page setup
st.set_page_config(page_title="🧠 RAG Chatbot", layout="wide")
st.markdown("<h1 style='text-align: center;'>🧠 Interview RAG Assistant</h1>", unsafe_allow_html=True)
st.markdown("### Ask anything about tech interviews, roles, and companies")

# 🧹 Sidebar
with st.sidebar:
    st.header("⚙️ Options")
    
    # Unique button key
    clear_chat = st.button("🗑️ Clear Chat", key="clear_chat")

    st.markdown("### 🏢 Company Dashboard")

    companies = company_utils.list_companies()
    if companies:
        for c in companies:
            st.markdown(f"- ✅ **{c[0].title()}**")
    else:
        st.info("No companies added yet.")

    new_company = st.text_input("➕ Add new company")
    if st.button("Scrape & Add", key="add_company"):
        if new_company.strip():
            with st.spinner("🔄 Scraping company data..."):
                output = main.scrape_and_add_company(new_company.strip().lower())
                st.success(f"✅ Added {new_company}")
                st.text_area("Scraper Output", output, height=200)
            st.rerun()
        else:
            st.warning("Enter a company name.")

    st.markdown("---")
    st.caption("Built with ❤️ using Ollama + PGVector + Streamlit")

# 🔁 Chat memory
if "history" not in st.session_state or clear_chat:
    st.session_state.history = []

# 🧾 Input area
user_input = st.chat_input("Ask about a company’s interview process...")

# 🗨️ Handle user message
if user_input:
    # 1. Show user message
    st.session_state.history.append({
        "role": "user",
        "content": user_input,
        "timestamp": datetime.now().strftime("%H:%M:%S")
    })
    with st.chat_message("user"):
        st.markdown(user_input)

    # 2. Generate assistant response
    # Reserve space for assistant reply (fresh for each query)
    with st.chat_message("assistant"):
        placeholder = st.empty()
        debug_placeholder = st.empty()  # 👈 separate space for debug
        time_placeholder = st.empty()   # 👈 separate space for response time

        with st.spinner("🤖 Thinking..."):
            start = time.time()
            response, debug = asyncio.run(
                agentic_rag.agentic_rag(user_input, max_loops=3, top_k=6)
            )
            duration = time.time() - start

        # Update assistant reply
        placeholder.markdown(response)

        # ✅ Clear old debug & time (these placeholders are re-created every new query)
        time_placeholder.caption(f"🕒 Responded in {duration:.2f} sec")

        with debug_placeholder.expander("🔍 Debug: Retrieved Chunks"):
            st.markdown(debug)

    # 3. Save assistant message to history
    st.session_state.history.append({
        "role": "assistant",
        "content": response,
        "timestamp": datetime.now().strftime("%H:%M:%S"),
        "duration": f"{duration:.2f} sec",
        "debug": debug
    })

# 🧠 Re-render chat history
for msg in st.session_state.history:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if msg["role"] == "assistant" and "duration" in msg:
            st.caption(f"🕒 Responded in {msg['duration']}")