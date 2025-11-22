"""
Analysis Module for F1 Analysis Dashboard

This module provides core race data analysis functions including lap times,
sector analysis, race pace, and weather data extraction.
"""

from typing import Dict, Any, List, Optional
import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
import fastf1
import streamlit as st


@st.cache_data(ttl=3600, show_spinner=False)
def get_fastest_laps(_session: fastf1.core.Session) -> pd.DataFrame:
    """
    Extract fastest lap for each driver.
    
    Args:
        _session: Loaded FastF1 session object (underscore prefix for Streamlit caching)
    
    Returns:
        DataFrame with columns: [Driver, Team, LapTime, LapNumber]
        Sorted by lap time (fastest first)
    """
    if _session.laps is None or _session.laps.empty:
        return pd.DataFrame(columns=['Driver', 'Team', 'LapTime', 'LapNumber'])
    
    fastest_laps = []
    
    # Get unique drivers
    drivers = _session.laps['Driver'].unique()
    
    for driver in drivers:
        # Get all laps for this driver
        driver_laps = _session.laps.pick_driver(driver)
        
        # Filter out invalid laps (no time recorded)
        valid_laps = driver_laps[driver_laps['LapTime'].notna()]
        
        if not valid_laps.empty:
            # Find fastest lap
            fastest_lap = valid_laps.loc[valid_laps['LapTime'].idxmin()]
            
            fastest_laps.append({
                'Driver': driver,
                'Team': fastest_lap['Team'],
                'LapTime': fastest_lap['LapTime'],
                'LapNumber': fastest_lap['LapNumber']
            })
    
    # Create DataFrame and sort by lap time
    result_df = pd.DataFrame(fastest_laps)
    
    if not result_df.empty:
        result_df = result_df.sort_values('LapTime').reset_index(drop=True)
    
    return result_df


@st.cache_data(ttl=3600, show_spinner=False)
def get_top_n_laps(_session: fastf1.core.Session, n: int = 10) -> pd.DataFrame:
    """
    Return top N fastest laps across all drivers.
    
    Args:
        _session: Loaded FastF1 session object
        n: Number of top laps to return (default: 10)
    
    Returns:
        DataFrame with columns: [Driver, Team, LapTime, LapNumber]
        Sorted by lap time (fastest first)
    """
    if _session.laps is None or _session.laps.empty:
        return pd.DataFrame(columns=['Driver', 'Team', 'LapTime', 'LapNumber'])
    
    # Filter out invalid laps
    valid_laps = _session.laps[_session.laps['LapTime'].notna()].copy()
    
    if valid_laps.empty:
        return pd.DataFrame(columns=['Driver', 'Team', 'LapTime', 'LapNumber'])
    
    # Sort by lap time and take top N
    top_laps = valid_laps.nsmallest(n, 'LapTime')
    
    # Select and return relevant columns
    result_df = top_laps[['Driver', 'Team', 'LapTime', 'LapNumber']].copy()
    result_df = result_df.reset_index(drop=True)
    
    return result_df


@st.cache_data(ttl=3600, show_spinner=False)
def analyze_sectors(_session: fastf1.core.Session) -> pd.DataFrame:
    """
    Calculate average sector times for each driver.
    
    Args:
        _session: Loaded FastF1 session object
    
    Returns:
        DataFrame with columns: [Driver, Sector1, Sector2, Sector3, TotalTime]
        Sorted by total time (fastest first)
    """
    if _session.laps is None or _session.laps.empty:
        return pd.DataFrame(columns=['Driver', 'Sector1', 'Sector2', 'Sector3', 'TotalTime'])
    
    sector_data = []
    drivers = _session.laps['Driver'].unique()
    
    for driver in drivers:
        driver_laps = _session.laps.pick_driver(driver)
        
        # Filter laps with valid sector times
        valid_laps = driver_laps[
            driver_laps['Sector1Time'].notna() &
            driver_laps['Sector2Time'].notna() &
            driver_laps['Sector3Time'].notna()
        ]
        
        if not valid_laps.empty:
            # Calculate average sector times
            sector1_avg = valid_laps['Sector1Time'].mean()
            sector2_avg = valid_laps['Sector2Time'].mean()
            sector3_avg = valid_laps['Sector3Time'].mean()
            total_avg = sector1_avg + sector2_avg + sector3_avg
            
            sector_data.append({
                'Driver': driver,
                'Sector1': sector1_avg,
                'Sector2': sector2_avg,
                'Sector3': sector3_avg,
                'TotalTime': total_avg
            })
    
    result_df = pd.DataFrame(sector_data)
    
    if not result_df.empty:
        result_df = result_df.sort_values('TotalTime').reset_index(drop=True)
    
    return result_df


