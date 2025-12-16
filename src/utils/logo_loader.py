import requests
from rapidfuzz import process, fuzz

FALLBACK_LOGO = "./src/images/fallback_logo.png"

def get_team_logo_url(team_name):
    """
    Return the logo image URL of a football team using Wikipedia API.
    Uses rapidfuzz fuzzy matching for better approximate matching.
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
    except (requests.JSONDecodeError, ValueError):
        return None

    search_results = search_resp.get("query", {}).get("search", [])
    if not search_results:
        return None

    # Step 2: Fuzzy-match the team name to the result titles
    titles = [r["title"] for r in search_results]

    # Use rapidfuzz to pick best match
    best_match = process.extractOne(
        team_name,
        titles,
        scorer=fuzz.WRatio,
        score_cutoff=60  # Adjust threshold if needed
    )

    if best_match:
        matched_title = best_match[0]
        page_id = next(r["pageid"] for r in search_results if r["title"] == matched_title)
    else:
        # fallback: take the first search result
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
    except (requests.JSONDecodeError, ValueError):
        return None

    page = image_resp.get("query", {}).get("pages", {}).get(str(page_id), {})
    if "thumbnail" not in page:
        return None

    return page["thumbnail"]["source"]
