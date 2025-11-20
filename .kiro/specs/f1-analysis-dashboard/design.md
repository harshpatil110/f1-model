# F1 Analysis Dashboard - Design Document

## Overview

The F1 Analysis Dashboard is a full-stack Python application built with Streamlit that provides comprehensive Formula One race data analysis. The system leverages the FastF1 API to retrieve telemetry, timing, and session data, processes it through specialized analysis modules, and presents insights through interactive visualizations.

### Architecture Philosophy

- **Modular Backend**: Separation of concerns with dedicated modules for data loading, analysis, comparison, strategy, and ML
- **Caching Strategy**: Aggressive caching at multiple levels to minimize API calls and improve performance
- **Stateful Frontend**: Streamlit session state management for seamless multi-page navigation
- **Visualization-First**: Rich, interactive plots using Plotly and Matplotlib with team color consistency

## Architecture

### High-Level System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Streamlit Frontend (app.py)               │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   │
│  │   Home   │  │  Driver  │  │Telemetry │  │ Strategy │   │
│  │   Page   │  │ Analysis │  │   Page   │  │   Page   │   │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘   │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                      Backend Modules                         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │ data_loader  │  │   analysis   │  │   compare    │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
│  ┌──────────────┐  ┌──────────────┐                        │
│  │   strategy   │  │   ml_model   │                        │
│  └──────────────┘  └──────────────┘                        │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                    Utilities Layer                           │
│  ┌──────────────┐  ┌──────────────┐                        │
│  │   plotting   │  │   helpers    │                        │
│  └──────────────┘  └──────────────┘                        │
└─────────────────────────────────────────────────────────────┐
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                    FastF1 API + Cache                        │
└─────────────────────────────────────────────────────────────┘
```

### Technology Stack

- **Frontend Framework**: Streamlit 1.28+
- **Data Processing**: Pandas 2.0+, NumPy 1.24+
- **Visualization**: Plotly 5.17+, Matplotlib 3.7+, Seaborn 0.12+
- **F1 Data**: FastF1 3.0+
- **Machine Learning**: Scikit-learn 1.3+
- **Python Version**: 3.9+

## Components and Interfaces

### 1. Data Loader Module (`backend/data_loader.py`)

**Purpose**: Centralized FastF1 API interaction with caching and error handling.

**Key Functions**:

```python
def setup_cache(cache_dir: str = "./f1_cache") -> None:
    """Initialize FastF1 cache directory"""
    
def load_session(year: int, grand_prix: str, session_type: str) -> fastf1.core.Session:
    """
    Load and return a FastF1 session object
    
    Args:
        year: Season year (e.g., 2023)
        grand_prix: Grand Prix name (e.g., "Monaco")
        session_type: One of ['FP1', 'FP2', 'FP3', 'Q', 'R']
    
    Returns:
        Loaded FastF1 session with laps data
    
    Raises:
        ValueError: If session cannot be loaded
    """

def get_drivers(session: fastf1.core.Session) -> List[str]:
    """Extract list of driver abbreviations from session"""

def get_team_colors(session: fastf1.core.Session) -> Dict[str, str]:
    """Return mapping of driver abbreviation to team color hex code"""

def get_available_years() -> List[int]:
    """Return list of years with available data (2018-present)"""

def get_grand_prix_list(year: int) -> List[str]:
    """Return list of Grand Prix names for given year"""
```

**Caching Strategy**:
- Use `@st.cache_data` decorator for session loading (TTL: 1 hour)
- FastF1 built-in cache for raw API responses
- Persistent cache directory across application restarts

**Error Handling**:
- Catch `fastf1.core.DataNotLoadedError` for missing sessions
- Validate year and GP name before API calls
- Return user-friendly error messages

### 2. Analysis Module (`backend/analysis.py`)

**Purpose**: Core race data analysis including lap times, sectors, and pace.

**Key Functions**:

```python
def get_fastest_laps(session: fastf1.core.Session) -> pd.DataFrame:
    """
    Extract fastest lap for each driver
    
    Returns:
        DataFrame with columns: [Driver, Team, LapTime, LapNumber]
    """

def get_top_n_laps(session: fastf1.core.Session, n: int = 10) -> pd.DataFrame:
    """Return top N fastest laps across all drivers"""

