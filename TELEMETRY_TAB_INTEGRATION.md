# Telemetry Tab Integration Guide

## How to Add Circuit Map to Your Existing Telemetry Tab

### Step 1: Add Import at the Top of Your App

Add this import with your other backend imports:

```python
from backend.circuit_map import cached_circuit_map
```

### Step 2: Add Circuit Map Section in Telemetry Tab

Add this code **BELOW** your existing telemetry graphs (speed, throttle, brake, gear, etc.) in the Telemetry tab:

```python
# ============================================================================
# CIRCUIT MAP SECTION - ADD THIS BELOW YOUR EXISTING TELEMETRY GRAPHS
# ============================================================================

st.markdown("---")  # Separator line

st.subheader("🗺️ Circuit Map – Driver vs Driver Performance")

st.markdown(
    """
    The circuit is color-coded to show which driver was faster at each section:
    - **Blue**: Driver 1 faster
    - **Red**: Driver 2 faster  
    - **Grey**: Equal pace
    
    Hover over the track to see detailed telemetry data at each point.
    """
)

# Generate unique session key for caching
session_key = f"{st.session_state.get('year', 2024)}_{st.session_state.get('gp', 'Unknown')}_{st.session_state.get('session_type', 'Race')}"

try:
    with st.spinner("Generating circuit map..."):
        # Call the cached circuit map function
        # Replace 'driver1' and 'driver2' with your actual driver selection variables
        # Replace 'session' with your actual session variable
        circuit_fig = cached_circuit_map(
            session_key=session_key,
            driver1=driver1,  # Your driver 1 variable
            driver2=driver2,  # Your driver 2 variable
            _session=session  # Your session variable
        )
        
        st.plotly_chart(circuit_fig, use_container_width=True)
        
except Exception as e:
    st.error(f"Unable to generate circuit map: {str(e)}")
    st.info("Circuit map requires GPS telemetry data which may not be available for all sessions.")

# ============================================================================
# END OF CIRCUIT MAP SECTION
# ============================================================================
```

### Step 3: Complete Integration Example

Here's a complete example of how your Telemetry tab structure should look:

```python
# In your Telemetry tab
with telemetry_tab:  # or however you define your telemetry tab
    st.header("Telemetry Analysis")
    
    # Driver selection (you probably already have this)
    col1, col2 = st.columns(2)
    with col1:
        driver1 = st.selectbox("Driver 1", options=drivers, key="tel_driver1")
    with col2:
        driver2 = st.selectbox("Driver 2", options=drivers, index=1, key="tel_driver2")
    
    # YOUR EXISTING TELEMETRY GRAPHS GO HERE
    # For example:
    # - Speed comparison graph
    # - Throttle/Brake graph
    # - RPM graph
    # - Gear usage graph
    # ... (keep all your existing code)
    
    # ============================================================================
    # ADD CIRCUIT MAP BELOW YOUR EXISTING GRAPHS
    # ============================================================================
    
    st.markdown("---")
    
    st.subheader("🗺️ Circuit Map – Driver vs Driver Performance")
    
    st.markdown(
        """
        The circuit is color-coded to show which driver was faster at each section:
        - **Blue**: Driver 1 faster
        - **Red**: Driver 2 faster  
        - **Grey**: Equal pace
        """
    )
    
    session_key = f"{selected_year}_{selected_gp}_{session_type}"
    
    try:
        with st.spinner("Generating circuit map..."):
            circuit_fig = cached_circuit_map(
                session_key=session_key,
                driver1=driver1,
                driver2=driver2,
                _session=session
            )
            
            st.plotly_chart(circuit_fig, use_container_width=True)
            
    except Exception as e:
        st.error(f"Unable to generate circuit map: {str(e)}")
        st.info("Circuit map requires GPS telemetry data.")
```

### Step 4: Variable Names to Update

Make sure to replace these placeholder variable names with your actual variable names:

- `driver1` → Your driver 1 selection variable
- `driver2` → Your driver 2 selection variable  
- `session` → Your FastF1 session object
- `selected_year` → Your year selection variable
- `selected_gp` → Your Grand Prix selection variable
- `session_type` → Your session type variable
- `drivers` → Your list of available drivers

### Step 5: Test the Integration

1. Run your Streamlit app
2. Load a session (preferably 2020 or newer for best telemetry data)
3. Navigate to the Telemetry tab
4. Select two drivers
5. Scroll down to see the circuit map below your existing graphs

### Troubleshooting

**If you get an import error:**
```python
# Make sure this is at the top of your app file
from backend.circuit_map import cached_circuit_map
```

**If the map doesn't appear:**
- Check that you have GPS telemetry data (works best with 2020+ sessions)
- Check the error message in the Streamlit app
- Verify your driver selection variables are correctly named

**If colors don't show correctly:**
- The function automatically gets team colors from FastF1
- Blue and Red are fallback colors if team colors aren't available

### Performance Notes

- The circuit map is cached using `@st.cache_data`
- First generation may take 2-5 seconds
- Subsequent loads with same drivers/session are instant
- Cache expires after 1 hour (3600 seconds)

### Customization Options

You can customize the circuit map by modifying parameters in `backend/circuit_map.py`:

- `delta_threshold`: Change sensitivity (default 0.5 km/h)
- `num_points`: Change interpolation resolution (default 500)
- `line width`: Change track line thickness (default 4)
- `height`: Change map height (default 600px)

---

## That's it! 

Your circuit map feature is now integrated into your Telemetry tab without affecting any other parts of your app.
