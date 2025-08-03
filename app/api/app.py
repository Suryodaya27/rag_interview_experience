from fastapi import FastAPI
from app.scraper_runner import ScraperRunner

app = FastAPI(title="Leetcode Scraper API")

@app.get("/")
async def root():
    return {"message": "Welcome to the Leetcode Scraper API"}

@app.post("/scrape/")
async def trigger_scraper(company: str):
    runner = ScraperRunner(company, ["gfg","leetcode"])
    await runner.process()  # ✅ This works inside FastAPI
    return {"status": "Scraping started for " + company}


def start_scraping(company: str):
    runner = ScraperRunner(company, ["gfg","leetcode"])
    import asyncio
    asyncio.run(runner.process())
