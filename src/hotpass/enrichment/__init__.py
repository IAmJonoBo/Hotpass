"""External data enrichment and validation module.

This module provides functionality for:
- Web scraping and content extraction
- External registry integration (CIPC, SACAA, etc.)
- Caching layer for API responses
- Data enrichment workflows
"""

import asyncio
import logging
import sqlite3
import warnings
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

import pandas as pd

try:
    import requests  # type: ignore[import-untyped]

    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False

try:
    import trafilatura

    TRAFILATURA_AVAILABLE = True
except ImportError:
    TRAFILATURA_AVAILABLE = False

logger = logging.getLogger(__name__)


def _initialise_website_enrichment(df: pd.DataFrame, website_column: str) -> pd.DataFrame | None:
    if website_column not in df.columns:
        logger.warning("Column %s not found in dataframe", website_column)
        return None

    enriched_df = df.copy()
    enriched_df["website_title"] = None
    enriched_df["website_description"] = None
    enriched_df["website_text_length"] = None
    enriched_df["website_enriched"] = False
    return enriched_df


def _apply_website_content(df: pd.DataFrame, idx: int, content: dict[str, Any]) -> None:
    if not content.get("success"):
        return

    df.at[idx, "website_title"] = content.get("title")
    df.at[idx, "website_description"] = content.get("description")
    text = content.get("text")
    df.at[idx, "website_text_length"] = len(text) if isinstance(text, str) else 0
    df.at[idx, "website_enriched"] = True


