# FootMetricX Analytics Dashboard

A comprehensive soccer match analytics dashboard built with Streamlit, powered by SkillCorner tracking data and the Kloppy library. FootMetricX provides real-time insights into team performance, player metrics, and advanced pitch control analysis.

---

## Project Overview

FootMetricX is an interactive analytics platform designed for coaches, analysts, and soccer enthusiasts to explore detailed match data. The dashboard combines:

- **Team Statistics**: Comprehensive team-level metrics including shots, passes, defensive actions, and possession analysis
- **Player Profiling**: Individual player performance metrics with radar charts, heatmaps, and pass maps
- **Pitch Control Analysis**: Advanced visualization of team dominance and space control across the pitch
- **Defensive Shape**: Tactical analysis of defensive formations and pressing engagement
- **Performance Comparison**: Side-by-side player comparison with key performance indicators

### Key Features

- Real-time data loading from SkillCorner's open API
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
  - Kloppy 0.9.0 - SkillCorner data loader and event processor
  - mplsoccer - Pitch visualization
- **Visualization**: Plotly, Matplotlib, Mplsoccer
- **API Integration**: Requests - GitHub raw data retrieval
- **Testing**: Pytest 7.0.0+ - Unit and integration testing

---

## Installation

### Prerequisites

- Python 3.10 or higher
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
3. **Data Loading**: Loads available matches from SkillCorner's open data API
4. **UI Initialization**: Sets up dashboard tabs and sidebar controls

---

## Project Structure

```
analytics_cup_analyst/
├── src/
│   ├── main.py                 # Main Streamlit application entry point
│   ├── __init__.py
│   ├── utils/
│   │   ├── preset.py           # Core analytics functions and UI setup
│   │   ├── logo_loader.py      # Team logo fetching from Wikipedia
│   │   ├── pitch_control.py    # Advanced pitch control calculations
│   │   └── __init__.py
│   ├── data/
│   │   ├── test.ipynb          # Development notebook for testing
│   │   └── 1886347_dynamic_events.csv  # Sample event data
│   └── images/                 # Logo and branding assets
├── tests/
│   ├── __init__.py
│   ├── conftest.py            # Pytest fixtures and mock data factories
│   ├── test_preset.py         # Unit tests for analytics functions
│   ├── test_pitch_control.py  # Tests for pitch control module
│   └── runner.py              # Test execution utility
├── .github/
│   └── copilot-instructions.md # AI agent guidelines
├── requirements.txt            # Python package dependencies
├── README.md                   # This file
└── LICENSE
```

---

## Usage Guide

### Selecting a Match

1. Open the dashboard in your browser
2. Use the sidebar dropdown to select an available match
3. Watch the status messages as the app loads:
   - Success message if all matches load
   - Warning message if some matches fail (app continues with available)
4. Select tabs to explore different analytics views

### Viewing Team Statistics

The **Team Stats** tab displays:

- Match score and team logos
- Key statistics: shots, passes, pass accuracy, clearances, fouls, and more
- Side-by-side comparison for home and away teams
- Real-time calculations from event data

### Player Profiling

The **Player Profiling** tab includes:

- Player selection by team
- 7-metric radar chart showing:
  - Shots and on-target accuracy
  - Offensive actions percentage
  - Defensive action frequency
  - Ball retention time
  - Forward pass percentage
  - Pressing engagement metrics
- Heatmap of player positioning and activity
- Pass map showing pass completion rates
- Individual player statistics

### Pitch Control Analysis

Analyze team dominance across the pitch:

- Frame-by-frame pitch control visualization
- Zone-based control breakdown (defensive, middle, attacking thirds)
- Interactive player movement simulation
- Space creation impact analysis

### Defensive Shape Analysis

Explore team defensive structure:

- Defensive line positioning
- Compactness metrics
- Pressing intensity zones

---

## Data Sources

### SkillCorner API

The application leverages SkillCorner's open data API:

