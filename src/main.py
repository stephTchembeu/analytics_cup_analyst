# initialize an app just by running the python file with streamlit
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from kloppy import skillcorner

from utils.preset import (
    preset_app,
    render_team_logo,
    get_stats,
    get_players_name,
    heatmap,
    covered_distance,
    max_speed,
    shots_on_target,
    expected_goals,
    expected_threat,
    shots_,
    offensive_action,
    pressing_engagement,
    avg_ball_retention_time,
    avg_forward_pass,
    plot_radar,
    TAB_NAMES,
    STATS_LABELS,
)


# define decorative elements
preset_app()

# Main tabs
tabs = st.tabs(TAB_NAMES)

# data_of_the_selected_match
match_data = skillcorner.load_open_data(
    match_id=st.session_state.selected_match_id,
    coordinates="skillcorner",
)


@st.cache_data
def load_event_data(game_id):
    url = f"https://raw.githubusercontent.com/SkillCorner/opendata/master/data/matches/{game_id}/{game_id}_dynamic_events.csv"
    return pd.read_csv(url)


st.session_state.event_data = load_event_data(match_data.metadata.game_id)

home, away = match_data.metadata.teams

# team stats
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
                        {match_data.metadata.score.home}&nbsp;&nbsp;–&nbsp;&nbsp;{match_data.metadata.score.away}
                    </h1>
                </div>
                """,
                unsafe_allow_html=True,
            )

        with logo_away:
            render_team_logo(away.name, align="right")

        st.markdown("<br>", unsafe_allow_html=True)

        # --- STATS ROW (aligned under logos & score) ---
        stats_home, stats_labels, stats_away = st.columns([0.25, 0.5, 0.25])

        # Example values (replace with computed ones)
        home_stats = get_stats(home)
        away_stats = get_stats(away)

        # HOME COLUMN
        with stats_home:
            for _, val in home_stats.items():
                st.markdown(
                    f"<p style='text-align:right; font-weight:800; margin:8px 0;'>{val}</p>",
                    unsafe_allow_html=True,
                )

        # LABEL COLUMN (centered under score)
        with stats_labels:
            for label in STATS_LABELS:
                st.markdown(
                    f"<p style='text-align:center; color:gray; margin:8px 0;'>{label}</p>",
                    unsafe_allow_html=True,
                )

        # AWAY COLUMN
        with stats_away:
            for _, val in away_stats.items():
                st.markdown(
                    f"<p style='text-align:left; font-weight:800; margin:8px 0;'>{val}</p>",
                    unsafe_allow_html=True,
                )


# player profiling
with tabs[3]:
    if st.session_state.selected_match:
        selected_team_name = st.selectbox(
            "Choose a team.", options=[home.name, away.name]
        )
        team = home if selected_team_name == home.name else away
        if selected_team_name:
            selected_players = get_players_name(selected_team_name, match_data)
            selected_player_name = st.selectbox(
                "Choose a team.", options=selected_players
            )
            selected_player = [
                player
                for player in team.players
                if player.full_name == str(selected_player_name)
            ][0]

            # Print player name and position
            st.markdown(
                f"""
                <div class="player">
                    <p class="name" ">{selected_player_name}</p>
                    <p class="position">{selected_player.position}</p>
                </div>
                """,
                unsafe_allow_html=True,
            )

            # Filter shot events
            shot_events = st.session_state.event_data[
                (st.session_state.event_data["end_type"] == "shot")
                & (
                    st.session_state.event_data["player_id"]
                    == int(selected_player.player_id)
                )
            ]

            # Filter pass events
            pass_events = st.session_state.event_data[
                (st.session_state.event_data["end_type"] == "pass")
                & (
                    st.session_state.event_data["player_id"]
                    == int(selected_player.player_id)
                )
            ]
            total_passes_count = len(pass_events)
            xs_pass = pass_events["x_start"]
            ys_pass = pass_events["y_start"]
            xs_shot = shot_events["x_start"]
            ys_shot = shot_events["y_start"]

            radar_, heatmap_, stats_ = st.columns([0.35, 0.45, 0.2])
            with radar_:
                metrics = [
                    "n_Shot",
                    "offensive_action %",
                    "Defensive_Action %",
                    "Ball retention",
                    "avg_forward_Pass %",
                    "avg_Pressing_actions %",
                    "Success_DA %",
                ]
                low = [0, 0, 0, 0, 0, 0, 0]
                high = [
                    (
                        len(
                            st.session_state.event_data[
                                st.session_state.event_data["end_type"] == "shot"
                            ]
                        )
                        + len(
                            st.session_state.event_data[
                                st.session_state.event_data["end_type"] == "shot"
                            ]
                        )
                        * 0.2
                    ),
                    100,
                    100,
                    round(
                        st.session_state.event_data["duration"].mean()
                        + st.session_state.event_data["duration"].mean() * 0.5,
                        2,
                    ),
                    100,
                    100,
                    100,
                ]
                team_id = st.session_state.event_data[
                    st.session_state.event_data["player_id"]
                    == float(selected_player.player_id)
                ]["team_id"].unique()[0]
                values = [
                    shots_(selected_player.player_id),
                    offensive_action(selected_player.player_id),
                    pressing_engagement(selected_player.player_id, team_id)[
                        "Defensive_Action_volume"
                    ],
                    avg_ball_retention_time(selected_player.player_id),
                    avg_forward_pass(selected_player.player_id),
                    pressing_engagement(selected_player.player_id, team_id)[
                        "avg_Pressing_actions"
                    ],
                    pressing_engagement(selected_player.player_id, team_id)[
                        "Success_DA"
                    ],
                ]
                plot_radar(metrics=metrics, low=low, high=high, values=values)
            with heatmap_:
                heatmap(xs_pass, ys_pass, xs_shot, ys_shot, match_data)
                loop_into = st.selectbox(
                    "filter pass",
                    options=[
                        "forward pass",
                        "backward pass",
                        "defensiveline-breaken",
                        "lead to goal",
                    ],
                )
            with stats_:
                st.markdown(
                    f"""
                <div class="player-stats">
                    <p class="label">Total Passes</p>
                    <p class="value">{total_passes_count}</p>
                    <p class="label">Distance covered</p>
                    <p class="value">{covered_distance(selected_player, match_data):.2f} km</p>
                    <p class="label">Max speed</p>
                    <p class="value">{max_speed(selected_player, match_data):.1f} m/s</p>
                    <p class="label">Expected Threat (xT)</p>
                    <p class="value">{expected_threat(selected_player, match_data):.2f}</p>
                    <p class="label">Expected Goals (xG)</p>
                    <p class="value">{expected_goals(selected_player, match_data):.2f}</p>
                    <p class="label">Shots on target</p>
                    <p class="value">{shots_on_target(selected_player, match_data)}</p>
                </div>
                """,
                    unsafe_allow_html=True,
                )
