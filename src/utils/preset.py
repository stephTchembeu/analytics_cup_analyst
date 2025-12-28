import os
import base64
import numpy as np
import pandas as pd
import streamlit as st
from mplsoccer import Pitch
from kloppy import skillcorner
from typing import List, Tuple
import matplotlib.pyplot as plt
from mplsoccer import Radar, FontManager, grid

from kloppy.domain.models.common import Team
from kloppy.domain.models.tracking import TrackingDataset

from .logo_loader import get_team_logo_url, FALLBACK_LOGO


# Error Handling Helper Functions
def safe_get_event_data() -> pd.DataFrame:
    """Safely retrieves event data from session state with validation.
    
    Validates that event_data exists, is a DataFrame, and is not empty.
    
    Returns:
        pd.DataFrame: Event data if valid, empty DataFrame otherwise.
        
    Raises:
        ValueError: If event data is not available or invalid.
    """
    if "event_data" not in st.session_state:
        raise ValueError("Event data has not been loaded. Please ensure event data is loaded before proceeding.")
    
    event_data = st.session_state.event_data
    
    if event_data is None:
        raise ValueError("Event data is None. Failed to load event data from source.")
    
    if not isinstance(event_data, pd.DataFrame):
        raise TypeError(f"Event data must be a DataFrame, got {type(event_data).__name__}")
    
    if event_data.empty:
        raise ValueError("Event data is empty. No events available for analysis.")
    
    return event_data


def safe_get_match_data() -> TrackingDataset:
    """Safely retrieves match data from session state with validation.
    
    Validates that match_data exists and is a TrackingDataset.
    
    Returns:
        TrackingDataset: Match data if valid.
        
    Raises:
        ValueError: If match data is not available or invalid.
    """
    if "match_data" not in st.session_state:
        raise ValueError("Match data has not been loaded. Please ensure match data is loaded before proceeding.")
    
    match_data = st.session_state.match_data
    
    if match_data is None:
        raise ValueError("Match data is None. Failed to load match data from SkillCorner API.")
    
    if not isinstance(match_data, TrackingDataset):
        raise TypeError(f"Match data must be a TrackingDataset, got {type(match_data).__name__}")
    
    return match_data


def safe_call(func, *args, default_value=None, error_context="", **kwargs):
    """Wrapper function to safely call functions with try-except-else logic.
    
    Handles data loading errors, missing attributes, type errors, and provides
    detailed error messages while returning default values on failure.
    
    Args:
        func: The function to call.
        *args: Positional arguments for the function.
        default_value: Value to return if function fails.
        error_context: Additional context for error messages.
        **kwargs: Keyword arguments for the function.
        
    Returns:
        The function result on success, default_value on failure.
    """
    try:
        result = func(*args, **kwargs)
    except ValueError as e:
        st.warning(f"Data Error: {str(e)}")
        return default_value
    except TypeError as e:
        st.warning(f"Type Error: {str(e)}")
        return default_value
    except AttributeError as e:
        st.warning(f"Missing Attribute: The required field '{str(e)}' is not defined in the data. {error_context}")
        return default_value
    except KeyError as e:
        st.warning(f"Missing Column: The required column {str(e)} is not found in the data. {error_context}")
        return default_value
    except Exception as e:
        st.warning(f"Unexpected Error: {str(e)} {error_context}")
        return default_value
    else:
        # Function executed successfully
        return result


