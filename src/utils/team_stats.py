"""Team Statistics Functions

Functions for calculating team-level statistics including shots, passes, possession,
clearances, fouls, and other defensive actions.
"""

import streamlit as st
import pandas as pd
from typing import Tuple
from kloppy.domain.models.common import Team

from .preset import safe_get_event_data


def shots(team: Team) -> Tuple[int, int]:
    """Calculates total shots and shots on target for a team.

    Filters event data for shot events and determines on-target shots based on
    goal outcomes.

    Args:
        team (Team): Team object with team_id attribute.

    Returns:
        Tuple[int, int]: Tuple of (total_shots, shots_on_target).
    """
    shots_df = st.session_state.event_data[
        st.session_state.event_data["end_type"].str.lower() == "shot"
    ].copy()
    shots_df["is_on_target"] = (shots_df["lead_to_goal"] == 1) & (
        shots_df["game_interruption_after"].isin(["goal_for", "corner_for"])
    )
    shots_df["is_on_target"] = shots_df["is_on_target"].astype("boolean")
    team_shots = shots_df[shots_df["team_id"] == team.team_id]
    total = len(team_shots)
    on_target = team_shots["is_on_target"].sum()
    return (total, on_target)


def passess(team: Team) -> Tuple[int, int]:
    """Calculates total passes and successful passes for a team.

    Filters event data for pass events and counts successful passes.

    Args:
        team (Team): Team object with team_id attribute.

    Returns:
        Tuple[int, int]: Tuple of (total_passes, successful_passes).
    """
    try:
        # Validate inputs
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
    try:
        if not isinstance(team, Team):
            raise TypeError(f"Expected Team object, got {type(team).__name__}")
        
        passes_data = passess(team)
        if not isinstance(passes_data, tuple) or len(passes_data) != 2:
            raise TypeError(f"passess() should return tuple of 2 integers, got {type(passes_data).__name__}")
        
        if passes_data[0] == 0:
            result = 0
        else:
            result = int(passes_data[1] * 100 / passes_data[0])
    except (ValueError, TypeError) as e:
        st.warning(f"Error calculating pass accuracy: {str(e)}")
        result = 0
    else:
        return result
    
    return result


def possession(team: Team) -> int:
    """Calculates possession percentage for a team based on event data.

    Calculates possession by summing the duration of events performed by each team.
    If duration data is unavailable, falls back to event count method.

    Args:
        team (Team): Team object with team_id attribute.

    Returns:
        int: Possession percentage (0-100).
    """
    try:
        if not isinstance(team, Team):
            raise TypeError(f"Expected Team object, got {type(team).__name__}")
        
        if not hasattr(team, 'team_id'):
            raise AttributeError("Team object missing 'team_id' attribute")
        
        event_data = safe_get_event_data()
        
        if 'team_id' not in event_data.columns:
            raise KeyError("Missing required column: 'team_id'")
        
        # Try to use duration-based calculation if duration column exists
        if 'duration' in event_data.columns:
            # Calculate possession based on total duration of events
            team_events = event_data[event_data["team_id"] == team.team_id]
            team_duration = team_events['duration'].sum()
            total_duration = event_data['duration'].sum()
            
            if total_duration == 0:
                result = 50
            else:
                result = int((team_duration / total_duration) * 100)
        else:
            # Fallback to event count method if duration not available
            team_events = event_data[event_data["team_id"] == team.team_id]
            total_events = len(event_data)
            
            if total_events == 0:
                result = 50
            else:
                result = int((len(team_events) / total_events) * 100)
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
        if not isinstance(team, Team):
            raise TypeError(f"Expected Team object, got {type(team).__name__}")
        
        if not hasattr(team, 'team_id'):
            raise AttributeError("Team object missing 'team_id' attribute")
        
        event_data = safe_get_event_data()
        
        required_cols = ['end_type', 'team_id']
        missing_cols = [col for col in required_cols if col not in event_data.columns]
        if missing_cols:
            raise KeyError(f"Missing required columns: {', '.join(missing_cols)}")
        
        clearances_df = event_data[
            event_data["end_type"].str.lower() == "clearance"
        ]
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
        if not isinstance(team, Team):
            raise TypeError(f"Expected Team object, got {type(team).__name__}")
        
        if not hasattr(team, 'team_id'):
            raise AttributeError("Team object missing 'team_id' attribute")
        
        event_data = safe_get_event_data()
        
        required_cols = ['end_type', 'team_id']
        missing_cols = [col for col in required_cols if col not in event_data.columns]
        if missing_cols:
            raise KeyError(f"Missing required columns: {', '.join(missing_cols)}")
        
        fouls_df = event_data[
            event_data["end_type"].str.lower() == "foul_committed"
        ]
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
        if not isinstance(team, Team):
            raise TypeError(f"Expected Team object, got {type(team).__name__}")
        
        if not hasattr(team, 'team_id'):
            raise AttributeError("Team object missing 'team_id' attribute")
        
        event_data = safe_get_event_data()
        
        required_cols = ['end_type', 'team_id']
        missing_cols = [col for col in required_cols if col not in event_data.columns]
        if missing_cols:
            raise KeyError(f"Missing required columns: {', '.join(missing_cols)}")
        
        disruptions_df = event_data[
            event_data["end_type"].str.lower() == "direct_disruption"
        ]
        team_disruptions = disruptions_df[disruptions_df["team_id"] == team.team_id]
        result = len(team_disruptions)
    except (ValueError, TypeError, AttributeError, KeyError) as e:
        st.warning(f"Error calculating disruptions: {str(e)}")
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
        if not isinstance(team, Team):
            raise TypeError(f"Expected Team object, got {type(team).__name__}")
        
        if not hasattr(team, 'team_id'):
            raise AttributeError("Team object missing 'team_id' attribute")
        
        event_data = safe_get_event_data()
        
        required_cols = ['end_type', 'team_id']
        missing_cols = [col for col in required_cols if col not in event_data.columns]
        if missing_cols:
            raise KeyError(f"Missing required columns: {', '.join(missing_cols)}")
        
        regains_df = event_data[
            event_data["end_type"].str.lower() == "direct_regain"
        ]
        team_regains = regains_df[regains_df["team_id"] == team.team_id]
        result = len(team_regains)
    except (ValueError, TypeError, AttributeError, KeyError) as e:
        st.warning(f"Error calculating regains: {str(e)}")
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
        if not isinstance(team, Team):
            raise TypeError(f"Expected Team object, got {type(team).__name__}")
        
        if not hasattr(team, 'team_id'):
            raise AttributeError("Team object missing 'team_id' attribute")
        
        event_data = safe_get_event_data()
        
        required_cols = ['end_type', 'team_id']
        missing_cols = [col for col in required_cols if col not in event_data.columns]
        if missing_cols:
            raise KeyError(f"Missing required columns: {', '.join(missing_cols)}")
        
        losses_df = event_data[
            event_data["end_type"].str.lower() == "possession_loss"
        ]
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
