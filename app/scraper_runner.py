# app/scraper_runner.py
import asyncio
from app.factory.scraper_factory import get_scraper
from app.db_functions.company_crud import add_company
from app.db_functions.add_embeddings import insert_post_async
from app.llm.llm_functions import create_embeddings
from app.llm import get_chunks
from app import cache_local


class ScraperRunner:
    def __init__(self, company: str, sources: list[str] = ["gfg"]):
        self.company = company
        self.sources = sources

    async def process(self):
        for source in self.sources:
            scraper = get_scraper(source)
            if not scraper:
                print(f"❌ No scraper found for {source}")
                continue

            print(f"🔍 Using {source} scraper for {self.company}")
            source_short = "gfg" if source == "gfg" else "lc"
            cache_key = f"{self.company}_{source_short}"

            links = cache_local.load_links_from_cache(cache_key)
            if not links:
                links = await scraper.get_links(self.company)
                cache_local.save_links_to_cache(cache_key, links)
            else:
                print(f"📦 Loaded cached links for {self.company} from {source}")

            posts = cache_local.load_scraped_data_from_cache(cache_key)
            if not posts:
                posts = await scraper.scrape_multiple_posts(links)
                cache_local.save_scraped_data_to_cache(cache_key, posts)
            else:
                print(f"📦 Loaded cached posts for {self.company} from {source}")

            print(f"🔗 Found {len(posts)} posts for {self.company} from {source}")

            for post in posts:
                if post.get("content"):
                    chunks = get_chunks.chunk_text_by_tokens(post["content"])
                    for chunk in chunks:
                        embeddings = await create_embeddings(chunk)
                        if embeddings:
                            await insert_post_async(post["link"], chunk, embeddings)

        add_company(self.company)
