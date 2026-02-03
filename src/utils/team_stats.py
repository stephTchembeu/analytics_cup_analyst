from typing import List
from utils.player_profiling import get_position,get_player_name_from_event
import streamlit as st
import mplsoccer
st.write(mplsoccer.__version__)

from mplsoccer.pitch import VerticalPitch

import pandas as pd
import numpy as np
import plotly.express as px
import matplotlib.colors as mcolors
from kloppy.domain import Team,TrackingDataset
from collections import defaultdict
from mplsoccer import Pitch
from matplotlib.patches import Rectangle
import matplotlib.pyplot as plt



def plot_formation(
    title: str,
    df_players: pd.DataFrame,
    player_color: str = "#1f77b4",
    pitch_type: str = "skillcorner",
    pitch_color="#d5dee7",
    pitch_alpha=0.2,
    line_color: str = "gray",
    pitch_length: float = 105,
    pitch_width: float = 68
):
    """
    Plot a vertical football formation on a pitch with SkillCorner-centered coordinates.

    Parameters:
    - title: str, title of the plot
    - df_players: pd.DataFrame with ["id","name","jersey_no","position"]
    - player_color: str, color of player circle
    - pitch_type: str, pitch type supported by mplsoccer
    - pitch_color: str, pitch background color
    - pitch_alpha: float, pitch alpha
    - line_color: str, color of pitch lines
    - pitch_length: float, pitch length in meters
    - pitch_width: float, pitch width in meters
    """
    position_ofset = 30
    # Pitch background color with alpha
    pitch_rgba = mcolors.to_rgba(pitch_color, alpha=pitch_alpha)

    # Vertical pitch
    pitch = VerticalPitch(
        pitch_type=pitch_type,
        pitch_color=pitch_rgba,
        line_color=line_color,
        pitch_length=pitch_length,
        pitch_width=pitch_width
    )
    
    fig, ax = pitch.draw(figsize=(3, 7))
    ax.set_title(
        title,
        fontsize=8,
        fontweight="bold",
        pad=1,
        loc="center"
    )
    scatter_objects = []
    metadata = []

    # ---------- Group players by position ----------
    position_groups = defaultdict(list)
    for idx, player in df_players.iterrows():
        position_groups[player["position"].upper()].append(idx)

    position_counters = defaultdict(int)
    for _, player in df_players.iterrows():
        pos = player["position"].upper()
        if pos not in POSITION_COORDS_H:
            continue

        x_h, y_h = POSITION_COORDS_H[pos]

        # Convert to SkillCorner-centered coordinates
        x_sc = x_h / 120 * pitch_length - pitch_length / 2
        y_sc = y_h / 80 * pitch_width - pitch_width / 2

        # Vertical pitch swap
        x_v = y_sc
        y_v = x_sc

        # ---------- Handle duplicate positions ----------
        count = len(position_groups[pos])
        idx_in_pos = position_counters[pos]

        if count > 1:
            offset_index = idx_in_pos - (count - 1) / 2
            x_v += offset_index * position_ofset

        position_counters[pos] += 1

        # Player circle
        sc = ax.scatter(
            x_v,
            y_v,
            s=200,
            color=player_color,
            edgecolors="#7D7E7D",
            linewidth=1,
            zorder=3,
        )

        # Jersey number inside circle
        ax.text(
            x_v,
            y_v,
            str(player["jersey_no"]),
            ha="center",
            va="center",
            color="white",
            fontsize=8,
            fontweight="bold",
            zorder=4,
        )

        # Position above
        ax.text(
            x_v,
            y_v + 4,
            player["position"],
            ha="center",
            va="bottom",
            color="black",
            fontsize=7,
            fontweight="normal",
            zorder=5,
        )

        # Name below
        ax.text(
            x_v,
            y_v - 4,
            player["name"],
            ha="center",
            va="top",
            color="black",
            fontsize=6,
            fontweight="normal",
            zorder=5,
        )

        scatter_objects.append(sc)
        metadata.append(player)
    st.pyplot(fig)

