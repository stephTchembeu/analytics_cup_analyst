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


# ============================================================================
# ERROR HANDLING HELPER FUNCTIONS
# ============================================================================

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


def display_status_messages() -> None:
    """Displays all data loading status messages in the sidebar under the selectbox.
    
    Shows messages for:
    - Match loading status (from get_teams_in_matches)
    - Match data loading status
    - Event data loading status
    """
    # Match loading status
    if "match_loading_message" in st.session_state:
        msg = st.session_state.match_loading_message
        if msg["type"] == "success":
            st.sidebar.success(msg["text"])
        elif msg["type"] == "warning":
            st.sidebar.warning(msg["text"])
    
    # Match data loading status
    if "match_data_error" in st.session_state and st.session_state.match_data_error:
        st.sidebar.error(f"Match Data Error: {st.session_state.match_data_error}")
    elif "match_data" in st.session_state and st.session_state.match_data:
        st.sidebar.success("Match data loaded")
    
    # Event data loading status
    if "event_data_error" in st.session_state and st.session_state.event_data_error:
        st.sidebar.error(f"Event Data Error: {st.session_state.event_data_error}")
    elif "event_data" in st.session_state and st.session_state.event_data is not None:
        st.sidebar.success("Event data loaded")


# ============================================================================
# UI FUNCTIONS
# ============================================================================

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
    gracefully, continuing with available matches while displaying warnings.

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
        # Store status in session state for later display by display_status_messages()
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
                "text": f"Loaded {len(output)} match{'es' if len(output) != 1 else ''} ({len(failed_matches)} failed: {failed_ids}). Continuing with available matches."
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


def shots(team: Team) -> Tuple[int, int]:
    """Calculates total shots and shots on target for a team.

    Filters event data for shot events and determines on-target shots based on
    goal outcomes.

    Args:
        team (Team): Team object with team_id attribute.

    Returns:
        Tuple[int, int]: Tuple of (total_shots, shots_on_target).
    """
    try:
        # Validate input
        if not isinstance(team, Team):
            raise TypeError(f"Expected Team object, got {type(team).__name__}")
        
        if not hasattr(team, 'team_id'):
            raise AttributeError("Team object missing 'team_id' attribute")
        
        # Get event data
        event_data = safe_get_event_data()
        
        # Validate required columns
        required_cols = ['end_type', 'team_id', 'lead_to_goal', 'game_interruption_after']
        missing_cols = [col for col in required_cols if col not in event_data.columns]
        if missing_cols:
            raise KeyError(f"Missing required columns: {', '.join(missing_cols)}")
        
        shots_df = event_data[
            event_data["end_type"].str.lower() == "shot"
        ].copy()
        shots_df["is_on_target"] = (shots_df["lead_to_goal"] == 1) & (
            shots_df["game_interruption_after"].isin(["goal_for", "corner_for"])
        )
        shots_df["is_on_target"] = shots_df["is_on_target"].astype("boolean")
        team_shots = shots_df[shots_df["team_id"] == team.team_id]
        total = len(team_shots)
        on_target = team_shots["is_on_target"].sum()
        result = (total, on_target)
    except (ValueError, TypeError, AttributeError, KeyError) as e:
        st.warning(f"Error calculating shots: {str(e)}")
        result = (0, 0)
    else:
        # Successfully calculated shots
        return result
    
    return result


