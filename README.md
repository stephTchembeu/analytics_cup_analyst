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
  - Kloppy 0.9.0 - SkillCorner data loader and event processor
  - mplsoccer - Pitch visualization
- **Visualization**: Plotly, Matplotlib, Mplsoccer
- **API Integration**: Requests - GitHub raw data retrieval
- **Testing**: Pytest 7.0.0+ - Unit and integration testing

---

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

---

## Data Sources

### SkillCorner API

The application leverages SkillCorner's open released data:

- Match metadata and tracking data via `kloppy.skillcorner.load_open_data()`

### SkillCorner's event data raw content

Event data is loaded into pd.DataFrame from:

```
https://raw.githubusercontent.com/SkillCorner/opendata/master/data/matches/{game_id}/{game_id}_dynamic_events.csv
```

### Available Matches

Configured in `src/utils/preset.py`:

- `AVAILABLE_MATCHES_IDS`: List of match IDs loaded at startup
- Graceful error handling if a match fails to load
- App continues with all successfully loaded matches


---

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

