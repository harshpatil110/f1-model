"""
Telemetry Module for F1 Analysis Dashboard

This module provides functions to extract and analyze detailed telemetry data
including speed, throttle, brake, gear, RPM, and DRS usage for driver comparison.
"""

from typing import Tuple, Dict, List, Optional, Union
import pandas as pd
import numpy as np
import fastf1
import streamlit as st


@st.cache_data(ttl=3600, show_spinner=False)
def get_telemetry_comparison(_session: fastf1.core.Session,
                            driver1: str, 
                            driver2: str,
                            lap_type: Union[str, int] = "fastest") -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Get telemetry data for two drivers.
    
    Args:
        _session: Loaded FastF1 session object (underscore prefix for Streamlit caching)
        driver1: First driver abbreviation (e.g., 'VER')
        driver2: Second driver abbreviation (e.g., 'HAM')
        lap_type: 'fastest' for fastest lap or specific lap number (int)
    
    Returns:
        Tuple of (driver1_telemetry, driver2_telemetry) DataFrames with columns:
        [Distance, Time, Speed, Throttle, Brake, nGear, RPM, DRS, X, Y]
    
    Raises:
        ValueError: If drivers not found or telemetry unavailable
    """
    if _session.laps is None or _session.laps.empty:
        raise ValueError("Session has no lap data")
    
    # Get laps for both drivers
    driver1_laps = _session.laps.pick_driver(driver1)
    driver2_laps = _session.laps.pick_driver(driver2)
    
    if driver1_laps.empty:
        raise ValueError(f"Driver '{driver1}' not found in session")
    if driver2_laps.empty:
        raise ValueError(f"Driver '{driver2}' not found in session")
    
    # Select the appropriate lap based on lap_type
    if lap_type == "fastest":
        # Get fastest lap for each driver
        valid_laps1 = driver1_laps[driver1_laps['LapTime'].notna()]
        valid_laps2 = driver2_laps[driver2_laps['LapTime'].notna()]
        
        if valid_laps1.empty or valid_laps2.empty:
            raise ValueError("No valid laps found for one or both drivers")
        
        lap1 = valid_laps1.loc[valid_laps1['LapTime'].idxmin()]
        lap2 = valid_laps2.loc[valid_laps2['LapTime'].idxmin()]
    else:
        # Get specific lap number
        lap_number = int(lap_type)
        lap1_filtered = driver1_laps[driver1_laps['LapNumber'] == lap_number]
        lap2_filtered = driver2_laps[driver2_laps['LapNumber'] == lap_number]
        
        if lap1_filtered.empty:
            raise ValueError(f"Lap {lap_number} not found for driver '{driver1}'")
        if lap2_filtered.empty:
            raise ValueError(f"Lap {lap_number} not found for driver '{driver2}'")
        
        lap1 = lap1_filtered.iloc[0]
        lap2 = lap2_filtered.iloc[0]
    
    # Get telemetry for both laps
    try:
        telemetry1 = lap1.get_telemetry()
        telemetry2 = lap2.get_telemetry()
    except Exception as e:
        raise ValueError(f"Failed to load telemetry data: {str(e)}")
    
    if telemetry1.empty or telemetry2.empty:
        raise ValueError("Telemetry data is empty for one or both drivers")
    
    return telemetry1, telemetry2


@st.cache_data(ttl=3600, show_spinner=False)
def get_speed_trace(lap: fastf1.core.Lap) -> pd.DataFrame:
    """
    Extract speed vs distance data for a lap.
    
    Args:
        lap: FastF1 Lap object
    
    Returns:
        DataFrame with columns: [Distance, Speed]
    """
    try:
        telemetry = lap.get_telemetry()
    except Exception as e:
        raise ValueError(f"Failed to load telemetry: {str(e)}")
    
    if telemetry.empty:
        return pd.DataFrame(columns=['Distance', 'Speed'])
    
    # Extract speed and distance
    speed_data = telemetry[['Distance', 'Speed']].copy()
    
    return speed_data


@st.cache_data(ttl=3600, show_spinner=False)
def get_brake_trace(lap: fastf1.core.Lap) -> pd.DataFrame:
    """
    Extract brake pressure vs distance data for a lap.
    
    Args:
        lap: FastF1 Lap object
    
    Returns:
        DataFrame with columns: [Distance, Brake]
    """
    try:
        telemetry = lap.get_telemetry()
    except Exception as e:
        raise ValueError(f"Failed to load telemetry: {str(e)}")
    
    if telemetry.empty:
        return pd.DataFrame(columns=['Distance', 'Brake'])
    
    # Extract brake and distance
    brake_data = telemetry[['Distance', 'Brake']].copy()
    
    return brake_data


@st.cache_data(ttl=3600, show_spinner=False)
def get_throttle_trace(lap: fastf1.core.Lap) -> pd.DataFrame:
    """
    Extract throttle position vs distance data for a lap.
    
    Args:
        lap: FastF1 Lap object
    
    Returns:
        DataFrame with columns: [Distance, Throttle]
    """
    try:
        telemetry = lap.get_telemetry()
    except Exception as e:
        raise ValueError(f"Failed to load telemetry: {str(e)}")
    
    if telemetry.empty:
        return pd.DataFrame(columns=['Distance', 'Throttle'])
    
    # Extract throttle and distance
    throttle_data = telemetry[['Distance', 'Throttle']].copy()
    
    return throttle_data



@st.cache_data(ttl=3600, show_spinner=False)
def calculate_corner_speeds(telemetry: pd.DataFrame, 
                           speed_threshold: int = 200) -> pd.DataFrame:
    """
    Identify corners (speed < threshold) and extract minimum speeds.
    
    Args:
        telemetry: DataFrame with telemetry data (must include 'Speed' and 'Distance' columns)
        speed_threshold: Speed threshold in km/h to identify corners (default: 200)
    
    Returns:
        DataFrame with columns: [CornerNumber, MinSpeed, Distance]
    """
    if telemetry.empty or 'Speed' not in telemetry.columns or 'Distance' not in telemetry.columns:
        return pd.DataFrame(columns=['CornerNumber', 'MinSpeed', 'Distance'])
    
    # Identify corner sections (speed below threshold)
    telemetry = telemetry.copy()
    telemetry['IsCorner'] = telemetry['Speed'] < speed_threshold
    
    # Find groups of consecutive corner points
    telemetry['CornerGroup'] = (telemetry['IsCorner'] != telemetry['IsCorner'].shift()).cumsum()
    
    corners = []
    corner_number = 1
    
    # Process each group
    for group_id, group_data in telemetry.groupby('CornerGroup'):
        # Only process groups that are actually corners
        if group_data['IsCorner'].iloc[0]:
            # Find minimum speed in this corner
            min_speed_idx = group_data['Speed'].idxmin()
            min_speed = group_data.loc[min_speed_idx, 'Speed']
            distance = group_data.loc[min_speed_idx, 'Distance']
            
            corners.append({
                'CornerNumber': corner_number,
                'MinSpeed': min_speed,
                'Distance': distance
            })
            corner_number += 1
    
    result_df = pd.DataFrame(corners)
    
    return result_df


@st.cache_data(ttl=3600, show_spinner=False)
def calculate_straight_speeds(telemetry: pd.DataFrame) -> pd.DataFrame:
    """
    Identify straights and extract maximum speeds.
    
    Args:
        telemetry: DataFrame with telemetry data (must include 'Speed' and 'Distance' columns)
    
    Returns:
        DataFrame with columns: [StraightNumber, MaxSpeed, Distance]
    """
    if telemetry.empty or 'Speed' not in telemetry.columns or 'Distance' not in telemetry.columns:
        return pd.DataFrame(columns=['StraightNumber', 'MaxSpeed', 'Distance'])
    
    # Identify straight sections (speed above 250 km/h as a reasonable threshold for straights)
    telemetry = telemetry.copy()
    telemetry['IsStraight'] = telemetry['Speed'] > 250
    
    # Find groups of consecutive straight points
    telemetry['StraightGroup'] = (telemetry['IsStraight'] != telemetry['IsStraight'].shift()).cumsum()
    
    straights = []
    straight_number = 1
    
    # Process each group
    for group_id, group_data in telemetry.groupby('StraightGroup'):
        # Only process groups that are actually straights
        if group_data['IsStraight'].iloc[0]:
            # Find maximum speed in this straight
            max_speed_idx = group_data['Speed'].idxmax()
            max_speed = group_data.loc[max_speed_idx, 'Speed']
            distance = group_data.loc[max_speed_idx, 'Distance']
            
            straights.append({
                'StraightNumber': straight_number,
                'MaxSpeed': max_speed,
                'Distance': distance
            })
            straight_number += 1
    
    result_df = pd.DataFrame(straights)
    
    return result_df


@st.cache_data(ttl=3600, show_spinner=False)
def get_gear_usage(telemetry: pd.DataFrame) -> Dict[int, float]:
    """
    Calculate percentage of lap in each gear.
    
    Args:
        telemetry: DataFrame with telemetry data (must include 'nGear' column)
    
    Returns:
        Dictionary mapping gear_number to percentage_of_lap
        Example: {1: 2.5, 2: 5.0, 3: 10.0, 4: 15.0, 5: 20.0, 6: 25.0, 7: 15.0, 8: 7.5}
    """
    if telemetry.empty or 'nGear' not in telemetry.columns:
        return {}
    
    # Count occurrences of each gear
    gear_counts = telemetry['nGear'].value_counts()
    
    # Calculate total data points
    total_points = len(telemetry)
    
    # Calculate percentage for each gear
    gear_usage = {}
    for gear, count in gear_counts.items():
        # Skip invalid gear values (NaN, 0, negative)
        if pd.notna(gear) and gear > 0:
            percentage = (count / total_points) * 100
            gear_usage[int(gear)] = round(percentage, 2)
    
    # Sort by gear number
    gear_usage = dict(sorted(gear_usage.items()))
    
    return gear_usage


@st.cache_data(ttl=3600, show_spinner=False)
def get_drs_zones(telemetry: pd.DataFrame) -> List[Tuple[float, float]]:
    """
    Identify DRS activation zones.
    
    Args:
        telemetry: DataFrame with telemetry data (must include 'DRS' and 'Distance' columns)
    
    Returns:
        List of (start_distance, end_distance) tuples for each DRS zone
        Example: [(1500.0, 2000.0), (4000.0, 4500.0)]
    
    Note:
        DRS values: 0 = closed, 1 = open, 8-14 = available but not activated
    """
    if telemetry.empty or 'DRS' not in telemetry.columns or 'Distance' not in telemetry.columns:
        return []
    
    telemetry = telemetry.copy()
    
    # DRS is active when value is greater than 0 (typically 1 for open, or 8-14 for available zones)
    telemetry['DRSActive'] = telemetry['DRS'] > 0
    
    # Find groups of consecutive DRS active points
    telemetry['DRSGroup'] = (telemetry['DRSActive'] != telemetry['DRSActive'].shift()).cumsum()
    
    drs_zones = []
    
    # Process each group
    for group_id, group_data in telemetry.groupby('DRSGroup'):
        # Only process groups where DRS is active
        if group_data['DRSActive'].iloc[0]:
            start_distance = group_data['Distance'].iloc[0]
            end_distance = group_data['Distance'].iloc[-1]
            
            # Only include zones with reasonable length (> 100m to filter noise)
            if end_distance - start_distance > 100:
                drs_zones.append((float(start_distance), float(end_distance)))
    
    return drs_zones



@st.cache_data(ttl=3600, show_spinner=False)
def load_aligned_telemetry(_session: fastf1.core.Session,
                          driver1: str,
                          driver2: str,
                          lap_type: Union[str, int] = "fastest") -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Load and align telemetry data for two drivers on a common distance reference.
    
    Args:
        _session: Loaded FastF1 session object
        driver1: First driver abbreviation (e.g., 'VER')
        driver2: Second driver abbreviation (e.g., 'HAM')
        lap_type: 'fastest' for fastest lap or specific lap number (int)
    
    Returns:
        Tuple of (aligned_driver1_telemetry, aligned_driver2_telemetry, common_distance_array)
        Each DataFrame contains interpolated values aligned to common distance points
    
    Raises:
        ValueError: If drivers not found or telemetry unavailable
    """
    # Get raw telemetry for both drivers
    tel1, tel2 = get_telemetry_comparison(_session, driver1, driver2, lap_type)
    
    # Ensure Distance column exists and add if needed
    if 'Distance' not in tel1.columns:
        tel1 = tel1.add_distance()
    if 'Distance' not in tel2.columns:
        tel2 = tel2.add_distance()
    
    # Remove NaN values from critical columns
    tel1 = tel1.dropna(subset=['Distance', 'X', 'Y'])
    tel2 = tel2.dropna(subset=['Distance', 'X', 'Y'])
    
    if tel1.empty or tel2.empty:
        raise ValueError("Insufficient telemetry data after cleaning")
    
    # Create common distance reference (use the shorter lap as reference)
    min_distance = max(tel1['Distance'].min(), tel2['Distance'].min())
    max_distance = min(tel1['Distance'].max(), tel2['Distance'].max())
    
    # Create common distance array with ~500 points for smooth visualization
    num_points = min(500, int(max_distance - min_distance))
    common_distance = np.linspace(min_distance, max_distance, num_points)
    
    # Interpolate driver 1 data
    aligned_tel1 = pd.DataFrame({'Distance': common_distance})
    for col in ['X', 'Y', 'Speed', 'Throttle', 'Brake', 'nGear', 'DRS']:
        if col in tel1.columns:
            aligned_tel1[col] = np.interp(
                common_distance,
                tel1['Distance'].values,
                tel1[col].fillna(0).values
            )
    
    # Interpolate driver 2 data
    aligned_tel2 = pd.DataFrame({'Distance': common_distance})
    for col in ['X', 'Y', 'Speed', 'Throttle', 'Brake', 'nGear', 'DRS']:
        if col in tel2.columns:
            aligned_tel2[col] = np.interp(
                common_distance,
                tel2['Distance'].values,
                tel2[col].fillna(0).values
            )
    
    return aligned_tel1, aligned_tel2, common_distance


