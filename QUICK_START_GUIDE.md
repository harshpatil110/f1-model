# Circuit Map Comparison Feature - Quick Start Guide

## 🚀 Installation

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

Required packages:
- `fastf1>=3.0.0` - F1 telemetry data API
- `streamlit>=1.28.0` - Web application framework
- `plotly>=5.17.0` - Interactive visualization
- `pandas>=2.0.0` - Data manipulation
- `numpy>=1.24.0` - Numerical operations
- `scikit-learn>=1.3.0` - Machine learning utilities

### 2. Verify Installation

```bash
python validate_circuit_map.py
```

You should see: `✅ ALL VALIDATIONS PASSED!`

## 🏁 Running the Application

### Start the Streamlit App

```bash
streamlit run app.py
```

The app will open in your browser at `http://localhost:8501`

## 📖 Using the Circuit Map Feature

### Step 1: Load a Session

1. In the sidebar, select:
   - **Year** (e.g., 2023)
   - **Grand Prix** (e.g., Monaco)
   - **Session Type** (e.g., Qualifying)

2. Click **"🔄 Load Session"**

3. Wait for the session to load (first load may take 30-60 seconds)

### Step 2: Navigate to Telemetry Tab

Click on the **"🎯 Telemetry & Circuit Map"** tab

### Step 3: Select Drivers

1. Choose **Driver 1** from the first dropdown (e.g., VER)
2. Choose **Driver 2** from the second dropdown (e.g., HAM)

### Step 4: Select Lap Type

Choose between:
- **Fastest Lap** - Compares each driver's fastest lap
- **Specific Lap** - Compare a specific lap number

### Step 5: View the Circuit Map

The circuit map will automatically generate showing:

- **Blue segments** - Driver 1 is faster
- **Red segments** - Driver 2 is faster
- **Grey segments** - Equal pace

### Step 6: Explore Hover Data

Hover over any point on the track to see:
- Distance along track
- Speed comparison
- Delta speed
- Gear, throttle, brake data
- DRS status

## 🎨 Understanding the Visualization

### Color Coding

The track is divided into segments based on which driver was faster:

```
Blue   = Driver 1 faster (speed delta > +0.5 km/h)
Red    = Driver 2 faster (speed delta < -0.5 km/h)
Grey   = Equal pace (within ±0.5 km/h)
```

### Hover Information

When you hover over the track, you'll see:

```
Distance: 1500m
VER Speed: 305.5 km/h
HAM Speed: 302.3 km/h
Δ Speed: +3.2 km/h
Faster: VER

VER: Gear 8 | Throttle 100% | Brake 0% | DRS Active
HAM: Gear 8 | Throttle 98% | Brake 0% | DRS Active
```

### Legend

The legend shows:
- Driver 1 name with their team color
- Driver 2 name with their team color
- "Equal pace" in grey

## 💡 Tips & Best Practices

### Getting the Best Results

1. **Use Qualifying Sessions**
   - Qualifying laps have the cleanest telemetry
   - Less traffic and yellow flags
   - More consistent data

2. **Compare Similar Lap Types**
   - Fastest lap vs fastest lap
   - Or same lap number for both drivers

3. **Check Data Availability**
   - Telemetry is most reliable for 2020+ seasons
   - Some older sessions may have incomplete data

4. **Zoom and Pan**
   - Use Plotly controls to zoom into specific corners
   - Double-click to reset view
   - Drag to pan around the circuit

### Interpreting the Results

**Blue Dominance (Driver 1 Faster)**
- Look for blue in corners = better cornering speed
- Blue on straights = better top speed or earlier throttle

**Red Dominance (Driver 2 Faster)**
- Same interpretation but for Driver 2

**Grey Sections**
- Both drivers taking similar lines
- Equal performance in that section

**Segment Transitions**
- Where colors change = key performance differences
- Look for patterns (e.g., one driver faster in all corners)

## 🔧 Troubleshooting

### Issue: "Session has no lap data"

**Solution:**
- Try a different session type (Qualifying instead of FP1)
- Check if the Grand Prix actually happened that year
- Some testing sessions don't have complete data

### Issue: "Telemetry data is empty"

