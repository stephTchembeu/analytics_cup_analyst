import os

FALLBACK_LOGO = "./src/images/fallback_logo.png"
TEAM_LOGO_DIR = "./src/images/teams_logo"

def get_team_logo(team_id: int | str) -> str:
    """
    Return the local path of a team's logo based on its team_id.
    Falls back to a default logo if not found.
    """

    if team_id is None:
        return FALLBACK_LOGO

    logo_path = os.path.join(TEAM_LOGO_DIR, f"{team_id}.png")

    if os.path.exists(logo_path):
        return logo_path

    return FALLBACK_LOGO

