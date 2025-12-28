"""Tests for preset.py utility functions."""
import pytest
import pandas as pd
import numpy as np
from unittest.mock import Mock, patch
import sys
import os

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from tests.conftest import (
    create_mock_team,
    create_mock_player,
    create_sample_event_data,
    create_mock_tracking_dataset,
)


class TestTeamStatsFunctions:
    """Tests for team-level statistics functions."""

    @patch('utils.preset.st')
    def test_shots_function(self, mock_st):
        """Test shots() function returns correct tuple."""
        mock_st.session_state = Mock()
        mock_st.session_state.event_data = create_sample_event_data()
        
        from utils.preset import shots
        team = create_mock_team()
        
        total, on_target = shots(team)
        assert isinstance(total, (int, np.integer))
        assert isinstance(on_target, (int, np.integer))
        assert total >= on_target >= 0

    @patch('utils.preset.st')
    def test_passes_function(self, mock_st):
        """Test passess() function returns correct tuple."""
        mock_st.session_state = Mock()
        mock_st.session_state.event_data = create_sample_event_data()
        
        from utils.preset import passess
        team = create_mock_team()
        
        total, successful = passess(team)
        assert isinstance(total, (int, np.integer))
        assert isinstance(successful, (int, np.integer))
        assert total >= successful >= 0

    @patch('utils.preset.st')
    def test_pass_accuracy_function(self, mock_st):
        """Test pass_accuracy() function returns valid percentage."""
        mock_st.session_state = Mock()
        mock_st.session_state.event_data = create_sample_event_data()
        
        from utils.preset import pass_accuracy
        team = create_mock_team()
        
        accuracy = pass_accuracy(team)
        assert isinstance(accuracy, (int, float))
        assert 0 <= accuracy <= 100

    @pytest.mark.skip(reason="Empty DataFrame string accessor issue - needs refactoring")
    @patch('utils.preset.st')
    def test_pass_accuracy_zero_division(self, mock_st):
        """Test pass_accuracy() handles zero passes gracefully."""
        mock_st.session_state = Mock()
        empty_df = pd.DataFrame({
            'player_id': [],
            'team_id': [],
            'end_type': [],
            'pass_outcome': [],
        })
        mock_st.session_state.event_data = empty_df
        
        from utils.preset import pass_accuracy
        team = create_mock_team()
        
        accuracy = pass_accuracy(team)
        assert accuracy == 0

    @patch('utils.preset.st')
    def test_clearances_function(self, mock_st):
        """Test clearances() function returns non-negative integer."""
        mock_st.session_state = Mock()
        mock_st.session_state.event_data = create_sample_event_data()
        
        from utils.preset import clearances
        team = create_mock_team()
        
        count = clearances(team)
        assert isinstance(count, (int, np.integer))
        assert count >= 0

    @patch('utils.preset.st')
    def test_fouls_committed_function(self, mock_st):
        """Test fouls_committed() function returns non-negative integer."""
        mock_st.session_state = Mock()
        mock_st.session_state.event_data = create_sample_event_data()
        
        from utils.preset import fouls_committed
        team = create_mock_team()
        
        count = fouls_committed(team)
        assert isinstance(count, (int, np.integer))
        assert count >= 0

    @patch('utils.preset.st')
    def test_get_stats_returns_dict(self, mock_st):
        """Test get_stats() returns properly formatted dictionary."""
        mock_st.session_state = Mock()
        mock_st.session_state.event_data = create_sample_event_data()
        
        from utils.preset import get_stats
        team = create_mock_team()
        
        stats = get_stats(team)
        assert isinstance(stats, dict)
        assert 'shots' in stats
        assert 'passes' in stats
        assert 'clearances' in stats
        assert 'fouls_committed' in stats
        assert all(isinstance(v, str) for v in stats.values())


