import os
from serpapi import GoogleSearch

SERPAPI_KEY = os.getenv("SERPAPI_API_KEY")

def find_competitors(idea: str, num_results: int = 5) -> list[str]:
    """
    Use SerpApi GoogleSearch to find top potential competitor names for a given idea.
    Returns a list of competitor names.
    """
    if not SERPAPI_KEY:
        raise RuntimeError("SERPAPI_API_KEY environment variable not set")
    # Build query to find existing competitor products
    query = f"{idea} product competitors"
    params = {
        "q": query,
        "location": "United States",
        "api_key": SERPAPI_KEY,
    }
    search = GoogleSearch(params)
    data = search.get_json()
    competitors: list[str] = []
    # Extract titles from organic results
    for item in data.get("organic_results", [])[:num_results]:
        title = item.get("title", "")
        # Split title at common separators to extract clean name
        name = title.split("–")[0].split("|")[0].strip()
        if name:
            competitors.append(name)
    return competitors