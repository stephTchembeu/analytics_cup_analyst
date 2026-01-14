# initialize an app just by running the python file with streamlit
from utils.team_stats import (
    plot_team_pitch_third,
    show_formation,
    plot_momentum_chart_plotly,
)
from utils.player_profiling import (
    add_position,
    get_events,
    get_player,
    get_players_name_,
    plot_defensive_action,
    plot_offensive_action,
    plot_retention,
    select_team,
    show_player_name_pos,
)
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
    LOWER_BOUNDS,
    get_radar_values,
    get_upper_bound,
    preset_app,
    display_status_messages,
    render_team_logo,
    get_stats,
    heatmap,
    pass_map,
    covered_distance,
    max_speed,
    shots_on_target,
    expected_threat,
    match_available,
    title,
    sub_title,
    plot_radar,
    TAB_NAMES,
    STATS_LABELS,
    RADAR_METRICS,
    OFFENSIVE_SUBTYPES,
    DEFENSIVE_END_TYPES,
    TEAM_colors,
)

from utils.player_performance import *

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
        st.session_state.event_data = load_event_data(
            st.session_state.match_data.metadata.game_id
        )
        st.session_state.event_data_error = None
    except Exception as e:
        st.session_state.event_data_error = str(e)
        st.session_state.event_data = None
else:
    st.session_state.event_data = None
    st.session_state.event_data_error = "Match data not loaded"

UPPER_BOUNDS = get_upper_bound()
# Display all status messages under the selectbox
display_status_messages()

# Get match data safely
match_data = st.session_state.get("match_data")
if match_data is None:
    st.stop()

home, away = match_data.metadata.teams
# st.session_state.home,st.session_state.away = home,away
home_default_color = "#0C37F5"  # whatever default you want
home_color = TEAM_colors.get(home.name, home_default_color)
away_default_color = "#B81111"  # whatever default you want
away_color = TEAM_colors.get(away.name, away_default_color)


# Tab 0: Team Stats
with tabs[0]:
    if st.session_state.selected_match:
        logo_home, score_col, logo_away = st.columns([0.25, 0.5, 0.25])
        with logo_home:
            render_team_logo(home.team_id, home.name, align="left")

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
            render_team_logo(away.team_id, away.name, align="right")

        st.markdown("<br>", unsafe_allow_html=True)

        # --- STATS ROW (aligned under logos & score) ---
        stats_home, pad_1, stats_labels, pad_2, stats_away = st.columns(
            [0.24, 0.01, 0.5, 0.01, 0.24]
        )

        # Get computed stats
        home_stats = get_stats(home)
        away_stats = get_stats(away)

        # HOME COLUMN
        with stats_home:
            home_attacking_third = plot_team_pitch_third(
                st.session_state.event_data,
                match_data,
                home,
                home_color,
                "left_to_right",
                "offensive",
            )
            home_defensive_third = plot_team_pitch_third(
                st.session_state.event_data,
                match_data,
                home,
                home_color,
                "left_to_right",
                "defensive",
            )
            st.pyplot(home_attacking_third)
            st.pyplot(home_defensive_third)
            show_formation(
                home,
                match_data=match_data,
                event_data=st.session_state.event_data,
                team_color=home_color,
            )

        # LABEL COLUMN (centered under score)
        with stats_labels:
            fig_momentum = plot_momentum_chart_plotly(
                st.session_state.event_data,
                home_team_id=home.team_id,
                away_team_id=away.team_id,
                home_color=home_color,
                away_color=away_color,
            )

            st.plotly_chart(fig_momentum, use_container_width=True)

            home_stats_, labels_stats_, away_stats_ = st.columns([0.25, 0.5, 0.25])
            with home_stats_:
                for _, val in home_stats.items():
                    st.markdown(
                        f"<p style='text-align:left; font-weight:800; margin:8px 0; font-size:22px;'>{val}</p>",
                        unsafe_allow_html=True,
                    )
            with labels_stats_:
                for label in STATS_LABELS:
                    st.markdown(
                        f"<p style='text-align:center; color:gray; margin:8px 0; font-size:22px;'>{label}</p>",
                        unsafe_allow_html=True,
                    )
            with away_stats_:
                for _, val in away_stats.items():
                    st.markdown(
                        f"<p style='text-align:right; font-weight:800; margin:8px 0; font-size:22px;'>{val}</p>",
                        unsafe_allow_html=True,
                    )

        # AWAY COLUMN
        with stats_away:
            away_attacking_third = plot_team_pitch_third(
                st.session_state.event_data,
                match_data,
                away,
                away_color,
                "right_to_left",
                "offensive",
            )
            away_defensive_third = plot_team_pitch_third(
                st.session_state.event_data,
                match_data,
                away,
                away_color,
                "right_to_left",
                "defensive",
            )
            st.pyplot(away_attacking_third)
            st.pyplot(away_defensive_third)
            show_formation(
                away,
                match_data=match_data,
                event_data=st.session_state.event_data,
                team_color=away_color,
            )


