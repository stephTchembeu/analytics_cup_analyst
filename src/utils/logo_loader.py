import requests

FALLBACK_LOGO = "./images/fallback_logo.png"  

def get_team_logo_url(team_name):
    """
    Return the logo image URL of a football team using Wikipedia API.
    Handles approximate names by picking the closest match.
    Returns None if no logo is found.
    """
    search_url = "https://en.wikipedia.org/w/api.php"
    HEADERS = {
        "User-Agent": "FootballLogoFinder/1.0 (https://example.com/; contact@example.com)"
    }
    
    team_name = team_name.strip()
    if not team_name:
        return None

    # Step 1: Search Wikipedia
    search_params = {
        "action": "query",
        "list": "search",
        "srsearch": team_name,
        "format": "json",
    }

    try:
        search_resp = requests.get(search_url, params=search_params, headers=HEADERS).json()
    except requests.JSONDecodeError:
        return None

    search_results = search_resp.get("query", {}).get("search", [])
    if not search_results:
        return None

    # Step 2: Pick the best match (exact title first, else first result)
    page_id = None
    for r in search_results:
        if r["title"].lower() == team_name.lower():
            page_id = r["pageid"]
            break
    if not page_id:
        page_id = search_results[0]["pageid"]

    # Step 3: Get the main image (logo)
    image_params = {
        "action": "query",
        "pageids": page_id,
        "prop": "pageimages",
        "pithumbsize": 800,
        "format": "json",
    }

    try:
        image_resp = requests.get(search_url, params=image_params, headers=HEADERS).json()
    except requests.JSONDecodeError:
        return None

    page = image_resp.get("query", {}).get("pages", {}).get(str(page_id), {})
    if "thumbnail" not in page:
        return None

    return page["thumbnail"]["source"]

