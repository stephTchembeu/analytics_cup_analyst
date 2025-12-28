# initialize an app just by running the python file with streamlit
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

from kloppy import skillcorner
from pathlib import Path
import sys

# Add parent directory to path for test imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.preset import (
    preset_app,
    display_status_messages,
    render_team_logo,
    get_stats,
    get_players_name,
    heatmap,
    pass_map,
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

from utils.pitch_control import (
    calculate_pitch_control,
    calculate_space_control_metrics,
    get_frame_positions,
    plot_pitch_control,
    plot_space_creation_impact,
)

# Run tests on startup
if "tests_validated" not in st.session_state:
    try:
        from tests.runner import run_tests, validate_imports

        # Validate imports first
        imports_ok, import_msg = validate_imports()
        if not imports_ok:
            st.warning(f"Import validation: {import_msg}")

        # Run test suite
        tests_ok, test_output = run_tests()
        if not tests_ok and test_output.strip():
            st.warning(f"Some tests failed:\n```\n{test_output}\n```")
        
        st.session_state.tests_validated = True
    except Exception as e:
        st.warning(f"Test runner error: {str(e)}")
        st.session_state.tests_validated = True

# define decorative elements
preset_app()

# Main tabs
tabs = st.tabs(TAB_NAMES)

# Load match data with error handling
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


@st.cache_data
def load_event_data(game_id):
    url = f"https://raw.githubusercontent.com/SkillCorner/opendata/master/data/matches/{game_id}/{game_id}_dynamic_events.csv"
    return pd.read_csv(url)


# Load event data with error handling (only if match_data loaded successfully)
if st.session_state.get("match_data") is not None:
    try:
        st.session_state.event_data = load_event_data(st.session_state.match_data.metadata.game_id)
        st.session_state.event_data_error = None
    except Exception as e:
        st.session_state.event_data_error = str(e)
        st.session_state.event_data = None
else:
    st.session_state.event_data = None
    st.session_state.event_data_error = "Match data not loaded"

# Display all status messages under the selectbox
display_status_messages()

# Get match data safely
match_data = st.session_state.get("match_data")
if match_data is None:
    st.stop()

home, away = match_data.metadata.teams

# Tab 0: Team Stats
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

        st.markdown("<br>", unsafe_allow_html=True)

        # --- STATS ROW (aligned under logos & score) ---
        stats_home, stats_labels, stats_away = st.columns([0.25, 0.5, 0.25])

        # Get computed stats
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


# Tab 1: Pitch Control (Placeholder)
with tabs[1]: 
    st.header("Pitch Control Analysis")
    st.info("This feature is under development. Coming soon!")
    st.markdown("""
    **Planned Features:**
    - Team possession zones heatmap
    - Dominant areas visualization
    - Territorial control metrics
    """)

# Tab 2: Defensive Shape (Placeholder)
with tabs[2]:
    st.header("Defensive Shape Analysis")
    st.info("This feature is under development. Coming soon!")
    st.markdown(
        """
    **Planned Features:**
    - Defensive line positioning
    - Compactness metrics
    - Pressing intensity zones
    """
    )