@st.cache_data(ttl=3600, show_spinner=False)
def calculate_sector_deltas(_session: fastf1.core.Session, reference_driver: str) -> pd.DataFrame:
    """
    Calculate sector time deltas relative to reference driver.
    
    Args:
        _session: Loaded FastF1 session object
        reference_driver: Driver abbreviation to use as reference (e.g., 'VER')
    
    Returns:
        DataFrame with columns: [Driver, Sector1Delta, Sector2Delta, Sector3Delta, TotalDelta]
        Positive values mean slower than reference, negative means faster
    """
    # Get sector analysis for all drivers
    sector_df = analyze_sectors(_session)
    
    if sector_df.empty:
        return pd.DataFrame(columns=['Driver', 'Sector1Delta', 'Sector2Delta', 'Sector3Delta', 'TotalDelta'])
    
    # Find reference driver's times
    reference_data = sector_df[sector_df['Driver'] == reference_driver]
    
    if reference_data.empty:
        raise ValueError(f"Reference driver '{reference_driver}' not found in session")
    
    ref_s1 = reference_data.iloc[0]['Sector1']
    ref_s2 = reference_data.iloc[0]['Sector2']
    ref_s3 = reference_data.iloc[0]['Sector3']
    ref_total = reference_data.iloc[0]['TotalTime']
    
    # Calculate deltas for all drivers
    deltas = []
    for _, row in sector_df.iterrows():
        deltas.append({
            'Driver': row['Driver'],
            'Sector1Delta': row['Sector1'] - ref_s1,
            'Sector2Delta': row['Sector2'] - ref_s2,
            'Sector3Delta': row['Sector3'] - ref_s3,
            'TotalDelta': row['TotalTime'] - ref_total
        })
    
    result_df = pd.DataFrame(deltas)
    result_df = result_df.sort_values('TotalDelta').reset_index(drop=True)
    
    return result_df



@st.cache_data(ttl=3600, show_spinner=False)
def analyze_race_pace(_session: fastf1.core.Session, driver: str, remove_outliers: bool = True) -> pd.DataFrame:
    """
    Calculate race pace with outlier removal.
    
    Args:
        _session: Loaded FastF1 session object
        driver: Driver abbreviation (e.g., 'VER')
        remove_outliers: Remove laps >107% of median (yellow flags, traffic)
    
    Returns:
        DataFrame with columns: [LapNumber, LapTime, Compound, IsOutlier]
    """
    if _session.laps is None or _session.laps.empty:
        return pd.DataFrame(columns=['LapNumber', 'LapTime', 'Compound', 'IsOutlier'])
    
    # Get driver's laps
    driver_laps = _session.laps.pick_driver(driver).copy()
    
    if driver_laps.empty:
        return pd.DataFrame(columns=['LapNumber', 'LapTime', 'Compound', 'IsOutlier'])
    
    # Filter out invalid laps
    valid_laps = driver_laps[driver_laps['LapTime'].notna()].copy()
    
    # Remove pit laps (laps with pit in/out times)
    valid_laps = valid_laps[
        valid_laps['PitInTime'].isna() & 
        valid_laps['PitOutTime'].isna()
    ]
    
    # Remove yellow flag laps (TrackStatus != '1' means not green flag)
    # TrackStatus: '1' = green, '2' = yellow, '4' = SC, '6' = VSC
    if 'TrackStatus' in valid_laps.columns:
        valid_laps = valid_laps[valid_laps['TrackStatus'] == '1']
    
    if valid_laps.empty:
        return pd.DataFrame(columns=['LapNumber', 'LapTime', 'Compound', 'IsOutlier'])
    
    # Initialize IsOutlier column
    valid_laps['IsOutlier'] = False
    
    # Remove outliers if requested
    if remove_outliers and len(valid_laps) > 0:
        # Calculate median lap time
        median_time = valid_laps['LapTime'].median()
        
        # 107% threshold
        threshold = median_time * 1.07
        
        # Mark outliers
        valid_laps['IsOutlier'] = valid_laps['LapTime'] > threshold
    
    # Select relevant columns
    result_df = valid_laps[['LapNumber', 'LapTime', 'Compound', 'IsOutlier']].copy()
    result_df = result_df.sort_values('LapNumber').reset_index(drop=True)
    
    return result_df


