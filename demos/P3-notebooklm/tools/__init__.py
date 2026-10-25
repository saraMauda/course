from tools.scrape import scrape_url
from tools.search_sources import run_search, search_sources
from tools.web_search import web_search

WEB_TOOLS = [web_search, scrape_url]


def tools_for(web: bool) -> list:
    """search_sources תמיד. הכלים החיצוניים רק כשהמשתמשת הפעילה «הרחבה לאינטרנט»."""
    return [search_sources] + (WEB_TOOLS if web else [])


TOOLS_BY_NAME = {t.name: t for t in [search_sources, *WEB_TOOLS]}

__all__ = ["tools_for", "TOOLS_BY_NAME", "run_search", "search_sources", "web_search", "scrape_url"]