def _get_driver_colors(_session: fastf1.core.Session, 
                       driver1: str, 
                       driver2: str) -> Tuple[str, str]:
    """
    Get team colors for two drivers, ensuring they are distinguishable.
    
    Args:
        _session: Loaded FastF1 session object
        driver1: First driver abbreviation
        driver2: Second driver abbreviation
    
    Returns:
        Tuple of (driver1_color, driver2_color) as hex strings
    """
    try:
        # Get driver laps to determine teams
        driver1_laps = _session.laps.pick_driver(driver1)
        driver2_laps = _session.laps.pick_driver(driver2)
        
        if not driver1_laps.empty and not driver2_laps.empty:
            team1 = driver1_laps.iloc[0]['Team']
            team2 = driver2_laps.iloc[0]['Team']
            
            color1 = fastf1.plotting.team_color(team1)
            color2 = fastf1.plotting.team_color(team2)
            
            # If same team (teammates), create contrasting colors
            if team1 == team2:
                # Use primary color for driver1, lighter shade for driver2
                color1 = color1
                # Create a lighter version by blending with white
                color2 = _lighten_color(color1, 0.4)
            
            return color1, color2
    except Exception:
        pass
    
    # Fallback colors
    return '#3671C6', '#FF1E1E'


def _lighten_color(hex_color: str, factor: float = 0.3) -> str:
    """
    Lighten a hex color by blending with white.
    
    Args:
        hex_color: Hex color string (e.g., '#3671C6')
        factor: Lightening factor (0-1, higher = lighter)
    
    Returns:
        Lightened hex color string
    """
    # Remove '#' if present
    hex_color = hex_color.lstrip('#')
    
    # Convert to RGB
    r = int(hex_color[0:2], 16)
    g = int(hex_color[2:4], 16)
    b = int(hex_color[4:6], 16)
    
    # Blend with white
    r = int(r + (255 - r) * factor)
    g = int(g + (255 - g) * factor)
    b = int(b + (255 - b) * factor)
    
    # Convert back to hex
    return f'#{r:02x}{g:02x}{b:02x}'


