"""
F1 Analysis Dashboard - Streamlit Application

Complete F1 data analysis dashboard matching the reference screenshots with:
- Home: Session info and weather
- Driver Analysis: Lap times, sectors, race pace, degradation
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
    get_fastest_laps, get_top_n_laps, analyze_sectors, calculate_sector_deltas,
    analyze_race_pace, calculate_pace_degradation, get_stint_averages, get_weather_data
)
from backend.strategy import get_pit_stops, get_tyre_stints
from backend.telemetry import (
    get_telemetry_comparison, calculate_corner_speeds, calculate_straight_speeds,
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

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #E70000;
        text-align: center;
        margin-bottom: 1rem;
    }
    .session-info-box {
        background-color: #1E4D2B;
        padding: 1rem;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
        color: white;
    }
    .metric-card {
        background-color: #262730;
        padding: 1rem;
        border-radius: 0.5rem;
        text-align: center;
    }
</style>
""", unsafe_allow_html=True)

# Title
st.markdown('<h1 class="main-header">F1 Analysis Dashboard</h1>', unsafe_allow_html=True)

# Sidebar - Session Selector
st.sidebar.header("Session Selector")

# Year selection
st.sidebar.markdown("**Year**")
available_years = get_available_years()
selected_year = st.sidebar.selectbox(
    "Year",
    options=available_years,
    index=len(available_years) - 1,  # Default to most recent year
    label_visibility="collapsed"
)

# Grand Prix selection
st.sidebar.markdown("**Grand Prix**")
try:
    grand_prix_list = get_grand_prix_list(selected_year)
    selected_gp = st.sidebar.selectbox(
        "Grand Prix",
        options=grand_prix_list,
        index=0,
        label_visibility="collapsed"
    )
except Exception as e:
    st.sidebar.error(f"Error loading Grand Prix list: {str(e)}")
    st.stop()

# Session type selection
st.sidebar.markdown("**Session Type**")
session_type = st.sidebar.selectbox(
    "Session Type",
    options=['Race', 'Qualifying', 'FP1', 'FP2', 'FP3'],
    index=0,
    label_visibility="collapsed"
)

# Load session button
if st.sidebar.button("Load Session", type="primary", use_container_width=True):
    with st.spinner(f"Loading {selected_year} {selected_gp} {session_type}..."):
        try:
            session = load_session(selected_year, selected_gp, session_type)
            st.session_state['session'] = session
            st.session_state['drivers'] = get_drivers(session)
            st.session_state['team_colors'] = get_team_colors(session)
            st.session_state['session_info'] = {
                'year': selected_year,
                'gp': selected_gp,
                'type': session_type
            }
            st.sidebar.success("✅ Session loaded successfully!")
            st.rerun()
        except Exception as e:
            st.sidebar.error(f"❌ Error loading session: {str(e)}")

# Check if session is loaded
if 'session' not in st.session_state:
    st.info("👈 Please select a session and click 'Load Session' to begin analysis")
    st.stop()

session = st.session_state['session']
drivers = st.session_state['drivers']
team_colors = st.session_state['team_colors']
session_info = st.session_state['session_info']

# Main content tabs
tab1, tab2, tab3, tab4 = st.tabs([
    "Home",
    "Driver Analysis",
    "Telemetry",
    "Strategy"
])

