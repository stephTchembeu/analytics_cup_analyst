# Copilot Instructions for FootMetricX Analytics Dashboard

## Project Overview
FootMetricX is a Streamlit-based soccer match analytics dashboard that visualizes match data from SkillCorner using the kloppy library. It displays team stats, pitch control, defensive shape, player profiling, and performance metrics.

## Architecture
- **Main Entry**: `src/main.py` - Streamlit app with tabbed interface
- **Data Loading**: Uses `kloppy.skillcorner.load_open_data()` for match metadata and CSV files for dynamic events
- **UI Components**: Custom HTML rendering via `st.markdown(unsafe_allow_html=True)` for logos, scores, and stats
- **Utilities**: `src/utils/preset.py` handles app setup, stats calculations, and team logo fetching; `src/utils/logo_loader.py` fetches logos from Wikipedia API
- **Data Flow**: Match selection → Load kloppy data → Load event CSV → Compute stats from events → Render tabs

## Key Patterns
- **State Management**: Use `st.session_state` for match selection and cached data (e.g., `st.session_state.event_data`)
- **Stats Computation**: Functions like `shots(team)`, `passess(team)`, `clearances(team)`, `fouls_committed(team)` filter `st.session_state.event_data` by team_id and event types (e.g., `end_type` == "shot")
- **Logo Rendering**: `render_team_logo()` uses Wikipedia API or fallback image; align with "left"/"right" for home/away
- **Styling**: Inline CSS in `st.markdown()` for centered scores, colored tabs (green: #217c23, blue: #052B72)
- **Hardcoded Values**: Possession defaults to 50%; available matches in `AVAILABLE_MATCHES_IDS` list

## Workflows
- **Run App**: `streamlit run src/main.py` (from project root)
- **Install Dependencies**: `pip install -r requirements.txt`
- **Data Sources**: Match IDs from SkillCorner opendata; events CSV from GitHub raw URLs
- **Dependencies**: Listed in `requirements.txt`; install with pip

## Conventions
- **Imports**: All imports in `src/main.py`; use `from src.utils.preset import ...` for utilities
- **File Paths**: Images in `src/images/`, data in `src/data/`
- **Event Filtering**: Use `end_type` for shots/passes, `team_id` for team-specific data
- **Player Data**: Access via `match_data.metadata.teams[0].players` for full names

## Integration Points
- **SkillCorner API**: Via kloppy for match metadata; coordinates="skillcorner"
- **Wikipedia API**: For team logos; handles approximate names
- **GitHub Raw**: For event CSVs; URL pattern: `https://raw.githubusercontent.com/SkillCorner/opendata/master/data/matches/{game_id}/{game_id}_dynamic_events.csv`

Reference: `src/utils/preset.py` for stats logic, `src/main.py` for UI structure.