import os
import requests
from bs4 import BeautifulSoup


def save_page(url, save_dir="saved_page"):
    os.makedirs(save_dir, exist_ok=True)

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    }

    resp = requests.get(url, headers=headers)
    resp.raise_for_status()

    soup = BeautifulSoup(resp.text, "html.parser")

    # Remove scripts, styles, and external resource links
    for tag in soup(["script", "style"]):
        tag.decompose()

    # Remove src/href from img, link, script
    for tag in soup.find_all(["img", "link", "script"]):
        if tag.has_attr("src"):
            del tag["src"]
        if tag.has_attr("href"):
            del tag["href"]

    html_file = os.path.join(save_dir, "index.html")
    with open(html_file, "w", encoding="utf-8") as f:
        f.write(str(soup))

    print(f"Saved HTML of {url} to {save_dir}")
