import asyncio
from playwright.async_api import async_playwright, Page, Browser, BrowserContext
from bs4 import BeautifulSoup
import random
from typing import List, Dict, Any, Optional

from app.interfaces.scraper_interface import ScraperInterface


class LeetCodeScraper(ScraperInterface):
    HEADLESS: bool = True  # Toggle this

    async def get_links(
        self, company_name: str, max_retries: int = 3, retry_delay: int = 2
    ) -> List[Dict[str, str]]:
        links: List[Dict[str, str]] = []
        company_name = company_name.lower().replace(" ", "-")
        print(f"🌐 Collecting leetcode links for company: {company_name}")
        company_name = 'facebook' if company_name.lower() == 'meta' else company_name  # Handle Meta as Facebook

        attempt: int = 0
        html: Optional[str] = None
        while attempt < max_retries:
            try:
                async with async_playwright() as p:
                    browser: Browser = await p.chromium.launch(headless=self.HEADLESS)
                    page: Page = await browser.new_page(user_agent=(
                        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                        "(KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36"
                    ))

                    url: str = f"https://leetcode.com/discuss/topic/{company_name}/"
                    print(f"🔗 Visiting: {url}")

                    try:
                        await page.goto(url, wait_until="domcontentloaded")
                        await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                        delay: int = random.randint(10, 20)
                        print(f"⏳ Waiting {delay} seconds for page to fully load...")
                        await page.wait_for_timeout(delay * 1000)
                    except Exception as e:
                        print(f"❌ Failed to load or scroll page: {e}")
                        await browser.close()
                        raise

                    interview_buttons = page.locator('button:has-text("Interview")')
                    count: int = await interview_buttons.count()
                    print(f"🧭 Found {count} Interview buttons")

                    if count < 2:
                        print("❌ Less than 2 Interview buttons found")
                        await browser.close()
                        raise Exception("Not enough Interview buttons")

                    try:
                        await interview_buttons.nth(1).click()
                        await page.wait_for_timeout(3000)
                        html = await page.content()
                    except Exception as e:
                        print(f"❌ Error during clicking or fetching content: {e}")
                        await browser.close()
                        raise

                    await browser.close()
                    print("✅ Page content collected")
                    break  # Success, exit retry loop

            except Exception as e:
                attempt += 1
                print(f"⚠️ Attempt {attempt} failed: {e}")
                if attempt < max_retries:
                    print(f"🔄 Retrying in {retry_delay} seconds...")
                    await asyncio.sleep(retry_delay)
                else:
                    print(f"❌ Error launching browser or accessing Playwright after {max_retries} attempts.")
                    return []

        if not html:
            print("❌ No HTML content collected after retries.")
            return []

        try:
            soup: BeautifulSoup = BeautifulSoup(html, "html.parser")
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
                        title: str = title_tag.get_text(strip=True)
                        href: str = "https://leetcode.com" + link_tag.get("href")
                        links.append({"title": title, "link": href})
                except Exception as e:
                    print(f"[{i}] ⚠️ Error extracting link: {e}")

        except Exception as e:
            print(f"❌ Error parsing HTML: {e}")
            return []

        print(f"\n✅ Total links collected: {len(links)}")
        return links

    async def scrape_single_post(self, link_obj: Dict[str, str], page: Page) -> Dict[str, str]:
        url: str = link_obj["link"]
        title: str = link_obj["title"]
        print(f"🔍 Scraping post: {url}")

        try:
            await page.goto(url, wait_until="domcontentloaded")
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            delay: int = random.randint(5, 10)
            print(f"⏳ Waiting {delay} seconds for page to fully load...")
            await page.wait_for_timeout(delay * 1000)
            html: str = await page.content()

            soup: BeautifulSoup = BeautifulSoup(html, "html.parser")
            content_div = soup.select_one("div.mYe_l.TAIHK")
            content: str = content_div.get_text(separator="\n", strip=True) if content_div else ""

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

    async def scrape_multiple_posts(
        self, links: List[Dict[str, str]], concurrency_limit: int = 5
    ) -> List[Dict[str, str]]:
        sem = asyncio.Semaphore(concurrency_limit)
        async with async_playwright() as p:
            browser: Browser = await p.chromium.launch(headless=self.HEADLESS)
            context: BrowserContext = await browser.new_context(user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36"
            ))

            async def worker(link_obj: Dict[str, str]) -> Dict[str, str]:
                async with sem:
                    page: Page = await context.new_page()
                    result: Dict[str, str] = await self.scrape_single_post(link_obj, page)
                    await page.close()
                    return result

            tasks = [worker(link) for link in links]
            results: List[Dict[str, str]] = await asyncio.gather(*tasks)

            await browser.close()
            return [r for r in results if r["content"]]