@st.cache_data(ttl=3600, show_spinner=False)
def calculate_pace_degradation(_laps_df: pd.DataFrame) -> Dict[str, float]:
    """
    Use linear regression to calculate lap time degradation per lap.
    
    Args:
        _laps_df: DataFrame with columns [LapNumber, LapTime, ...]
                  Should be output from analyze_race_pace()
    
    Returns:
        Dictionary with keys:
        - 'slope': seconds per lap (degradation rate)
        - 'intercept': initial pace in seconds
        - 'r_squared': fit quality (0-1)
    """
    if _laps_df.empty or len(_laps_df) < 2:
        return {'slope': 0.0, 'intercept': 0.0, 'r_squared': 0.0}
    
    # Filter out outliers if IsOutlier column exists
    if 'IsOutlier' in _laps_df.columns:
        clean_laps = _laps_df[~_laps_df['IsOutlier']].copy()
    else:
        clean_laps = _laps_df.copy()
    
    if len(clean_laps) < 2:
        return {'slope': 0.0, 'intercept': 0.0, 'r_squared': 0.0}
    
    # Convert LapTime (timedelta) to seconds
    lap_times_seconds = clean_laps['LapTime'].dt.total_seconds().values
    lap_numbers = clean_laps['LapNumber'].values
    
    # Reshape for sklearn
    X = lap_numbers.reshape(-1, 1)
    y = lap_times_seconds
    
    # Fit linear regression
    model = LinearRegression()
    model.fit(X, y)
    
    # Calculate R-squared
    r_squared = model.score(X, y)
    
    return {
        'slope': float(model.coef_[0]),
        'intercept': float(model.intercept_),
        'r_squared': float(r_squared)
    }


@st.cache_data(ttl=3600, show_spinner=False)
def get_stint_averages(_session: fastf1.core.Session, driver: str) -> pd.DataFrame:
    """
    Calculate average pace for each stint.
    
    Args:
        _session: Loaded FastF1 session object
        driver: Driver abbreviation (e.g., 'VER')
    
    Returns:
        DataFrame with columns: [StintNumber, Compound, AvgLapTime, LapCount]
    """
    if _session.laps is None or _session.laps.empty:
        return pd.DataFrame(columns=['StintNumber', 'Compound', 'AvgLapTime', 'LapCount'])
    
    # Get driver's laps
    driver_laps = _session.laps.pick_driver(driver).copy()
    
    if driver_laps.empty:
        return pd.DataFrame(columns=['StintNumber', 'Compound', 'AvgLapTime', 'LapCount'])
    
    # Filter valid laps (no pit laps, valid lap times)
    valid_laps = driver_laps[
        driver_laps['LapTime'].notna() &
        driver_laps['PitInTime'].isna() &
        driver_laps['PitOutTime'].isna()
    ].copy()
    
    if valid_laps.empty:
        return pd.DataFrame(columns=['StintNumber', 'Compound', 'AvgLapTime', 'LapCount'])
    
    # Identify stints by compound changes
    # Create stint number based on compound changes
    valid_laps['StintNumber'] = (valid_laps['Compound'] != valid_laps['Compound'].shift()).cumsum()
    
    # Group by stint and calculate averages
    stint_data = []
    for stint_num, stint_laps in valid_laps.groupby('StintNumber'):
        # Remove outliers (107% threshold)
        median_time = stint_laps['LapTime'].median()
        threshold = median_time * 1.07
        clean_stint = stint_laps[stint_laps['LapTime'] <= threshold]
        
        if not clean_stint.empty:
            stint_data.append({
                'StintNumber': int(stint_num),
                'Compound': clean_stint['Compound'].iloc[0],
                'AvgLapTime': clean_stint['LapTime'].mean(),
                'LapCount': len(clean_stint)
            })
    
    result_df = pd.DataFrame(stint_data)
    
    if not result_df.empty:
        result_df = result_df.sort_values('StintNumber').reset_index(drop=True)
    
    return result_df



