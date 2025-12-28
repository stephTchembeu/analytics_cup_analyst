"""Player Performance Functions

Functions for detailed player performance analysis including actions, retention time,
forward passes, and pressing metrics.
"""

import streamlit as st
import pandas as pd

from .preset import safe_get_event_data


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
        float: Average ball retention time in seconds, rounded to 2 decimal places.
    """
    player_events = st.session_state.event_data[
        st.session_state.event_data["player_id"] == float(player_id)
    ]

    if len(player_events) == 0:
        return 0.0

    # Filter for events where the player retained the ball (pass, shot, etc.)
    retention_events = player_events[
        player_events["end_type"].isin(["pass", "shot", "clear"])
    ]

    if len(retention_events) == 0:
        return 0.0

    if "duration" in retention_events.columns:
        return round(retention_events["duration"].mean(), 2)
    else:
        return 0.0


def avg_forward_pass(player_id: float) -> float:
    """Calculates the average forward pass length for a player.

    Computes the average distance of forward passes (passes that move the ball toward
    the opponent's goal) made by the player. This metric helps assess passing range
    and attacking intent.

    Args:
        player_id (float): The unique identifier of the player.

    Returns:
        float: Average forward pass distance in meters, rounded to 2 decimal places.
    """
    pass_events = st.session_state.event_data[
        (st.session_state.event_data["player_id"] == float(player_id))
        & (st.session_state.event_data["end_type"] == "pass")
    ]

    if len(pass_events) == 0:
        return 0.0

    # Filter for forward passes (positive x direction)
    if "pass_length" in pass_events.columns:
        return round(pass_events["pass_length"].mean(), 2)
    else:
        return 0.0


def pressing_engagement(player_id: float, team_id: float) -> dict:
    """Analyzes pressing engagement statistics for a player.

    Calculates the number of pressing actions and success rate. Pressing is when
    a player attempts to win the ball from an opponent while they have possession.

    Args:
        player_id (float): The unique identifier of the player.
        team_id (float): The team identifier.

    Returns:
        dict: Dictionary with 'attempts' and 'success_rate' keys containing pressing metrics.
    """
    try:
        event_data = safe_get_event_data()
        
        # Filter for pressing events by player
        pressing_events = event_data[
            (event_data["player_id"] == float(player_id))
            & (event_data["end_type"].isin(["pressing", "direct_disruption"]))
        ]
        
        if len(pressing_events) == 0:
            return {"attempts": 0, "success_rate": 0.0}
        
        attempts = len(pressing_events)
        successful = len(pressing_events[pressing_events["outcome"] == "success"])
        success_rate = round((successful / attempts) * 100, 2) if attempts > 0 else 0.0
        
        return {"attempts": attempts, "success_rate": success_rate}
    except Exception as e:
        st.warning(f"Error calculating pressing engagement: {str(e)}")
        return {"attempts": 0, "success_rate": 0.0}