class CacheManager:
    """Simple SQLite-based cache for API responses and web content."""

    def __init__(self, db_path: str = "data/.cache/enrichment.db", ttl_hours: int = 168):
        """Initialize cache manager.

        Args:
            db_path: Path to SQLite database file
            ttl_hours: Time-to-live for cached entries in hours (default: 168 = 1 week)
        """
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.ttl = timedelta(hours=ttl_hours)
        self._init_db()

    @contextmanager
    def _connect(self) -> Iterator[sqlite3.Connection]:
        with warnings.catch_warnings():
            warnings.filterwarnings(
                "ignore",
                category=ResourceWarning,
                message="unclosed database",
            )
            conn = sqlite3.connect(self.db_path)
        try:
            yield conn
        finally:
            conn.close()

    def _init_db(self) -> None:
        """Initialize database schema."""
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS cache (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    accessed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    hit_count INTEGER DEFAULT 0
                )
            """
            )
            conn.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_created_at ON cache(created_at)
            """
            )
            conn.commit()

    def get(self, key: str) -> str | None:
        """Retrieve cached value if not expired.

        Args:
            key: Cache key

        Returns:
            Cached value if found and not expired, None otherwise
        """
        with self._connect() as conn:
            cursor = conn.execute("SELECT value, created_at FROM cache WHERE key = ?", (key,))
            row = cursor.fetchone()

            if row is None:
                return None

            value, created_at = row
            created_dt = datetime.fromisoformat(created_at)

            # Check if expired
            if datetime.now() - created_dt > self.ttl:
                self.delete(key)
                return None

            # Update access stats
            conn.execute(
                """
                UPDATE cache
                SET accessed_at = CURRENT_TIMESTAMP, hit_count = hit_count + 1
                WHERE key = ?
                """,
                (key,),
            )
            conn.commit()

            return value

    def set(self, key: str, value: str) -> None:
        """Store value in cache.

        Args:
            key: Cache key
            value: Value to cache
        """
        with self._connect() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO cache (key, value, created_at, accessed_at, hit_count)
                VALUES (?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 0)
                """,
                (key, value),
            )
            conn.commit()

    def delete(self, key: str) -> None:
        """Delete cached value.

        Args:
            key: Cache key
        """
        with self._connect() as conn:
            conn.execute("DELETE FROM cache WHERE key = ?", (key,))
            conn.commit()

    def clear_expired(self) -> int:
        """Remove expired cache entries.

        Returns:
            Number of entries deleted
        """
        cutoff = (datetime.now() - self.ttl).isoformat()
        with self._connect() as conn:
            cursor = conn.execute("DELETE FROM cache WHERE created_at < ?", (cutoff,))
            count = cursor.rowcount
            conn.commit()
            return count

    def stats(self) -> dict[str, Any]:
        """Get cache statistics.

        Returns:
            Dictionary with cache statistics
        """
        with self._connect() as conn:
            cursor = conn.execute(
                """
                SELECT
                    COUNT(*) as total_entries,
                    SUM(hit_count) as total_hits,
                    AVG(hit_count) as avg_hits_per_entry
                FROM cache
                """
            )
            row = cursor.fetchone()

            return {
                "total_entries": row[0] or 0,
                "total_hits": row[1] or 0,
                "avg_hits_per_entry": round(row[2] or 0, 2),
                "db_path": str(self.db_path),
                "ttl_hours": self.ttl.total_seconds() / 3600,
            }


def extract_website_content(url: str, cache: CacheManager | None = None) -> dict[str, Any]:
    """Extract structured content from a website.

    Args:
        url: Website URL to extract content from
        cache: Optional cache manager for storing results

    Returns:
        Dictionary with extracted content including title, text, metadata
    """
    if not TRAFILATURA_AVAILABLE:
        logger.warning("Trafilatura not available, skipping website extraction")
        return {"url": url, "error": "Trafilatura not installed"}

    if not REQUESTS_AVAILABLE:
        logger.warning("Requests not available, skipping website extraction")
        return {"url": url, "error": "Requests not installed"}

    # Check cache first
    cache_key = f"website:{url}"
    if cache:
        cached = cache.get(cache_key)
        if cached:
            logger.debug(f"Cache hit for {url}")
            import json

            return json.loads(cached)

    try:
        # Download HTML content
        logger.info(f"Fetching website content from {url}")
        response = requests.get(
            url,
            timeout=30,
            headers={"User-Agent": "Hotpass/1.0 (Data Refinement Pipeline)"},
        )
        response.raise_for_status()

        # Extract content with Trafilatura
        downloaded = response.text
        text = trafilatura.extract(downloaded)
        metadata = trafilatura.extract_metadata(downloaded)

        result = {
            "url": url,
            "title": metadata.title if metadata else None,
            "author": metadata.author if metadata else None,
            "date": metadata.date if metadata else None,
            "description": metadata.description if metadata else None,
            "text": text,
            "extracted_at": datetime.now().isoformat(),
            "success": text is not None,
        }

        # Store in cache
        if cache:
            import json

            cache.set(cache_key, json.dumps(result))

        return result

    except Exception as e:
        logger.error(f"Failed to extract content from {url}: {e}")
        return {
            "url": url,
            "error": str(e),
            "success": False,
            "extracted_at": datetime.now().isoformat(),
        }


def enrich_from_registry(
    org_name: str,
    registry_type: str = "cipc",
    cache: CacheManager | None = None,
) -> dict[str, Any]:
    """Fetch organization data from external registries.

    This is a stub implementation that provides the extensibility framework
    for integrating with CIPC, SACAA, and other registries.

    Args:
        org_name: Organization name to look up
        registry_type: Type of registry (cipc, sacaa, etc.)
        cache: Optional cache manager

    Returns:
        Dictionary with registry data or error information
    """
    cache_key = f"registry:{registry_type}:{org_name}"

    # Check cache
    if cache:
        cached = cache.get(cache_key)
        if cached:
            logger.debug(f"Cache hit for registry lookup: {org_name}")
            import json

            return json.loads(cached)

    logger.info(f"Looking up {org_name} in {registry_type} registry")

    # This is a stub that returns a framework for integration
    result: dict[str, Any] = {
        "org_name": org_name,
        "registry_type": registry_type,
        "status": "not_implemented",
        "message": f"{registry_type.upper()} integration is a stub. "
        f"Extend this function to integrate with actual registry API.",
        "looked_up_at": datetime.now().isoformat(),
        # Placeholder fields for actual registry data
        "registration_number": None,
        "registered_address": None,
        "registration_date": None,
        "status_code": None,
        "directors": [],
        "contact_info": {},
    }

    # Cache the result
    if cache:
        import json

        cache.set(cache_key, json.dumps(result))

    return result


def enrich_dataframe_with_websites(
    df: pd.DataFrame,
    website_column: str = "organization_website",
    cache: CacheManager | None = None,
) -> pd.DataFrame:
    """Enrich dataframe by extracting content from organization websites.

    Args:
        df: Input dataframe
        website_column: Column containing website URLs
        cache: Optional cache manager

    Returns:
        Dataframe with additional enrichment columns
    """
    enriched_df = _initialise_website_enrichment(df, website_column)
    if enriched_df is None:
        return df

    # Extract content for each website
    for idx, row in enriched_df.iterrows():
        website = row[website_column]

        if pd.isna(website) or not website:
            continue

        content = extract_website_content(website, cache=cache)
        _apply_website_content(enriched_df, idx, content)

    enriched_count = enriched_df["website_enriched"].sum()
    logger.info(f"Enriched {enriched_count}/{len(df)} organizations with website content")

    return enriched_df


async def enrich_dataframe_with_websites_async(
    df: pd.DataFrame,
    website_column: str = "organization_website",
    cache: CacheManager | None = None,
    *,
    concurrency: int = 8,
) -> pd.DataFrame:
    """Asynchronously enrich organisation websites using a worker pool."""

    enriched_df = _initialise_website_enrichment(df, website_column)
    if enriched_df is None:
        return df

    urls: list[tuple[int, Any]] = []
    for idx, website in enriched_df[website_column].items():
        if pd.isna(website) or not website:
            continue
        urls.append((idx, website))

    if not urls:
        return enriched_df

    concurrency = max(1, concurrency)
    semaphore = asyncio.Semaphore(concurrency)

    async def _enrich(idx: int, url: Any) -> tuple[int, dict[str, Any]]:
        async with semaphore:
            content = await asyncio.to_thread(extract_website_content, url, cache)
        return idx, content

    tasks = [_enrich(idx, url) for idx, url in urls]
    results: list[tuple[int, dict[str, Any]] | BaseException] = await asyncio.gather(
        *tasks, return_exceptions=True
    )

    for result in results:
        if isinstance(result, BaseException):
            logger.error("Website enrichment task failed: %s", result)
            continue
        idx, content = result
        _apply_website_content(enriched_df, idx, content)

    enriched_count = enriched_df["website_enriched"].sum()
    logger.info(
        "Enriched %s/%s organizations with website content (concurrency=%s)",
        enriched_count,
        len(df),
        concurrency,
    )
    return enriched_df


def enrich_dataframe_with_websites_concurrent(
    df: pd.DataFrame,
    website_column: str = "organization_website",
    cache: CacheManager | None = None,
    *,
    concurrency: int = 8,
) -> pd.DataFrame:
    """Convenience wrapper around the async enrichment helper."""

    try:
        asyncio.get_running_loop()
    except RuntimeError:
        return asyncio.run(
            enrich_dataframe_with_websites_async(
                df,
                website_column=website_column,
                cache=cache,
                concurrency=concurrency,
            )
        )

    msg = (
        "enrich_dataframe_with_websites_concurrent() must not be invoked from an active "
        "event loop. Await enrich_dataframe_with_websites_async() instead."
    )
    raise RuntimeError(msg)


def enrich_dataframe_with_registries(
    df: pd.DataFrame,
    org_name_column: str = "organization_name",
    registry_type: str = "cipc",
    cache: CacheManager | None = None,
) -> pd.DataFrame:
    """Enrich dataframe with data from external registries.

    Args:
        df: Input dataframe
        org_name_column: Column containing organization names
        registry_type: Type of registry to query
        cache: Optional cache manager

    Returns:
        Dataframe with additional registry columns
    """
    if org_name_column not in df.columns:
        logger.warning(f"Column {org_name_column} not found in dataframe")
        return df

    enriched_df = df.copy()

    # Initialize new columns
    enriched_df["registry_type"] = None
    enriched_df["registry_status"] = None
    enriched_df["registry_number"] = None
    enriched_df["registry_enriched"] = False

    # Query registry for each organization
    for idx, row in enriched_df.iterrows():
        org_name = row[org_name_column]

        if pd.isna(org_name) or not org_name:
            continue

        registry_data = enrich_from_registry(org_name, registry_type, cache=cache)

        enriched_df.at[idx, "registry_type"] = registry_type
        enriched_df.at[idx, "registry_status"] = registry_data.get("status")
        enriched_df.at[idx, "registry_number"] = registry_data.get("registration_number")
        enriched_df.at[idx, "registry_enriched"] = registry_data.get("status") != "not_implemented"

    enriched_count = enriched_df["registry_enriched"].sum()
    logger.info(
        f"Queried {registry_type} registry for {len(df)} organizations ({enriched_count} with data)"
    )

    return enriched_df