@st.cache_data(ttl=3600, show_spinner=False)
def build_circuit_comparison_map(_session: fastf1.core.Session,
                                driver1: str,
                                driver2: str,
                                lap_type: Union[str, int] = "fastest",
                                delta_threshold: float = 0.5) -> 'plotly.graph_objects.Figure':
    """
    Build a circuit map showing performance comparison between two drivers.
    
    The circuit is color-coded by segments:
    - Blue: Driver 1 faster
    - Red: Driver 2 faster
    - Grey: Equal/negligible difference
    
    Args:
        _session: Loaded FastF1 session object
        driver1: First driver abbreviation (e.g., 'VER')
        driver2: Second driver abbreviation (e.g., 'HAM')
        lap_type: 'fastest' for fastest lap or specific lap number (int)
        delta_threshold: Speed difference threshold in km/h for color coding (default: 0.5)
    
    Returns:
        Plotly Figure object with circuit map and performance comparison
    
    Raises:
        ValueError: If drivers not found or telemetry unavailable
    """
    try:
        import plotly.graph_objects as go
    except ImportError:
        raise ImportError("plotly is required for circuit map visualization")
    
    # Load aligned telemetry
    tel1, tel2, common_distance = load_aligned_telemetry(_session, driver1, driver2, lap_type)
    
    # Calculate speed delta (positive = driver1 faster)
    speed_delta = tel1['Speed'] - tel2['Speed']
    
    # Get driver colors
    color1, color2 = _get_driver_colors(_session, driver1, driver2)
    
    # Create figure
    fig = go.Figure()
    
    # Identify segments where faster driver changes
    faster_driver = np.where(speed_delta > delta_threshold, 1,
                            np.where(speed_delta < -delta_threshold, 2, 0))
    
    # Find segment boundaries (where faster driver changes)
    segment_changes = np.where(np.diff(faster_driver) != 0)[0] + 1
    segment_starts = np.concatenate([[0], segment_changes])
    segment_ends = np.concatenate([segment_changes, [len(tel1)]])
    
    # Plot each segment with appropriate color
    for start, end in zip(segment_starts, segment_ends):
        if start >= end:
            continue
        
        segment_tel1 = tel1.iloc[start:end+1]
        segment_tel2 = tel2.iloc[start:end+1]
        segment_delta = speed_delta.iloc[start:end+1]
        
        # Determine segment color
        avg_delta = segment_delta.mean()
        if avg_delta > delta_threshold:
            color = color1
            faster = driver1
        elif avg_delta < -delta_threshold:
            color = color2
            faster = driver2
        else:
            color = 'lightgrey'
            faster = 'Equal'
        
        # Create hover text
        hover_text = []
        for i in range(len(segment_tel1)):
            distance = segment_tel1['Distance'].iloc[i]
            speed1 = segment_tel1['Speed'].iloc[i]
            speed2 = segment_tel2['Speed'].iloc[i]
            delta = segment_delta.iloc[i]
            
            # Get additional telemetry data
            throttle1 = segment_tel1.get('Throttle', pd.Series([0])).iloc[i]
            throttle2 = segment_tel2.get('Throttle', pd.Series([0])).iloc[i]
            brake1 = segment_tel1.get('Brake', pd.Series([0])).iloc[i]
            brake2 = segment_tel2.get('Brake', pd.Series([0])).iloc[i]
            gear1 = int(segment_tel1.get('nGear', pd.Series([0])).iloc[i])
            gear2 = int(segment_tel2.get('nGear', pd.Series([0])).iloc[i])
            drs1 = segment_tel1.get('DRS', pd.Series([0])).iloc[i]
            drs2 = segment_tel2.get('DRS', pd.Series([0])).iloc[i]
            
            drs1_status = 'Active' if drs1 > 0 else 'Inactive'
            drs2_status = 'Active' if drs2 > 0 else 'Inactive'
            
            hover = (
                f"<b>Distance:</b> {distance:.0f}m<br>"
                f"<b>{driver1} Speed:</b> {speed1:.1f} km/h<br>"
                f"<b>{driver2} Speed:</b> {speed2:.1f} km/h<br>"
                f"<b>Δ Speed:</b> {delta:+.1f} km/h<br>"
                f"<b>Faster:</b> {faster}<br>"
                f"<br>"
                f"<b>{driver1}:</b> Gear {gear1} | Throttle {throttle1:.0f}% | Brake {brake1:.0f}% | DRS {drs1_status}<br>"
                f"<b>{driver2}:</b> Gear {gear2} | Throttle {throttle2:.0f}% | Brake {brake2:.0f}% | DRS {drs2_status}"
            )
            hover_text.append(hover)
        
        # Add trace for this segment
        fig.add_trace(go.Scatter(
            x=segment_tel1['X'],
            y=segment_tel1['Y'],
            mode='lines',
            line=dict(color=color, width=5),
            hovertemplate='%{text}<extra></extra>',
            text=hover_text,
            showlegend=False,
            name=f'{faster} faster'
        ))
    
    # Add legend traces (invisible points just for legend)
    fig.add_trace(go.Scatter(
        x=[None], y=[None],
        mode='lines',
        line=dict(color=color1, width=5),
        name=f'{driver1} faster',
        showlegend=True
    ))
    
    fig.add_trace(go.Scatter(
        x=[None], y=[None],
        mode='lines',
        line=dict(color=color2, width=5),
        name=f'{driver2} faster',
        showlegend=True
    ))
    
    fig.add_trace(go.Scatter(
        x=[None], y=[None],
        mode='lines',
        line=dict(color='lightgrey', width=5),
        name='Equal pace',
        showlegend=True
    ))
    
    # Update layout
    fig.update_layout(
        title=dict(
            text=f"Circuit Map — {driver1} vs {driver2} Performance Comparison",
            x=0.5,
            xanchor='center',
            font=dict(size=18, color='white')
        ),
        xaxis=dict(
            showgrid=False,
            showticklabels=False,
            zeroline=False,
            title=''
        ),
        yaxis=dict(
            showgrid=False,
            showticklabels=False,
            zeroline=False,
            title='',
            scaleanchor='x',
            scaleratio=1
        ),
        plot_bgcolor='#0E1117',
        paper_bgcolor='#0E1117',
        font=dict(color='white'),
        hovermode='closest',
        legend=dict(
            orientation='h',
            yanchor='bottom',
            y=1.02,
            xanchor='center',
            x=0.5,
            bgcolor='rgba(0,0,0,0.5)',
            bordercolor='white',
            borderwidth=1
        ),
        margin=dict(l=20, r=20, t=80, b=20),
        height=600
    )
    
    return fig
