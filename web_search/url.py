from ddgs import DDGS


def list_url(query, n=5):
    """
    Returns the first n URLs for a search query using DuckDuckGo.
    """
    urls = []
    with DDGS() as ddgs:
        for r in ddgs.text(query, max_results=n):
            urls.append(r["href"])
    return urls