# Tab 3: Player Profiling
with tabs[3]:
    if st.session_state.selected_match:
        selected_team_name = st.selectbox(
            "Choose a team.",
            options=[home.name, away.name],
            key="team_select_profiling",
        )
        team = home if selected_team_name == home.name else away

        if selected_team_name:
            selected_players = get_players_name(selected_team_name, match_data)
            selected_player_name = st.selectbox(
                "Choose a player.",
                options=selected_players,
                key="player_select_profiling",
            )
            selected_player = [
                player
                for player in team.players
                if player.full_name == str(selected_player_name)
            ][0]

            # Print player name and position
            # If position is None or unknown, get from event_data
            player_position = selected_player.position
            if not player_position or str(player_position).lower() in ["none", "unknown", "nan"]:
                # Try to get from event_data
                player_events = st.session_state.event_data[
                    st.session_state.event_data["player_id"] == float(selected_player.player_id)
                ]
                # Get the most common non-null position
                if not player_events.empty and "player_position" in player_events.columns:
                    pos_counts = player_events["player_position"].dropna()
                    if not pos_counts.empty:
                        player_position = pos_counts.mode().iloc[0]
                    else:
                        player_position = "Unknown"
                else:
                    player_position = "Unknown"

            st.markdown(
                f"""
                <div class="player">
                    <p class="name">{selected_player_name}</p>
                    <p class="position">{player_position}</p>
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
            attacking_side_pass = pass_events["attacking_side"]

            xs_shot = shot_events["x_start"]
            ys_shot = shot_events["y_start"]
            attacking_side_shot = shot_events["attacking_side"]

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
                    25,
                    25,
                    round(
                        st.session_state.event_data["duration"].mean()
                        + st.session_state.event_data["duration"].mean() * 0.5,
                        2,
                    ),
                    25,
                    25,
                    25,
                ]
                player_events = st.session_state.event_data[
                    st.session_state.event_data["player_id"] == float(selected_player.player_id)
                ]
                team_id_arr = player_events["team_id"].unique()
                if len(team_id_arr) > 0:
                    team_id = team_id_arr[0]
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
                else:
                    # No events for this player, fill with zeros
                    values = [0, 0, 0, 0, 0, 0, 0]
                plot_radar(metrics=metrics, low=low, high=high, values=values)

            with heatmap_:
                heatmap(
                    xs_pass,
                    ys_pass,
                    attacking_side_pass,
                    xs_shot,
                    ys_shot,
                    attacking_side_shot,
                    match_data,
                )

                # Pass filtering options
                st.session_state.pass_filter = st.selectbox(
                    "Filter passes by type",
                    options=[
                        "All passes",
                        "Forward passes",
                        "Backward passes",
                        "Defensive line-breaking",
                        "Lead to goal",
                    ],
                    key="pass_filter_select",
                )

                # Apply filter and show pass map
                if st.session_state.pass_filter != "All passes":
                    filtered_passes = pass_events.copy()

                    if st.session_state.pass_filter == "Forward passes":
                        filtered_passes = filtered_passes[
                            filtered_passes["pass_direction"] == "forward"
                        ]
                    elif st.session_state.pass_filter == "Backward passes":
                        filtered_passes = filtered_passes[
                            filtered_passes["pass_direction"] == "backward"
                        ]
                    elif st.session_state.pass_filter == "Defensive line-breaking":
                        filtered_passes = filtered_passes[
                            filtered_passes["defensive_line_break"] == 1
                        ]
                    elif st.session_state.pass_filter == "Lead to goal":
                        filtered_passes = filtered_passes[
                            filtered_passes["lead_to_goal"] == 1
                        ]

                    if len(filtered_passes) > 0:
                        pass_map(
                            filtered_passes["x_start"],
                            filtered_passes["y_start"],
                            filtered_passes["x_end"],
                            filtered_passes["y_end"],
                            filtered_passes["pass_outcome"],
                            match_data,
                        )
                    else:
                        st.warning(
                            f"No passes found for filter: {st.session_state.pass_filter}"
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
                    <p class="label">Shots on target</p>
                    <p class="value">{shots_on_target(selected_player, match_data)}</p>
                </div>
                """,
                    unsafe_allow_html=True,
                )

            plot_1, plot_2, plot_3 = st.columns([.33, .33, .33])
            # Plot 1: Ball Retention
            with plot_1:
                player_events = st.session_state.event_data[
                    st.session_state.event_data["player_id"] == float(selected_player.player_id)
                ]
                retention_events = player_events[player_events["duration"] > 0]
                durations = retention_events[["event_id", "duration", "end_type"]].reset_index(drop=True)
                mean_retention = durations["duration"].mean()
                fig = px.bar(
                    x=durations["event_id"],
                    y=durations["duration"],
                    labels={"x": "Event Id", "y": "Ball duration (s)"},
                    title=f"Ball Retention for {selected_player_name}",
                    color_discrete_sequence=["#0e8d34"],
                    custom_data=[durations["end_type"]]
                )
                fig.update_traces(
                    hovertemplate="Event Id: %{x}<br>Ball duration (s): %{y}<br>Event type: %{customdata[0]}<extra></extra>"
                )
                fig.add_trace(
                    go.Scatter(
                        x=durations["event_id"],
                        y=[mean_retention] * len(durations),
                        mode="lines",
                        line=dict(color="red", dash="dash"),
                        name=f"Mean: {mean_retention:.2f}s",
                        hovertemplate="Mean: %{y:.2f}s<extra></extra>"
                    )
                )
                fig.update_layout(showlegend=True)
                st.plotly_chart(fig, use_container_width=True)

            # Plot 2: Offensive Actions
            with plot_2:
                OFFENSIVE_SUBTYPES = [
                    "coming_short", "run_ahead_of_the_ball", "behind", "dropping_off", "pulling_wide",
                    "pulling_half_space", "overlap", "underlap", "support", "cross_receiver"
                ]
                player_events = st.session_state.event_data[
                    st.session_state.event_data["player_id"] == float(selected_player.player_id)
                ]
                offensive_events = player_events[player_events["event_subtype"].isin(OFFENSIVE_SUBTYPES)]
                if not offensive_events.empty:
                    offensive_df = offensive_events[["event_id", "event_subtype", "duration", "end_type"]].reset_index(drop=True)
                    mean_offensive = offensive_df["duration"].mean() if "duration" in offensive_df else 0
                    fig2 = px.bar(
                        x=offensive_df["event_id"],
                        y=offensive_df["duration"] if "duration" in offensive_df else [0]*len(offensive_df),
                        labels={"x": "Event Id", "y": "Duration (s)"},
                        title=f"Offensive Actions for {selected_player_name}",
                        color_discrete_sequence=["#217c23"],
                        custom_data=[offensive_df["event_subtype"], offensive_df["end_type"]]
                    )
                    fig2.update_traces(
                        hovertemplate="Event Id: %{x}<br>Duration (s): %{y}<br>Subtype: %{customdata[0]}<br>Event type: %{customdata[1]}<extra></extra>"
                    )
                    fig2.add_trace(
                        go.Scatter(
                            x=offensive_df["event_id"],
                            y=[mean_offensive] * len(offensive_df),
                            mode="lines",
                            line=dict(color="red", dash="dash"),
                            name=f"Mean: {mean_offensive:.2f}s",
                            hovertemplate="Mean: %{y:.2f}s<extra></extra>"
                        )
                    )
                    fig2.update_layout(showlegend=True)
                    st.plotly_chart(fig2, use_container_width=True)
                else:
                    st.info("No offensive actions found for this player.")

            # Plot 3: Defensive Actions
            with plot_3:
                DEFENSIVE_END_TYPES = [
                    "indirect_disruption", "indirect_regain", "direct_regain", "direct_disruption",
                    "possession_loss", "foul_committed", "clearance"
                ]
                player_events = st.session_state.event_data[
                    st.session_state.event_data["player_id"] == float(selected_player.player_id)
                ]
                defensive_events = player_events[player_events["end_type"].isin(DEFENSIVE_END_TYPES)]
                if not defensive_events.empty:
                    defensive_df = defensive_events[["event_id", "end_type", "duration", "event_subtype"]].reset_index(drop=True)
                    mean_defensive = defensive_df["duration"].mean() if "duration" in defensive_df else 0
                    fig3 = px.bar(
                        x=defensive_df["event_id"],
                        y=defensive_df["duration"] if "duration" in defensive_df else [0]*len(defensive_df),
                        labels={"x": "Event Id", "y": "Duration (s)"},
                        title=f"Defensive Actions for {selected_player_name}",
                        color_discrete_sequence=["#052B72"],
                        custom_data=[defensive_df["end_type"], defensive_df["event_subtype"]]
                    )
                    fig3.update_traces(
                        hovertemplate="Event Id: %{x}<br>Duration (s): %{y}<br>Event type: %{customdata[0]}<br>Subtype: %{customdata[1]}<extra></extra>"
                    )
                    fig3.add_trace(
                        go.Scatter(
                            x=defensive_df["event_id"],
                            y=[mean_defensive] * len(defensive_df),
                            mode="lines",
                            line=dict(color="red", dash="dash"),
                            name=f"Mean: {mean_defensive:.2f}s",
                            hovertemplate="Mean: %{y:.2f}s<extra></extra>"
                        )
                    )
                    fig3.update_layout(showlegend=True)
                    st.plotly_chart(fig3, use_container_width=True)
                else:
                    st.info("No defensive actions found for this player.")
                