def show_formation(team:Team,match_data,event_data,team_color="#1f77b4"):
    title = f"starting XI" 
    team_players = get_players_of(match_data,team,frame_number=0)
    df_players = pd.DataFrame(fetch_player_data(event_data,team_players))

    plot_formation(
        title,
        df_players,
        player_color=team_color,
        pitch_length=match_data.metadata.coordinate_system.pitch_length,
        pitch_width=match_data.metadata.coordinate_system.pitch_width,
    )

def plot_momentum_chart_plotly(
    events: pd.DataFrame,
    home_team_id: int,
    away_team_id: int,
    home_team_name: str = "Home",
    away_team_name: str = "Away",
    home_color: str = "#0F12D6",
    away_color: str = "#C9B36A",
    rolling_window: int = 5,
):
    """
    Interactive momentum (tug-of-war) chart with goal info using Plotly.
    """

    events = events.copy()

    # ----------------- Minute handling -----------------
    if "minute_start" in events.columns:
        events["minute"] = events["minute_start"]
    elif "timestamp" in events.columns:
        events["minute"] = (events["timestamp"] / 60).astype(int)
    else:
        st.warning("No time information found.")
        return

    max_min = int(events["minute"].max())
    minute_grid = np.arange(0, max_min + 1)

    # ----------------- Momentum calculation -----------------
    def calc_score(team_events: pd.DataFrame):
        shots = (team_events["end_type"] == "shot").sum()
        passes = (team_events["end_type"] == "pass").sum()
        return shots*3 + (passes * 0.05)

    momentum = []
    for m in minute_grid:
        min_events = events[events["minute"] == m]
        home_score = calc_score(min_events[min_events["team_id"] == home_team_id])
        away_score = calc_score(min_events[min_events["team_id"] == away_team_id])
        momentum.append(home_score - away_score)

    momentum_series = (
        pd.Series(momentum)
        .rolling(window=rolling_window, center=True, min_periods=1)
        .mean()
    )

    momentum_df = pd.DataFrame({
        "minute": minute_grid,
        "momentum": momentum_series,
        "team": np.where(momentum_series >= 0, home_team_name, away_team_name)
    })

    # ----------------- Goal events -----------------
    goals = events[
        (events["end_type"] == "shot") & (events["lead_to_goal"] == True)
    ].copy()

    if not goals.empty:
        goals["team"] = goals["team_id"].map({
            home_team_id: home_team_name,
            away_team_id: away_team_name
        })

        goals["y"] = goals["minute"].apply(
            lambda m: momentum_series.iloc[int(m)]
            if int(m) < len(momentum_series)
            else 0
        )

        player_names = (
            goals["player_name"]
            if "player_name" in goals.columns
            else pd.Series(["Unknown"] * len(goals), index=goals.index)
        )

    else:
        goals = pd.DataFrame(columns=["minute", "team", "y"])
        player_names = pd.Series(dtype=str)
        

    # ----------------- Plotly bar chart -----------------
    fig = px.bar(
    momentum_df,
    x="minute",
    y="momentum",
    color="team",
    color_discrete_map={home_team_name: home_color, away_team_name: away_color},
    title="Full Match Momentum",
    labels={"minute": "Minute", "momentum": "Momentum"},
    )

    # Center the title
    fig.update_layout(title_x=0.5)

    # ----------------- Add goal markers -----------------
    if not goals.empty:
        fig.add_scatter(
            x=goals["minute"],
            y=goals["y"],
            mode="text",
            text=["⚽"] * len(goals),  
            textfont=dict(size=15),    
            name="Goals",
            hovertemplate=
                "<b>Goal</b><br>"
                "Minute: %{x}'<br>"
                "Player: %{customdata[0]}<br>"
                "Team: %{customdata[1]}<br>",
            customdata=np.stack([
                player_names.values,
                goals["team"].values,
            ], axis=-1)
        )



    fig.update_layout(
        template="plotly_white",
        bargap=0,
        hovermode="x unified",
        yaxis=dict(zeroline=True),
    )

    return fig