# Tab 1: Pitch Control (Placeholder)
with tabs[1]:
    st.header("Pitch Control Analysis")
    st.info("This feature is under development. Coming soon!")
    st.markdown(
        """
    **Planned Features:**
    - Team possession zones heatmap
    - Dominant areas visualization
    - Territorial control metrics
    """
    )

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
    if match_available():
        selected_team = select_team(home, away)
        if selected_team:
            # select player from team print player name and position logic
            selected_players = get_players_name_(selected_team.name, match_data)
            selected_players = add_position(
                selected_players["names"],
                selected_players["ids"],
                st.session_state.event_data,
            )
            choosed_player = get_player(players=selected_players, team=selected_team)
            show_player_name_pos(
                player=choosed_player, event_data=st.session_state.event_data
            )

            # filtering the event.
            shot_events = get_events(
                choosed_player, "shot", event_data=st.session_state.event_data
            )
            pass_events = get_events(
                choosed_player, "pass", event_data=st.session_state.event_data
            )

            total_passes_count = len(pass_events)
            # starting coordinates for passes
            xs_pass = pass_events["x_start"]
            ys_pass = pass_events["y_start"]
            attacking_side_pass = pass_events["attacking_side"]
            # starting coordinates for shots
            xs_shot = shot_events["x_start"]
            ys_shot = shot_events["y_start"]
            attacking_side_shot = shot_events["attacking_side"]

            radar_, heatmap_, stats_ = st.columns([0.35, 0.45, 0.2])
            with radar_:
                values = get_radar_values(choosed_player)
                plot_radar(
                    metrics=RADAR_METRICS,
                    low=LOWER_BOUNDS,
                    high=UPPER_BOUNDS,
                    values=values,
                )
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
                    <p class="value">{covered_distance(choosed_player, match_data):.2f} km</p>
                    <p class="label">Max speed</p>
                    <p class="value">{max_speed(choosed_player, match_data):.1f} m/s</p>
                    <p class="label">Shots on target</p>
                    <p class="value">{shots_on_target(choosed_player, match_data)}</p>
                </div>
                """,
                    unsafe_allow_html=True,
                )

            plot_1, plot_2, plot_3 = st.columns([0.33, 0.33, 0.33])
            player_events = st.session_state.event_data[
                st.session_state.event_data["player_id"]
                == float(choosed_player.player_id)
            ]

            # Plot 1: Ball Retention
            with plot_1:
                plot_retention(
                    player_events=player_events, player_name=choosed_player.full_name
                )
            with plot_2:
                offensive_events = player_events[
                    player_events["event_subtype"].isin(OFFENSIVE_SUBTYPES)
                ]
                if not offensive_events.empty:
                    plot_offensive_action(
                        offensive_events, player_name=choosed_player.full_name
                    )
                else:
                    st.info("No offensive actions found for this player.")
            with plot_3:
                defensive_events = player_events[
                    player_events["end_type"].isin(DEFENSIVE_END_TYPES)
                ]
                if not defensive_events.empty:
                    plot_defensive_action(
                        defensive_events, player_name=choosed_player.full_name
                    )
                else:
                    st.info("No defensive actions found for this player.")
        else:
            st.warning("None team have been seleected")
    else:
        st.warning("None Match have been seleected")

# Tab 4: Player Performance (Comparison)
with tabs[4]:
    title()
    if match_available():
        # players selection
        col1, col2 = st.columns(2)
        index = 1
        with col1:
            player1 = player_info(index, home, away, match_data)
            index += 1
        with col2:
            player2 = player_info(index, home, away, match_data)

        # Comparison table
        sub_title("Performance Comparison")
        df_comparison = get_comparison_data(player1, player2, match_data)
        st.dataframe(df_comparison, use_container_width=True, hide_index=True)

        # Visualization comparison
        sub_title("Visual Comparison")
        # data for radar charts
        values_player1 = get_radar_values(player1)
        values_player2 = get_radar_values(player2)
        col_radar1, col_radar2 = st.columns(2)
        with col_radar1:
            st.markdown(f"**{player1.full_name}**")
            plot_radar(
                metrics=RADAR_METRICS,
                low=LOWER_BOUNDS,
                high=UPPER_BOUNDS,
                values=values_player1,
            )
        with col_radar2:
            st.markdown(f"**{player2.full_name}**")
            plot_radar(
                metrics=RADAR_METRICS,
                low=LOWER_BOUNDS,
                high=UPPER_BOUNDS,
                values=values_player2,
            )
    else:
        st.info(
            "Please select a match from the sidebar to view player performance comparisons."
        )
# I will come back into this only for amelioration.
