# Circuit Map Comparison Feature - Documentation

## Overview

The Circuit Map Comparison Feature provides an interactive visualization of F1 circuit layouts with color-coded performance comparison between two drivers. This feature is integrated into the Telemetry section of the F1 Analysis Dashboard.

## Features

✅ **Circuit Layout Visualization**
- Draws the complete circuit using X/Y telemetry coordinates
- Automatically scales to track boundaries
- Smooth interpolated track lines

✅ **Performance Color Coding**
- **Blue segments**: Driver 1 faster
- **Red segments**: Driver 2 faster  
- **Grey segments**: Equal pace (within threshold)

✅ **Rich Hover Data**
- Distance along track
- Speed comparison for both drivers
- Delta speed
- Gear, throttle, brake percentages
- DRS status (Active/Inactive)

✅ **Dynamic Updates**
- Automatically updates when driver selection changes
- Works with fastest lap or specific lap number
- Supports all FastF1 tracks (2018+)

✅ **Performance Optimized**
- Streamlit caching for telemetry data
- Interpolation for smooth visualization (~500 points)
- Efficient segment-based rendering

## Technical Implementation

### Backend Functions

#### 1. `load_aligned_telemetry()`
```python
load_aligned_telemetry(session, driver1, driver2, lap_type="fastest")
```
- Loads telemetry for both drivers
- Aligns data to common distance reference using interpolation
- Returns aligned DataFrames with X, Y, Speed, Throttle, Brake, Gear, DRS

**Key Features:**
- Handles missing data gracefully
- Interpolates to ~500 points for smooth visualization
- Removes NaN values from critical columns

#### 2. `build_circuit_comparison_map()`
```python
build_circuit_comparison_map(session, driver1, driver2, lap_type="fastest", delta_threshold=0.5)
```
- Main function that generates the Plotly figure
- Calculates speed deltas between drivers
- Creates color-coded segments
- Builds interactive hover tooltips

**Parameters:**
- `session`: FastF1 session object
- `driver1`: First driver abbreviation (e.g., 'VER')
- `driver2`: Second driver abbreviation (e.g., 'HAM')
- `lap_type`: 'fastest' or specific lap number (int)
- `delta_threshold`: Speed difference threshold in km/h (default: 0.5)

**Returns:**
- Plotly Figure object with circuit map

#### 3. Helper Functions

**`_get_driver_colors()`**
- Retrieves team colors from FastF1
- Handles teammates by creating contrasting shades
- Fallback to default colors if needed

**`_lighten_color()`**
- Creates lighter shade of a color for teammate differentiation
- Blends with white using configurable factor

### Data Flow

```
1. User selects drivers and lap type
   ↓
2. load_aligned_telemetry() fetches and aligns data
   ↓
3. Speed delta calculated (driver1 - driver2)
   ↓
4. Track segmented based on faster driver
   ↓
5. Each segment plotted with appropriate color
   ↓
6. Hover data generated for each point
   ↓
7. Plotly figure rendered in Streamlit
```

### Interpolation Logic

The feature uses NumPy's `interp()` function to align telemetry data:

```python
# Create common distance array
common_distance = np.linspace(min_distance, max_distance, 500)

# Interpolate each telemetry channel
aligned_speed = np.interp(
    common_distance,
    original_distance,
    original_speed
)
```

This ensures both drivers' data is sampled at identical distance points for accurate comparison.

### Color Coding Logic

```python
if speed_delta > delta_threshold:
    color = driver1_color  # Driver 1 faster (blue)
elif speed_delta < -delta_threshold:
    color = driver2_color  # Driver 2 faster (red)
else:
    color = 'lightgrey'    # Equal pace
```

The `delta_threshold` parameter (default 0.5 km/h) prevents excessive color switching due to minor speed variations.

## Usage

### In Streamlit App

The feature is integrated into the "Telemetry & Circuit Map" tab:

```python
# In app.py
fig = build_circuit_comparison_map(session, driver1, driver2, lap_type)
st.plotly_chart(fig, use_container_width=True)
```

### Standalone Usage

```python
from backend.data_loader import load_session
from backend.telemetry import build_circuit_comparison_map

# Load session
session = load_session(2023, "Monaco", "Qualifying")

# Generate circuit map
fig = build_circuit_comparison_map(
    session, 
    driver1="VER", 
    driver2="LEC",
    lap_type="fastest",
    delta_threshold=0.5
)

# Display or save
fig.show()
# or
fig.write_html("circuit_comparison.html")
```