- Match metadata and tracking data via `kloppy.skillcorner.load_open_data()`
- Coordinate system: SkillCorner normalized (pitch_length=105m, pitch_width=68m)
- Frame rate: 25 fps

### GitHub Raw Content

Event data is loaded from:

```
https://raw.githubusercontent.com/SkillCorner/opendata/master/data/matches/{game_id}/{game_id}_dynamic_events.csv
```

### Available Matches

Configured in `src/utils/preset.py`:

- `AVAILABLE_MATCHES_IDS`: List of match IDs loaded at startup
- Graceful error handling if a match fails to load
- App continues with all successfully loaded matches

---

## Core Functions

### Team Statistics (`src/utils/preset.py`)

| Function                    | Purpose                      |
| --------------------------- | ---------------------------- |
| `shots(team)`               | Total and on-target shots    |
| `passess(team)`             | Total and successful passes  |
| `pass_accuracy(team)`       | Pass completion percentage   |
| `possession(team)`          | Ball possession percentage   |
| `clearances(team)`          | Defensive clearance count    |
| `fouls_committed(team)`     | Foul statistics              |
| `offensive_action(team)`    | Offensive action frequency   |
| `pressing_engagement(team)` | Pressing metrics             |
| `direct_disruptions(team)`  | Direct defensive disruptions |
| `direct_regains(team)`      | Direct ball regains          |
| `possession_losses(team)`   | Possession loss count        |

### Player Metrics

| Function                               | Purpose                      | Returns |
| -------------------------------------- | ---------------------------- | ------- |
| `shots_on_target(player, match_data)`  | On-target shot count         | int     |
| `expected_goals(player, match_data)`   | xG calculation               | float   |
| `expected_threat(player, match_data)`  | xT calculation               | float   |
| `covered_distance(player, match_data)` | Total distance in kilometers | float   |
| `max_speed(player, match_data)`        | Maximum recorded speed (m/s) | float   |
| `avg_forward_pass(player_id)`          | Forward pass percentage      | float   |

### Visualizations

| Function                         | Purpose                            |
| -------------------------------- | ---------------------------------- |
| `heatmap(xs, ys)`                | Kernel density estimation heatmap  |
| `pass_map(player_id)`            | Pass success/failure visualization |
| `plot_radar(metrics, low, high)` | Multidimensional radar chart       |
| `plot_pitch_control(grid)`       | Pitch control heatmap              |

### UI Components

| Function                                  | Purpose                                |
| ----------------------------------------- | -------------------------------------- |
| `preset_app()`                            | Initialize page config, logos, sidebar |
| `render_team_logo(team_name, align)`      | Fetch and display team logo            |
| `get_stats(team)`                         | Return formatted stats dictionary      |
| `get_players_name(team_name, match_data)` | Get list of player names               |

---

## Testing

The project includes a comprehensive test suite run automatically at startup:

### Test Categories

1. **Team Stats Functions** (8 tests)

   - shots, passes, pass accuracy
   - clearances, fouls, defensive metrics
   - stats aggregation

2. **Player Stats Functions** (4 tests)

   - shots on target
   - expected goals and threat
   - forward pass metrics

3. **Utility Functions** (3 tests)

   - first_word extraction
   - player name retrieval
   - empty team handling

4. **Data Validation** (2 tests)

   - empty event data handling
   - sample data structure validation

5. **Pitch Control** (7 tests)
   - module import verification
   - visualization functions
   - space control metrics

### Running Tests Manually

```bash
# Run all tests
pytest tests/

# Run specific test file
pytest tests/test_preset.py -v

# Run with coverage
pytest tests/ --cov=src --cov-report=html

# Run single test class
pytest tests/test_preset.py::TestTeamStatsFunctions -v
```

### Test Results

- **18+ tests passing** at startup
- Tests validate all analytics functions
- Mock fixtures for SkillCorner data
- Edge case coverage