def passess(team: Team) -> Tuple[int, int]:
    """Calculates total passes and successful passes for a team.

    Filters event data for pass events and counts successful passes.

    Args:
        team (Team): Team object with team_id attribute.

    Returns:
        Tuple[int, int]: Tuple of (total_passes, successful_passes).
    """
    try:
        # Validate input
        if not isinstance(team, Team):
            raise TypeError(f"Expected Team object, got {type(team).__name__}")
        
        if not hasattr(team, 'team_id'):
            raise AttributeError("Team object missing 'team_id' attribute")
        
        # Get event data
        event_data = safe_get_event_data()
        
        # Validate required columns
        required_cols = ['end_type', 'team_id', 'pass_outcome']
        missing_cols = [col for col in required_cols if col not in event_data.columns]
        if missing_cols:
            raise KeyError(f"Missing required columns: {', '.join(missing_cols)}")
        
        pass_df = event_data[
            event_data["end_type"].str.lower() == "pass"
        ].copy()
        total_pass = pass_df[(pass_df["team_id"] == team.team_id)]
        good_pass = pass_df[
            (pass_df["team_id"] == team.team_id) & (pass_df["pass_outcome"] == "successful")
        ]
        result = (len(total_pass), len(good_pass))
    except (ValueError, TypeError, AttributeError, KeyError) as e:
        st.warning(f"Error calculating passes: {str(e)}")
        result = (0, 0)
    else:
        # Successfully calculated passes
        return result
    
    return result


def pass_accuracy(team: Team) -> int:
    """Calculates pass accuracy percentage for a team.

    Args:
        team (Team): Team object with team_id attribute.

    Returns:
        int: Pass accuracy as a percentage (0-100).
    """
    passes_data = passess(team)
    if passes_data[0] == 0:
        return 0
    return int(passes_data[1] * 100 / passes_data[0])


def possession(team: Team) -> int:
    """Calculates possession percentage for a team based on event duration.

    Calculates possession by summing the duration of events (in seconds)
    performed by each team and computing the percentage.

    Args:
        team (Team): Team object with team_id attribute.

    Returns:
        int: Possession percentage (rounded up if decimal > 0.5).
    """
    try:
        # Validate input
        if not isinstance(team, Team):
            raise TypeError(f"Expected Team object, got {type(team).__name__}")
        
        if not hasattr(team, 'team_id'):
            raise AttributeError("Team object missing 'team_id' attribute")
        
        # Get event data
        event_data = safe_get_event_data()
        
        # Validate required columns
        required_cols = ['team_id', 'duration']
        missing_cols = [col for col in required_cols if col not in event_data.columns]
        if missing_cols:
            raise KeyError(f"Missing required columns: {', '.join(missing_cols)}")
        
        # Get all events for both teams
        team_events = event_data[event_data["team_id"] == team.team_id]
        total_duration = event_data['duration'].sum()
        
        if total_duration == 0:
            result = 50
        else:
            team_duration = team_events['duration'].sum()
            possession_value = (team_duration / total_duration) * 100
            # Round to nearest integer (round up if decimal > 0.5)
            result = round(possession_value)
    except (ValueError, TypeError, AttributeError, KeyError) as e:
        st.warning(f"Error calculating possession: {str(e)}")
        result = 50
    else:
        return result
    
    return result


def clearances(team: Team) -> int:
    """Counts clearance events for a team.

    Args:
        team (Team): Team object with team_id attribute.

    Returns:
        int: Number of clearances made by the team.
    """
    try:
        # Validate input
        if not isinstance(team, Team):
            raise TypeError(f"Expected Team object, got {type(team).__name__}")
        
        if not hasattr(team, 'team_id'):
            raise AttributeError("Team object missing 'team_id' attribute")
        
        # Get event data
        event_data = safe_get_event_data()
        
        # Validate required columns
        required_cols = ['end_type', 'team_id']
        missing_cols = [col for col in required_cols if col not in event_data.columns]
        if missing_cols:
            raise KeyError(f"Missing required columns: {', '.join(missing_cols)}")
        
        clearances_df = event_data[event_data["end_type"].str.lower() == "clearance"]
        team_clearances = clearances_df[clearances_df["team_id"] == team.team_id]
        result = len(team_clearances)
    except (ValueError, TypeError, AttributeError, KeyError) as e:
        st.warning(f"Error calculating clearances: {str(e)}")
        result = 0
    else:
        return result
    
    return result


