"""Search functionality for bwctl."""

from bwctl.db.connection import get_connection
from bwctl.db.models import ContentType, DeviceType, SearchResult


def search_content(
    query: str,
    content_type: ContentType | None = None,
    device_type: DeviceType | None = None,
    category: str | None = None,
    package_id: int | None = None,
    parent_device: str | None = None,
    limit: int = 50,
    offset: int = 0,
) -> list[SearchResult]:
    """Search for content in the database.

    Args:
        query: Search query (supports fuzzy matching)
        content_type: Filter by content type
        device_type: Filter by device type
        category: Filter by category (partial match)
        package_id: Filter by package ID
        parent_device: Filter by parent device name (partial match)
        limit: Maximum number of results
        offset: Number of results to skip

    Returns:
        List of search results sorted by relevance
    """
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT * FROM search_content(
                    %s, %s, %s, %s, %s, %s, %s, %s
                )
                """,
                (
                    query or None,
                    content_type.value if content_type else None,
                    device_type.value if device_type else None,
                    category,
                    package_id,
                    parent_device,
                    limit,
                    offset,
                ),
            )
            rows = cur.fetchall()
            return [SearchResult.from_row(row) for row in rows]


def autocomplete(query: str, limit: int = 10) -> list[tuple[str, ContentType, int]]:
    """Get autocomplete suggestions.

    Args:
        query: Partial search query
        limit: Maximum number of suggestions

    Returns:
        List of (suggestion, content_type, count) tuples
    """
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT * FROM autocomplete_content(%s, %s)",
                (query, limit),
            )
            rows = cur.fetchall()
            return [
                (row["suggestion"], ContentType(row["content_type"]), row["match_count"])
                for row in rows
            ]


def get_content_by_id(content_id: int) -> SearchResult | None:
    """Get content by ID.

    Args:
        content_id: The content ID

    Returns:
        The content or None if not found
    """
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT
                    c.id, c.name, c.content_type, c.category,
                    c.parent_device, c.file_path, p.name as package_name,
                    1.0::REAL as relevance
                FROM content c
                LEFT JOIN packages p ON c.package_id = p.id
                WHERE c.id = %s
                """,
                (content_id,),
            )
            row = cur.fetchone()
            if row:
                return SearchResult.from_row(row)
            return None


def get_stats() -> dict[str, int]:
    """Get content statistics.

    Returns:
        Dictionary of content type to count
    """
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT content_type, count FROM content_stats")
            rows = cur.fetchall()
            return {row["content_type"]: row["count"] for row in rows}
