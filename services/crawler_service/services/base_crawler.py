"""IJDCrawler interface — adapter pattern for multiple JD sources."""
from abc import ABC, abstractmethod

from services.crawler_service.models.schemas import RawJD


class IJDCrawler(ABC):
    """Common interface for all JD source crawlers."""

    source_name: str = "unknown"

    @abstractmethod
    def crawl_listing(self, category: str, max_pages: int = 10) -> list[str]:
        """Return list of detail-page URLs for a category."""

    @abstractmethod
    def crawl_detail(self, url: str) -> RawJD | None:
        """Crawl one JD detail page. Return None if parsing fails."""

    @abstractmethod
    def health_check(self) -> bool:
        """Quick self-test: crawl 1 sample URL and verify required fields present."""

    @abstractmethod
    def list_categories(self) -> list[str]:
        """Return category keys this crawler supports (backend, frontend, ...)."""
