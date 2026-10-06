"""Expose FitFindr search over MCP stdio; the two model tools remain local.

Run `python mcp_client.py` to discover the tool. The client starts this server
with the same Python interpreter and closes it after each request.
"""

from mcp.server.fastmcp import FastMCP
from tools import search_listings as _search_listings_impl

mcp = FastMCP("fitfindr", log_level="WARNING")


@mcp.tool()
def search_listings(
    description: str,
    size: str | None = None,
    max_price: float | None = None,
) -> list[dict]:
    """Search local listings by keyword description, optional size string, and inclusive max_price in dollars; return ranked listing dictionaries or [] when nothing matches."""
    return _search_listings_impl(description, size, max_price)


if __name__ == "__main__":
    mcp.run()
