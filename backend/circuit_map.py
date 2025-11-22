"""
Circuit Map Module for F1 Analysis Dashboard
Provides circuit map visualization with driver performance comparison.
"""

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
import fastf1


def build_circuit_map_comparison(session, driver1, driver2):
    """
    Build circuit map comparing two drivers' fastest laps.
    
    Args:
        session: FastF1 session object
        driver1: First driver abbreviation (e.g., 'VER')
        driver2: Second driver abbreviation (e.g., 'HAM')
    
    Returns:
        Plotly Figure object with color-coded circuit map
    """
    # Load fastest laps for both drivers
    lap1 = session.laps.pick_driver(driver1).pick_fastest()
    lap2 = session.laps.pick_driver(driver2).pick_fastest()
    
    # Extract telemetry with coordinates
    tel1 = lap1.get_telemetry().add_distance()
    tel2 = lap2.get_telemetry().add_distance()
    
    # Remove NaN values
    tel1 = tel1.dropna(subset=['Distance', 'X', 'Y'])
    tel2 = tel2.dropna(subset=['Distance', 'X', 'Y'])
    
    # Create common distance base for interpolation
    min_dist = max(tel1['Distance'].min(), tel2['Distance'].min())
    max_dist = min(tel1['Distance'].max(), tel2['Distance'].max())
    common_distance = np.linspace(min_dist, max_dist, 500)
    
    # Interpolate speed + XY to common distance base
    x1 = np.interp(common_distance, tel1['Distance'].values, tel1['X'].values)
    y1 = np.interp(common_distance, tel1['Distance'].values, tel1['Y'].values)
    speed1 = np.interp(common_distance, tel1['Distance'].values, tel1['Speed'].values)
    
    x2 = np.interp(common_distance, tel2['Distance'].values, tel2['X'].values)
    y2 = np.interp(common_distance, tel2['Distance'].values, tel2['Y'].values)
    speed2 = np.interp(common_distance, tel2['Distance'].values, tel2['Speed'].values)
    
    # Interpolate additional telemetry data
    throttle1 = np.interp(common_distance, tel1['Distance'].values, tel1['Throttle'].fillna(0).values)
    throttle2 = np.interp(common_distance, tel2['Distance'].values, tel2['Throttle'].fillna(0).values)
    brake1 = np.interp(common_distance, tel1['Distance'].values, tel1['Brake'].fillna(0).values)
    brake2 = np.interp(common_distance, tel2['Distance'].values, tel2['Brake'].fillna(0).values)
    gear1 = np.interp(common_distance, tel1['Distance'].values, tel1['nGear'].fillna(0).values)
    gear2 = np.interp(common_distance, tel2['Distance'].values, tel2['nGear'].fillna(0).values)
    drs1 = np.interp(common_distance, tel1['Distance'].values, tel1['DRS'].fillna(0).values)
    drs2 = np.interp(common_distance, tel2['Distance'].values, tel2['DRS'].fillna(0).values)
    
    # Compute delta speed
    delta = speed1 - speed2
    
    # Get driver colors
    try:
        color1 = fastf1.plotting.team_color(lap1['Team'])
    except:
        color1 = '#3671C6'
    
    try:
        color2 = fastf1.plotting.team_color(lap2['Team'])
    except:
        color2 = '#FF1E1E'
    
    # Split track into segments based on delta sign change
    # Driver1 faster → Blue, Driver2 faster → Red, Tie → Grey
    threshold = 0.5  # km/h threshold for "tie"
    
    faster = np.where(delta > threshold, 1, np.where(delta < -threshold, 2, 0))
    segment_changes = np.where(np.diff(faster) != 0)[0] + 1
    segment_starts = np.concatenate([[0], segment_changes])
    segment_ends = np.concatenate([segment_changes, [len(common_distance)]])
    
    # Create Plotly figure
    fig = go.Figure()
    
    # Plot each segment
    for start, end in zip(segment_starts, segment_ends):
        if start >= end:
            continue
        
        avg_delta = delta[start:end].mean()
        
        if avg_delta > threshold:
            color = color1
            faster_driver = driver1
        elif avg_delta < -threshold:
            color = color2
            faster_driver = driver2
        else:
            color = 'lightgrey'
            faster_driver = 'Equal'
        
        # Create hover info
        hover_text = []
        for i in range(start, min(end + 1, len(common_distance))):
            drs1_status = 'Active' if drs1[i] > 0 else 'Inactive'
            drs2_status = 'Active' if drs2[i] > 0 else 'Inactive'
            
            hover = (
                f"Distance: {common_distance[i]:.0f}m<br>"
                f"Speed {driver1}: {speed1[i]:.1f} km/h<br>"
                f"Speed {driver2}: {speed2[i]:.1f} km/h<br>"
                f"Delta: {delta[i]:+.1f} km/h<br>"
                f"<br>"
                f"{driver1}: Throttle {throttle1[i]:.0f}% | Brake {brake1[i]:.0f}% | Gear {int(gear1[i])} | DRS {drs1_status}<br>"
                f"{driver2}: Throttle {throttle2[i]:.0f}% | Brake {brake2[i]:.0f}% | Gear {int(gear2[i])} | DRS {drs2_status}"
            )
            hover_text.append(hover)
        
        # Add segment trace
        fig.add_trace(go.Scatter(
            x=x1[start:end+1],
            y=y1[start:end+1],
            mode='lines',
            line=dict(color=color, width=4),
            hovertemplate='%{text}<extra></extra>',
            text=hover_text,
            showlegend=False,
            name=f'{faster_driver} faster'
        ))
    
    # Add legend traces
    fig.add_trace(go.Scatter(
        x=[None], y=[None],
        mode='lines',
        line=dict(color=color1, width=4),
        name=f'{driver1} faster',
        showlegend=True
    ))
    
    fig.add_trace(go.Scatter(
        x=[None], y=[None],
        mode='lines',
        line=dict(color=color2, width=4),
        name=f'{driver2} faster',
        showlegend=True
    ))
    
    fig.add_trace(go.Scatter(
        x=[None], y=[None],
        mode='lines',
        line=dict(color='lightgrey', width=4),
        name='Equal pace',
        showlegend=True
    ))
    
    # Update layout
    fig.update_layout(
        title=dict(
            text=f"Circuit Map – {driver1} vs {driver2}",
            x=0.5,
            xanchor='center',
            font=dict(size=18)
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
        hovermode='closest',
        legend=dict(
            orientation='h',
            yanchor='bottom',
            y=1.02,
            xanchor='center',
            x=0.5
        ),
        margin=dict(l=20, r=20, t=60, b=20),
        height=600
    )
    
    return fig


@st.cache_data(show_spinner=False)
def cached_circuit_map(session_key, driver1, driver2, _session):
    """
    Cached wrapper for circuit map generation.
    
    Args:
        session_key: Unique session identifier for caching
        driver1: First driver abbreviation
        driver2: Second driver abbreviation
        _session: FastF1 session object (not hashed due to underscore prefix)
    
    Returns:
        Plotly Figure object
    """
    return build_circuit_map_comparison(_session, driver1, driver2)
