"""Test fixtures and utilities for testing."""
import pandas as pd
import numpy as np
from unittest.mock import Mock


def create_mock_team():
    """Creates a mock Team object for testing."""
    mock_team = Mock()
    mock_team.team_id = 1
    mock_team.name = "Test Team"
    return mock_team


def create_mock_player():
    """Creates a mock Player object for testing."""
    mock_player = Mock()
    mock_player.player_id = 101
    mock_player.full_name = "John Doe"
    mock_player.position = "Forward"
    return mock_player


def create_mock_tracking_dataset():
    """Creates a mock TrackingDataset object for testing."""
    mock_dataset = Mock()
    mock_dataset.metadata = Mock()
    mock_dataset.metadata.coordinate_system = Mock()
    mock_dataset.metadata.coordinate_system.pitch_length = 105.0
    mock_dataset.metadata.coordinate_system.pitch_width = 68.0
    mock_dataset.metadata.frame_rate = 25
    
    # Add frames attribute with pitch dimensions
    mock_dataset.frames = pd.DataFrame({
        'timestamp': [0.0, 0.04, 0.08],
        'pitch_length': [105.0, 105.0, 105.0],
        'pitch_width': [68.0, 68.0, 68.0],
    })
    
    return mock_dataset


def create_sample_event_data():
    """Creates sample event data for testing with proper data types."""
    data = {
        'player_id': [101, 101, 102, 102, 101, 103],
        'team_id': [1, 1, 2, 2, 1, 2],
        'end_type': ['pass', 'shot', 'pass', 'clearance', 'pass', 'foul_committed'],
        'pass_outcome': ['successful', np.nan, 'successful', np.nan, 'unsuccessful', np.nan],
        'pass_direction': ['forward', np.nan, 'backward', np.nan, 'forward', np.nan],
        'lead_to_goal': [0, 0, 0, 0, 0, 0],
        'game_interruption_after': [np.nan, np.nan, np.nan, np.nan, np.nan, np.nan],
        'event_subtype': ['short_pass', 'shot', 'long_pass', 'clearance', 'pass', 'foul'],
        'duration': [0.5, 0.0, 0.8, 0.2, 0.6, 1.0],
        'ball_state': ['in_play', 'in_play', 'in_play', 'in_play', 'in_play', 'in_play'],
    }
    df = pd.DataFrame(data)
    # Ensure end_type is string type for .str operations
    df['end_type'] = df['end_type'].astype(str)
    df['pass_outcome'] = df['pass_outcome'].astype('object')
    df['pass_direction'] = df['pass_direction'].astype('object')
    df['game_interruption_after'] = df['game_interruption_after'].astype('object')
    return df