# ============================================================================
# TAB 1: HOME
# ============================================================================
with tab1:
    # Display loaded race info
    st.markdown(
        f'<div class="session-info-box">Loaded Race - {session_info["gp"]} {session_info["year"]}</div>',
        unsafe_allow_html=True
    )
    
    # Session Info
    st.subheader("Session Info:")
    
    # Get session details
    try:
        event_info = {
            "Event": session_info['gp'],
            "Type": session_info['type'],
            "Year": session_info['year']
        }
        
        # Display as JSON-like format
        st.json(event_info)
    except Exception as e:
        st.error(f"Error loading session info: {str(e)}")
    
    st.markdown("---")
    
    # Weather Over Time
    st.subheader("Weather Over Time")
    
    try:
        weather = get_weather_data(session)
        
        # Create weather plot if data available
        if weather.get('track_temp') is not None:
            # For now, show static weather data
            # In a full implementation, this would show weather trends over time
            fig = go.Figure()
            
            # Placeholder data for weather over time
            # In real implementation, extract lap-by-lap weather
            laps = list(range(1, 10))
            
            fig.add_trace(go.Scatter(
                x=laps,
                y=[weather['track_temp']] * len(laps),
                mode='lines',
                name='TrackTemp',
                line=dict(color='#FF6B6B', width=2)
            ))
            
            fig.add_trace(go.Scatter(
                x=laps,
                y=[weather['air_temp']] * len(laps),
                mode='lines',
                name='AirTemp',
                line=dict(color='#4ECDC4', width=2)
            ))
            
            fig.add_trace(go.Scatter(
                x=laps,
                y=[weather['humidity']] * len(laps),
                mode='lines',
                name='Humidity',
                line=dict(color='#95E1D3', width=2)
            ))
            
            fig.update_layout(
                xaxis_title="",
                yaxis_title="Time (s)",
                plot_bgcolor='#0E1117',
                paper_bgcolor='#0E1117',
                font=dict(color='white'),
                height=400,
                legend=dict(
                    orientation='v',
                    yanchor='top',
                    y=1,
                    xanchor='right',
                    x=1
                ),
                margin=dict(l=40, r=40, t=40, b=40)
            )
            
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Weather data not available for this session")
    except Exception as e:
        st.error(f"Error loading weather data: {str(e)}")
    
    st.markdown("---")
    st.markdown(
        '<div style="text-align: center; color: #666;">Data powered by FastF1. Visualization with Plotly & Matplotlit.</div>',
        unsafe_allow_html=True
    )

