import os
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from web_search.url import list_url

load_dotenv()
API_KEY = os.getenv("OPENROUTER_API_KEY")

MODEL = "arcee-ai/trinity-large-preview:free"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
}


def _fetch_and_clean(url: str) -> str:
    """Fetches a URL and returns cleaned plain text. No disk I/O."""
    try:
        resp = requests.get(url, headers=HEADERS, timeout=10)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")
        return soup.get_text(separator=" ", strip=True)
    except requests.RequestException as e:
        print(f"Skipping {url}: {e}")
        return ""


def run(args):
    query: str = args["query"]
    n_results: int = int(args.get("n_results", 3))

    urls = list_url(query, n_results)
    if not urls:
        return "No results found for that search."

    # Fetch and clean all pages in memory — no SD card writes
    cleaned_text = "\n".join(_fetch_and_clean(url) for url in urls).strip()
    if not cleaned_text:
        return "Could not retrieve content for that search."

    # Truncate to avoid blowing the context window / max_tokens
    cleaned_text = cleaned_text[:6000]
    print(f"[DEBUG] cleaned_text length: {len(cleaned_text)}")
    print(f"[DEBUG] cleaned_text preview: {cleaned_text[:200]}")

    payload = {
        "model": MODEL,
        "messages": [
            {
                "role": "system",
                "content": (
                    "You are IVA, a smart voice assistant. Answer the user's question directly and concisely "
                    "based on the provided web content. No sources, URLs, citations, emojis, or filler. "
                    "Sound natural, as if you already knew this. Keep it short."
                ),
            },
            {
                "role": "user",
                "content": f"Question: {query}\n\nWeb content:\n{cleaned_text}",
            },
        ],
        "max_tokens": 300,
        "temperature": 0.5,
    }

    try:
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={"Authorization": f"Bearer {API_KEY}"},
            json=payload,
            timeout=30,
        )
        response.raise_for_status()
        result = response.json()["choices"][0]["message"]["content"]
        print(f"[DEBUG] web_search result: {repr(result)}")
        return result
    except requests.RequestException as e:
        print(f"[DEBUG] web_search API error: {e}")
        return f"Search summary failed: {e}"