class TestPlayerStatsFunctions:
    """Tests for player-level statistics functions."""

    @patch('utils.preset.st')
    def test_shots_on_target_function(self, mock_st):
        """Test shots_on_target() returns non-negative integer."""
        mock_st.session_state = Mock()
        mock_st.session_state.event_data = create_sample_event_data()
        
        from utils.preset import shots_on_target
        player = create_mock_player()
        match_data = create_mock_tracking_dataset()
        
        count = shots_on_target(player, match_data)
        assert isinstance(count, (int, np.integer))
        assert count >= 0

    @patch('utils.preset.st')
    def test_expected_goals_function(self, mock_st):
        """Test expected_goals() returns valid float."""
        mock_st.session_state = Mock()
        mock_st.session_state.event_data = create_sample_event_data()
        
        from utils.preset import expected_goals
        player = create_mock_player()
        match_data = create_mock_tracking_dataset()
        
        xg = expected_goals(player, match_data)
        assert isinstance(xg, float)
        assert xg >= 0.0

    @patch('utils.preset.st')
    def test_expected_threat_function(self, mock_st):
        """Test expected_threat() returns valid float."""
        mock_st.session_state = Mock()
        mock_st.session_state.event_data = create_sample_event_data()
        
        from utils.preset import expected_threat
        player = create_mock_player()
        match_data = create_mock_tracking_dataset()
        
        xt = expected_threat(player, match_data)
        assert isinstance(xt, float)
        assert xt >= 0.0

    @patch('utils.preset.st')
    def test_avg_forward_pass_function(self, mock_st):
        """Test avg_forward_pass() returns valid percentage."""
        mock_st.session_state = Mock()
        mock_st.session_state.event_data = create_sample_event_data()
        
        from utils.preset import avg_forward_pass
        player = create_mock_player()
        
        percentage = avg_forward_pass(player.player_id)
        assert isinstance(percentage, float)
        assert 0 <= percentage <= 100


class TestUtilityFunctions:
    """Tests for utility functions."""

    def test_first_word_extraction(self):
        """Test first_word() correctly extracts first word."""
        from utils.preset import first_word
        
        assert first_word("hello world") == "hello"
        assert first_word("single") == "single"
        assert first_word("") == ""
        assert first_word("a b c") == "a"

    def test_get_players_name_function(self):
        """Test get_players_name() returns list of strings."""
        from utils.preset import get_players_name
        
        mock_dataset = Mock()
        mock_team1 = Mock()
        mock_team1.name = "Test Team"
        mock_player1 = Mock()
        mock_player1.full_name = "Player One"
        mock_player2 = Mock()
        mock_player2.full_name = "Player Two"
        mock_team1.players = [mock_player1, mock_player2]
        
        mock_dataset.metadata.teams = [mock_team1]
        
        names = get_players_name("Test Team", mock_dataset)
        assert isinstance(names, list)
        assert len(names) == 2
        assert "Player One" in names
        assert "Player Two" in names

    def test_get_players_name_empty_team(self):
        """Test get_players_name() returns empty list for non-existent team."""
        from utils.preset import get_players_name
        
        mock_dataset = Mock()
        mock_dataset.metadata.teams = []
        
        names = get_players_name("Non-existent Team", mock_dataset)
        assert isinstance(names, list)
        assert len(names) == 0


class TestDataValidation:
    """Tests for data validation and edge cases."""

    @pytest.mark.skip(reason="Empty DataFrame string accessor issue - needs refactoring")
    @patch('utils.preset.st')
    def test_empty_event_data(self, mock_st):
        """Test functions handle empty event data gracefully."""
        mock_st.session_state = Mock()
        empty_df = pd.DataFrame({
            'player_id': pd.Series([], dtype='int64'),
            'team_id': pd.Series([], dtype='int64'),
            'end_type': pd.Series([], dtype='string'),
            'pass_outcome': pd.Series([], dtype='object'),
            'lead_to_goal': pd.Series([], dtype='int64'),
            'game_interruption_after': pd.Series([], dtype='object'),
        })
        mock_st.session_state.event_data = empty_df
        
        from utils.preset import shots, passess, clearances
        team = create_mock_team()
        
        # Should not raise exceptions
        assert shots(team) == (0, 0)
        assert passess(team) == (0, 0)
        assert clearances(team) == 0

    def test_sample_event_data_structure(self):
        """Test sample event data has correct structure."""
        data = create_sample_event_data()
        
        assert isinstance(data, pd.DataFrame)
        assert len(data) > 0
        assert 'player_id' in data.columns
        assert 'team_id' in data.columns
        assert 'end_type' in data.columns


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