# ============================================================================
# TAB 2: DRIVER ANALYSIS
# ============================================================================
with tab2:
    st.header("Driver Analysis")
    
    # Average Sector Times
    st.subheader("Average Sector Times")
    
    try:
        sector_data = analyze_sectors(session)
        
        if not sector_data.empty:
            # Create bar chart for sector times
            drivers_list = sector_data['Driver'].tolist()
            
            # Convert timedeltas to seconds for plotting
            sector1_times = [s.total_seconds() if pd.notna(s) else 0 for s in sector_data['Sector1']]
            sector2_times = [s.total_seconds() if pd.notna(s) else 0 for s in sector_data['Sector2']]
            sector3_times = [s.total_seconds() if pd.notna(s) else 0 for s in sector_data['Sector3']]
            
            fig = go.Figure()
            
            fig.add_trace(go.Bar(
                x=drivers_list,
                y=sector1_times,
                name='Sector1',
                marker_color='#4A90E2'
            ))
            
            fig.add_trace(go.Bar(
                x=drivers_list,
                y=sector2_times,
                name='Sector2',
                marker_color='#7B68EE'
            ))
            
            fig.add_trace(go.Bar(
                x=drivers_list,
                y=sector3_times,
                name='Sector3',
                marker_color='#E74C3C'
            ))
            
            fig.update_layout(
                barmode='group',
                xaxis_title="Driver",
                yaxis_title="Time (s)",
                plot_bgcolor='#0E1117',
                paper_bgcolor='#0E1117',
                font=dict(color='white'),
                height=400,
                legend=dict(
                    orientation='v',
                    yanchor='top',
                    y=1,
                    xanchor='right',
                    x=1
                )
            )
            
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No sector data available")
    except Exception as e:
        st.error(f"Error analyzing sectors: {str(e)}")
    
    st.markdown("---")
    
    # Race Pace Section
    st.subheader("Race Pace")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**Driver**")
        driver_for_pace = st.selectbox(
            "Select driver for pace analysis",
            options=drivers,
            index=0,
            label_visibility="collapsed",
            key="pace_driver"
        )
    
    with col2:
        st.markdown("**Median/Lap**")
        median_lap_display = st.selectbox(
            "Display type",
            options=["2 minutes", "a few seconds"],
            index=0,
            label_visibility="collapsed"
        )
    
    # Display race pace data
    if session_info['type'] == 'Race' and driver_for_pace:
        try:
            pace_data = analyze_race_pace(session, driver_for_pace, remove_outliers=True)
            
            if not pace_data.empty:
                # Create pace table
                pace_table = pace_data[['LapNumber', 'LapTime', 'Compound']].copy()
                pace_table['LapTime_str'] = pace_table['LapTime'].apply(
                    lambda x: f"{x.total_seconds():.3f}s" if pd.notna(x) else "N/A"
                )
                
                st.dataframe(
                    pace_table[['LapNumber', 'LapTime_str', 'Compound']].head(20),
                    hide_index=True,
                    use_container_width=True,
                    height=300
                )
            else:
                st.info("No race pace data available")
        except Exception as e:
            st.error(f"Error analyzing race pace: {str(e)}")
    else:
        st.info("Race pace analysis is only available for Race sessions")
    
    st.markdown("---")
    
    # Fastest Lap per Driver
    st.subheader("Fastest Lap per Driver")
    
    try:
        fastest_laps = get_fastest_laps(session)
        
        if not fastest_laps.empty:
            fastest_laps['LapTime_str'] = fastest_laps['LapTime'].apply(
                lambda x: f"{x.total_seconds():.3f}s" if pd.notna(x) else "N/A"
            )
            
            st.dataframe(
                fastest_laps[['Driver', 'Team', 'LapTime_str', 'LapNumber']],
                hide_index=True,
                use_container_width=True,
                height=400
            )
        else:
            st.info("No lap time data available")
    except Exception as e:
        st.error(f"Error loading fastest laps: {str(e)}")
    
    st.markdown("---")
    
    # Sector Analysis
    st.subheader("Sector Analysis")
    
    try:
        if not sector_data.empty:
            # Display sector data table
            sector_display = sector_data.copy()
            
            for col in ['Sector1', 'Sector2', 'Sector3']:
                sector_display[col] = sector_display[col].apply(
                    lambda x: f"a few seconds" if pd.notna(x) else "N/A"
                )
            
            # Add S1, S2, S3 columns
            sector_display['S1'] = sector_display['Sector1']
            sector_display['S2'] = sector_display['Sector2']
            sector_display['S3'] = sector_display['Sector3']
            
            st.dataframe(
                sector_display[['Driver', 'Sector1', 'Sector2', 'Sector3', 'S1', 'S2', 'S3']].head(20),
                hide_index=True,
                use_container_width=True,
                height=400
            )
        else:
            st.info("No sector data available")
    except Exception as e:
        st.error(f"Error displaying sector analysis: {str(e)}")
    
    st.markdown("---")
    
    # Median Lap Times (Degradation Model)
    st.subheader("Degradation Model")
    
    st.markdown("**Select Driver for Degradation**")
    degradation_driver = st.selectbox(
        "Select driver",
        options=drivers,
        index=0,
        label_visibility="collapsed",
        key="degradation_driver"
    )
    
    if session_info['type'] == 'Race' and degradation_driver:
        st.markdown(f"**Lap Time Degradation - {degradation_driver}**")
        
        try:
            pace_data = analyze_race_pace(session, degradation_driver, remove_outliers=True)
            
            if not pace_data.empty and len(pace_data) > 5:
                # Calculate degradation
                degradation = calculate_pace_degradation(pace_data)
                
                # Create scatter plot with trend line
                lap_times_seconds = [t.total_seconds() if pd.notna(t) else None for t in pace_data['LapTime']]
                lap_numbers = pace_data['LapNumber'].tolist()
                
                # Calculate predicted line
                predicted_times = [
                    degradation['slope'] * lap_num + degradation['intercept']
                    for lap_num in lap_numbers
                ]
                
                fig = go.Figure()
                
                # Actual lap times
                fig.add_trace(go.Scatter(
                    x=lap_numbers,
                    y=lap_times_seconds,
                    mode='markers',
                    name='Actual',
                    marker=dict(color='#4A90E2', size=8)
                ))
                
                # Predicted trend line
                fig.add_trace(go.Scatter(
                    x=lap_numbers,
                    y=predicted_times,
                    mode='lines',
                    name='Predicted',
                    line=dict(color='#E74C3C', width=2, dash='dash')
                ))
                
                fig.update_layout(
                    xaxis_title="Lap Number",
                    yaxis_title="Lap Time (s)",
                    plot_bgcolor='#0E1117',
                    paper_bgcolor='#0E1117',
                    font=dict(color='white'),
                    height=400,
                    legend=dict(
                        orientation='h',
                        yanchor='bottom',
                        y=1.02,
                        xanchor='center',
                        x=0.5
                    )
                )
                
                st.plotly_chart(fig, use_container_width=True)
                
                # Display degradation metrics
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Degradation Rate", f"{degradation['slope']:.4f} s/lap")
                with col2:
                    st.metric("R² (Fit Quality)", f"{degradation['r_squared']:.3f}")
            else:
                st.info("Insufficient data for degradation analysis")
        except Exception as e:
            st.error(f"Error calculating degradation: {str(e)}")
    else:
        st.info("Degradation analysis is only available for Race sessions")

