# initialize an app just by running the python file with streamlit
from main_app_requirement import *
from utils.preset import preset_app,render_team_logo,get_stats,TAB_NAMES,STATS_LABELS

# define decorative elements
preset_app()

# Main tabs
tabs = st.tabs(TAB_NAMES)

# data_of_the_selected_match
match_data = skillcorner.load_open_data(
    match_id= st.session_state.selected_match_id,
    coordinates="skillcorner",
    )

@st.cache_data
def load_event_data(game_id):
    url = (
        f"https://raw.githubusercontent.com/SkillCorner/opendata/master/data/matches/{game_id}/{game_id}_dynamic_events.csv"
    )
    return pd.read_csv(url)

st.session_state.event_data = load_event_data(match_data.metadata.game_id)

home,away = match_data.metadata.teams

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
            for _,val in home_stats.items():
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
            for _,val in away_stats.items():
                st.markdown(
                    f"<p style='text-align:left; font-weight:800; margin:8px 0;'>{val}</p>",
                    unsafe_allow_html=True,
                )
    

    # player profiling
    with tabs[4]:
        if st.session_state.selected_match:
            st.write("data accessible")
        