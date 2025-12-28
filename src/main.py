"""FootMetricX - Soccer Analytics Dashboard

Main Streamlit application runner for the FootMetricX analytics dashboard.
Loads match data, initializes UI, and renders tabs.
"""

import streamlit as st
import pandas as pd
from kloppy import skillcorner
from pathlib import Path
import sys

# Add parent directory to path for test imports
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import app configuration
from utils.preset import (
    preset_app,
    TAB_NAMES,
)

# Import tab rendering functions
from utils.tabs import (
    render_team_stats_tab,
    render_pitch_control_tab,
    render_defensive_shape_tab,
    render_player_profiling_tab,
    render_player_performance_tab,
)

# Run tests on startup
if "tests_validated" not in st.session_state:
    try:
        from tests.runner import run_tests, validate_imports

        imports_ok, import_msg = validate_imports()
        if not imports_ok:
            st.warning(f"Import validation: {import_msg}")

        tests_ok, test_output = run_tests()
        if not tests_ok and test_output.strip():
            st.warning(f"Some tests failed:\n```\n{test_output}\n```")
        
        st.session_state.tests_validated = True
    except Exception as e:
        st.warning(f"Test runner error: {str(e)}")
        st.session_state.tests_validated = True


def load_event_data(game_id):
    """Load event data from GitHub for a given game ID."""
    url = f"https://raw.githubusercontent.com/SkillCorner/opendata/master/data/matches/{game_id}/{game_id}_dynamic_events.csv"
    return pd.read_csv(url)


def load_and_validate_data():
    """Load and validate both match and event data with error handling."""
    # Load match data
    try:
        match_data = skillcorner.load_open_data(
            match_id=st.session_state.selected_match_id,
            coordinates="skillcorner",
        )
        st.session_state.match_data = match_data
        st.session_state.match_data_error = None
    except Exception as e:
        st.session_state.match_data = None
        st.session_state.match_data_error = str(e)
    else:
        st.sidebar.success("Match data loaded successfully!")

    # Load event data (only if match_data loaded successfully)
    if st.session_state.get("match_data") is not None:
        try:
            st.session_state.event_data = load_event_data(st.session_state.match_data.metadata.game_id)
        except Exception as e:
            st.session_state.event_data_error = str(e)
            st.session_state.event_data = None
        else:
            st.session_state.event_data_error = None
            st.sidebar.success("Event data loaded successfully!")

        # Display error messages if there were any
        if st.session_state.get("event_data_error"):
            st.sidebar.warning(f"Failed to load event data: {st.session_state.event_data_error}")
        
        if st.session_state.get("match_data_error"):
            st.sidebar.warning(f"Failed to load match data: {st.session_state.match_data_error}")
    else:
        st.sidebar.error("Match data failed to load. Cannot proceed with analysis.")
        st.stop()


def main():
    """Main application runner."""
    # Setup app configuration and sidebar
    preset_app()

    # Load and validate data
    load_and_validate_data()

    # Get match data from session state
    match_data = st.session_state.match_data
    home, away = match_data.metadata.teams

    # Create tabs
    tabs = st.tabs(TAB_NAMES)

    # Render each tab
    render_team_stats_tab(tabs, match_data, home, away)
    render_pitch_control_tab(tabs)
    render_defensive_shape_tab(tabs)
    render_player_profiling_tab(tabs, match_data)
    render_player_performance_tab(tabs, match_data)


if __name__ == "__main__":
    main()

