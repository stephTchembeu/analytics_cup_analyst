from typing import List, Dict
import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from kloppy.domain import TrackingDataset, Player, Team


def select_team(home: Team, away: Team) -> Team:
    """
    Display team selection interface and return the selected team object.

    Creates a Streamlit selectbox for choosing between home and away teams.

    Args:
        home: The home Team object from kloppy containing team information and players
        away: The away Team object from kloppy containing team information and players

    Returns:
        Team: The selected kloppy Team object (either home or away)
    """
    selected_team_name = st.selectbox(
        "Choose a team.",
        options=[home.name, away.name],
        key="team_select_profiling",
    )
    team = home if selected_team_name == home.name else away
    return team

def get_player(players: List[str], team: Team) -> Player:
    """
    Display player selection interface and return the selected player object.

    Creates a Streamlit selectbox for choosing a player from the provided list,
    then retrieves and returns the corresponding Player object from the team.

    Args:
        players: List of player names (potentially with positions appended)
        team: kloppy Team object containing a list of Player objects

    Returns:
        Player: The selected kloppy Player object from the team's roster
    """
    selected_player_name = st.selectbox(
        "Choose a player.",
        options=players,
        key="player_select_profiling",
    )
    name_parts = selected_player_name.rsplit(' ', 1)
    player_name_only = name_parts[0] if len(name_parts) > 1 else selected_player_name
    
    selected_player = [
        player
        for player in team.players
        if player.full_name == player_name_only
    ][0]
    return selected_player

def get_players_name_(team_name: str, match_data: TrackingDataset) -> Dict[str, List]:
    """
    Retrieve all player names and IDs for a specific team from match data.

    Args:
        team_name: Name of the team to retrieve players for
        match_data: SkillCorner TrackingDataset object containing match metadata

    Returns:
        Dict[str, List]: Dictionary with two keys:
            - 'names': List of player full names (List[str])
            - 'ids': List of corresponding player IDs (List[int|str])
        Returns empty dict if team not found
    """
    for team in match_data.metadata.teams:
        if team.name == team_name:
            return {
                "names": [player.full_name for player in team.players],
                "ids": [player.player_id for player in team.players],
            }
    return {}

def get_position(player_id: int | str, event_data: pd.DataFrame) -> str:
    """
    Determine a player's position from event data.

    Filters events for the specified player and extracts their position,
    filtering out invalid values like 'none', 'unknown', or NaN.

    Args:
        player_id: Unique identifier for the player
        event_data: DataFrame containing event data with 'player_id' and
                   'player_position' columns

    Returns:
        str: Player's position or "Unknown" if position cannot be determined
    """
    player_events = event_data[event_data["player_id"] == float(player_id)]

    if player_events.empty:
        return "Unknown"

    # Drop missing/invalid positions
    positions = player_events["player_position"].dropna()
    positions = positions[~positions.str.lower().isin(["none", "unknown", "nan"])]

    if positions.empty:
        return "Unknown"

    return positions.iloc[0]

def get_player_name_from_event(player_id: int | str, event_data: pd.DataFrame) -> str:
    """
    Determine a player's position from event data.

    Filters events for the specified player and extracts their position,
    filtering out invalid values like 'none', 'unknown', or NaN.

    Args:
        player_id: Unique identifier for the player
        event_data: DataFrame containing event data with 'player_id' and
                   'player_position' columns

    Returns:
        str: Player's name or "Unknown" if name cannot be determined
    """
    player_events = event_data[event_data["player_id"] == float(player_id)]

    if player_events.empty:
        return "Unknown"

    # Drop missing/invalid positions
    positions = player_events["player_name"].dropna()
    positions = positions[~positions.str.lower().isin(["none", "unknown", "nan"])]

    if positions.empty:
        return "Unknown"

    return positions.iloc[0]

def add_position(
    players_name: List[str], players_id: List[int | str], event_data: pd.DataFrame
) -> List[str]:
    """
    Append position information to player names.

    Creates a list of formatted strings combining player names with their positions
    for display in UI elements like dropdowns.

    Args:
        players_name: List of player full names
        players_id: List of corresponding player IDs
        event_data: DataFrame containing event data with position information

    Returns:
        List[str]: List of formatted strings in the format "Player Name Position"
    """
    result = []
    for name, pid in zip(players_name, players_id):
        position = get_position(pid, event_data)
        result.append(f"{name} {position}")
    return result

