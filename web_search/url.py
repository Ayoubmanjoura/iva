from ddgs import DDGS


def list_url(query: str, n_results: int = 3) -> list[str]:
    """Returns up to n_results URLs for the given search query."""
    with DDGS() as ddgs:
        results = list(ddgs.text(query, max_results=n_results))
    return [r["href"] for r in results]