# Tab 4: Player Performance (Comparison)
with tabs[4]:
    st.header("Player Performance Comparison")

    if st.session_state.selected_match:
        col1, col2 = st.columns(2)

        with col1:
            st.subheader("Player 1")
            team1_name = st.selectbox(
                "Choose team for Player 1",
                options=[home.name, away.name],
                key="team1_performance",
            )
            team1 = home if team1_name == home.name else away
            players1 = get_players_name(team1_name, match_data)
            player1_name = st.selectbox(
                "Choose Player 1", options=players1, key="player1_performance"
            )
            player1 = [p for p in team1.players if p.full_name == player1_name][0]

        with col2:
            st.subheader("Player 2")
            team2_name = st.selectbox(
                "Choose team for Player 2",
                options=[home.name, away.name],
                key="team2_performance",
            )
            team2 = home if team2_name == home.name else away
            players2 = get_players_name(team2_name, match_data)
            player2_name = st.selectbox(
                "Choose Player 2", options=players2, key="player2_performance"
            )
            player2 = [p for p in team2.players if p.full_name == player2_name][0]

        # Comparison table
        st.subheader("Performance Comparison")

        comparison_data = {
            "Metric": [
                "Distance Covered (km)",
                "Max Speed (m/s)",
                "Total Passes",
                "Expected Goals (xG)",
                "Expected Threat (xT)",
                "Shots on Target",
                "Shots Total",
            ],
            player1_name: [
                covered_distance(player1, match_data),
                max_speed(player1, match_data),
                len(
                    st.session_state.event_data[
                        (st.session_state.event_data["end_type"] == "pass")
                        & (
                            st.session_state.event_data["player_id"]
                            == int(player1.player_id)
                        )
                    ]
                ),
                expected_goals(player1, match_data),
                expected_threat(player1, match_data),
                shots_on_target(player1, match_data),
                shots_(player1.player_id),
            ],
            player2_name: [
                covered_distance(player2, match_data),
                max_speed(player2, match_data),
                len(
                    st.session_state.event_data[
                        (st.session_state.event_data["end_type"] == "pass")
                        & (
                            st.session_state.event_data["player_id"]
                            == int(player2.player_id)
                        )
                    ]
                ),
                expected_goals(player2, match_data),
                expected_threat(player2, match_data),
                shots_on_target(player2, match_data),
                shots_(player2.player_id),
            ],
        }

        df_comparison = pd.DataFrame(comparison_data)
        st.dataframe(df_comparison, use_container_width=True, hide_index=True)

        # Visualization comparison
        st.subheader("Visual Comparison")

        # Create side-by-side radar charts
        col_radar1, col_radar2 = st.columns(2)

        team1_id = st.session_state.event_data[
            st.session_state.event_data["player_id"] == float(player1.player_id)
        ]["team_id"].unique()[0]

        team2_id = st.session_state.event_data[
            st.session_state.event_data["player_id"] == float(player2.player_id)
        ]["team_id"].unique()[0]

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
            len(
                st.session_state.event_data[
                    st.session_state.event_data["end_type"] == "shot"
                ]
            )
            * 1.2,
            25,
            25,
            round(st.session_state.event_data["duration"].mean() * 1.5, 2),
            25,
            25,
            25,
        ]

        values1 = [
            shots_(player1.player_id),
            offensive_action(player1.player_id),
            pressing_engagement(player1.player_id, team1_id)["Defensive_Action_volume"],
            avg_ball_retention_time(player1.player_id),
            avg_forward_pass(player1.player_id),
            pressing_engagement(player1.player_id, team1_id)["avg_Pressing_actions"],
            pressing_engagement(player1.player_id, team1_id)["Success_DA"],
        ]

        values2 = [
            shots_(player2.player_id),
            offensive_action(player2.player_id),
            pressing_engagement(player2.player_id, team2_id)["Defensive_Action_volume"],
            avg_ball_retention_time(player2.player_id),
            avg_forward_pass(player2.player_id),
            pressing_engagement(player2.player_id, team2_id)["avg_Pressing_actions"],
            pressing_engagement(player2.player_id, team2_id)["Success_DA"],
        ]

        with col_radar1:
            st.markdown(f"**{player1_name}**")
            plot_radar(metrics=metrics, low=low, high=high, values=values1)

        with col_radar2:
            st.markdown(f"**{player2_name}**")
            plot_radar(metrics=metrics, low=low, high=high, values=values2)
    else:
        st.info(
            "Please select a match from the sidebar to view player performance comparisons."
        )