def fouls_committed(team: Team) -> int:
    """Counts fouls committed by a team.

    Args:
        team (Team): Team object with team_id attribute.

    Returns:
        int: Number of fouls committed by the team.
    """
    try:
        # Validate input
        if not isinstance(team, Team):
            raise TypeError(f"Expected Team object, got {type(team).__name__}")
        
        if not hasattr(team, 'team_id'):
            raise AttributeError("Team object missing 'team_id' attribute")
        
        # Get event data
        event_data = safe_get_event_data()
        
        # Validate required columns
        required_cols = ['end_type', 'team_id']
        missing_cols = [col for col in required_cols if col not in event_data.columns]
        if missing_cols:
            raise KeyError(f"Missing required columns: {', '.join(missing_cols)}")
        
        fouls_df = event_data[event_data["end_type"].str.lower() == "foul_committed"]
        team_fouls = fouls_df[fouls_df["team_id"] == team.team_id]
        result = len(team_fouls)
    except (ValueError, TypeError, AttributeError, KeyError) as e:
        st.warning(f"Error calculating fouls: {str(e)}")
        result = 0
    else:
        return result
    
    return result


def direct_disruptions(team: Team) -> int:
    """Counts direct disruption events for a team.

    Direct disruptions occur when a team directly breaks up an opponent's play.

    Args:
        team (Team): Team object with team_id attribute.

    Returns:
        int: Number of direct disruptions made by the team.
    """
    try:
        # Validate input
        if not isinstance(team, Team):
            raise TypeError(f"Expected Team object, got {type(team).__name__}")
        
        if not hasattr(team, 'team_id'):
            raise AttributeError("Team object missing 'team_id' attribute")
        
        # Get event data
        event_data = safe_get_event_data()
        
        # Validate required columns
        required_cols = ['end_type', 'team_id']
        missing_cols = [col for col in required_cols if col not in event_data.columns]
        if missing_cols:
            raise KeyError(f"Missing required columns: {', '.join(missing_cols)}")
        
        disruptions_df = event_data[event_data["end_type"].str.lower() == "direct_disruption"]
        team_disruptions = disruptions_df[disruptions_df["team_id"] == team.team_id]
        result = len(team_disruptions)
    except (ValueError, TypeError, AttributeError, KeyError) as e:
        st.warning(f"Error calculating direct disruptions: {str(e)}")
        result = 0
    else:
        return result
    
    return result


def direct_regains(team: Team) -> int:
    """Counts direct regain events for a team.

    Direct regains occur when a team directly wins back the ball.

    Args:
        team (Team): Team object with team_id attribute.

    Returns:
        int: Number of direct regains by the team.
    """
    try:
        # Validate input
        if not isinstance(team, Team):
            raise TypeError(f"Expected Team object, got {type(team).__name__}")
        
        if not hasattr(team, 'team_id'):
            raise AttributeError("Team object missing 'team_id' attribute")
        
        # Get event data
        event_data = safe_get_event_data()
        
        # Validate required columns
        required_cols = ['end_type', 'team_id']
        missing_cols = [col for col in required_cols if col not in event_data.columns]
        if missing_cols:
            raise KeyError(f"Missing required columns: {', '.join(missing_cols)}")
        
        regains_df = event_data[event_data["end_type"].str.lower() == "direct_regain"]
        team_regains = regains_df[regains_df["team_id"] == team.team_id]
        result = len(team_regains)
    except (ValueError, TypeError, AttributeError, KeyError) as e:
        st.warning(f"Error calculating direct regains: {str(e)}")
        result = 0
    else:
        return result
    
    return result


def possession_losses(team: Team) -> int:
    """Counts possession loss events for a team.

    Args:
        team (Team): Team object with team_id attribute.

    Returns:
        int: Number of possession losses by the team.
    """
    try:
        # Validate input
        if not isinstance(team, Team):
            raise TypeError(f"Expected Team object, got {type(team).__name__}")
        
        if not hasattr(team, 'team_id'):
            raise AttributeError("Team object missing 'team_id' attribute")
        
        # Get event data
        event_data = safe_get_event_data()
        
        # Validate required columns
        required_cols = ['end_type', 'team_id']
        missing_cols = [col for col in required_cols if col not in event_data.columns]
        if missing_cols:
            raise KeyError(f"Missing required columns: {', '.join(missing_cols)}")
        
        losses_df = event_data[event_data["end_type"].str.lower() == "possession_loss"]
        team_losses = losses_df[losses_df["team_id"] == team.team_id]
        result = len(team_losses)
    except (ValueError, TypeError, AttributeError, KeyError) as e:
        st.warning(f"Error calculating possession losses: {str(e)}")
        result = 0
    else:
        return result
    
    return result


