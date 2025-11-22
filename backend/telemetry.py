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
