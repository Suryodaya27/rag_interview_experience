from app.scrapers.gfg_scraper import GfgScraper
from app.scrapers.leetcode_scraper import LeetCodeScraper
# from app.scrapers.leetcode_scraper import LeetcodeScraper

def get_scraper(source: str):
    if source.lower() == "gfg":
        return GfgScraper()
    elif source.lower() == "leetcode":
        return LeetCodeScraper()
    else:
        raise ValueError("Unknown scraper source")