def get_stats(team: Team) -> dict:
    """Aggregates all match statistics for a team.

    Computes and formats all available stats including shots, passes, clearances,
    fouls, and disruptions.

    Args:
        team (Team): Team object with team_id attribute.

    Returns:
        dict: Dictionary with formatted stat strings ready for display.
    """
    stats = {
        "shots": f"{shots(team)[0]}[{shots(team)[1]}]",
        "possession": f"{possession(team)}%",
        "passes": f"{passess(team)[0]}[{passess(team)[1]}]",
        "passes_accuracy": f"{pass_accuracy(team)}%",
        "clearances": f"{clearances(team)}",
        "fouls_committed": f"{fouls_committed(team)}",
        "direct_disruptions": f"{direct_disruptions(team)}",
        "direct_regains": f"{direct_regains(team)}",
        "possession_losses": f"{possession_losses(team)}",
    }
    return stats


def get_players_name(team_name: str, match_data: TrackingDataset) -> List[str]:
    """Retrieves all player names for a specific team from match data.

    Args:
        team_name (str): Name of the team.
        match_data (TrackingDataset): SkillCorner TrackingDataset object.

    Returns:
        List[str]: List of player full names for the team.
    """
    for team in match_data.metadata.teams:
        if team.name == team_name:
            return [player.full_name for player in team.players]
    return []


def heatmap(
    xs: pd.Series,
    ys: pd.Series,
    attacking_side: pd.Series,
    xs_shot: pd.Series,
    ys_shot: pd.Series,
    attacking_side_shot: pd.Series,
    match_data: TrackingDataset,
) -> None:
    """Generates and displays a heatmap of player movements and shot locations.

    Creates a visualization showing where a player spends most of their time on the pitch
    using kernel density estimation (KDE), with shot locations overlaid as scatter points.
    Normalizes coordinates so that all movements are shown from left to right attacking direction.

    Args:
        xs (pd.Series): X coordinates of player movements/pass starts.
        ys (pd.Series): Y coordinates of player movements/pass starts.
        attacking_side (pd.Series): Direction team was attacking ('left_to_right' or 'right_to_left').
        xs_shot (pd.Series): X coordinates of shot locations.
        ys_shot (pd.Series): Y coordinates of shot locations.
        attacking_side_shot (pd.Series): Direction team was attacking when taking shots.
        match_data (TrackingDataset): SkillCorner TrackingDataset for pitch dimensions.

    Returns:
        None: Displays the chart using st.pyplot().
    """
    # Normalize movement coordinates
    xs_plot = xs.copy()
    ys_plot = ys.copy()

    mask = attacking_side == "right_to_left"
    xs_plot[mask] = -xs_plot[mask]
    ys_plot[mask] = -ys_plot[mask]

    # Normalize shot coordinates
    xs_shot_plot = xs_shot.copy()
    ys_shot_plot = ys_shot.copy()

    mask_shot = attacking_side_shot == "right_to_left"
    xs_shot_plot[mask_shot] = -xs_shot_plot[mask_shot]
    ys_shot_plot[mask_shot] = -ys_shot_plot[mask_shot]

    pitch = Pitch(
        pitch_type="skillcorner",
        pitch_length=105,
        pitch_width=68,
        line_zorder=2,
    )

    fig, ax = pitch.draw()
    ax.set_title("Pass / movement heatmap (L→R normalized)")

    # Only plot KDE if we have movement data
    if len(xs_plot) > 0:
        pitch.kdeplot(
            xs_plot,
            ys_plot,
            ax=ax,
            cmap="YlOrRd",
            fill=True,
            levels=100
        )

    # Only plot shots if we have shot data
    if len(xs_shot_plot) > 0:
        pitch.scatter(
            xs_shot_plot,
            ys_shot_plot,
            ax=ax,
            c="green",
            s=50,
            edgecolors="black",
            label="Shots"
        )
        ax.legend()

    st.pyplot(fig)