**Solution:**
- Telemetry may not be available for that session
- Try a more recent season (2020+)
- Some sessions have incomplete telemetry

### Issue: "Driver not found in session"

**Solution:**
- Check driver abbreviation spelling
- Driver may not have participated in that session
- Try selecting from the dropdown instead of typing

### Issue: Map looks jagged or pixelated

**Solution:**
- This is normal for some tracks with complex layouts
- The interpolation uses 500 points for performance
- You can increase this in the code if needed

### Issue: Colors not distinguishable

**Solution:**
- If drivers are teammates, the code automatically creates contrast
- You can adjust the `_lighten_color()` factor in the code
- Try comparing drivers from different teams

### Issue: Slow loading

**Solution:**
- First load always takes longer (downloading data)
- Subsequent loads use cache (much faster)
- Check your internet connection
- FastF1 API may be slow during peak times

## 📊 Example Use Cases

### 1. Qualifying Battle Analysis

Compare pole position vs P2:
```
Session: 2023 Monaco Qualifying
Driver 1: VER (Pole)
Driver 2: ALO (P2)
Lap Type: Fastest Lap
```

Look for:
- Where did VER gain time?
- Which corners were crucial?
- Top speed differences on straights

### 2. Teammate Comparison

Compare teammates to see who's faster where:
```
Session: 2023 Bahrain Qualifying
Driver 1: VER
Driver 2: PER
Lap Type: Fastest Lap
```

Insights:
- Driving style differences
- Corner-by-corner comparison
- Setup differences

### 3. Race Pace Analysis

Compare specific race laps:
```
Session: 2023 Silverstone Race
Driver 1: HAM
Driver 2: VER
Lap Type: Specific Lap (Lap 15)
```

Analyze:
- Tire degradation effects
- Fuel load impact
- Traffic influence

### 4. Track Evolution

Compare same driver across sessions:
```
Session 1: FP1
Session 2: Qualifying
Driver 1: LEC
Driver 2: LEC
Lap Type: Fastest Lap
```

See how:
- Track grip improved
- Driver found time
- Setup changes affected performance

## 🎯 Advanced Features

### Adjusting Delta Threshold

In the code, you can modify the sensitivity:

```python
fig = build_circuit_comparison_map(
    session, 
    driver1, 
    driver2,
    delta_threshold=1.0  # Increase for less color switching
)
```

Lower threshold = more sensitive (more color changes)
Higher threshold = less sensitive (larger segments)

### Exporting the Map

Save the circuit map as an image:

```python
fig = build_circuit_comparison_map(session, "VER", "HAM")
fig.write_html("circuit_comparison.html")
fig.write_image("circuit_comparison.png")  # Requires kaleido
```

### Custom Color Schemes

Modify colors in the code:

```python
# In build_circuit_comparison_map()
if avg_delta > delta_threshold:
    color = '#0000FF'  # Custom blue
elif avg_delta < -delta_threshold:
    color = '#FF0000'  # Custom red
else:
    color = '#808080'  # Custom grey
```

## 📚 Additional Resources

### Documentation
- Full feature documentation: `CIRCUIT_MAP_FEATURE.md`
- FastF1 documentation: https://docs.fastf1.dev/
- Plotly documentation: https://plotly.com/python/

### Code Structure
```
backend/telemetry.py
├── load_aligned_telemetry()      # Data alignment
├── build_circuit_comparison_map() # Main visualization
├── _get_driver_colors()           # Color management
└── _lighten_color()               # Color utilities

app.py
└── Telemetry & Circuit Map tab    # UI integration
```

### Testing
Run validation:
```bash
python validate_circuit_map.py
```

Run unit tests:
```bash
python tests/test_circuit_map.py
```

## 🤝 Support

If you encounter issues:

1. Check this guide's troubleshooting section
2. Review `CIRCUIT_MAP_FEATURE.md` for technical details
3. Verify all dependencies are installed
4. Check FastF1 API status
5. Try a different session/track

## 🎉 Enjoy!

You're now ready to analyze F1 telemetry with the Circuit Map Comparison Feature!

Try different tracks, drivers, and sessions to discover performance insights.

---

**Happy Racing! 🏎️💨**
