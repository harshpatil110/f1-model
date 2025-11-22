"""
F1 Analysis Dashboard - Streamlit Application

Complete F1 data analysis dashboard with:
- Home: Session info and weather
- Driver Analysis: Lap times, sectors, degradation
- Telemetry: Circuit map comparison
- Strategy: Pit stops and tyre stints
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
import fastf1

from backend.data_loader import (
    setup_cache, load_session, get_drivers, get_team_colors,
    get_available_years, get_grand_prix_list
)
from backend.analysis import (
    get_fastest_laps, analyze_sectors, analyze_race_pace,
    calculate_pace_degradation, get_weather_data
)
from backend.strategy import get_pit_stops, eds, calculate_straight_speeds,
    get_gear_usage, get_drs_zones, build_circuit_comparison_map
)

# Page configuration
st.set_page_config(
    page_title="F1 Analysis Dashboard",
    page_icon="🏎️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize cache
setup_cache()

# Title
st.title("🏎️ F1 Analysis Dashboard")
st.markdown("---")

# Sidebar - Session Selection
st.sidebar.header("📊 Session Selection")

# Year selection
available_years = get_available_years()
selected_year = st.sidebar.selectbox(
    "Year",
    options=available_years,
    index=len(available_years) - 1  # Default to most recent year
)

# Grand Prix selection
try:
    grand_prix_list = get_grand_prix_list(selected_year)
    selected_gp = st.sidebar.selectbox(
        "Grand Prix",
        options=grand_prix_list,
        index=0
    )
except Exception as e:
    st.sidebar.error(f"Error loading Grand Prix list: {str(e)}")
    st.stop()

# Session type selection
session_type = st.sidebar.selectbox(
    "Session Type",
    options=['Race', 'Qualifying', 'FP1', 'FP2', 'FP3'],
    index=0
)

# Load session button
if st.sidebar.button("🔄 Load Session", type="primary"):
    with st.spinner(f"Loading {selected_year} {selected_gp} {session_type}..."):
        try:
            session = load_session(selected_year, selected_gp, session_type)
            st.session_state['session'] = session
            st.session_state['drivers'] = get_drivers(session)
            st.session_state['team_colors'] = get_team_colors(session)
            st.sidebar.success("✅ Session loaded successfully!")
        except Exception as e:
            st.sidebar.error(f"❌ Error loading session: {str(e)}")

# Check if session is loaded
if 'session' not in st.session_state:
    st.info("👈 Please select a session and click 'Load Session' to begin analysis")
    st.stop()

session = st.session_state['session']
drivers = st.session_state['drivers']
team_colors = st.session_state['team_colors']

# Display session info
st.sidebar.markdown("---")
st.sidebar.markdown("### 📋 Session Info")
st.sidebar.markdown(f"**Event:** {selected_gp}")
st.sidebar.markdown(f"**Year:** {selected_year}")
st.sidebar.markdown(f"**Session:** {session_type}")
st.sidebar.markdown(f"**Drivers:** {len(drivers)}")

# Main content tabs
tab1, tab2, tab3, tab4 = st.tabs([
    "📈 Lap Times",
    "🔍 Sector Analysis",
    "🏁 Race Pace",
    "🎯 Telemetry & Circuit Map"
])

# Tab 1: Lap Times
with tab1:
    st.header("Fastest Lap Times")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Fastest Lap per Driver")
        fastest_laps = get_fastest_laps(session)
        if not fastest_laps.empty:
            # Format lap time for display
            fastest_laps['LapTime_str'] = fastest_laps['LapTime'].apply(
                lambda x: f"{x.total_seconds():.3f}s" if pd.notna(x) else "N/A"
            )
            st.dataframe(
                fastest_laps[['Driver', 'Team', 'LapTime_str', 'LapNumber']],
                hide_index=True,
                use_container_width=True
            )
        else:
            st.info("No lap time data available")
    
    with col2:
        st.subheader("Top 10 Fastest Laps")
        top_laps = get_top_n_laps(session, n=10)
        if not top_laps.empty:
            top_laps['LapTime_str'] = top_laps['LapTime'].apply(
                lambda x: f"{x.total_seconds():.3f}s" if pd.notna(x) else "N/A"
            )
            st.dataframe(
                top_laps[['Driver', 'Team', 'LapTime_str', 'LapNumber']],
                hide_index=True,
                use_container_width=True
            )
        else:
            st.info("No lap time data available")

# Tab 2: Sector Analysis
with tab2:
    st.header("Sector Time Analysis")
    
    sector_data = analyze_sectors(session)
    
    if not sector_data.empty:
        st.subheader("Average Sector Times")
        
        # Format sector times
        for col in ['Sector1', 'Sector2', 'Sector3', 'TotalTime']:
            sector_data[f'{col}_str'] = sector_data[col].apply(
                lambda x: f"{x.total_seconds():.3f}s" if pd.notna(x) else "N/A"
            )
        
        st.dataframe(
            sector_data[['Driver', 'Sector1_str', 'Sector2_str', 'Sector3_str', 'TotalTime_str']],
            hide_index=True,
            use_container_width=True
        )
        
        # Sector deltas
        st.subheader("Sector Deltas (vs Reference Driver)")
        reference_driver = st.selectbox(
            "Select Reference Driver",
            options=drivers,
            index=0
        )
        
        if reference_driver:
            try:
                deltas = calculate_sector_deltas(session, reference_driver)
                if not deltas.empty:
                    for col in ['Sector1Delta', 'Sector2Delta', 'Sector3Delta', 'TotalDelta']:
                        deltas[f'{col}_str'] = deltas[col].apply(
                            lambda x: f"{x.total_seconds():+.3f}s" if pd.notna(x) else "N/A"
                        )
                    st.dataframe(
                        deltas[['Driver', 'Sector1Delta_str', 'Sector2Delta_str', 'Sector3Delta_str', 'TotalDelta_str']],
                        hide_index=True,
                        use_container_width=True
                    )
            except Exception as e:
                st.error(f"Error calculating deltas: {str(e)}")
    else:
        st.info("No sector data available")

# Tab 3: Race Pace
with tab3:
    st.header("Race Pace Analysis")
    
    if session_type == 'Race':
        selected_driver = st.selectbox(
            "Select Driver for Race Pace",
            options=drivers,
            key="race_pace_driver"
        )
        
        if selected_driver:
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader(f"{selected_driver} - Lap Times")
                pace_data = analyze_race_pace(session, selected_driver, remove_outliers=True)
                
                if not pace_data.empty:
                    st.write(f"Total laps: {len(pace_data)}")
                    st.write(f"Outliers removed: {pace_data['IsOutlier'].sum()}")
                    
                    # Calculate degradation
                    degradation = calculate_pace_degradation(pace_data)
                    st.metric(
                        "Pace Degradation",
                        f"{degradation['slope']:.3f} s/lap",
                        help="Linear regression slope showing lap time increase per lap"
                    )
                    st.metric(
                        "R² (fit quality)",
                        f"{degradation['r_squared']:.3f}",
                        help="How well the linear model fits the data (0-1)"
                    )
            
            with col2:
                st.subheader("Stint Averages")
                stint_data = get_stint_averages(session, selected_driver)
                
                if not stint_data.empty:
                    stint_data['AvgLapTime_str'] = stint_data['AvgLapTime'].apply(
                        lambda x: f"{x.total_seconds():.3f}s" if pd.notna(x) else "N/A"
                    )
                    st.dataframe(
                        stint_data[['StintNumber', 'Compound', 'AvgLapTime_str', 'LapCount']],
                        hide_index=True,
                        use_container_width=True
                    )
                else:
                    st.info("No stint data available")
    else:
        st.info("Race pace analysis is only available for Race sessions")
    
    # Weather data
    st.subheader("Weather Conditions")
    weather = get_weather_data(session)
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if weather['track_temp'] is not None:
            st.metric("Track Temp", f"{weather['track_temp']:.1f}°C")
    
    with col2:
        if weather['air_temp'] is not None:
            st.metric("Air Temp", f"{weather['air_temp']:.1f}°C")
    
    with col3:
        if weather['humidity'] is not None:
            st.metric("Humidity", f"{weather['humidity']:.1f}%")
    
    with col4:
        if weather['rainfall']:
            st.metric("Rainfall", "Yes ☔")
        else:
            st.metric("Rainfall", "No ☀️")

# Tab 4: Telemetry & Circuit Map
with tab4:
    st.header("Telemetry Analysis & Circuit Map")
    
    # Driver selection for comparison
    col1, col2 = st.columns(2)
    
    with col1:
        driver1 = st.selectbox(
            "Driver 1",
            options=drivers,
            index=0,
            key="telemetry_driver1"
        )
    
    with col2:
        driver2 = st.selectbox(
            "Driver 2",
            options=drivers,
            index=min(1, len(drivers) - 1),
            key="telemetry_driver2"
        )
    
    # Lap type selection
    lap_type = st.radio(
        "Lap Selection",
        options=["Fastest Lap", "Specific Lap"],
        horizontal=True
    )
    
    lap_param = "fastest"
    if lap_type == "Specific Lap":
        lap_number = st.number_input(
            "Lap Number",
            min_value=1,
            max_value=100,
            value=1
        )
        lap_param = lap_number
    
    if driver1 and driver2:
        try:
            # Circuit Map Comparison
            st.subheader("🗺️ Circuit Map — Driver Performance Split")
            st.markdown(
                "The circuit is color-coded to show which driver was faster at each section. "
                "Hover over the track to see detailed telemetry data."
            )
            
            with st.spinner("Generating circuit map..."):
                fig = build_circuit_comparison_map(session, driver1, driver2, lap_param)
                st.plotly_chart(fig, use_container_width=True)
            
            st.markdown("---")
            
            # Additional telemetry analysis
            st.subheader("📊 Detailed Telemetry Comparison")
            
            tel1, tel2 = get_telemetry_comparison(session, driver1, driver2, lap_param)
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown(f"### {driver1}")
                
                # Gear usage
                gear_usage1 = get_gear_usage(tel1)
                if gear_usage1:
                    st.write("**Gear Usage:**")
                    for gear, pct in gear_usage1.items():
                        st.write(f"Gear {gear}: {pct}%")
                
                # Corner speeds
                corners1 = calculate_corner_speeds(tel1)
                if not corners1.empty:
                    st.write(f"**Corners identified:** {len(corners1)}")
                    st.write(f"**Avg min corner speed:** {corners1['MinSpeed'].mean():.1f} km/h")
                
                # Straight speeds
                straights1 = calculate_straight_speeds(tel1)
                if not straights1.empty:
                    st.write(f"**Max speed:** {straights1['MaxSpeed'].max():.1f} km/h")
            
            with col2:
                st.markdown(f"### {driver2}")
                
                # Gear usage
                gear_usage2 = get_gear_usage(tel2)
                if gear_usage2:
                    st.write("**Gear Usage:**")
                    for gear, pct in gear_usage2.items():
                        st.write(f"Gear {gear}: {pct}%")
                
                # Corner speeds
                corners2 = calculate_corner_speeds(tel2)
                if not corners2.empty:
                    st.write(f"**Corners identified:** {len(corners2)}")
                    st.write(f"**Avg min corner speed:** {corners2['MinSpeed'].mean():.1f} km/h")
                
                # Straight speeds
                straights2 = calculate_straight_speeds(tel2)
                if not straights2.empty:
                    st.write(f"**Max speed:** {straights2['MaxSpeed'].max():.1f} km/h")
            
            # DRS zones
            st.subheader("DRS Zones")
            drs_zones1 = get_drs_zones(tel1)
            drs_zones2 = get_drs_zones(tel2)
            
            if drs_zones1 or drs_zones2:
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write(f"**{driver1} DRS activations:** {len(drs_zones1)}")
                    for i, (start, end) in enumerate(drs_zones1, 1):
                        st.write(f"Zone {i}: {start:.0f}m - {end:.0f}m")
                
                with col2:
                    st.write(f"**{driver2} DRS activations:** {len(drs_zones2)}")
                    for i, (start, end) in enumerate(drs_zones2, 1):
                        st.write(f"Zone {i}: {start:.0f}m - {end:.0f}m")
            else:
                st.info("No DRS data available")
                
        except Exception as e:
            st.error(f"Error loading telemetry: {str(e)}")
            st.info("Telemetry data may not be available for this session")

# Footer
st.markdown("---")
st.markdown(
    """
    <div style='text-align: center; color: #666;'>
        <p>F1 Analysis Dashboard | Powered by FastF1 & Streamlit</p>
        <p>Data source: Formula 1 © via FastF1</p>
    </div>
    """,
    unsafe_allow_html=True
)