def pass_map(
    xs: pd.Series,
    ys: pd.Series,
    xs_end: pd.Series,
    ys_end: pd.Series,
    pass_outcome: pd.Series,
    match_data: TrackingDataset,
) -> None:
    """Generates and displays a pass map showing pass start and end locations.

    Creates a visualization of all passes made by a player or team, with lines connecting
    pass start positions to end positions. Pass outcomes are color-coded: green for successful
    passes and red for unsuccessful passes.

    Args:
        xs (pd.Series): X coordinates of pass start positions.
        ys (pd.Series): Y coordinates of pass start positions.
        xs_end (pd.Series): X coordinates of pass end positions (receiver location).
        ys_end (pd.Series): Y coordinates of pass end positions (receiver location).
        pass_outcome (pd.Series): Series indicating pass outcome ('successful' or other).
        match_data (TrackingDataset): SkillCorner TrackingDataset for pitch dimensions.

    Returns:
        None: Displays the chart using st.pyplot().
    """
    pitch = Pitch(
        pitch_type="skillcorner",
        pitch_length=match_data.metadata.coordinate_system.pitch_length,
        pitch_width=match_data.metadata.coordinate_system.pitch_width,
        line_zorder=2,
    )
    fig, ax = pitch.draw()
    ax.set_title("Pass Map")

    # Separate successful and unsuccessful passes
    successful_mask = pass_outcome == "successful"

    # Plot unsuccessful passes in red
    unsuccessful_xs = xs[~successful_mask]
    unsuccessful_ys = ys[~successful_mask]
    unsuccessful_xs_end = xs_end[~successful_mask]
    unsuccessful_ys_end = ys_end[~successful_mask]

    # Plot successful passes in green
    successful_xs = xs[successful_mask]
    successful_ys = ys[successful_mask]
    successful_xs_end = xs_end[successful_mask]
    successful_ys_end = ys_end[successful_mask]

    # Draw arrows for unsuccessful passes
    if len(unsuccessful_xs) > 0:
        pitch.arrows(
            unsuccessful_xs,
            unsuccessful_ys,
            unsuccessful_xs_end,
            unsuccessful_ys_end,
            ax=ax,
            color="red",
            alpha=0.4,
            width=1.5,
            headwidth=4,
            headlength=3,
        )

    # Draw arrows for successful passes
    if len(successful_xs) > 0:
        pitch.arrows(
            successful_xs,
            successful_ys,
            successful_xs_end,
            successful_ys_end,
            ax=ax,
            color="green",
            alpha=0.6,
            width=1.5,
            headwidth=4,
            headlength=3,
        )

    # Add legend
    from matplotlib.patches import Patch

    legend_elements = [
        Patch(facecolor="green", alpha=0.6, label="Successful Pass"),
        Patch(facecolor="red", alpha=0.4, label="Unsuccessful Pass"),
    ]
    ax.legend(handles=legend_elements, loc="upper left")

    st.pyplot(fig)


def max_speed(player, tracking_df):
    """
    Calculates the maximum speed reached by a player during the match in m/s,
    with filtering to remove unrealistic spikes using Mbappé's max speed as threshold.

    Args:
        player: Player object (must have `player_id`)
        tracking_df: TrackingDataset (Kloppy or similar) with columns
                     '{player_id}_x' and '{player_id}_y' per frame.

    Returns:
        float: Maximum speed in m/s.
    """
    player_id = player.player_id
    x_col = f"{player_id}_x"
    y_col = f"{player_id}_y"

    # Convert tracking dataset to pandas
    df = tracking_df.to_df(engine="pandas")[[x_col, y_col]].dropna(
        subset=[x_col, y_col]
    )

    if df.empty:
        return 0.0

    # Compute differences frame to frame
    dx = df[x_col].diff()
    dy = df[y_col].diff()

    # Euclidean distance per frame (in meters)
    step_distance = np.sqrt(dx**2 + dy**2)

    # Frame rate
    fps = tracking_df.metadata.frame_rate

    # Maximum step per frame threshold based on realistic max speed (Mbappé ~10.28 m/s)
    max_speed_threshold_m_s = 10.277777  # m/s
    max_step_per_frame = max_speed_threshold_m_s / fps

    # Filter unrealistic steps (likely data errors)
    step_distance = step_distance.where(step_distance <= max_step_per_frame, 0)

    # Compute speed per frame in m/s: distance(meters) * fps(frames/second) = meters/second
    speed_m_s = step_distance * fps

    # Get maximum speed
    max_speed_value = speed_m_s.max()

    return round(max_speed_value, 2)