def show_player_name_pos(player: Player, event_data: pd.DataFrame) -> None:
    """
    Display player name and position in a formatted HTML div.

    Retrieves the player's position and renders it alongside their name
    using Streamlit's markdown with custom HTML/CSS.

    Args:
        player: kloppy Player object containing player_id and full_name attributes
        event_data: DataFrame containing event data with position information

    Returns:
        None
    """
    choosed_player_position = get_position(player.player_id, event_data)
    st.markdown(
        f"""
        <div class="player">
            <p class="name">{player.full_name}</p>
            <p class="position">{choosed_player_position}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

def get_events(
    target_player: Player, event_type: str, event_data: pd.DataFrame
) -> pd.DataFrame:
    """
    Filter events for a specific player and event type.

    Args:
        target_player: kloppy Player object containing player_id attribute
        event_type: Type of event to filter (e.g., 'shot', 'pass', 'tackle')
        event_data: DataFrame containing all event data with 'end_type' and
                   'player_id' columns

    Returns:
        pd.DataFrame: Filtered DataFrame containing only events matching the
                     specified player and event type
    """
    events = event_data[
        (event_data["end_type"] == event_type)
        & (event_data["player_id"] == int(target_player.player_id))
    ]
    return events

def plot_retention(player_events: pd.DataFrame, player_name: str) -> None:
    """
    Create and display a bar chart of average ball retention durations per match minute.

    Args:
        player_events: DataFrame containing all events for the player with columns:
                      'event_id', 'duration', 'end_type', 'minute_start'
        player_name: Full name of the player for chart title

    Returns:
        None: Displays the chart directly in Streamlit
    """
    # Keep only events with duration > 0
    retention_events = player_events[player_events["duration"] > 0].copy()

    # Aggregate by minute_start
    retention_minute = (
        retention_events.groupby("minute_start")["duration"]
        .mean()
        .reset_index()
    )

    # Overall mean
    mean_retention = retention_events["duration"].mean() if len(retention_events) > 0 else 0

    # Plot
    fig = px.bar(
        retention_minute,
        x="minute_start",
        y="duration",
        labels={"minute_start": "Match Minute", "duration": "Avg Ball Retention (s)"},
        title=f"Ball Retention per Minute for {player_name}",
        color_discrete_sequence=["#0e8d34"]
    )

    # Mean line
    fig.add_trace(
        go.Scatter(
            x=retention_minute["minute_start"],
            y=[mean_retention] * len(retention_minute),
            mode="lines",
            line=dict(color="red", dash="dash"),
            name=f"Overall Mean: {mean_retention:.2f}s",
            hovertemplate="Mean: %{y:.2f}s<extra></extra>"
        )
    )

    st.plotly_chart(fig, use_container_width=True)
 
def plot_offensive_action(offensive_events: pd.DataFrame, player_name: str) -> None:
    """
    Create and display a bar chart of average offensive action durations per match minute.

    Args:
        offensive_events: DataFrame containing offensive events with columns:
                          'event_id', 'event_subtype', 'duration', 'end_type', 'minute_start'
        player_name: Full name of the player for chart title

    Returns:
        None: Displays the chart directly in Streamlit
    """
    # Keep only events with duration > 0
    offensive_events = offensive_events[offensive_events["duration"] > 0].copy()

    # Aggregate by minute
    offensive_minute = (
        offensive_events.groupby("minute_start")["duration"]
        .mean()
        .reset_index()
    )

    # Overall mean
    mean_offensive = offensive_events["duration"].mean() if len(offensive_events) > 0 else 0

    # Plot
    fig = px.bar(
        offensive_minute,
        x="minute_start",
        y="duration",
        labels={"minute_start": "Match Minute", "duration": "Avg Offensive Duration (s)"},
        title=f"Offensive Actions per Minute for {player_name}",
        color_discrete_sequence=["#217c23"]
    )

    # Mean line
    fig.add_trace(
        go.Scatter(
            x=offensive_minute["minute_start"],
            y=[mean_offensive] * len(offensive_minute),
            mode="lines",
            line=dict(color="red", dash="dash"),
            name=f"Overall Mean: {mean_offensive:.2f}s",
            hovertemplate="Mean: %{y:.2f}s<extra></extra>"
        )
    )

    st.plotly_chart(fig, use_container_width=True)

def plot_defensive_action(defensive_events: pd.DataFrame, player_name: str) -> None:
    """
    Create and display a bar chart of average defensive action durations per match minute.

    Args:
        defensive_events: DataFrame containing defensive events with columns:
                          'event_id', 'end_type', 'duration', 'event_subtype', 'minute_start'
        player_name: Full name of the player for chart title

    Returns:
        None: Displays the chart directly in Streamlit
    """
    # Keep only events with duration > 0
    defensive_events = defensive_events[defensive_events["duration"] > 0].copy()

    # Aggregate by minute
    defensive_minute = (
        defensive_events.groupby("minute_start")["duration"]
        .mean()
        .reset_index()
    )

    # Overall mean
    mean_defensive = defensive_events["duration"].mean() if len(defensive_events) > 0 else 0

    # Plot
    fig = px.bar(
        defensive_minute,
        x="minute_start",
        y="duration",
        labels={"minute_start": "Match Minute", "duration": "Avg Defensive Duration (s)"},
        title=f"Defensive Actions per Minute for {player_name}",
        color_discrete_sequence=["#052B72"]
    )

    # Mean line
    fig.add_trace(
        go.Scatter(
            x=defensive_minute["minute_start"],
            y=[mean_defensive] * len(defensive_minute),
            mode="lines",
            line=dict(color="red", dash="dash"),
            name=f"Overall Mean: {mean_defensive:.2f}s",
            hovertemplate="Mean: %{y:.2f}s<extra></extra>"
        )
    )

    st.plotly_chart(fig, use_container_width=True)