---

## Configuration

### App Settings

Edit `src/utils/preset.py` to customize:

- `AVAILABLE_MATCHES_IDS`: List of match IDs to load
- `COLOR_PALETTE`: Custom color scheme for visualizations
  - `green`: Primary highlight color (default: #217c23)
  - `blue`: Secondary color (default: #052B72)
- `TAB_NAMES`: Dashboard tab titles and order
- `STATS_LABELS`: Displayed statistics labels

### Streamlit Configuration

Create `.streamlit/config.toml` for advanced options:

```toml
[theme]
primaryColor = "#217c23"
backgroundColor = "#FFFFFF"
secondaryBackgroundColor = "#f0f2f6"

[client]
showErrorDetails = true

[server]
maxUploadSize = 200
```

---

## Error Handling

### Match Loading

The application includes robust error handling:

- **Success Message**: All matches loaded successfully
- **Warning Message**: Some matches failed, continuing with available
- **Graceful Degradation**: App remains functional with loaded matches

### Data Validation

- Division-by-zero protection in calculations
- Empty DataFrame handling
- Type checking and conversion
- Missing data fallbacks

---

## Troubleshooting

### Common Issues

**Issue**: "No such file or directory: ./src/images/..."

- **Solution**: Run the app from project root: `streamlit run src/main.py`

**Issue**: "ModuleNotFoundError: No module named 'kloppy'"

- **Solution**: Install dependencies: `pip install -r requirements.txt`

**Issue**: Match loading fails with warning

- **Solution**: Check internet connection. The app continues with available matches.

**Issue**: Jupyter notebook won't run

- **Solution**: Install Jupyter: `pip install jupyter`

**Issue**: Test suite fails at startup

- **Solution**: Tests are validation only. Review warnings but app continues normally.

---

## API Reference

### Key Imports

```python
# Analytics functions
from utils.preset import (
    shots, passess, pass_accuracy, possession,
    clearances, fouls_committed, get_stats,
    heatmap, pass_map, plot_radar,
    shots_on_target, expected_goals, expected_threat,
    covered_distance, max_speed
)

# Pitch control
from utils.pitch_control import (
    calculate_pitch_control,
    calculate_space_control_metrics,
    get_frame_positions,
    plot_pitch_control
)

# UI components
from utils.logo_loader import render_team_logo
from utils.preset import preset_app, get_players_name
```

### Data Structures

**Event Data (pandas DataFrame)**:

```python
columns: [
    'player_id', 'team_id', 'end_type', 'pass_outcome',
    'pass_direction', 'duration', 'ball_state',
    'game_interruption_after', 'lead_to_goal', ...
]
```

**Match Data (kloppy TrackingDataset)**:

```python
match_data.metadata.teams  # [home_team, away_team]
match_data.metadata.game_id  # Match identifier
match_data.metadata.coordinate_system.pitch_length  # 105
match_data.metadata.coordinate_system.pitch_width  # 68
match_data.metadata.frame_rate  # 25 fps
```

---

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Commit changes: `git commit -m "Add feature"`
4. Push to branch: `git push origin feature-name`
5. Submit a pull request

---

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## Acknowledgments

- **SkillCorner**: For providing open-source tracking data
- **PySport/Kloppy**: For sports data loading and processing library
- **Streamlit**: For the interactive web framework
- **mplsoccer**: For football pitch visualization

---

## Contact & Support

For questions or support:

- Open an issue on GitHub
- Check the [Copilot Instructions](.github/copilot-instructions.md) for AI agent guidelines

---

## Changelog

### Version 1.0.0 (Current)

- Initial release
- Team statistics dashboard with 11+ metrics
- Player profiling with radar charts, heatmaps, pass maps
- Pitch control analysis with frame-by-frame visualization
- Defensive shape analysis tools
- Automated test suite (18+ tests)
- Error handling with graceful degradation
- Match loading with success/warning feedback