def shots_on_target(player, match_data: TrackingDataset) -> int:
    """Counts the number of shots on target made by a player.

    Filters shot events by player_id and determines on-target shots based on
    goal outcomes and game interruption events.

    Args:
        player: Player object with player_id attribute.
        match_data (TrackingDataset): SkillCorner TrackingDataset object.

    Returns:
        int: Number of shots on target.
    """
    shots_df = st.session_state.event_data[
        (st.session_state.event_data["end_type"].str.lower() == "shot")
        & (st.session_state.event_data["player_id"] == int(player.player_id))
    ].copy()

    if shots_df.empty:
        return 0

    shots_df["is_on_target"] = (shots_df["lead_to_goal"] == 1) & (
        shots_df["game_interruption_after"].isin(["goal_for", "corner_for"])
    )
    on_target = shots_df["is_on_target"].sum()
    return int(on_target)


def expected_goals(player, match_data: TrackingDataset) -> float:
    """Calculates expected goals (xG) for a player.

    Counts the number of shots by the player. If xG values are available in the
    event data, they will be summed; otherwise defaults to 0.15 per shot as an estimate.

    Args:
        player: Player object with player_id attribute.
        match_data (TrackingDataset): SkillCorner TrackingDataset object.

    Returns:
        float: Expected goals value.
    """
    shots_df = st.session_state.event_data[
        (st.session_state.event_data["end_type"].str.lower() == "shot")
        & (st.session_state.event_data["player_id"] == int(player.player_id))
    ]

    if shots_df.empty:
        return 0.0

    # If xG column exists, sum it; otherwise estimate 0.15 per shot
    if "xG" in shots_df.columns:
        return round(shots_df["xG"].sum(), 2)
    else:
        return round(len(shots_df) * 0.15, 2)


def expected_threat(player, match_data: TrackingDataset) -> float:
    """Calculates expected threat (xT) generated by a player.

    Counts successful passes and estimates xT. If xT values are available in the
    event data, they will be summed; otherwise defaults to 0.02 per successful pass.

    Args:
        player: Player object with player_id attribute.
        match_data (TrackingDataset): SkillCorner TrackingDataset object.

    Returns:
        float: Expected threat value.
    """
    pass_df = st.session_state.event_data[
        (st.session_state.event_data["end_type"].str.lower() == "pass")
        & (st.session_state.event_data["player_id"] == int(player.player_id))
        & (st.session_state.event_data["pass_outcome"] == "successful")
    ]

    if pass_df.empty:
        return 0.0

    # If xT column exists, sum it; otherwise estimate 0.02 per successful pass
    if "xT" in pass_df.columns:
        return round(pass_df["xT"].sum(), 2)
    else:
        return round(len(pass_df) * 0.02, 2)


def shots_(player_id: float) -> int:
    """Counts the total number of shot events for a specific player.

    Filters shot events from the event data by player_id.

    Args:
        player_id (float): The unique identifier of the player.

    Returns:
        int: The number of shot events attempted by the player.
    """
    shot_events = st.session_state.event_data[
        (st.session_state.event_data["end_type"] == "shot")
        & (st.session_state.event_data["player_id"] == float(player_id))
    ]
    return len(shot_events)


def total_shot(shot_events: pd.DataFrame) -> int:
    """Counts the total number of shots in a given DataFrame.

    Simple utility function that returns the row count of a shot events DataFrame.

    Args:
        shot_events (pd.DataFrame): DataFrame containing shot event data.

    Returns:
        int: The number of rows (shot events) in the DataFrame.
    """
    return len(shot_events)


