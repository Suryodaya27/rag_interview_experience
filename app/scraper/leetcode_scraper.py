import asyncio
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup

HEADLESS = True  # Toggle this


async def get_links(company_name):
    links = []
    company_name = company_name.lower().replace(" ", "-")
    print(f"🌐 Collecting leetcode links for company: {company_name}")
    company_name = 'facebook' if company_name.lower() == 'meta' else company_name  # Handle Meta as Facebook

    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=HEADLESS)
            page = await browser.new_page(user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36"
            ))

            url = f"https://leetcode.com/discuss/topic/{company_name}/"
            print(f"🔗 Visiting: {url}")

            try:
                await page.goto(url, wait_until="domcontentloaded")
                # await page.wait_for_load_state("networkidle")
                await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                await page.wait_for_timeout(2000)
            except Exception as e:
                print(f"❌ Failed to load or scroll page: {e}")
                await browser.close()
                return []

            interview_buttons = page.locator('button:has-text("Interview")')
            count = await interview_buttons.count()
            print(f"🧭 Found {count} Interview buttons")

            if count < 2:
                print("❌ Less than 2 Interview buttons found")
                await browser.close()
                return []

            try:
                await interview_buttons.nth(1).click()
                await page.wait_for_timeout(3000)
                html = await page.content()
            except Exception as e:
                print(f"❌ Error during clicking or fetching content: {e}")
                await browser.close()
                return []

            await browser.close()
            print("✅ Page content collected")

    except Exception as e:
        print(f"❌ Error launching browser or accessing Playwright: {e}")
        return []

    try:
        soup = BeautifulSoup(html, "html.parser")
        parent_div = soup.select_one("div.mt-2.flex.flex-col.gap-4")
        if not parent_div:
            print("❌ Parent div not found")
            return []

        post_divs = parent_div.select("div.flex-none")
        print(f"🧱 Found {len(post_divs)} post cards")

        for i, div in enumerate(post_divs):
            try:
                title_tag = div.select_one(
                    "div.text-sd-foreground.line-clamp-1.whitespace-normal.text-lg.font-semibold"
                )
                link_tag = div.select_one("a[href^='/discuss/post/']")
                if title_tag and link_tag:
                    title = title_tag.get_text(strip=True)
                    href = "https://leetcode.com" + link_tag.get("href")
                    links.append({"title": title, "link": href})
            except Exception as e:
                print(f"[{i}] ⚠️ Error extracting link: {e}")

    except Exception as e:
        print(f"❌ Error parsing HTML: {e}")
        return []

    print(f"\n✅ Total links collected: {len(links)}")
    return links


async def scrape_post_content(url):
    print(f"🔍 Scraping post: {url}")
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=HEADLESS)
            page = await browser.new_page(user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36"
            ))

            try:
                await page.goto(url, wait_until="domcontentloaded")
                # await page.wait_for_load_state("networkidle")
                await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                await page.wait_for_timeout(1500)
                html = await page.content()
            except Exception as e:
                print(f"❌ Failed to scrape page: {e}")
                await browser.close()
                return ""

            await browser.close()

    except Exception as e:
        print(f"❌ Error launching browser: {e}")
        return ""

    try:
        soup = BeautifulSoup(html, "html.parser")
        content_div = soup.select_one("div.mYe_l.TAIHK")
        if content_div:
            return content_div.get_text(separator="\n", strip=True)
        else:
            print("⚠️ Content div not found.")
            return ""
    except Exception as e:
        print(f"❌ Error parsing content HTML: {e}")
        return ""


complete_scraped_data = []

def get_links_data(links):
    for link in links:
        try:
            print(f"\n🔗 Processing: {link}")
            content = asyncio.run(scrape_post_content(link['link']))
            if content:
                complete_scraped_data.append({"link": link['link'], "content": content})
            else:
                print(f"⚠️ Empty content for {link}")
        except Exception as e:
            print(f"❌ Error scraping {link['link']}: {e}")
    return complete_scraped_data


# ---------------------------ASYNC FUNCTION FOR SCRAPING---------------------------

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
        content_div = soup.select_one("div.mYe_l.TAIHK")
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


