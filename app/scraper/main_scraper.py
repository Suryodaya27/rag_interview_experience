import asyncio
from scraper import leetcode_scraper
from scraper import gfg_scraper
from gemini import gemini_functions as gemini
from gemini import get_chunks
import cache_local

def scrape_data(company_name, role="software engineer"):
    """Scrape interview experiences for a given company."""
    # Check cache
    lc_links = cache_local.load_links_from_cache(f"{company_name}_lc")
    gfg_links = cache_local.load_links_from_cache(f"{company_name}_gfg")
    if lc_links or gfg_links:
        print(f"📦 Loaded cached links for {company_name}")
    else:
        print(f"🌐 Scraping fresh links for {company_name}...")
        lc_links = asyncio.run(leetcode_scraper.get_links(company_name))
        gfg_links = asyncio.run(gfg_scraper.get_links(company_name))
        cache_local.save_links_to_cache(f"{company_name}_lc", lc_links)
        cache_local.save_links_to_cache(f"{company_name}_gfg", gfg_links)


    summarize_scraped_data = []
    if lc_links or gfg_links:
        scraped_data = cache_local.load_scraped_data_from_cache(company_name)
        if(scraped_data):
            print(f"📦 Loaded cached scraped data for {company_name}")
        else:
            print(f"🌐 Scraping content for {len(lc_links)+len(gfg_links)} filtered links...")
            # scraped_data = leetcode_scraper.get_links_data(filtered_links)
            scraped_data1 = asyncio.run(leetcode_scraper.scrape_multiple_posts(lc_links))
            scraped_data2 = asyncio.run(gfg_scraper.scrape_multiple_posts(gfg_links))
            cache_local.save_scraped_data_to_cache(f"{company_name}", scraped_data1 + scraped_data2)
            scraped_data = scraped_data1 + scraped_data2

        for item in scraped_data:
            content = item.get('content', '')
            if content:
                chunks = get_chunks.chunk_text_by_tokens(content)
                for chunk in chunks:
                    summarize_scraped_data.append({
                        "link": item['link'],
                        "summary": chunk
                    })
    return summarize_scraped_data