def analyze_sectors(session: fastf1.core.Session) -> pd.DataFrame:
    """
    Calculate average sector times for each driver
    
    Returns:
        DataFrame with columns: [Driver, Sector1, Sector2, Sector3, TotalTime]
    """

def calculate_sector_deltas(session: fastf1.core.Session, 
                           reference_driver: str) -> pd.DataFrame:
    """Calculate sector time deltas relative to reference driver"""

def analyze_race_pace(session: fastf1.core.Session, 
                     driver: str,
                     remove_outliers: bool = True) -> pd.DataFrame:
    """
    Calculate race pace with outlier removal
    
    Args:
        remove_outliers: Remove laps >107% of median (yellow flags, traffic)
    
    Returns:
        DataFrame with columns: [LapNumber, LapTime, Compound, IsOutlier]
    """

def calculate_pace_degradation(laps_df: pd.DataFrame) -> Dict[str, float]:
    """
    Use linear regression to calculate lap time degradation per lap
    
    Returns:
        {'slope': seconds_per_lap, 'intercept': initial_pace, 'r_squared': fit_quality}
    """

def get_stint_averages(session: fastf1.core.Session, driver: str) -> pd.DataFrame:
    """
    Calculate average pace for each stint
    
    Returns:
        DataFrame with columns: [StintNumber, Compound, AvgLapTime, LapCount]
    """

def get_weather_data(session: fastf1.core.Session) -> Dict[str, Any]:
    """
    Extract weather information
    
    Returns:
        {'track_temp': float, 'air_temp': float, 'humidity': float, 
         'rainfall': bool, 'wind_speed': float}
    """
