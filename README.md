# FootMetricX Analytics Dashboard

A comprehensive soccer match analytics dashboard built with Streamlit, powered by SkillCorner tracking data and the Kloppy library.

---

## Project Overview

FootMetricX is an interactive analytics platform designed for coaches, analysts, and soccer enthusiasts to explore detailed match data. The dashboard combines:

- **Team Statistics**: Comprehensive team-level metrics at a basic level including shots, passes, defensive actions, and possession analysis
- **Player Profiling**: Individual player performance metrics with radar charts, heatmaps, and pass maps
- **Pitch Control Analysis**: Advanced visualization of team dominance and space control across the pitch
- **Defensive Shape**: Tactical analysis of defensive formations and pressing engagement
- **Performance Comparison**: Side-by-side player comparison with key performance indicators

### Key Features

- Data loading from SkillCorner's open data using Kloppy
- Interactive match selection and player filtering
- Statistical aggregation from tracking and event data
- Radar charts for multidimensional player profiling
- Heatmaps and pass maps for spatial analysis
- Pitch control visualization with frame-by-frame analysis
- Error handling and graceful data loading with user feedback
- Automated test suite with startup validation

---

## Technology Stack

- **Frontend**: Streamlit 1.28.1+ - Interactive web framework
- **Data Processing**: Pandas, NumPy - Data manipulation and analysis
- **Sports Analytics**:
  - Kloppy 0.9.0+ - SkillCorner data loader and event processor
  - mplsoccer - Pitch visualization
- **Visualization**: Plotly, Matplotlib, mplsoccer
- **API Integration**: Requests, BeautifulSoup - GitHub and Wikipedia data retrieval
- **Testing**: Pytest 7.0.0+ - Unit and integration testing

---

## Recent Improvements

### Code Quality & Maintainability

- Removed ~370 lines of unused team-level stat functions from `preset.py`
- Consolidated analytics functions to eliminate code duplication
- Improved code organization for better maintainability

### Bug Fixes & Stability

- Fixed KeyError in player tracking data validation (covered_distance function)
- Fixed ValueError in heatmap contour level plotting for players with few passes
- Added defensive checks for empty DataFrames when accessing player team_id
- Improved error handling and data validation throughout

### UI/UX Enhancements

- Team logos now display with consistent square aspect ratio (equal width/height)
- Enhanced CSS styling with `object-fit: contain` for better logo presentation
- Improved visual consistency across dashboard tabs

## Installation

### Prerequisites

- Python >=3.10.
- pip package manager
- Virtual environment (recommended)

### Setup Steps

1. **Clone the repository**:

   ```bash
   git clone https://github.com/stephTchembeu/analytics_cup_analyst.git
   cd analytics_cup_analyst
   ```

2. **Create a virtual environment** (optional but recommended):

   ```bash
   # On macOS/Linux
   python -m venv venv
   source venv/bin/activate

   # On Windows
   python -m venv venv
   venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

---

## Running the Application

### Start the Dashboard

From the project root directory, run:

```bash
streamlit run src/main.py
```

Or directly from the /src folder run

```bash
streamlit run main.py
```

The application will start and automatically open in your default web browser at `http://localhost:8501`

### Command-line Options

```bash
# Run with specific port
streamlit run src/main.py --server.port 8502

# Run in headless mode (no browser launch)
streamlit run src/main.py --logger.level=debug
```

### What Happens at Startup

1. **Test Validation**: The app automatically runs the test suite to validate core functions
2. **Import Verification**: Checks that all required packages are installed
3. **Data Loading**: Loads available matches from SkillCorner's using Kloppy
4. **UI Initialization**: Sets up dashboard tabs and sidebar controls

---

## Project Structure

```
analytics_cup_analyst/
├── src/
│   ├── main.py                    # Streamlit app entry point (5 tabs)
│   ├── images/                    # Team logos & assets
│   └── utils/
│       ├── preset.py              # Core analytics & visualization functions (~1000 lines)
│       ├── logo_loader.py         # Team logo management via Wikipedia API
│       ├── player_profiling.py    # Player radar charts and heatmaps
│       ├── player_performance.py  # Player comparison metrics
│       └── team_stats.py          # Team-level statistics
├── tests/
│   ├── runner.py                  # Test runner
│   ├── conftest.py                # Pytest fixtures
│   └── test_preset.py             # Unit tests
├── requirements.txt               # Dependencies
├── LICENSE                        # MIT License
└── README.md
```

---

## Usage Guide

### Dashboard Tabs

1. **Team Stats**: High-level team metrics including shots, passes, possession, and defensive actions
2. **Player Profiling**: Individual player performance with radar charts, heatmaps, and spatial pass maps
3. **Player Performance Comparison**: Side-by-side comparison of multiple players with key performance indicators

### Selecting a Match

1. Open the dashboard in your browser at `http://localhost:8501`
2. Use the sidebar dropdown to select an available match
3. The app automatically loads:
   - Match metadata from SkillCorner via Kloppy
   - Event data from GitHub raw content
   - Tracking data for space control and heatmap analysis
4. Explore different tabs to analyze team and player performance

### Player Analysis Features

- **Heatmaps**: Visualize player positioning density across the pitch
- **Pass Maps**: Display all passes from a player with successful/unsuccessful pass indicators
- **Covered Distance**: Track total distance covered during the match
- **Radar Charts**: Compare multiple performance metrics in a single view
- **Performance Metrics**: Goals, assists, pass accuracy, pressures, and more

## Data Sources

### SkillCorner API

The application leverages SkillCorner's open-source released data:

- **Match Metadata & Tracking Data**: Via `kloppy.skillcorner.load_open_data()`
- **Tracking Coordinates**: SkillCorner format with automatic coordinate system handling
- **Player Positions**: Frame-by-frame tracking data for heatmaps and pitch control analysis

### Event Data

Event data is loaded from GitHub's raw content repository:

```
https://raw.githubusercontent.com/SkillCorner/opendata/master/data/matches/{game_id}/{game_id}_dynamic_events.csv
```

Data includes: passes, shots, fouls, clearances, pressures, and other game events.

### Team Logos

Team logos are fetched from Wikipedia API with fallback to local assets:

- Primary: Wikipedia search for official team logos
- Fallback: Local image files in `src/images/`
- Graceful degradation if logo unavailable

### Available Matches

Match IDs are configured in `src/utils/preset.py`:

- `AVAILABLE_MATCHES_IDS`: List of match IDs pre-loaded at startup
- Graceful error handling if a match fails to load
- Dashboard continues with all successfully loaded matches
- User can select from dropdown to switch between matches

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## Acknowledgments

- **SkillCorner**: For providing open-source tracking data.
- **PySport/Kloppy**: For sports data loading and processing library.
- **PySport/KloppyXSkillCorner**: For the launched Hackathon.
- **Streamlit**: For the interactive web framework.
- **mplsoccer**: For football pitch visualization.

---
