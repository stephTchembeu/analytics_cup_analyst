"""Player Profiling Functions

Functions for player-level analysis including heatmaps, pass maps, speed calculations,
shots, and expected metrics.
"""

import streamlit as st
import pandas as pd
import numpy as np
from typing import List
from mplsoccer import Pitch
from kloppy.domain.models.tracking import TrackingDataset

from .preset import safe_get_event_data


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
    try:
        if not isinstance(match_data, TrackingDataset):
            raise TypeError(f"Expected TrackingDataset, got {type(match_data).__name__}")
        
        if not isinstance(xs, pd.Series) or not isinstance(ys, pd.Series):
            raise TypeError("xs and ys must be pandas Series")
        
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
    except (ValueError, TypeError, AttributeError) as e:
        st.warning(f"Error generating heatmap: {str(e)}")


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
    try:
        if not isinstance(match_data, TrackingDataset):
            raise TypeError(f"Expected TrackingDataset, got {type(match_data).__name__}")
        
        required_series = [xs, ys, xs_end, ys_end, pass_outcome]
        if not all(isinstance(s, pd.Series) for s in required_series):
            raise TypeError("All coordinate and outcome parameters must be pandas Series")
        
        if not hasattr(match_data.metadata, 'coordinate_system'):
            raise AttributeError("Match data missing 'coordinate_system' attribute")
        
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
    except (ValueError, TypeError, AttributeError) as e:
        st.warning(f"Error generating pass map: {str(e)}")


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
    try:
        if not hasattr(player, 'player_id'):
            raise AttributeError("Player object missing 'player_id' attribute")
        
        if not isinstance(tracking_df, TrackingDataset):
            raise TypeError(f"Expected TrackingDataset, got {type(tracking_df).__name__}")
        
        player_id = player.player_id
        x_col = f"{player_id}_x"
        y_col = f"{player_id}_y"

        # Convert tracking dataset to pandas
        df = tracking_df.to_df(engine="pandas")[[x_col, y_col]].dropna(
            subset=[x_col, y_col]
        )

        if df.empty:
            result = 0.0
        else:
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
            result = round(max_speed_value, 2)
    except (ValueError, TypeError, AttributeError, KeyError) as e:
        st.warning(f"Error calculating max speed: {str(e)}")
        result = 0.0
    else:
        return result
    
    return result


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
    try:
        if not hasattr(player, 'player_id'):
            raise AttributeError("Player object missing 'player_id' attribute")
        
        if not isinstance(match_data, TrackingDataset):
            raise TypeError(f"Expected TrackingDataset, got {type(match_data).__name__}")
        
        event_data = safe_get_event_data()
        
        required_cols = ['end_type', 'player_id', 'lead_to_goal', 'game_interruption_after']
        missing_cols = [col for col in required_cols if col not in event_data.columns]
        if missing_cols:
            raise KeyError(f"Missing required columns: {', '.join(missing_cols)}")
        
        shots_df = event_data[
            (event_data["end_type"].str.lower() == "shot")
            & (event_data["player_id"] == int(player.player_id))
        ].copy()

        if shots_df.empty:
            result = 0
        else:
            shots_df["is_on_target"] = (shots_df["lead_to_goal"] == 1) & (
                shots_df["game_interruption_after"].isin(["goal_for", "corner_for"])
            )
            on_target = shots_df["is_on_target"].sum()
            result = int(on_target)
    except (ValueError, TypeError, AttributeError, KeyError) as e:
        st.warning(f"Error calculating shots on target: {str(e)}")
        result = 0
    else:
        return result
    
    return result


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
    try:
        if not hasattr(player, 'player_id'):
            raise AttributeError("Player object missing 'player_id' attribute")
        
        if not isinstance(match_data, TrackingDataset):
            raise TypeError(f"Expected TrackingDataset, got {type(match_data).__name__}")
        
        event_data = safe_get_event_data()
        
        required_cols = ['end_type', 'player_id']
        missing_cols = [col for col in required_cols if col not in event_data.columns]
        if missing_cols:
            raise KeyError(f"Missing required columns: {', '.join(missing_cols)}")
        
        shots_df = event_data[
            (event_data["end_type"].str.lower() == "shot")
            & (event_data["player_id"] == int(player.player_id))
        ]

        if shots_df.empty:
            result = 0.0
        else:
            # If xG column exists, sum it; otherwise estimate 0.15 per shot
            if "xG" in shots_df.columns:
                result = round(shots_df["xG"].sum(), 2)
            else:
                result = round(len(shots_df) * 0.15, 2)
    except (ValueError, TypeError, AttributeError, KeyError) as e:
        st.warning(f"Error calculating expected goals: {str(e)}")
        result = 0.0
    else:
        return result
    
    return result


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
    try:
        if not hasattr(player, 'player_id'):
            raise AttributeError("Player object missing 'player_id' attribute")
        
        if not isinstance(match_data, TrackingDataset):
            raise TypeError(f"Expected TrackingDataset, got {type(match_data).__name__}")
        
        event_data = safe_get_event_data()
        
        required_cols = ['end_type', 'player_id', 'pass_outcome']
        missing_cols = [col for col in required_cols if col not in event_data.columns]
        if missing_cols:
            raise KeyError(f"Missing required columns: {', '.join(missing_cols)}")
        
        pass_df = event_data[
            (event_data["end_type"].str.lower() == "pass")
            & (event_data["player_id"] == int(player.player_id))
            & (event_data["pass_outcome"] == "successful")
        ]

        if pass_df.empty:
            result = 0.0
        else:
            # If xT column exists, sum it; otherwise estimate 0.02 per successful pass
            if "xT" in pass_df.columns:
                result = round(pass_df["xT"].sum(), 2)
            else:
                result = round(len(pass_df) * 0.02, 2)
    except (ValueError, TypeError, AttributeError, KeyError) as e:
        st.warning(f"Error calculating expected threat: {str(e)}")
        result = 0.0
    else:
        return result
    
    return result