# Function
def render_team_logo(team_name: str, align: str = "left", width: int = 100) -> None:
    """Renders the team logo with the team name below it using HTML.

    Fetches the logo from Wikipedia API or uses a fallback image if not found.

    Args:
        team_name (str): The name of the team to display.
        align (str): Text alignment for the logo and name ('left' or 'right').
        width (int): The width of the logo image in pixels.
    """
    logo_url = get_team_logo_url(team_name)

    if logo_url:
        img_html = f'<img src="{logo_url}" width="{width}"/>'
    elif os.path.exists(FALLBACK_LOGO):
        encoded = base64.b64encode(open(FALLBACK_LOGO, "rb").read()).decode()
        img_html = f'<img src="data:image/png;base64,{encoded}" width="{width}"/>'
    else:
        st.error("No logo found")
        return

    st.markdown(
        f"""
        <div style="text-align: {align};">
            {img_html}
            <p style="font-size: 0.8rem; margin-top: 0.3rem; ">
                {team_name.title()}
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def covered_distance(player, tracking_df: TrackingDataset) -> float:
    """Calculates the total distance covered by a player during the match in kilometers.

    Computes the Euclidean distance traveled by the player from tracking data by calculating
    frame-by-frame movements using X and Y coordinates and summing them up.

    Args:
        player: Player object with player_id attribute from kloppy Team.
        tracking_df (TrackingDataset): SkillCorner TrackingDataset containing tracking positions
                                       with columns formatted as '{player_id}_x' and '{player_id}_y'.

    Returns:
        float: Total distance covered in kilometers, rounded to 2 decimal places.
    """
    player_id = player.player_id
    x_col = f"{player_id}_x"
    y_col = f"{player_id}_y"

    df = tracking_df.to_df(engine="pandas")[[x_col, y_col]].dropna(subset=[x_col])

    # Calculate frame-to-frame distance differences
    dx = df[x_col].diff()
    dy = df[y_col].diff()

    # Compute Euclidean distance per frame
    df["step_distance"] = np.sqrt(dx**2 + dy**2)

    # Sum total distance and convert from meters to kilometers
    distance_totale = df["step_distance"].sum()

    return round(distance_totale / 1000, 2)


def get_teams_in_matches(
    available_matches_ids: List[int],
) -> List[Tuple[str, str, int]]:
    """Retrieves team names and match IDs for a list of available matches.

    Loads match metadata from SkillCorner API for each match ID and extracts
    home and away team names. Uses try-except-else logic to handle load failures
    gracefully, continuing with available matches while storing status in session state.

    Args:
        available_matches_ids (List[int]): List of match IDs from SkillCorner.

    Returns:
        List[Tuple[str, str, int]]: List of tuples (home_team_name, away_team_name, match_id).
    """
    output = []
    failed_matches = []
    
    for match_id in available_matches_ids:
        try:
            dataset = skillcorner.load_open_data(
                match_id=match_id, coordinates="skillcorner", limit=2
            )
            home, away = dataset.metadata.teams
            output.append((home.name, away.name, match_id))
        except Exception as e:
            failed_matches.append((match_id, str(e)))
    else:
        # All matches processed (else executes after the loop completes, unless break occurs)
        if not failed_matches:
            # All matches loaded successfully
            st.session_state.match_loading_message = {
                "type": "success",
                "text": f"Successfully loaded {len(output)} match{'es' if len(output) != 1 else ''}!"
            }
        else:
            # Some matches failed
            failed_ids = ", ".join(str(m[0]) for m in failed_matches)
            st.session_state.match_loading_message = {
                "type": "warning",
                "text": f"Loaded {len(output)} match{'es' if len(output) != 1 else ''} "
                        f"({len(failed_matches)} failed: {failed_ids}). Continuing with available matches."
            }
    
    return output


def preset_app() -> None:
    """Sets up the Streamlit app configuration and UI elements.

    Configures page layout, logos, sidebar match selector, and tab styling.
    This function should be called once at the start of the app to initialize
    unchangeable UI elements and set global app state.
    """
    st.markdown(
        """
        <style>
        .player {
            margin-top: 5px;
        }

        .player .name {
            font-size: 50px;
            font-weight: 700;
            margin: 0;
        }

        .player .position {
            font-size: 35px;
            color: darkgreen;
            margin: 0;
        }

        .player-stats {
        background-color: #f8f9fa;
        padding: 16px;
        border-radius: 12px;
        box-shadow: 0 4px 10px rgba(0,0,0,0.08);
        }

        .player-stats .label {
            font-size: 20px;
            color: #6c757d;
            margin: 6px 0 0 0;
        }

        .player-stats .value {
            font-size: 25px;
            font-weight: 800;
            color: #006400;
            margin: 0 0 10px 0;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    # set title and icon
    st.set_page_config(
        page_title="FootMetricX",
        page_icon=SIMPLE_LOGO,
        layout="wide",
        initial_sidebar_state="auto",
    )

    # set our logo
    st.logo(LOGO_OPTIONS[1], icon_image=LOGO_OPTIONS[0])  # sidebar.

    # set the central logo
    image_path = LOGO_WITH_TEXT
    with open(image_path, "rb") as file:
        data = base64.b64encode(file.read()).decode()
    st.markdown(
        f"""
    <div style="margin-top:-30px; text-align:left;    ">
        <img src="data:image/png;base64,{data}" style="width:250px; ">
    </div>
    """,
        unsafe_allow_html=True,
    )

    # Sidebar choosing a match
    st.sidebar.markdown(
        f"<h2 style='color: {COLOR_PALETTE['blue']}; font-size: 25px; padding: 0rem 0px; padding-top:0.5rem;'>Choose a match.</h2>",
        unsafe_allow_html=True,
    )  # we set the title of the upload section
    st.session_state.selected_match = st.sidebar.selectbox(
        "Available Matches.", options=AVAILABLE_MATCHES
    )
    st.session_state.selected_match_id = first_word(st.session_state.selected_match)

    # Display match loading message under the selectbox
    if "match_loading_message" in st.session_state:
        msg = st.session_state.match_loading_message
        if msg["type"] == "success":
            st.sidebar.success(msg["text"])
        elif msg["type"] == "warning":
            st.sidebar.warning(msg["text"])

    st.markdown(
        f"""
    <style>
    .stTabs [data-baseweb="tab"] {{
        color: #000;
    }}
    .stTabs [data-baseweb="tab"]:hover {{
        color: {COLOR_PALETTE["green"]};
    }}
    .stTabs [data-baseweb="tab"][aria-selected="true"] {{
        color: {COLOR_PALETTE["green"]} !important;
    }}
    </style>
    """,
        unsafe_allow_html=True,
    )

    st.markdown(
        f"""
    <style>
    .stTabs [aria-selected="true"] {{
        border-bottom: 3px solid {COLOR_PALETTE["green"]} !important;
    }}
    .stTabs [data-baseweb="tab"] {{
        border-bottom: 3px solid transparent !important;
    }}
    </style>
    """,
        unsafe_allow_html=True,
    )
    return


def first_word(string: str) -> str:
    """Extracts the first word from a space-separated string.

    Args:
        string (str): Input string to split.

    Returns:
        str: The first word from the string, or empty string if input is empty.
    """
    words = string.split(" ")
    if words:
        return words[0]
    return ""


# variables
SIMPLE_LOGO = "./src/images/logo.png"  # logo when no side bar
LOGO_WITH_TEXT = "./src/images/logo_with_text.png"  # central logo and sidebar logo
AVAILABLE_MATCHES_IDS = [
    1886347,
    1899585,
    1925299,
    1953632,
    1996435,
    2006229,
    2011166,
    2013725,
    2015213,
    2017461
]
LOGO_OPTIONS = (SIMPLE_LOGO, LOGO_WITH_TEXT)
TAB_NAMES = (
    "Team Stats",
    "Pitch Control",
    "Defensive Shape",
    "Player Profiling",
    "Player Performance",
)
COLOR_PALETTE = {"blue": "#052B72", "green": "#217c23"}  # color palette.
AVAILABLE_MATCHES = [
    f"{x[2]} {x[0]} - {x[1]}" for x in get_teams_in_matches(AVAILABLE_MATCHES_IDS)
]
STATS_LABELS = [
    "Shots off target [Shots on target]",
    "Possession",
    "Total passes [succeed pass]",
    "Pass accuracy percentage",
    "Clearances",
    "Fouls committed",
    "Direct disruptions",
    "Direct regains",
    "Possession losses",
]