def offensive_action(player_id: float) -> float:
    """Calculates the percentage of offensive actions performed by a player.

    Measures the quantity and intensity of offensive actions by analyzing event subtypes
    that indicate attacking, movement, and positioning during possession. Returns the percentage
    of offensive actions relative to all player actions.

    Offensive subtypes include: short passing reception, forward runs, positioning behind
    defenders, dropping back, wide movement, half-space positioning, overlaps, underlaps,
    support movement, and cross reception.

    Args:
        player_id (float): The unique identifier of the player.

    Returns:
        float: The percentage of offensive actions out of total player actions (0-25).
    """
    OFFENSIVE_SUBTYPES = [
        "coming_short",
        "run_ahead_of_the_ball",
        "behind",
        "dropping_off",
        "pulling_wide",
        "pulling_half_space",
        "overlap",
        "underlap",
        "support",
        "cross_receiver",
    ]

    player_events = st.session_state.event_data[
        st.session_state.event_data["player_id"] == float(player_id)
    ]
    offensive_events = player_events[
        player_events["event_subtype"].isin(OFFENSIVE_SUBTYPES)
    ]

    if len(player_events) == 0:
        return 0.0

    return round(len(offensive_events) / len(player_events) * 25, 2)


def avg_ball_retention_time(player_id: float) -> float:
    """Calculates the average ball retention time for a player during possession.

    Computes the average duration the player keeps the ball during events that lead to
    either a direct regain followed by a pass/shot, or a direct pass/shot. This metric
    indicates how long a player typically holds the ball before releasing it.

    Args:
        player_id (float): The unique identifier of the player.

    Returns:
        float: Average retention time in seconds, with higher values indicating longer ball possession.
    """
    mask = (st.session_state.event_data["player_id"] == float(player_id)) & (
        (
            (st.session_state.event_data["end_type"] == "direct_regain")
            & (st.session_state.event_data["end_type"].shift(-1).isin(["pass", "shot"]))
        )
        | (st.session_state.event_data["end_type"].isin(["shot", "pass"]))
    )
    filtered_events = st.session_state.event_data[mask]

    if len(filtered_events) == 0:
        return 0.0

    return round(filtered_events["duration"].sum() / len(filtered_events), 2)


def avg_forward_pass(player_id: float) -> float:
    """Calculates the percentage of forward passes made by a player.

    Analyzes all pass events by a player and determines what proportion are forward passes
    (passes directed toward the opponent's goal). This metric helps assess a player's
    attacking intent and ability to progress the ball up the pitch.

    Args:
        player_id (float): The unique identifier of the player.

    Returns:
        float: The percentage of forward passes out of total passes (0-25).
    """
    pass_events = st.session_state.event_data[
        (st.session_state.event_data["end_type"] == "pass")
        & (st.session_state.event_data["player_id"] == float(player_id))
    ]

    if len(pass_events) == 0:
        return 0.0

    forward_passes = pass_events[pass_events["pass_direction"] == "forward"]
    return round(len(forward_passes) / len(pass_events) * 25, 2)


