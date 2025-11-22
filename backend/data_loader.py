"""
Data Loader Module for F1 Analysis Dashboard

This module provides functions to interact with the FastF1 API,
including session loading, driver extraction, and data caching.
"""

import os
from typing import List, Dict, Optional
from datetime import datetime
import fastf1
import streamlit as st


def setup_cache(cache_dir: str = "./f1_cache") -> None:
    """
    Initialize FastF1 cache directory.
    
    Args:
        cache_dir: Path to cache directory (default: "./f1_cache")
    
    Creates the cache directory if it doesn't exist and enables FastF1 caching.
    """
    # Create cache directory if it doesn't exist
    if not os.path.exists(cache_dir):
        os.makedirs(cache_dir)
    
    # Enable FastF1 cache
    fastf1.Cache.enable_cache(cache_dir)


@st.cache_data(ttl=3600, show_spinner=False)
def load_session(year: int, grand_prix: str, session_type: str) -> fastf1.core.Session:
    """
    Load and return a FastF1 session object with error handling.
    
    Args:
        year: Season year (e.g., 2023)
        grand_prix: Grand Prix name (e.g., "Monaco")
        session_type: One of ['FP1', 'FP2', 'FP3', 'Q', 'R', 'Qualifying', 'Race']
    
    Returns:
        Loaded FastF1 session with laps data
    
    Raises:
        ValueError: If session cannot be loaded or parameters are invalid
    """
    try:
        # Validate year
        available_years = get_available_years()
        if year not in available_years:
            raise ValueError(f"Year {year} is not available. Available years: {available_years}")
        
        # Normalize session type
        session_type_map = {
            'FP1': 'FP1',
            'FP2': 'FP2',
            'FP3': 'FP3',
            'Q': 'Q',
            'Qualifying': 'Q',
            'R': 'R',
            'Race': 'R'
        }
        
        normalized_session_type = session_type_map.get(session_type, session_type)
        
        # Load the session
        session = fastf1.get_session(year, grand_prix, normalized_session_type)
        
        # Load session data (laps, telemetry metadata, etc.)
        session.load()
        
        return session
        
    except Exception as e:
        raise ValueError(f"Failed to load session: {str(e)}")


def get_drivers(session: fastf1.core.Session) -> List[str]:
    """
    Extract list of driver abbreviations from session.
    
    Args:
        session: Loaded FastF1 session object
    
    Returns:
        List of driver abbreviations (e.g., ['VER', 'HAM', 'LEC'])
    """
    if session.laps is None or session.laps.empty:
        return []
    
    # Get unique driver abbreviations from laps data
    drivers = session.laps['Driver'].unique().tolist()
    
    # Sort alphabetically for consistent ordering
    drivers.sort()
    
    return drivers


def get_team_colors(session: fastf1.core.Session) -> Dict[str, str]:
    """
    Return mapping of driver abbreviation to team color hex code.
    
    Args:
        session: Loaded FastF1 session object
    
    Returns:
        Dictionary mapping driver abbreviation to team color hex code
        (e.g., {'VER': '#3671C6', 'HAM': '#27F4D2'})
    """
    if session.laps is None or session.laps.empty:
        return {}
    
    team_colors = {}
    drivers = get_drivers(session)
    
    for driver in drivers:
        try:
            # Get driver's laps
            driver_laps = session.laps.pick_driver(driver)
            
            if not driver_laps.empty:
                # Get team name from first lap
                team = driver_laps.iloc[0]['Team']
                
                # Get team color using FastF1's color mapping
                color = fastf1.plotting.team_color(team)
                
                team_colors[driver] = color
        except Exception:
            # If color retrieval fails, use a default gray color
            team_colors[driver] = '#808080'
    
    return team_colors


def get_available_years() -> List[int]:
    """
    Return list of years with available data (2018-present).
    
    Returns:
        List of years from 2018 to current year
    """
    current_year = datetime.now().year
    return list(range(2018, current_year + 1))


def get_grand_prix_list(year: int) -> List[str]:
    """
    Return list of Grand Prix names for given year.
    
    Args:
        year: Season year (e.g., 2023)
    
    Returns:
        List of Grand Prix names (e.g., ['Bahrain', 'Saudi Arabia', 'Australia'])
    
    Raises:
        ValueError: If year is invalid or event schedule cannot be retrieved
    """
    try:
        # Validate year
        available_years = get_available_years()
        if year not in available_years:
            raise ValueError(f"Year {year} is not available. Available years: {available_years}")
        
        # Get event schedule for the year
        event_schedule = fastf1.get_event_schedule(year)
        
        # Extract event names (Grand Prix names)
        # Filter out testing events
        grand_prix_list = []
        for _, event in event_schedule.iterrows():
            event_name = event['EventName']
            # Exclude pre-season testing
            if 'Test' not in event_name and 'Testing' not in event_name:
                grand_prix_list.append(event_name)
        
        return grand_prix_list
        
    except Exception as e:
        raise ValueError(f"Failed to retrieve Grand Prix list for {year}: {str(e)}")