```

**Design Decisions**:
- **Outlier Removal**: Use 107% threshold (standard F1 rule for 107% qualifying)
- **Pace Calculation**: Median instead of mean to handle outliers
- **Stint Detection**: Identify by compound changes and pit lap flags

### 3. Telemetry Module (`backend/telemetry.py`)

**Purpose**: Extract and process detailed telemetry data for driver comparison.

**Key Functions**:

```python
def get_telemetry_comparison(session: fastf1.core.Session,
                            driver1: str, 
                            driver2: str,
                            lap_type: str = "fastest") -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Get telemetry data for two drivers
    
    Args:
        lap_type: 'fastest' or specific lap number
    
    Returns:
        (driver1_telemetry, driver2_telemetry) DataFrames with columns:
        [Distance, Speed, Throttle, Brake, nGear, RPM, DRS]
    """

def get_speed_trace(lap: fastf1.core.Lap) -> pd.DataFrame:
    """Extract speed vs distance data"""

def get_brake_trace(lap: fastf1.core.Lap) -> pd.DataFrame:
    """Extract brake pressure vs distance"""

def get_throttle_trace(lap: fastf1.core.Lap) -> pd.DataFrame:
    """Extract throttle position vs distance"""

def calculate_corner_speeds(telemetry: pd.DataFrame, 
                           speed_threshold: int = 200) -> pd.DataFrame:
    """
    Identify corners (speed < threshold) and extract minimum speeds
    
    Returns:
        DataFrame with columns: [CornerNumber, MinSpeed, Distance]
    """

def calculate_straight_speeds(telemetry: pd.DataFrame) -> pd.DataFrame:
    """
    Identify straights and extract maximum speeds
    
    Returns:
        DataFrame with columns: [StraightNumber, MaxSpeed, Distance]
    """

def get_gear_usage(telemetry: pd.DataFrame) -> Dict[int, float]:
    """
    Calculate percentage of lap in each gear
    
    Returns:
        {gear_number: percentage_of_lap}
    """

def get_drs_zones(telemetry: pd.DataFrame) -> List[Tuple[float, float]]:
    """
    Identify DRS activation zones
    
    Returns:
        List of (start_distance, end_distance) tuples
    """
```

**Design Decisions**:
- **Telemetry Frequency**: FastF1 provides ~10Hz data, no interpolation needed
- **Distance-Based**: All telemetry aligned to track distance for accurate comparison
- **Corner Detection**: Speed threshold approach (< 200 km/h = corner)

### 4. Compare Module (`backend/compare.py`)

**Purpose**: High-level driver comparison orchestration.

**Key Functions**:

```python
def compare_fastest_laps(session: fastf1.core.Session,
                        driver1: str,
                        driver2: str) -> Dict[str, Any]:
    """
    Comprehensive fastest lap comparison
    
    Returns:
        {
            'lap_time_delta': float,
            'sector_deltas': [s1_delta, s2_delta, s3_delta],
            'telemetry': (driver1_tel, driver2_tel),
            'speed_stats': {'driver1': {...}, 'driver2': {...}}
        }
    """

def compare_race_pace(session: fastf1.core.Session,
                     driver1: str,
                     driver2: str) -> pd.DataFrame:
    """
    Compare race pace lap-by-lap
    
    Returns:
        DataFrame with columns: [LapNumber, Driver1Time, Driver2Time, Delta]
    """

def compare_sector_performance(session: fastf1.core.Session,
                              driver1: str,
                              driver2: str) -> pd.DataFrame:
    """
    Compare average sector times
    
    Returns:
        DataFrame with columns: [Sector, Driver1, Driver2, Delta, Winner]
    """

def compare_consistency(session: fastf1.core.Session,
                       driver1: str,
                       driver2: str) -> Dict[str, float]:
    """
    Calculate lap time standard deviation
    
    Returns:
        {'driver1_std': float, 'driver2_std': float}
    """
```

### 5. Strategy Module (`backend/strategy.py`)

**Purpose**: Pit stop and tyre strategy analysis.

**Key Functions**:

```python
def detect_pit_stops(session: fastf1.core.Session, driver: str) -> pd.DataFrame:
    """
    Identify all pit stops
    
    Returns:
        DataFrame with columns: [LapNumber, InLapTime, OutLapTime, PitDuration]
    """

def identify_stints(session: fastf1.core.Session, driver: str) -> pd.DataFrame:
    """
    Segment race into stints
    
    Returns:
        DataFrame with columns: [StintNumber, StartLap, EndLap, Compound, LapCount]
    """

def analyze_tyre_compounds(session: fastf1.core.Session) -> pd.DataFrame:
    """
    Analyze compound usage across all drivers
    
    Returns:
        DataFrame with columns: [Driver, Compound, LapCount, AvgPace]
    """

def calculate_undercut_effect(session: fastf1.core.Session,
                              driver1: str,
                              driver2: str,
                              pit_lap: int) -> Dict[str, float]:
    """
    Calculate undercut time gain/loss
    
    Returns:
        {
            'pre_pit_delta': float,  # Gap before pit
            'post_pit_delta': float,  # Gap after pit
            'undercut_gain': float    # Time gained/lost
        }
    """

def calculate_overcut_effect(session: fastf1.core.Session,
                            driver1: str,
                            driver2: str,
                            pit_lap: int) -> Dict[str, float]:
    """Calculate overcut time gain/loss"""

def get_stint_pace_comparison(session: fastf1.core.Session,
                             driver1: str,
                             driver2: str) -> pd.DataFrame:
    """
    Compare pace stint-by-stint
    
    Returns:
        DataFrame with columns: [StintNumber, Driver1Pace, Driver2Pace, 
                                Compound1, Compound2, Delta]
    """

def create_strategy_timeline(session: fastf1.core.Session) -> pd.DataFrame:
    """
    Create Gantt-style data for all drivers
    
    Returns:
        DataFrame with columns: [Driver, StintNumber, StartLap, EndLap, 
                                Compound, Duration]
    """
```

**Design Decisions**:
- **Pit Detection**: Use `PitInTime` and `PitOutTime` flags from FastF1
- **Stint Boundaries**: Compound changes + pit laps
- **Undercut Calculation**: Compare 3-lap average before/after pit window

### 6. ML Model Module (`backend/ml_model.py`)

**Purpose**: Predictive modeling for degradation and performance.

**Key Functions**:

```python
def predict_tyre_degradation(session: fastf1.core.Session,
                            driver: str,
                            stint_number: int = -1) -> Dict[str, Any]:
    """
    Predict future lap times based on current stint
    
    Args:
        stint_number: -1 for current/last stint
    
    Returns:
        {
            'model': LinearRegression object,
            'predictions': [lap_times],
            'confidence_interval': (lower, upper),
            'r_squared': float
        }
    """

def predict_qualifying_gap(session: fastf1.core.Session,
                          driver1: str,
                          driver2: str) -> float:
    """
    Predict qualifying gap using sector times
    
    Returns:
        Predicted time delta in seconds
    """

def predict_pit_window(session: fastf1.core.Session,
                      driver: str,
                      target_lap_time: float) -> int:
    """
    Predict optimal pit lap based on degradation
    
    Returns:
        Recommended pit lap number
    """

def train_pace_model(historical_data: pd.DataFrame) -> RandomForestRegressor:
    """
    Train model on historical pace data
    
    Args:
        historical_data: DataFrame with features [TrackTemp, AirTemp, Compound, 
                        TyreAge, FuelLoad] and target [LapTime]
    
    Returns:
        Trained RandomForestRegressor
    """
```

**Design Decisions**:
- **Degradation Model**: Linear regression (simple, interpretable)
- **Qualifying Prediction**: Sector-based approach with historical correlation
- **Pit Window**: Degradation threshold-based (when lap time exceeds target)
- **Feature Engineering**: Track temp, compound, tyre age, fuel load

### 7. Plotting Utilities (`utils/plotting.py`)

**Purpose**: Unified visualization functions with consistent styling.

**Key Functions**:

```python
def plot_telemetry_comparison(driver1_tel: pd.DataFrame,
                             driver2_tel: pd.DataFrame,
                             driver1_name: str,
                             driver2_name: str,
                             metric: str,
                             colors: Tuple[str, str]) -> go.Figure:
    """
    Create Plotly overlay plot for telemetry metric
    
    Args:
        metric: 'Speed', 'Throttle', 'Brake', 'RPM', 'nGear'
    
    Returns:
        Plotly Figure object
    """

def plot_sector_comparison(sector_data: pd.DataFrame,
                          colors: Dict[str, str]) -> go.Figure:
    """Create grouped bar chart for sector times"""

def plot_race_pace(pace_data: pd.DataFrame,
                  driver_name: str,
                  color: str,
                  show_trend: bool = True) -> go.Figure:
    """
    Create lap time vs lap number scatter with regression line
    
    Args:
        show_trend: Add linear regression trend line
    """

def plot_strategy_timeline(timeline_data: pd.DataFrame,
                          colors: Dict[str, str]) -> go.Figure:
    """
    Create Gantt-style timeline for tyre strategies
    
    Uses Plotly timeline chart with compound colors
    """

def plot_speed_heatmap(telemetry: pd.DataFrame,
                      track_map: pd.DataFrame) -> plt.Figure:
    """
    Create matplotlib heatmap of speed on track map
    
    Args:
        track_map: X, Y coordinates from FastF1
    """

def plot_tyre_degradation(stint_data: pd.DataFrame,
                         predictions: np.ndarray,
                         confidence_interval: Tuple[np.ndarray, np.ndarray]) -> go.Figure:
    """
    Plot actual lap times with predicted degradation and confidence bands
    """

def create_radar_chart(sector_data: pd.DataFrame,
                      drivers: List[str],
                      colors: List[str]) -> go.Figure:
    """
    Create radar chart for multi-driver sector comparison
    """
```

**Styling Standards**:
- **Team Colors**: Always use FastF1 official team colors
- **Font**: Arial, 12pt for labels, 14pt for titles
- **Grid**: Light gray, dashed
- **Legends**: Top-right position, transparent background
- **Plotly Theme**: "plotly_white"
- **Matplotlib Style**: "seaborn-v0_8-darkgrid"

### 8. Helper Utilities (`utils/helpers.py`)

**Purpose**: Common utility functions.

**Key Functions**:

```python
def format_lap_time(seconds: float) -> str:
    """Convert seconds to MM:SS.mmm format"""

def parse_lap_time(time_str: str) -> float:
    """Convert MM:SS.mmm to seconds"""

def validate_driver(session: fastf1.core.Session, driver: str) -> bool:
    """Check if driver exists in session"""

def get_session_type_display_name(session_type: str) -> str:
    """Convert 'Q' to 'Qualifying', 'R' to 'Race', etc."""

def calculate_percentage_change(old_value: float, new_value: float) -> float:
    """Calculate percentage change between values"""

def remove_outliers_iqr(data: pd.Series, multiplier: float = 1.5) -> pd.Series:
    """Remove outliers using IQR method"""

def smooth_telemetry(telemetry: pd.DataFrame, 
                    window: int = 5) -> pd.DataFrame:
    """Apply rolling average to smooth telemetry noise"""
```

## Data Models

### Session Data Structure

```python
@dataclass
class SessionData:
    """Container for loaded session data"""
    year: int
    grand_prix: str
    session_type: str
    session: fastf1.core.Session
    drivers: List[str]
    team_colors: Dict[str, str]
    weather: Dict[str, Any]
    loaded_at: datetime
```

### Telemetry Data Structure

```python
# Pandas DataFrame with columns:
- Distance: float (meters from start line)
- Time: timedelta (elapsed time)
- Speed: float (km/h)
- Throttle: float (0-100%)
- Brake: bool or float (0-100%)
- nGear: int (1-8)
- RPM: float
- DRS: int (0=closed, 1=open, 8-14=available zones)
- X: float (track position X)
- Y: float (track position Y)
```

### Lap Data Structure

```python
# Pandas DataFrame with columns:
- LapNumber: int
- LapTime: timedelta
- Driver: str (3-letter abbreviation)
- Team: str
- Compound: str ('SOFT', 'MEDIUM', 'HARD', 'INTERMEDIATE', 'WET')
- TyreLife: int (laps on current tyres)
- Sector1Time: timedelta
- Sector2Time: timedelta
- Sector3Time: timedelta
- IsPersonalBest: bool
- PitInTime: timedelta (NaT if no pit)
- PitOutTime: timedelta (NaT if no pit)
- TrackStatus: str ('1'=green, '2'=yellow, '4'=SC, '6'=VSC)
```

## Error Handling

### Error Categories and Responses

1. **Data Loading Errors**
   - FastF1 API unavailable → Display warning, suggest retry
   - Session not found → Show available sessions for year
   - Network timeout → Cache fallback if available

2. **Analysis Errors**
   - Insufficient lap data → Disable affected features, show message
   - Missing telemetry → Fall back to lap time analysis only
   - Driver not found → Validate against session driver list

3. **Visualization Errors**
   - Empty dataset → Display "No data available" message
   - Plotting failure → Log error, show text-based summary

4. **ML Model Errors**
   - Insufficient training data → Disable predictions, show warning
   - Model convergence failure → Fall back to simple linear model

### Error Handling Pattern

```python
try:
    session = load_session(year, gp, session_type)
except ValueError as e:
    st.error(f"Failed to load session: {str(e)}")
    st.info("Please check year and Grand Prix selection")
    return None
except Exception as e:
    st.error("Unexpected error occurred")
    logging.error(f"Session load error: {str(e)}", exc_info=True)
    return None
```

## Testing Strategy

### Unit Tests

**Test Coverage Areas**:
1. Data loader functions (mock FastF1 responses)
2. Analysis calculations (lap time processing, sector analysis)
3. Telemetry extraction (distance alignment, corner detection)
4. Strategy functions (pit detection, stint identification)
5. ML model training and prediction
6. Utility functions (time formatting, validation)

**Test Framework**: pytest

**Example Test Structure**:
```python
# tests/test_analysis.py
def test_get_fastest_laps():
    """Test fastest lap extraction"""
    mock_session = create_mock_session()
    result = get_fastest_laps(mock_session)
    assert len(result) == 20  # 20 drivers
    assert 'Driver' in result.columns
    assert result['LapTime'].min() == result.iloc[0]['LapTime']

def test_remove_outliers():
    """Test outlier removal in race pace"""
    laps = create_mock_laps_with_outliers()
    clean_laps = analyze_race_pace(laps, remove_outliers=True)
    assert len(clean_laps) < len(laps)
    assert clean_laps['LapTime'].max() < laps['LapTime'].max()
```

### Integration Tests

1. **End-to-End Session Loading**
   - Load real session from FastF1
   - Verify all data structures populated
   - Check cache persistence

2. **Visualization Pipeline**
   - Generate all plot types
   - Verify no rendering errors
   - Check color consistency

3. **Multi-Driver Comparison**
   - Compare two drivers across all metrics
   - Verify data alignment
   - Check calculation accuracy

### Manual Testing Checklist

- [ ] Load session from each year (2018-2024)
- [ ] Test all session types (FP1, FP2, FP3, Q, R)
- [ ] Compare drivers from different teams
- [ ] Verify telemetry plots render correctly
- [ ] Test strategy timeline with multiple pit stops
- [ ] Validate ML predictions with known results
- [ ] Check responsive behavior with missing data
- [ ] Test cache performance (cold vs warm)

## Performance Considerations

### Optimization Strategies

1. **Caching Layers**
   - FastF1 cache: Raw API responses (persistent)
   - Streamlit cache: Processed DataFrames (session-based)
   - Function-level cache: Expensive calculations

2. **Data Loading**
   - Lazy loading: Only load telemetry when requested
   - Selective loading: Load only required laps/drivers
   - Parallel loading: Use threading for multi-driver comparisons

3. **Visualization**
   - Downsample telemetry for plotting (every 10th point for overview)
   - Use Plotly WebGL for large datasets
   - Lazy plot rendering: Generate on tab selection

4. **Memory Management**
   - Clear old session data when loading new session
   - Limit cache size (max 10 sessions)
   - Use pandas categorical dtype for repeated strings

### Expected Performance Metrics

- **Cold session load**: 10-30 seconds (FastF1 API download)
- **Cached session load**: 1-3 seconds
- **Telemetry comparison**: < 2 seconds
- **Strategy analysis**: < 1 second
- **Plot rendering**: < 1 second per plot

## Deployment Configuration

### Requirements File

```
fastf1>=3.0.0
pandas>=2.0.0
numpy>=1.24.0
matplotlib>=3.7.0
plotly>=5.17.0
streamlit>=1.28.0
scikit-learn>=1.3.0
seaborn>=0.12.0
```

### Directory Structure

```
f1_analysis_app/
├── app.py
├── requirements.txt
├── README.md
├── .gitignore
├── backend/
│   ├── __init__.py
│   ├── data_loader.py
│   ├── analysis.py
│   ├── telemetry.py
│   ├── compare.py
│   ├── strategy.py
│   └── ml_model.py
├── utils/
│   ├── __init__.py
│   ├── plotting.py
│   └── helpers.py
├── assets/
│   └── logo.png
├── f1_cache/
│   └── (FastF1 cache files)
└── tests/
    ├── __init__.py
    ├── test_data_loader.py
    ├── test_analysis.py
    ├── test_telemetry.py
    ├── test_compare.py
    ├── test_strategy.py
    └── test_ml_model.py
```

### Streamlit Configuration

Create `.streamlit/config.toml`:
```toml
[theme]
primaryColor = "#E70000"  # F1 Red
backgroundColor = "#FFFFFF"
secondaryBackgroundColor = "#F0F2F6"
textColor = "#262730"
font = "sans serif"

[server]
maxUploadSize = 200
enableXsrfProtection = true
enableCORS = false
```

### Environment Variables

```bash
# Optional: Custom cache directory
F1_CACHE_DIR=./f1_cache

# Optional: FastF1 API settings
FASTF1_CACHE_ENABLED=true
```

## Security Considerations

1. **Input Validation**
   - Validate year range (2018-2024)
   - Sanitize Grand Prix names
   - Validate driver abbreviations against session

2. **Data Privacy**
   - No user data collection
   - All data from public FastF1 API
   - Local cache only

3. **Error Information**
   - Don't expose internal paths in error messages
   - Log detailed errors server-side only
   - Show user-friendly messages in UI

## Future Enhancements

1. **Advanced ML Features**
   - Race outcome prediction
   - Optimal strategy recommendation
   - Driver performance clustering

2. **Additional Visualizations**
   - 3D track maps with telemetry overlay
   - Animated race replay
   - Interactive strategy simulator

3. **Data Export**
   - Export analysis to PDF report
   - CSV download for custom analysis
   - Share analysis via URL

4. **Multi-Session Comparison**
   - Compare same driver across races
   - Season-long performance trends
   - Team development tracking