def pressing_engagement(player_id: float, team_id: float) -> dict:
    """Calculates pressing and defensive engagement metrics for a player.

    Analyzes defensive actions and pressing events, including direct and indirect
    disruptions, regains, possession losses, fouls, and clearances. Returns a dictionary
    with three key metrics:

    - avg_Pressing_actions: Player's pressing events as percentage of team's total pressing events
    - Defensive_Action_volume: Player's defensive actions as percentage of their total actions
    - Success_DA: Count of successful defensive actions resulting in ball recovery

    Args:
        player_id (float): The unique identifier of the player.
        team_id (float): The unique identifier of the player's team.

    Returns:
        dict: Dictionary with three keys:
            - 'avg_Pressing_actions' (float): Percentage of team pressing actions
            - 'Defensive_Action_volume' (float): Percentage of player's actions that are defensive
            - 'Success_DA' (int): Count of successful defensive actions
    """
    pressing_event = st.session_state.event_data[
        (st.session_state.event_data["team_id"] == team_id)
        & (
            (
                st.session_state.event_data["event_subtype_id"].isin(
                    ["pressing", "presure", "counter_press", "recovery_press"]
                )
            )
            | (
                st.session_state.event_data["end_type"].isin(
                    [
                        "indirect_disruption",
                        "indirect_regain",
                        "direct_regain",
                        "direct_disruption",
                        "possession_loss",
                        "foul_committed",
                        "clearance",
                    ]
                )
            )
        )
    ]
    player_pressing_event = pressing_event[
        pressing_event["player_id"] == float(player_id)
    ]

    player_action = st.session_state.event_data[
        st.session_state.event_data["player_id"] == float(player_id)
    ]

    success_DA = player_pressing_event[
        player_pressing_event["end_type"].isin(
            [
                "indirect_disruption",
                "indirect_regain",
                "direct_regain",
                "direct_disruption",
                "possession_loss",
                "foul_committed",
                "clearance",
            ]
        )
    ]

    avg_pressing = (
        0.0
        if len(pressing_event) == 0
        else round(len(player_pressing_event) / len(pressing_event) * 25, 2)
    )
    defensive_volume = (
        0.0
        if len(player_action) == 0
        else round(len(player_pressing_event) / len(player_action) * 25, 2)
    )

    return {
        "avg_Pressing_actions": avg_pressing,
        "Defensive_Action_volume": defensive_volume,
        "Success_DA": success_DA.shape[0],
    }


def plot_radar(
    metrics: List[str], low: List[float], high: List[float], values: List[float]
) -> None:
    """Generates and displays a radar chart comparing player metrics against benchmarks.

    Creates a radar (spider) plot visualization showing player performance across multiple
    metrics. Each metric is normalized between low and high bounds, displayed with green fill
    and outlined vertices. The chart includes range labels, parameter labels, and spoke lines.

    Args:
        metrics (List[str]): List of metric names to display on the radar chart.
        low (List[float]): List of minimum values (lower bound) for each metric.
        high (List[float]): List of maximum values (upper bound) for each metric.
        values (List[float]): List of actual player values for each metric to display.

    Returns:
        None: Displays the chart using st.pyplot().
    """
    radar = Radar(
        metrics,
        low,
        high,
        round_int=[False] * len(metrics),
        num_rings=5,
        ring_width=1,
        center_circle_radius=1,
    )

    fig, ax = radar.setup_axis()
    rings_inner = radar.draw_circles(
        ax=ax, facecolor="#e4e8e9", edgecolor="#e1e6e7", alpha=0.4
    )
    radar_output = radar.draw_radar(
        values,
        ax=ax,
        kwargs_radar={"facecolor": "#0e8d34", "alpha": 0.7},
        kwargs_rings={"facecolor": "#0e8d34"},
    )
    radar_poly, rings_outer, vertices = radar_output

    radar.draw_range_labels(ax=ax, fontsize=15)
    radar.draw_param_labels(ax=ax, fontsize=15)
    radar.spoke(ax=ax, color="#a6a4a1", linestyle="--", zorder=2)

    ax.scatter(
        vertices[:, 0],
        vertices[:, 1],
        c="#047426",
        edgecolors="#055216",
        marker="o",
        s=150,
        zorder=2,
    )

    # Close polygon and plot border
    polygon = np.vstack([vertices, vertices[0]])
    ax.plot(polygon[:, 0], polygon[:, 1], color="#055216", linewidth=3, zorder=3)

    st.pyplot(fig)


# variables
SIMPLE_LOGO = "./src/images/logo.png"  # logo when no side bar
LOGO_WITH_TEXT = "./src/images/logo_with_text.png"  # central logo and sidebar logo
AVAILABLE_MATCHES_IDS = [
    1886347,
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
    "Total passes[succeed pass]",
    "Pass accuracy percentage",
    "Clearances",
    "Fouls committed",
    "Direct disruptions",
    "Direct regains",
    "Possession losses",
]