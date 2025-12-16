import os
import base64
import pandas as pd
import streamlit as st
from kloppy import skillcorner

from utils.logo_loader import get_team_logo_url ,FALLBACK_LOGO


# Function
def render_team_logo(team_name, align="left", width=100):
    logo_url = get_team_logo_url(team_name)

    if logo_url:
        img_html = f'<img src="{logo_url}" width="{width}"/>'
    elif os.path.exists(FALLBACK_LOGO):
        encoded = base64.b64encode(open(FALLBACK_LOGO, "rb").read()).decode()
        img_html = f'<img src="data:image/png;base64,{encoded}" width="{width}"/>'
    else:
        st.error("No logo found")
        return

    st.markdown(
        f"""
        <div style="text-align: {align};">
            {img_html}
            <p style="font-size: 0.8rem; margin-top: 0.3rem; ">
                {team_name.title()}
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def get_teams_in_matches(available_matches_ids: list) -> list:
    """
    function to import assets of the name of home and away team from the list of available id
    input:
        available_matches_id: the list of available matches id's.
    output:
        the list of (home_name,away_name).
    """
    output = []
    for match_id in available_matches_ids:
        dataset = skillcorner.load_open_data(
            match_id=match_id, coordinates="skillcorner", limit=2
        )
        home, away = dataset.metadata.teams
        output.append(
            (home.name, away.name,match_id)
        )
    return output


def preset_app():
    """
    A function to preset unchangeable elemet of the dashboard the logo the elements within the tab.
    """
    # set title and icon
    st.set_page_config(
        page_title="FootMetricX",
        page_icon=SIMPLE_LOGO,
        layout="wide",
        initial_sidebar_state="auto",
    )

    # set our logo
    st.logo(LOGO_OPTIONS[1], icon_image=LOGO_OPTIONS[0])  # sidebar.

    # set the central logo
    image_path = LOGO_WITH_TEXT
    with open(image_path, "rb") as file:
        data = base64.b64encode(file.read()).decode()
    st.markdown(
        f"""
    <div style="margin-top:-30px; text-align:left;    ">
        <img src="data:image/png;base64,{data}" style="width:250px; ">
    </div>
    """,
        unsafe_allow_html=True,
    )

    # Sidebar choosing a match
    st.sidebar.markdown(
        f"<h2 style='color: {COLOR_PALETTE['blue']}; font-size: 25px; padding: 0rem 0px; padding-top:0.5rem;'>Choose a match.</h2>",
        unsafe_allow_html=True,
    )  # we set the title of the upload section
    st.session_state.selected_match = st.sidebar.selectbox(
        "Available Matches.", options=AVAILABLE_MATCHES
    )
    st.session_state.selected_match_id = first_word(st.session_state.selected_match)
    
    st.markdown(
        f"""
    <style>
    .stTabs [data-baseweb="tab"] {{
        color: #000;
    }}
    .stTabs [data-baseweb="tab"]:hover {{
        color: {COLOR_PALETTE["green"]};
    }}
    .stTabs [data-baseweb="tab"][aria-selected="true"] {{
        color: {COLOR_PALETTE["green"]} !important;
    }}
    </style>
    """,
        unsafe_allow_html=True,
    )

    st.markdown(
        f"""
    <style>
    .stTabs [aria-selected="true"] {{
        border-bottom: 3px solid {COLOR_PALETTE["green"]} !important;
    }}
    .stTabs [data-baseweb="tab"] {{
        border-bottom: 3px solid transparent !important;
    }}
    </style>
    """,
        unsafe_allow_html=True,
    )
    return

def first_word(string):
    """
    Splits the string into words using a space as the separator
    and returns the first word.
    """
    words = string.split(" ")
    if words:
        return words[0]
    return ""  # Returns an empty string if the input string is empty

def shots(team):
    # Filter shots
    shots = st.session_state.event_data[st.session_state.event_data['end_type'].str.lower() == "shot"].copy()
    shots['is_on_target'] = (
        (shots['lead_to_goal'] == 1) &
        (shots['game_interruption_after'].isin(['goal_for', 'corner_for']))
    )
    shots['is_on_target'] = shots['is_on_target'].astype('boolean')
    team_shots = shots[shots["team_id"] == team.team_id]
    total = len(team_shots)
    targeted = team_shots['is_on_target'].sum()
    return (total,targeted)

def passess(team):
    pass_df= st.session_state.event_data[st.session_state.event_data['end_type'].str.lower() == "pass"].copy()
    total_pass = pass_df[(pass_df["team_id"] == team.team_id)]
    good_pass = pass_df[(pass_df["team_id"] == team.team_id) & (pass_df["pass_outcome"]== "successful")]
    return (len(total_pass),len(good_pass))

def pass_accuracy(team):
    _passess = passess(team)
    return int(_passess[1]*100/_passess[0])

def possession(team):
    posses = 50
    return posses

def get_stats(team):
    stats = {
            "shots":f"{shots(team)[0]}[{shots(team)[1]}]",
            "possession":f"{possession(team)}%",
            "passes":f"{passess(team)[0]}[{passess(team)[1]}]",
            "passes_accuracy":f"{pass_accuracy(team)}%",
            }
    return stats


# variables
SIMPLE_LOGO = "./images/logo.png"  # logo when no side =bar
LOGO_WITH_TEXT = "./images/logo_with_text.png"  # central logo and siderbar logo
AVAILABLE_MATCHES_IDS = [
    1886347,
]
LOGO_OPTIONS = (SIMPLE_LOGO, LOGO_WITH_TEXT)
TAB_NAMES = (
    "team_stats",
    "pitch_control",
    "defensive shape",
    "player_profilling",
    "player_performance",
)
COLOR_PALETTE = {"blue": "#052B72", "green": "#217c23"}  # color palette.
AVAILABLE_MATCHES = [
    f"{x[2]} {x[0]} - {x[1]}" for x in get_teams_in_matches(AVAILABLE_MATCHES_IDS)
]
STATS_LABELS = [
            "Shots off target [Shots on target]",
            "Possession",
            "Total passes[succeed pass]",
            "Pass accuracy percentage",
        ]