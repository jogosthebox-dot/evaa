import requests
from bs4 import BeautifulSoup
from urllib.parse import quote

def web_search(query, limit=5):
    try:
        url = "https://html.duckduckgo.com/html/?q=" + quote(query)
        r = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=8)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")
        results = []
        for item in soup.select(".result")[:limit]:
            a = item.select_one(".result__a")
            s = item.select_one(".result__snippet")
            if a:
                results.append({
                    "title": a.get_text(" ", strip=True),
                    "snippet": s.get_text(" ", strip=True) if s else "",
                    "url": a.get("href", "")
                })
        return results
    except Exception:
        return []
