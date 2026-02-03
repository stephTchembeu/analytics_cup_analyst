from typing import List, Optional, Tuple
import pandas as pd
from src.utils.preset import (
    covered_distance,
    expected_threat,
    get_players_name,
    max_speed,
    shots_,
    shots_on_target,
    sub_title,
)
import streamlit as st

def player_clearance(player_id,event_data) -> int:
    """Counts clearance events for a plaer.

    Args:
        player_id: int representing the player id.
        event_data: the event data
    Returns:
        int: Number of clearances made by the player.
    """
    try:
        required_cols = ['end_type', 'player_id']
        missing_cols = [col for col in required_cols if col not in event_data.columns]
        if missing_cols:
            raise KeyError(f"Missing required columns: {', '.join(missing_cols)}")
        
        clearances_df = event_data[event_data["end_type"].str.lower() == "clearance"]
        player_clearances = clearances_df[clearances_df["player_id"] == player_id]
        result = len(player_clearances)
    except (ValueError, TypeError, AttributeError, KeyError) as e:
        st.warning(f"Error calculating clearances: {str(e)}")
        result = 0
    else:
        return result
    
    return result

def press(
    player_id,
    type_press,
    event_data,
    match_data
):
    """
    Count pressing events in offensive or defensive third
    using SkillCorner coordinate system.
    Direction is evaluated per event.
    """
    pressure_event_type = [
        "pressing",
        "presure",  # keep only if present in raw data
        "recovery_press",
        "indirect_regain",
        "direct_regain",
        "counter_press"
    ]

    df = event_data[
        event_data["event_subtype"].isin(pressure_event_type) &
        (event_data["player_id"].astype(int) == int(player_id))
    ]

    L = match_data.metadata.coordinate_system.pitch_length
    third_limit = L / 6

    x = df["x_start"]
    direction = df["attacking_side"] 

    if type_press == "offensive":
        mask = (
            ((direction == "left_to_right") & (x >= third_limit)) |
            ((direction == "right_to_left") & (x <= -third_limit))
        )
        return mask.sum()

    elif type_press == "defensive":
        mask = (
            ((direction == "left_to_right") & (x <= -third_limit)) |
            ((direction == "right_to_left") & (x >= third_limit))
        )
        return mask.sum()

    return 0



def player_info(index: int, home, away, match_data) -> Optional[object]:
    """
    Display player selection interface and return the selected player object.

    Creates Streamlit UI elements for selecting a team and player, then returns
    the corresponding player object from the selected team's roster.

    Args:
        index: The player number (1 or 2) used for UI labeling and unique keys
        home: The home team object containing team name and players list
        away: The away team object containing team name and players list
        match_data: The match data object containing all match information

    Returns:
        Optional[object]: The selected player object if found, None otherwise
    """
    sub_title(f"Player {index}")
    team_name = st.selectbox(
        f"Choose team for Player {index}",
        options=[home.name, away.name],
        key=f"team{index}_performance",
    )
    selected_team = home if team_name == home.name else away
    players_list = get_players_name(team_name, match_data)
    selected_player_name = st.selectbox(
        f"Choose Player {index}",
        options=players_list,
        key=f"player{index}_performance",
    )
    player = next(
        (p for p in selected_team.players if p.full_name == selected_player_name), None
    )
    return player


def get_comparison_data(player1, player2, match_data) -> pd.DataFrame:
    """
    Generate a comparison DataFrame of performance metrics for two players.

    Creates a pandas DataFrame with predefined metrics comparing two players'
    performance statistics including distance, speed, passing, and goal metrics.

    Args:
        player1: First player object to compare
        player2: Second player object to compare
        match_data: The match data object containing all match information

    Returns:
        pd.DataFrame: DataFrame with three columns - 'Metrics', player1.name, and player2.name,
                     containing the comparison data for all metrics
    """
    metrics = [
        "Distance Covered (km)",
        "Max Speed (m/s)",
        "Total Passes",
        "Expected Threat (xT)",
        "Shots on Target",
        "Shots Total",
        "clearance",
        "offensive press",
        "deffensive press",
    ]
    player1_data = get_player_data(player1, st.session_state.event_data, match_data)
    player2_data = get_player_data(player2, st.session_state.event_data, match_data)
    return pd.DataFrame(
        {"Metrics": metrics, player1.name: player1_data, player2.name: player2_data}
    )


def get_player_data(player, event_data: pd.DataFrame, match_data) -> List[float]:
    """
    Extract and calculate performance metrics for a single player.

    Computes various performance statistics including distance covered, speed,
    passing, and shooting metrics from event and match data.

    Args:
        player: Player object containing player information and identifiers
        event_data: DataFrame containing all match events with columns including
                   'end_type', 'player_id', and 'duration'
        match_data: The match data object containing all match information

    Returns:
        List[float]: List of seven performance metrics in order:
                    [distance_covered, max_speed, total_passes, xG, xT,
                     shots_on_target, total_shots]
    """
    data = [
        covered_distance(player, match_data),
        max_speed(player, match_data),
        len(
            event_data[
                (event_data["end_type"] == "pass")
                & (event_data["player_id"] == int(player.player_id))
            ]
        ),
        expected_threat(player),
        shots_on_target(player, match_data),
        shots_(player.player_id),
        player_clearance(player.player_id,event_data),
        press(player.player_id,"offensive",event_data,match_data),
        press(player.player_id,"defensive",event_data,match_data),
    ]
    return data




