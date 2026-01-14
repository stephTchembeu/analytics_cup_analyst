from typing import List, Optional, Tuple
import pandas as pd
from src.utils.preset import (
    covered_distance,
    expected_goals,
    expected_threat,
    get_players_name,
    max_speed,
    shots_,
    shots_on_target,
    sub_title,
)
import streamlit as st


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
        "Expected Goals (xG)",
        "Expected Threat (xT)",
        "Shots on Target",
        "Shots Total",
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
        expected_goals(player, match_data),
        expected_threat(player, match_data),
        shots_on_target(player, match_data),
        shots_(player.player_id),
    ]
    return data