def plot_team_pitch_third(events: pd.DataFrame,
                          match_data,
                          team,
                          team_color: str = "#0F12D6",
                          attacking_direction: str = "left_to_right",
                          type_="offensive",period=1):
    """
    Plot a single SkillCorner-style pitch (centered at 0,0) showing the % of passes+shots per third.
    Adds an arrow showing attacking direction.
    Returns a matplotlib figure for Streamlit.
    """
    pitch_length = match_data.metadata.coordinate_system.pitch_length
    pitch_width = match_data.metadata.coordinate_system.pitch_width
    third = pitch_length / 3
    
    # Filter events for this team
    if type_ == "offensive":
        events = events[(((events['end_type'].isin(['pass','shot'])) | 
                        (events["event_subtype"].isin([
                            "coming_short", "run_ahead_of_the_ball", "behind", "dropping_off", "pulling_wide",
                            "pulling_half_space", "overlap", "underlap", "support", "cross_receiver"
                        ]))))&(events["period"].astype(int) == int(period))].copy()
    elif type_ == "defensive":
        events = events[(events["event_subtype"].isin([
            "pressing","presure","recovery_press","indirect_disruption","indirect_regain",
            "direct_regain","direct_disruption","possession_loss","foul_committed","clearance"
        ]))&(events["period"].astype(int) == int(period))].copy()
        
    if (team.ground.name == "AWAY")&(period==1):
        attacking_direction = "left_to_right" 
    elif (team.ground.name == "AWAY")&(period==2):
        attacking_direction = "right_to_left"
    elif (team.ground.name == "HOME")&(period==1):
        attacking_direction = "right_to_left"
    elif (team.ground.name == "HOME")&(period==2):
        attacking_direction = "left_to_right"

    team_events = events[events['team_id'] == team.team_id]
    
    # Convert centered coordinates to 0 → pitch_length for calculation
    x = team_events['x_start'] + pitch_length/2
    
    # Define thirds based on attacking direction
    if attacking_direction == 'left_to_right':
        thirds = {
            "Defensive": (0, third),
            "Midfield": (third, 2*third),
            "Attacking": (2*third, pitch_length)
        }
    else:  # right->left
        thirds = {
            "Attacking": (0, third),
            "Midfield": (third, 2*third),
            "Defensive": (2*third, pitch_length)
        }
    
    # Count % of events per third
    counts = {name: np.sum((x >= x_min) & (x < x_max)) for name, (x_min, x_max) in thirds.items()}
    total = sum(counts.values())
    percentages = {k: 100*v/total if total>0 else 0 for k,v in counts.items()}
    
    # Map percentages to alpha
    min_alpha, max_alpha = 0.1, 0.5
    max_val = max(percentages.values()) if len(percentages) > 0 else 0
    alphas = {k: min_alpha + (v/max_val)*(max_alpha - min_alpha) if max_val > 0 else min_alpha
              for k,v in percentages.items()}
    
    # Draw pitch
    fig, ax = plt.subplots(figsize=(7,6))
    pitch = Pitch(pitch_type='skillcorner', pitch_length=pitch_length, pitch_width=pitch_width, 
                  pitch_color='white', line_color='gray', positional=False)
    pitch.draw(ax=ax)
    
    # Draw thirds
    for name, (x_min, x_max) in thirds.items():
        ax.add_patch(Rectangle(
            (x_min - pitch_length/2, -pitch_width/2),
            x_max - x_min,
            pitch_width,
            color=team_color,
            alpha=alphas[name],
            zorder=1
        ))
        # percentage label
        ax.text(
            (x_min+x_max)/2 - pitch_length/2,
            0,
            f"{percentages[name]:.1f}%",
            color='black',
            fontsize=26,
            ha='center',
            va='center',
            weight='bold'
        )
    
    # X-axis labels
    xtick_positions = [-pitch_length/2 + third/2, 0, pitch_length/2 - third/2]
    xtick_labels = ["Defensive","Midfield","Attacking"] if attacking_direction == "left_to_right" else ["Attacking","Midfield","Defensive"]
    ax.set_xticks(xtick_positions)
    ax.set_xticklabels(xtick_labels, fontsize=12, weight='bold')
    ax.tick_params(axis='x', length=5)
    ax.set_yticks([])
    
    # Title
    periods=  {1:"first",2:"second"}
    title = f"Attacking behavior {periods[period]} half" if type_ == "offensive" else f"Defensive behavior {periods[period]} half"
    ax.set_title(title, fontsize=24,weight='bold')
    
    # ---- Attacking direction arrow ----
    arrow_y = arrow_y = pitch_width / 2 - 6
    arrow_length = pitch_length * 0.20

    if attacking_direction == "left_to_right":
        start_x, end_x = -arrow_length/2, arrow_length/2
    else:
        start_x, end_x = arrow_length/2, -arrow_length/2

    ax.annotate(
        "",
        xy=(end_x, arrow_y),
        xytext=(start_x, arrow_y),
        arrowprops=dict(arrowstyle="->", color="black", lw=5),
        zorder=5
    )

    plt.tight_layout()
    return fig