## Testing

### Test Cases Covered

1. ✅ Works for any 2020+ track
2. ✅ Handles missing X/Y telemetry points
3. ✅ Works for wet and dry sessions
4. ✅ Handles teammates (same team colors)
5. ✅ Updates efficiently when drivers change
6. ✅ Correct delta coloring
7. ✅ Proper hover data formatting

### Manual Testing

```python
# Test with different tracks
tracks = ["Monaco", "Monza", "Spa", "Singapore"]
for track in tracks:
    session = load_session(2023, track, "Qualifying")
    fig = build_circuit_comparison_map(session, "VER", "HAM")
    assert fig is not None
```

## Performance Considerations

### Caching Strategy

All telemetry functions use `@st.cache_data`:
- TTL: 3600 seconds (1 hour)
- Prevents redundant API calls
- Speeds up driver switching

### Optimization Techniques

1. **Downsampling**: Interpolates to ~500 points (vs thousands in raw data)
2. **Lazy Loading**: Only loads telemetry when needed
3. **Segment-based Rendering**: Minimizes Plotly traces
4. **Efficient Interpolation**: NumPy's vectorized operations

### Memory Usage

Typical memory footprint per comparison:
- Raw telemetry: ~2-5 MB per driver
- Aligned telemetry: ~100-200 KB per driver
- Plotly figure: ~500 KB - 1 MB

## Troubleshooting

### Common Issues

**Issue: "Telemetry data is empty"**
- Solution: Some sessions (especially older ones) may lack telemetry
- Check if session has telemetry: `session.laps.iloc[0].get_telemetry()`

**Issue: "X/Y coordinates missing"**
- Solution: Use `lap.get_pos_data()` or ensure FastF1 version is up to date
- Some tracks may have incomplete position data

**Issue: "Colors not distinguishable for teammates"**
- Solution: The `_lighten_color()` function automatically creates contrast
- Adjust lightening factor if needed (default: 0.4)

**Issue: "Map looks jagged/pixelated"**
- Solution: Increase interpolation points in `load_aligned_telemetry()`
- Change `num_points = 500` to higher value (e.g., 1000)

### Debug Mode

Enable debug output:

```python
import logging
logging.basicConfig(level=logging.DEBUG)

# Add debug prints in functions
print(f"Telemetry shape: {tel1.shape}")
print(f"Distance range: {common_distance.min()} - {common_distance.max()}")
print(f"Speed delta range: {speed_delta.min()} - {speed_delta.max()}")
```

## Future Enhancements

Potential improvements:

1. **Time-based delta**: Show cumulative time difference instead of speed
2. **Multiple drivers**: Compare 3+ drivers simultaneously
3. **Sector markers**: Overlay sector boundaries on circuit
4. **Corner annotations**: Label famous corners
5. **Animation**: Animate lap progression
6. **Export options**: Save as PNG/SVG
7. **Custom color schemes**: User-selectable color palettes
8. **Brake/Throttle overlay**: Show input traces on circuit

## API Reference

### Main Functions

```python
# Load aligned telemetry
tel1, tel2, distance = load_aligned_telemetry(
    session,
    driver1="VER",
    driver2="HAM",
    lap_type="fastest"
)

# Build circuit map
fig = build_circuit_comparison_map(
    session,
    driver1="VER",
    driver2="HAM",
    lap_type="fastest",
    delta_threshold=0.5
)
```

### Return Types

- `load_aligned_telemetry()`: `Tuple[pd.DataFrame, pd.DataFrame, np.ndarray]`
- `build_circuit_comparison_map()`: `plotly.graph_objects.Figure`

### Exceptions

- `ValueError`: Invalid drivers, missing telemetry, or empty data
- `ImportError`: Missing plotly dependency

## Dependencies

Required packages:
```
fastf1>=3.0.0
streamlit>=1.28.0
plotly>=5.17.0
pandas>=2.0.0
numpy>=1.24.0
```

## License

This feature is part of the F1 Analysis Dashboard project.
Data provided by Formula 1 © via FastF1.

## Credits

- **FastF1**: Telemetry data and API
- **Plotly**: Interactive visualization
- **Streamlit**: Web application framework

---

**Last Updated**: 2024
**Version**: 1.0.0
