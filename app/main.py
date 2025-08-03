import asyncio
from app.scraper_runner import ScraperRunner

def main():
    company = "Atlassian"
    print(f"🌐 Scraping data for {company}...")
    runner = ScraperRunner(company, ["gfg","leetcode"])
    asyncio.run(runner.process())
    print(f"✅ Finished scraping and storing data for {company}.")

if __name__ == "__main__":
    main()