def get_players_of(data:TrackingDataset,target_team:Team,frame_number:int):
    player_list = []
    for player in data.frames[frame_number].players_coordinates.keys():
        if str(player.team.name) == str(target_team.name):
            player_list.append(player)
    return player_list

def fetch_player_data(event_data:pd.DataFrame,list_players:List):
    players_coordinates = {
        "id":[],
        "jersey_no":[],
        "name":[],
        "position":[]
    }

    for player in list_players:
        players_coordinates["jersey_no"].append(player.jersey_no)
        players_coordinates["name"].append(get_player_name_from_event(player.player_id,event_data))
        players_coordinates["id"].append(player.player_id)
        players_coordinates["position"].append(get_position(player.player_id,event_data))
    return players_coordinates

POSITION_COORDS_H = {

# =================================================
# Goalkeeper
# =================================================
"GK": (10, 40),

# =================================================
# Defensive line
# =================================================
"RB": (30, 10),
"RCB": (30, 30),
"CB": (30, 40),
"LCB": (30, 50),
"LB": (30, 70),

"RWB": (35, 20),
"LWB": (35, 60),

"RCB-FB": (28, 30),
"LCB-FB": (28, 50),

# =================================================
# Defensive Midfielders (UNDER middle line)
# Middle line ≈ x = 60
# =================================================
"DM": (52, 40),
"CDM": (52, 40),

"RDM": (52, 17),
"LDM": (52, 62),

"CDMF": (52, 40),

# =================================================
# Central / Neutral Midfielders (ON middle line)
# =================================================
"CM": (60, 40),
"RCM": (60, 30),
"LCM": (60, 50),

"CMR": (60, 30),
"CML": (60, 50),

# Hybrid roles
"RWB-CM": (58, 22),
"LWB-CM": (58, 58),

# =================================================
# Attacking Midfielders (IN FRONT of middle line)
# =================================================
"AM": (72, 40),
"CAM": (72, 40),

"RAM": (72, 30),
"LAM": (72, 50),

"RAMF": (72, 32),
"LAMF": (72, 48),

# =================================================
# Wide attackers / wingers
# =================================================
"RW": (85, 15),
"LW": (85, 65),

"RW-F": (88, 25),
"LW-F": (88, 55),

"RIF": (88, 28),
"LIF": (88, 52),

"RF": (92, 30),
"LF": (92, 50),

# =================================================
# Forwards / Strikers
# =================================================
"CF": (105, 40),
"ST": (115, 40),

"RS": (115, 35),
"LS": (115, 45),
}