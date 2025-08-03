from abc import ABC, abstractmethod

class ScraperInterface(ABC):
    @abstractmethod
    async def get_links(self, company_name: str) -> list[dict]:
        pass

    @abstractmethod
    async def scrape_multiple_posts(self, links: list[dict]) -> list[dict]:
        pass