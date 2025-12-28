"""Tab Rendering Functions
Handles all tab content rendering for the Streamlit app, keeping the main.py clean.
"""

import streamlit as st
import pandas as pd
from kloppy.domain.models.tracking import TrackingDataset

from .team_stats import get_stats
from .player_profiling import get_players_name
from .preset import render_team_logo, STATS_LABELS


def render_team_stats_tab(tabs, match_data: TrackingDataset, home, away):
    """Renders the Team Stats tab content."""
    with tabs[0]:
        if st.session_state.selected_match:
            logo_home, score_col, logo_away = st.columns([0.25, 0.5, 0.25])
            with logo_home:
                render_team_logo(home.name, align="left")

            with score_col:
                st.markdown(
                    f"""
                    <div style="text-align:center;">
                        <h1 style="font-size:80px; color:gray; margin:0;">
                            {match_data.metadata.score.home}&nbsp;&nbsp;—&nbsp;&nbsp;{match_data.metadata.score.away}
                        </h1>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

            with logo_away:
                render_team_logo(away.name, align="right")

            st.markdown("---")

            # Display team stats
            col1, col2 = st.columns(2)

            home_stats = get_stats(home)
            away_stats = get_stats(away)

            with col1:
                st.markdown(f"## {home.name}")
                for i, label in enumerate(STATS_LABELS):
                    cols = st.columns([0.5, 0.5])
                    with cols[0]:
                        st.metric(label, home_stats[list(home_stats.keys())[i]])
                    with cols[1]:
                        st.metric(label, away_stats[list(away_stats.keys())[i]])

            with col2:
                st.markdown(f"## {away.name}")


def render_pitch_control_tab(tabs):
    """Renders the Pitch Control tab content."""
    with tabs[1]:
        st.markdown("### Pitch Control Analysis")
        st.info("Pitch control analysis tab - under development")


def render_defensive_shape_tab(tabs):
    """Renders the Defensive Shape tab content."""
    with tabs[2]:
        st.markdown("### Defensive Shape Analysis")
        st.info("Defensive shape analysis tab - under development")


def render_player_profiling_tab(tabs, match_data: TrackingDataset):
    """Renders the Player Profiling tab content."""
    with tabs[3]:
        if st.session_state.selected_match:
            st.markdown("### Player Profiling")
            
            team_name = st.selectbox(
                "Select Team",
                [team.name for team in match_data.metadata.teams],
            )
            
            players = get_players_name(team_name, match_data)
            if players:
                player_name = st.selectbox("Select Player", players)
                st.success(f"Selected: {player_name}")
            else:
                st.warning("No players found for this team")


def render_player_performance_tab(tabs, match_data: TrackingDataset):
    """Renders the Player Performance tab content."""
    with tabs[4]:
        if st.session_state.selected_match:
            st.markdown("### Player Performance Comparison")
            
            team_name = st.selectbox(
                "Select Team for Comparison",
                [team.name for team in match_data.metadata.teams],
                key="perf_team_select"
            )
            
            players = get_players_name(team_name, match_data)
            if players:
                st.success(f"Found {len(players)} players")
            else:
                st.warning("Please select a match from the sidebar to view player performance comparisons.")
