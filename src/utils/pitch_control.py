"""
Pitch Control Module for FootMetricX
Calculates space control and influence zones for player positions
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from mplsoccer import Pitch
import streamlit as st
from scipy.ndimage import gaussian_filter
from kloppy.domain.models.tracking import TrackingDataset


def calculate_pitch_control(
    player_positions: dict,
    pitch_length: float = 105,
    pitch_width: float = 68,
    grid_size: int = 50,
    sigma: float = 5.0
) -> tuple:
    """
    Calculate pitch control using Voronoi-based influence zones.
    
    Args:
        player_positions: Dict with 'home' and 'away' keys, each containing 
                         list of (x, y) tuples
        pitch_length: Length of the pitch in meters
        pitch_width: Width of the pitch in meters
        grid_size: Resolution of the control grid
        sigma: Smoothing parameter for Gaussian filter
    
    Returns:
        tuple: (control_grid, x_grid, y_grid) where control_grid contains 
               values from -1 (away control) to 1 (home control)
    """
    # Create grid
    x = np.linspace(-pitch_length/2, pitch_length/2, grid_size)
    y = np.linspace(-pitch_width/2, pitch_width/2, grid_size)
    xx, yy = np.meshgrid(x, y)
    
    # Initialize control surfaces
    home_control = np.zeros((grid_size, grid_size))
    away_control = np.zeros((grid_size, grid_size))
    
    # Calculate influence for home team
    for px, py in player_positions.get('home', []):
        # Distance from each grid point to player
        dist = np.sqrt((xx - px)**2 + (yy - py)**2)
        # Influence decreases with distance (inverse relationship)
        influence = 1 / (1 + (dist / 10)**2)
        home_control += influence
    
    # Calculate influence for away team
    for px, py in player_positions.get('away', []):
        dist = np.sqrt((xx - px)**2 + (yy - py)**2)
        influence = 1 / (1 + (dist / 10)**2)
        away_control += influence
    
    # Smooth the control surfaces
    home_control = gaussian_filter(home_control, sigma=sigma)
    away_control = gaussian_filter(away_control, sigma=sigma)
    
    # Combine into single control grid (-1 to 1)
    total_control = home_control + away_control
    control_grid = np.where(
        total_control > 0,
        (home_control - away_control) / (total_control + 1e-10),
        0
    )
    
    return control_grid, x, y


def get_frame_positions(
    tracking_data: TrackingDataset,
    frame_idx: int,
    home_team_id: str,
    away_team_id: str
) -> dict:
    """
    Extract player positions from a specific frame of tracking data.
    
    Args:
        tracking_data: Kloppy TrackingDataset
        frame_idx: Frame index to extract
        home_team_id: Team ID for home team
        away_team_id: Team ID for away team
    
    Returns:
        dict: {'home': [(x1, y1), ...], 'away': [(x2, y2), ...]}
    """
    df = tracking_data.to_df(engine="pandas")
    
    # Get frame data
    frame_data = df.iloc[frame_idx]
    
    positions = {'home': [], 'away': []}
    
    # Extract home team positions
    home_team = [team for team in tracking_data.metadata.teams if team.team_id == home_team_id][0]
    for player in home_team.players:
        x_col = f"{player.player_id}_x"
        y_col = f"{player.player_id}_y"
        
        if x_col in frame_data and y_col in frame_data:
            x, y = frame_data[x_col], frame_data[y_col]
            if not pd.isna(x) and not pd.isna(y):
                positions['home'].append((x, y))
    
    # Extract away team positions
    away_team = [team for team in tracking_data.metadata.teams if team.team_id == away_team_id][0]
    for player in away_team.players:
        x_col = f"{player.player_id}_x"
        y_col = f"{player.player_id}_y"
        
        if x_col in frame_data and y_col in frame_data:
            x, y = frame_data[x_col], frame_data[y_col]
            if not pd.isna(x) and not pd.isna(y):
                positions['away'].append((x, y))
    
    return positions


def plot_pitch_control(
    control_grid: np.ndarray,
    x_grid: np.ndarray,
    y_grid: np.ndarray,
    player_positions: dict,
    pitch_length: float = 105,
    pitch_width: float = 68,
    title: str = "Pitch Control Map"
) -> plt.Figure:
    """
    Visualize pitch control with player positions.
    
    Args:
        control_grid: Grid of control values (-1 to 1)
        x_grid: X coordinates of grid
        y_grid: Y coordinates of grid
        player_positions: Dict with 'home' and 'away' player positions
        pitch_length: Length of the pitch
        pitch_width: Width of the pitch
        title: Plot title
    
    Returns:
        matplotlib Figure object
    """
    pitch = Pitch(
        pitch_type='custom',
        pitch_length=pitch_length,
        pitch_width=pitch_width,
        line_zorder=2,
        line_color='white',
        pitch_color='#22543d'
    )
    
    fig, ax = pitch.draw(figsize=(12, 8))
    
    # Plot control heatmap
    im = ax.contourf(
        x_grid,
        y_grid,
        control_grid,
        levels=20,
        cmap='RdBu',
        alpha=0.6,
        vmin=-1,
        vmax=1
    )
    
    # Add colorbar
    cbar = plt.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
    cbar.set_label('Team Control (Blue=Home, Red=Away)', rotation=270, labelpad=20)
    
    # Plot home team players
    home_x = [pos[0] for pos in player_positions.get('home', [])]
    home_y = [pos[1] for pos in player_positions.get('home', [])]
    if home_x and home_y:
        ax.scatter(
            home_x, home_y,
            c='blue',
            s=300,
            edgecolors='white',
            linewidth=2,
            zorder=3,
            alpha=0.9,
            label='Home Team'
        )
    
    # Plot away team players
    away_x = [pos[0] for pos in player_positions.get('away', [])]
    away_y = [pos[1] for pos in player_positions.get('away', [])]
    if away_x and away_y:
        ax.scatter(
            away_x, away_y,
            c='red',
            s=300,
            edgecolors='white',
            linewidth=2,
            zorder=3,
            alpha=0.9,
            label='Away Team'
        )
    
    ax.legend(loc='upper center', bbox_to_anchor=(0.5, -0.05), ncol=2)
    ax.set_title(title, fontsize=16, fontweight='bold', pad=20)
    
    return fig


def calculate_space_control_metrics(
    control_grid: np.ndarray,
    pitch_length: float = 105,
    pitch_width: float = 68
) -> dict:
    """
    Calculate metrics from pitch control grid.
    
    Args:
        control_grid: Grid of control values (-1 to 1)
        pitch_length: Length of the pitch
        pitch_width: Width of the pitch
    
    Returns:
        dict: Metrics including control percentages and field zones
    """
    # Total control percentages
    home_control_pct = np.sum(control_grid > 0) / control_grid.size * 100
    away_control_pct = np.sum(control_grid < 0) / control_grid.size * 100
    neutral_pct = np.sum(control_grid == 0) / control_grid.size * 100
    
    # Divide pitch into thirds
    third_size = control_grid.shape[1] // 3
    
    defensive_third = control_grid[:, :third_size]
    middle_third = control_grid[:, third_size:2*third_size]
    attacking_third = control_grid[:, 2*third_size:]
    
    metrics = {
        'home_control_total': round(home_control_pct, 1),
        'away_control_total': round(away_control_pct, 1),
        'neutral_control': round(neutral_pct, 1),
        'home_defensive_third': round(np.sum(defensive_third > 0) / defensive_third.size * 100, 1),
        'home_middle_third': round(np.sum(middle_third > 0) / middle_third.size * 100, 1),
        'home_attacking_third': round(np.sum(attacking_third > 0) / attacking_third.size * 100, 1),
        'away_defensive_third': round(np.sum(attacking_third < 0) / attacking_third.size * 100, 1),
        'away_middle_third': round(np.sum(middle_third < 0) / middle_third.size * 100, 1),
        'away_attacking_third': round(np.sum(defensive_third < 0) / defensive_third.size * 100, 1),
    }
    
    return metrics


def analyze_space_creation(
    original_positions: dict,
    modified_positions: dict,
    pitch_length: float = 105,
    pitch_width: float = 68
) -> dict:
    """
    Analyze the impact of moving a player on space control.
    
    Args:
        original_positions: Original player positions
        modified_positions: Modified player positions (after moving a player)
        pitch_length: Length of the pitch
        pitch_width: Width of the pitch
    
    Returns:
        dict: Analysis results including control changes
    """
    # Calculate original control
    orig_control, x, y = calculate_pitch_control(
        original_positions,
        pitch_length,
        pitch_width
    )
    
    # Calculate modified control
    mod_control, _, _ = calculate_pitch_control(
        modified_positions,
        pitch_length,
        pitch_width
    )
    
    # Calculate difference
    control_diff = mod_control - orig_control
    
    # Metrics
    orig_metrics = calculate_space_control_metrics(orig_control)
    mod_metrics = calculate_space_control_metrics(mod_control)
    
    # Calculate changes
    control_change = mod_metrics['home_control_total'] - orig_metrics['home_control_total']
    
    analysis = {
        'original_metrics': orig_metrics,
        'modified_metrics': mod_metrics,
        'control_change': round(control_change, 2),
        'control_diff_grid': control_diff,
        'space_gained': np.sum(control_diff > 0.1),
        'space_lost': np.sum(control_diff < -0.1),
        'x_grid': x,
        'y_grid': y
    }
    
    return analysis


def plot_space_creation_impact(
    analysis: dict,
    original_positions: dict,
    modified_positions: dict,
    moved_player_idx: int = 0,
    pitch_length: float = 105,
    pitch_width: float = 68
) -> plt.Figure:
    """
    Visualize the impact of player movement on space control.
    
    Args:
        analysis: Output from analyze_space_creation()
        original_positions: Original player positions
        modified_positions: Modified player positions
        moved_player_idx: Index of the moved player
        pitch_length: Length of the pitch
        pitch_width: Width of the pitch
    
    Returns:
        matplotlib Figure object
    """
    pitch = Pitch(
        pitch_type='custom',
        pitch_length=pitch_length,
        pitch_width=pitch_width,
        line_zorder=2,
        line_color='white',
        pitch_color='#22543d'
    )
    
    fig, ax = pitch.draw(figsize=(12, 8))
    
    # Plot control difference
    control_diff = analysis['control_diff_grid']
    x_grid = analysis['x_grid']
    y_grid = analysis['y_grid']
    
    im = ax.contourf(
        x_grid,
        y_grid,
        control_diff,
        levels=20,
        cmap='RdYlGn',
        alpha=0.7,
        vmin=-0.5,
        vmax=0.5
    )
    
    cbar = plt.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
    cbar.set_label('Control Change (Green=Gained, Red=Lost)', rotation=270, labelpad=20)
    
    # Plot original positions (semi-transparent)
    home_orig = original_positions.get('home', [])
    away_orig = original_positions.get('away', [])
    
    if home_orig:
        ax.scatter(
            [pos[0] for pos in home_orig],
            [pos[1] for pos in home_orig],
            c='blue',
            s=200,
            edgecolors='white',
            linewidth=1,
            alpha=0.3,
            zorder=2
        )
    
    if away_orig:
        ax.scatter(
            [pos[0] for pos in away_orig],
            [pos[1] for pos in away_orig],
            c='red',
            s=200,
            edgecolors='white',
            linewidth=1,
            alpha=0.3,
            zorder=2
        )
    
    # Plot new positions (solid)
    home_new = modified_positions.get('home', [])
    away_new = modified_positions.get('away', [])
    
    if home_new:
        ax.scatter(
            [pos[0] for pos in home_new],
            [pos[1] for pos in home_new],
            c='blue',
            s=300,
            edgecolors='yellow',
            linewidth=3,
            alpha=0.9,
            zorder=3
        )
    
    if away_new:
        ax.scatter(
            [pos[0] for pos in away_new],
            [pos[1] for pos in away_new],
            c='red',
            s=300,
            edgecolors='yellow',
            linewidth=3,
            alpha=0.9,
            zorder=3
        )
    
    # Draw arrow showing movement
    if moved_player_idx < len(home_orig):
        orig_pos = home_orig[moved_player_idx]
        new_pos = home_new[moved_player_idx]
        ax.annotate(
            '',
            xy=new_pos,
            xytext=orig_pos,
            arrowprops=dict(
                arrowstyle='->',
                lw=3,
                color='yellow',
                alpha=0.8
            ),
            zorder=4
        )
    
    control_change = analysis['control_change']
    ax.set_title(
        f'Space Control Impact: {control_change:+.1f}% control change',
        fontsize=16,
        fontweight='bold',
        pad=20
    )
    
    return fig