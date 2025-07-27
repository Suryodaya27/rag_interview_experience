# https://www.geeksforgeeks.org/tag/amazon/page/5/?type=recent
# TagCategoryArticle_articleContainer_headerContainer-header__OvTzc
import asyncio
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup

HEADLESS = True  # Toggle this

async def get_links(company_name):
    company_name = company_name.lower().replace(" ", "-")
    print(f"🌐 Collecting gfg links for company: {company_name}")
    links = []
    try:
        async with async_playwright() as p:
            try:
                browser = await p.chromium.launch(headless=HEADLESS)
                page = await browser.new_page(user_agent=(
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                    "(KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36"
                ))
                for page_number in range(1, 6):
                    url = f"https://www.geeksforgeeks.org/tag/{company_name}/page/{page_number}/?type=recent"
                    print(f"🔗 Visiting: {url}")
                    max_retries = 3
                    for attempt in range(1, max_retries + 1):
                        try:
                            await page.goto(url, wait_until="domcontentloaded")
                            print(f"🔗 Successfully loaded page {page_number}")
                            await page.wait_for_timeout(2000)
                            html = await page.content()
                            print("✅ Page content collected")
                            soup = BeautifulSoup(html, 'html.parser')
                            articles = soup.select("div.TagCategoryArticle_articleContainer__yJdy6")
                            for article in articles:
                                try:
                                    a_tag = article.select_one("a")
                                    if a_tag:
                                        title = a_tag.get_text(strip=True)
                                        link = a_tag["href"]
                                        links.append({"title": title, "link": link})
                                except Exception as e:
                                    print(f"❌ Error parsing article: {e}")
                            break  # Success, exit retry loop
                        except Exception as e:
                            print(f"❌ Failed to load or process page {url} (attempt {attempt}): {e}")
                            if attempt == max_retries:
                                print(f"❌ Giving up on {url} after {max_retries} attempts.")
                            else:
                                await asyncio.sleep(2)  # Wait before retrying
                await browser.close()
            except Exception as e:
                print(f"❌ Error launching browser or creating page: {e}")
                return []
    except Exception as e:
        print(f"❌ Error initializing Playwright: {e}")
        return []
    return links


async def scrape_single_post(link_obj, page):
    url = link_obj["link"]
    title = link_obj["title"]
    print(f"🔍 Scraping post: {url}")
    
    try:
        await page.goto(url, wait_until="domcontentloaded")
        # await page.wait_for_load_state("networkidle")
        await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        await page.wait_for_timeout(1500)
        html = await page.content()

        soup = BeautifulSoup(html, "html.parser")
        content_div = soup.select_one("div.text")
        content = content_div.get_text(separator="\n", strip=True) if content_div else ""

        if not content:
            print(f"⚠️ Content div not found for: {url}")

        return {
            "link": url,
            "title": title,
            "content": content
        }
        
    except Exception as e:
        print(f"❌ Error scraping {url}: {e}")
        return {
            "link": url,
            "title": title,
            "content": ""
        }

async def scrape_multiple_posts(links, concurrency_limit=5):
    sem = asyncio.Semaphore(concurrency_limit)
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=HEADLESS)
        context = await browser.new_context(user_agent=(
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36"
        ))

        async def worker(link_obj):
            async with sem:
                page = await context.new_page()
                result = await scrape_single_post(link_obj, page)
                await page.close()
                return result

        tasks = [worker(link) for link in links]
        results = await asyncio.gather(*tasks)

        await browser.close()
        return [r for r in results if r["content"]]
                        