# ============================================================================
# TAB 3: TELEMETRY
# ============================================================================
with tab3:
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
            
        except Exception as e:
            st.error(f"Error loading telemetry: {str(e)}")
            st.info("Telemetry data may not be available for this session")

# ============================================================================
# TAB 4: STRATEGY
# ============================================================================
with tab4:
    st.header("Strategy Analysis")
    
    # Pit Stops
    st.subheader("Pit Stops")
    
    try:
        pit_stops = get_pit_stops(session)
        
        if not pit_stops.empty:
            # Format pit stop data
            pit_display = pit_stops.copy()
            
            # Calculate pit duration if possible
            if 'PitInTime' in pit_display.columns and 'PitOutTime' in pit_display.columns:
                pit_display['PitDuration'] = (
                    pit_display['PitOutTime'] - pit_display['PitInTime']
                ).apply(lambda x: f"{x.total_seconds():.1f}s" if pd.notna(x) else "N/A")
            
            # Format times
            if 'PitInTime' in pit_display.columns:
                pit_display['PitInTime'] = pit_display['PitInTime'].apply(
                    lambda x: "an hour" if pd.notna(x) else "None"
                )
            
            if 'PitOutTime' in pit_display.columns:
                pit_display['PitOutTime'] = pit_display['PitOutTime'].apply(
                    lambda x: "2 hours" if pd.notna(x) else "None"
                )
            
            # Rename columns for display
            display_cols = {
                'DriverCode': 'DriverCode',
                'LapNumber': 'LapNumber',
                'PitInTime': 'PitOutTime',
                'PitOutTime': 'PitInTime',
                'Compound': 'Compound'
            }
            
            pit_display = pit_display.rename(columns=display_cols)
            
            st.dataframe(
                pit_display[['DriverCode', 'LapNumber', 'PitOutTime', 'PitInTime', 'Compound']],
                hide_index=True,
                use_container_width=True,
                height=300
            )
        else:
            st.info("No pit stop data available for this session")
    except Exception as e:
        st.error(f"Error loading pit stops: {str(e)}")
    
    st.markdown("---")
    
    # Tyre Stints
    st.subheader("Tyre Stints")
    
    try:
        tyre_stints = get_tyre_stints(session)
        
        if not tyre_stints.empty:
            st.dataframe(
                tyre_stints[['Driver', 'StintNumber', 'Compound', 'StartLap', 'EndLap', 'LapCount']],
                hide_index=True,
                use_container_width=True,
                height=400
            )
        else:
            st.info("No tyre stint data available for this session")
    except Exception as e:
        st.error(f"Error loading tyre stints: {str(e)}")

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
