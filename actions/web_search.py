# actions/web_search.py
import os
import shutil
from pathlib import Path
from bs4 import BeautifulSoup
import requests
from dotenv import load_dotenv
from web_search.url import list_url  # your DDGS function
import json

load_dotenv()
API_KEY = os.getenv("OPENROUTER_API_KEY")


def run(args):
    """
    Downloads N pages for a query, cleans the HTML, deletes saved folders,
    and summarizes the result using OpenRouter API via requests.
    Expects args = { "query": "search term", "n_results": int }
    """

    query = args.get("query")
    n_results = args.get("n_results", 3)

    if not query:
        raise ValueError("Missing required argument: query")
    if not isinstance(n_results, int) or n_results < 1:
        raise ValueError("n_results must be a positive integer")

    forbidden_words = ["hack", "illegal", "dangerous"]
    if any(word in query.lower() for word in forbidden_words):
        raise PermissionError("This search query is not allowed")

    urls = list_url(query, n_results)
    saved_folders = []

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        )
    }

    # Download HTML pages
    for i, url in enumerate(urls, 1):
        folder_name = f"saved_page_{i}"
        os.makedirs(folder_name, exist_ok=True)
        try:
            resp = requests.get(url, headers=headers, timeout=15)
            resp.raise_for_status()
            with open(
                os.path.join(folder_name, "index.html"), "w", encoding="utf-8"
            ) as f:
                f.write(resp.text)
            saved_folders.append(folder_name)
            print(f"Saved HTML of {url} → {folder_name}")
        except requests.exceptions.HTTPError as e:
            print(f"Skipping {url} → HTTP error: {e}")
        except requests.exceptions.RequestException as e:
            print(f"Skipping {url} → Request failed: {e}")

    # Clean downloaded HTML
    def clean_html_file_bs4(*file_paths):
        all_text = ""
        for file_path in file_paths:
            with open(file_path, "r", encoding="utf-8") as f:
                html_content = f.read()
            soup = BeautifulSoup(html_content, "html.parser")
            all_text += soup.get_text(separator=" ", strip=True) + "\n"
        return all_text

    html_files = [
        str(Path(folder) / "index.html")
        for folder in saved_folders
        if (Path(folder) / "index.html").exists()
    ]

    cleaned_output = clean_html_file_bs4(*html_files)

    # Remove downloaded folders
    for folder in saved_folders:
        shutil.rmtree(folder)

    # Summarize via OpenRouter HTTP API
    payload = {
        "model": "xiaomi/mimo-v2-flash:free",
        "messages": [
            {
                "role": "system",
                "content": "You are IVA, a smart virtual assistant similar to Alexa or Google Assistant, but more natural and thoughtful. You give short, clear, and useful answers. You avoid unnecessary explanations, filler, emojis, special characters, and verbosity. Your tone is calm, confident, and slightly clever. Never robotic. Never dull. Do not include sources, citations, URLs, or website names in your responses. Only return the main content requested by the user.",
            },
            {
                "role": "user",
                "content": f"Summarize this content concisely without mentioning that you are summarizing text, as if you were only explain stuff you already knew:\n{cleaned_output}",
            },
        ],
        "max_tokens": 300,
        "temperature": 0.5,
    }

    response = requests.post(
        "https://openrouter.ai/api/v1/chat/completions",
        headers={"Authorization": f"Bearer {API_KEY}"},
        json=payload,
        timeout=30,
    )

    response.raise_for_status()
    data = response.json()
    return data["choices"][0]["message"]["content"]
