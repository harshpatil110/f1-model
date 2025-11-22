"""
Strategy Analysis Module for F1 Analysis Dashboard

This module provides race strategy analysis including pit stops and tyre stints.
"""

import pandas as pd
import streamlit as st
import fastf1


@st.cache_data(ttl=3600, show_spinner=False)
def get_pit_stops(_session: fastf1.core.Session) -> pd.DataFrame:
    """
    Extract pit stop data from session.
    
    Args:
        _session: Loaded FastF1 session object
    
    Returns:
        DataFrame with columns: [DriverCode, LapNumber, PitInTime, PitTime, Compound]
    """
    if _session.laps is None or _session.laps.empty:
        return pd.DataFrame(columns=['DriverCode', 'LapNumber', 'PitInTime', 'PitTime', 'Compound'])
    
    pit_stops = []
    
    # Get all laps with pit stops
    pit_laps = _session.laps[_session.laps['PitInTime'].notna()].copy()
    
    for _, lap in pit_laps.iterrows():
        pit_stops.append({
            'DriverCode': lap['Driver'],
            'LapNumber': lap['LapNumber'],
            'PitInTime': lap['PitInTime'],
            'PitOutTime': lap['PitOutTime'],
            'Compound': lap['Compound']
        })
    
    result_df = pd.DataFrame(pit_stops)
    
    if not result_df.empty:
        result_df = result_df.sort_values(['DriverCode', 'LapNumber']).reset_index(drop=True)
    
    return result_df


@st.cache_data(ttl=3600, show_spinner=False)
def get_tyre_stints(_session: fastf1.core.Session) -> pd.DataFrame:
    """
    Extract tyre stint information for all drivers.
    
    Args:
        _session: Loaded FastF1 session object
    
    Returns:
        DataFrame with columns: [Driver, StintNumber, Compound, StartLap, EndLap, LapCount]
    """
    if _session.laps is None or _session.laps.empty:
        return pd.DataFrame(columns=['Driver', 'StintNumber', 'Compound', 'StartLap', 'EndLap', 'LapCount'])
    
    stints = []
    
    drivers = _session.laps['Driver'].unique()
    
    for driver in drivers:
        driver_laps = _session.laps.pick_driver(driver).copy()
        
        if driver_laps.empty:
            continue
        
        # Identify stint changes (compound changes)
        driver_laps['StintNumber'] = (driver_laps['Compound'] != driver_laps['Compound'].shift()).cumsum()
        
        # Group by stint
        for stint_num, stint_laps in driver_laps.groupby('StintNumber'):
            stints.append({
                'Driver': driver,
                'StintNumber': int(stint_num),
                'Compound': stint_laps['Compound'].iloc[0],
                'StartLap': int(stint_laps['LapNumber'].min()),
                'EndLap': int(stint_laps['LapNumber'].max()),
                'LapCount': len(stint_laps)
            })
    
    result_df = pd.DataFrame(stints)
    
    if not result_df.empty:
        result_df = result_df.sort_values(['Driver', 'StintNumber']).reset_index(drop=True)
    
    return result_df