@st.cache_data(ttl=3600, show_spinner=False)
def get_weather_data(_session: fastf1.core.Session) -> Dict[str, Any]:
    """
    Extract weather information from session.
    
    Args:
        _session: Loaded FastF1 session object
    
    Returns:
        Dictionary with keys:
        - 'track_temp': float (average track temperature in Celsius)
        - 'air_temp': float (average air temperature in Celsius)
        - 'humidity': float (average humidity percentage)
        - 'rainfall': bool (whether it rained during session)
        - 'wind_speed': float (average wind speed in m/s)
        - 'pressure': float (average air pressure in mbar)
        - 'track_temp_range': tuple (min, max) if varies
        - 'air_temp_range': tuple (min, max) if varies
    """
    weather_data = {
        'track_temp': None,
        'air_temp': None,
        'humidity': None,
        'rainfall': False,
        'wind_speed': None,
        'pressure': None,
        'track_temp_range': None,
        'air_temp_range': None
    }
    
    # Try to get weather data from laps
    if _session.laps is not None and not _session.laps.empty:
        laps = _session.laps
        
        # Track temperature
        if 'TrackTemp' in laps.columns:
            track_temps = laps['TrackTemp'].dropna()
            if not track_temps.empty:
                weather_data['track_temp'] = float(track_temps.mean())
                if track_temps.max() - track_temps.min() > 2:  # Significant variation
                    weather_data['track_temp_range'] = (float(track_temps.min()), float(track_temps.max()))
        
        # Air temperature
        if 'AirTemp' in laps.columns:
            air_temps = laps['AirTemp'].dropna()
            if not air_temps.empty:
                weather_data['air_temp'] = float(air_temps.mean())
                if air_temps.max() - air_temps.min() > 2:  # Significant variation
                    weather_data['air_temp_range'] = (float(air_temps.min()), float(air_temps.max()))
        
        # Humidity
        if 'Humidity' in laps.columns:
            humidity = laps['Humidity'].dropna()
            if not humidity.empty:
                weather_data['humidity'] = float(humidity.mean())
        
        # Rainfall
        if 'Rainfall' in laps.columns:
            rainfall = laps['Rainfall'].dropna()
            if not rainfall.empty:
                weather_data['rainfall'] = bool(rainfall.any())
        
        # Wind speed
        if 'WindSpeed' in laps.columns:
            wind_speed = laps['WindSpeed'].dropna()
            if not wind_speed.empty:
                weather_data['wind_speed'] = float(wind_speed.mean())
        
        # Pressure
        if 'Pressure' in laps.columns:
            pressure = laps['Pressure'].dropna()
            if not pressure.empty:
                weather_data['pressure'] = float(pressure.mean())
    
    # Try to get weather data from session weather_data attribute if available
    try:
        if hasattr(_session, 'weather_data') and _session.weather_data is not None:
            session_weather = _session.weather_data
            
            if 'TrackTemp' in session_weather.columns:
                track_temps = session_weather['TrackTemp'].dropna()
                if not track_temps.empty and weather_data['track_temp'] is None:
                    weather_data['track_temp'] = float(track_temps.mean())
            
            if 'AirTemp' in session_weather.columns:
                air_temps = session_weather['AirTemp'].dropna()
                if not air_temps.empty and weather_data['air_temp'] is None:
                    weather_data['air_temp'] = float(air_temps.mean())
            
            if 'Humidity' in session_weather.columns:
                humidity = session_weather['Humidity'].dropna()
                if not humidity.empty and weather_data['humidity'] is None:
                    weather_data['humidity'] = float(humidity.mean())
            
            if 'Rainfall' in session_weather.columns:
                rainfall = session_weather['Rainfall'].dropna()
                if not rainfall.empty and weather_data['rainfall'] is False:
                    weather_data['rainfall'] = bool(rainfall.any())
            
            if 'WindSpeed' in session_weather.columns:
                wind_speed = session_weather['WindSpeed'].dropna()
                if not wind_speed.empty and weather_data['wind_speed'] is None:
                    weather_data['wind_speed'] = float(wind_speed.mean())
            
            if 'Pressure' in session_weather.columns:
                pressure = session_weather['Pressure'].dropna()
                if not pressure.empty and weather_data['pressure'] is None:
                    weather_data['pressure'] = float(pressure.mean())
    except Exception:
        # If weather_data attribute doesn't exist or has issues, continue with lap data
        pass
    
    return weather_data
