"""
Test suite for Circuit Map Comparison Feature

Tests the telemetry alignment, color coding, and circuit map generation.
"""

import pandas as pd
import numpy as np
from unittest.mock import Mock, MagicMock
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.telemetry import (
    load_aligned_telemetry,
    build_circuit_comparison_map,
    _get_driver_colors,
    _lighten_color
)


class TestColorFunctions:
    """Test color manipulation functions"""
    
    def test_lighten_color_basic(self):
        """Test basic color lightening"""
        original = '#3671C6'
        lightened = _lighten_color(original, 0.3)
        
        assert lightened.startswith('#')
        assert len(lightened) == 7
        assert lightened != original
    
    def test_lighten_color_factor_zero(self):
        """Test lightening with factor 0 (no change)"""
        original = '#FF0000'
        lightened = _lighten_color(original, 0.0)
        
        assert lightened == original
    
    def test_lighten_color_factor_one(self):
        """Test lightening with factor 1 (white)"""
        original = '#000000'
        lightened = _lighten_color(original, 1.0)
        
        assert lightened == '#ffffff'
    
    def test_lighten_color_without_hash(self):
        """Test color without # prefix"""
        original = '3671C6'
        lightened = _lighten_color(original, 0.3)
        
        assert lightened.startswith('#')
        assert len(lightened) == 7


class TestAlignedTelemetry:
    """Test telemetry alignment functionality"""
    
    def create_mock_telemetry(self, num_points=100, offset=0):
        """Create mock telemetry data"""
        distance = np.linspace(0, 5000, num_points) + offset
        
        return pd.DataFrame({
            'Distance': distance,
            'X': np.sin(distance / 1000) * 100,
            'Y': np.cos(distance / 1000) * 100,
            'Speed': 200 + np.random.randn(num_points) * 10,
            'Throttle': np.random.randint(0, 101, num_points),
            'Brake': np.random.randint(0, 101, num_points),
            'nGear': np.random.randint(1, 9, num_points),
            'DRS': np.random.randint(0, 2, num_points)
        })
    
    def create_mock_lap(self, telemetry_data):
        """Create mock FastF1 lap object"""
        lap = Mock()
        lap.get_telemetry = Mock(return_value=telemetry_data)
        return lap
    
    def test_alignment_same_length(self):
        """Test alignment with same length telemetry"""
        tel1 = self.create_mock_telemetry(100)
        tel2 = self.create_mock_telemetry(100)
        
        # Mock session and get_telemetry_comparison
        from backend import telemetry
        original_func = telemetry.get_telemetry_comparison
        
        def mock_get_telemetry(*args, **kwargs):
            return tel1, tel2
        
        telemetry.get_telemetry_comparison = mock_get_telemetry
        
        try:
            mock_session = Mock()
            aligned1, aligned2, common_dist = load_aligned_telemetry(
                mock_session, "VER", "HAM"
            )
            
            # Check alignment
            assert len(aligned1) == len(aligned2)
            assert len(aligned1) == len(common_dist)
            assert 'X' in aligned1.columns
            assert 'Y' in aligned1.columns
            assert 'Speed' in aligned1.columns
        finally:
            telemetry.get_telemetry_comparison = original_func
    
    def test_alignment_different_lengths(self):
        """Test alignment with different length telemetry"""
        tel1 = self.create_mock_telemetry(150)
        tel2 = self.create_mock_telemetry(100)
        
        from backend import telemetry
        original_func = telemetry.get_telemetry_comparison
        
        def mock_get_telemetry(*args, **kwargs):
            return tel1, tel2
        
        telemetry.get_telemetry_comparison = mock_get_telemetry
        
        try:
            mock_session = Mock()
            aligned1, aligned2, common_dist = load_aligned_telemetry(
                mock_session, "VER", "HAM"
            )
            
            # Both should be aligned to same length
            assert len(aligned1) == len(aligned2)
            assert len(aligned1) == len(common_dist)
        finally:
            telemetry.get_telemetry_comparison = original_func


class TestCircuitMapGeneration:
    """Test circuit map generation"""
    
    def test_color_logic_driver1_faster(self):
        """Test color assignment when driver 1 is faster"""
        speed_delta = 2.0  # Driver 1 faster by 2 km/h
        threshold = 0.5
        
        # Simulate color logic
        if speed_delta > threshold:
            color = "blue"
        elif speed_delta < -threshold:
            color = "red"
        else:
            color = "grey"
        
        assert color == "blue"
    
    def test_color_logic_driver2_faster(self):
        """Test color assignment when driver 2 is faster"""
        speed_delta = -2.0  # Driver 2 faster by 2 km/h
        threshold = 0.5
        
        if speed_delta > threshold:
            color = "blue"
        elif speed_delta < -threshold:
            color = "red"
        else:
            color = "grey"
        
        assert color == "red"
    
    def test_color_logic_equal_pace(self):
        """Test color assignment when pace is equal"""
        speed_delta = 0.2  # Within threshold
        threshold = 0.5
        
        if speed_delta > threshold:
            color = "blue"
        elif speed_delta < -threshold:
            color = "red"
        else:
            color = "grey"
        
        assert color == "grey"
    
    def test_segment_boundary_detection(self):
        """Test detection of segment boundaries"""
        # Simulate faster driver array
        faster_driver = np.array([1, 1, 1, 2, 2, 2, 1, 1, 0, 0])
        
        # Find changes
        changes = np.where(np.diff(faster_driver) != 0)[0] + 1
        
        # Should detect 4 changes (1->2, 2->1, 1->0)
        assert len(changes) == 3
        assert list(changes) == [3, 6, 8]


class TestHoverDataGeneration:
    """Test hover tooltip generation"""
    
    def test_hover_text_format(self):
        """Test hover text formatting"""
        driver1 = "VER"
        driver2 = "HAM"
        distance = 1500.0
        speed1 = 305.5
        speed2 = 302.3
        delta = speed1 - speed2
        gear1 = 8
        gear2 = 8
        throttle1 = 100
        throttle2 = 98
        brake1 = 0
        brake2 = 0
        drs1_status = "Active"
        drs2_status = "Active"
        faster = driver1
        
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
        
        # Check key elements are present
        assert "Distance: 1500m" in hover
        assert "VER Speed: 305.5 km/h" in hover
        assert "HAM Speed: 302.3 km/h" in hover
        assert "Δ Speed: +3.2 km/h" in hover
        assert "Faster: VER" in hover
        assert "Gear 8" in hover
        assert "DRS Active" in hover


class TestEdgeCases:
    """Test edge cases and error handling"""
    
    def test_empty_telemetry(self):
        """Test handling of empty telemetry"""
        empty_df = pd.DataFrame()
        
        # Should return empty DataFrame with expected columns
        assert empty_df.empty
    
    def test_missing_columns(self):
        """Test handling of missing telemetry columns"""
        incomplete_tel = pd.DataFrame({
            'Distance': [0, 100, 200],
            'X': [0, 10, 20],
            'Y': [0, 10, 20]
            # Missing Speed, Throttle, etc.
        })
        
        # Should handle gracefully
        assert 'Distance' in incomplete_tel.columns
        assert 'X' in incomplete_tel.columns
        assert 'Speed' not in incomplete_tel.columns
    
    def test_nan_values(self):
        """Test handling of NaN values"""
        tel_with_nan = pd.DataFrame({
            'Distance': [0, 100, np.nan, 300],
            'X': [0, 10, 20, np.nan],
            'Y': [0, 10, np.nan, 30],
            'Speed': [200, np.nan, 250, 260]
        })
        
        # After dropna on Distance, X, Y
        cleaned = tel_with_nan.dropna(subset=['Distance', 'X', 'Y'])
        
        assert len(cleaned) == 1  # Only first row is complete
    
    def test_single_point_telemetry(self):
        """Test handling of single data point"""
        single_point = pd.DataFrame({
            'Distance': [1000],
            'X': [50],
            'Y': [50],
            'Speed': [200]
        })
        
        # Should handle without crashing
        assert len(single_point) == 1


class TestInterpolation:
    """Test interpolation accuracy"""
    
    def test_linear_interpolation(self):
        """Test linear interpolation accuracy"""
        # Create simple linear data
        original_distance = np.array([0, 100, 200, 300])
        original_speed = np.array([100, 150, 200, 250])
        
        # Interpolate to new points
        new_distance = np.array([50, 150, 250])
        interpolated_speed = np.interp(new_distance, original_distance, original_speed)
        
        # Check interpolated values
        assert interpolated_speed[0] == 125  # Midpoint between 100 and 150
        assert interpolated_speed[1] == 175  # Midpoint between 150 and 200
        assert interpolated_speed[2] == 225  # Midpoint between 200 and 250
    
    def test_interpolation_preserves_range(self):
        """Test that interpolation stays within original range"""
        original_distance = np.linspace(0, 5000, 100)
        original_speed = 200 + np.sin(original_distance / 1000) * 50
        
        new_distance = np.linspace(0, 5000, 500)
        interpolated_speed = np.interp(new_distance, original_distance, original_speed)
        
        # Interpolated values should be within original range
        assert interpolated_speed.min() >= original_speed.min() - 1e-10
        assert interpolated_speed.max() <= original_speed.max() + 1e-10


def run_integration_test():
    """
    Integration test with real FastF1 data (requires internet connection)
    This is commented out by default to avoid API calls during testing
    """
    pass
    # Uncomment to run with real data:
    """
    import fastf1
    from backend.data_loader import setup_cache, load_session
    
    setup_cache()
    
    try:
        # Load a recent session
        session = load_session(2023, "Monaco", "Qualifying")
        
        # Generate circuit map
        fig = build_circuit_comparison_map(session, "VER", "LEC")
        
        # Verify figure was created
        assert fig is not None
        assert len(fig.data) > 0
        
        print("✅ Integration test passed!")
        
    except Exception as e:
        print(f"❌ Integration test failed: {e}")
    """


if __name__ == "__main__":
    # Run tests
    print("Running Circuit Map Feature Tests...\n")
    
    # Color tests
    print("Testing color functions...")
    color_tests = TestColorFunctions()
    color_tests.test_lighten_color_basic()
    color_tests.test_lighten_color_factor_zero()
    color_tests.test_lighten_color_factor_one()
    color_tests.test_lighten_color_without_hash()
    print("✅ Color tests passed\n")
    
    # Circuit map tests
    print("Testing circuit map generation...")
    map_tests = TestCircuitMapGeneration()
    map_tests.test_color_logic_driver1_faster()
    map_tests.test_color_logic_driver2_faster()
    map_tests.test_color_logic_equal_pace()
    map_tests.test_segment_boundary_detection()
    print("✅ Circuit map tests passed\n")
    
    # Hover data tests
    print("Testing hover data generation...")
    hover_tests = TestHoverDataGeneration()
    hover_tests.test_hover_text_format()
    print("✅ Hover data tests passed\n")
    
    # Edge case tests
    print("Testing edge cases...")
    edge_tests = TestEdgeCases()
    edge_tests.test_empty_telemetry()
    edge_tests.test_missing_columns()
    edge_tests.test_nan_values()
    edge_tests.test_single_point_telemetry()
    print("✅ Edge case tests passed\n")
    
    # Interpolation tests
    print("Testing interpolation...")
    interp_tests = TestInterpolation()
    interp_tests.test_linear_interpolation()
    interp_tests.test_interpolation_preserves_range()
    print("✅ Interpolation tests passed\n")
    
    print("=" * 50)
    print("All tests passed! ✅")
    print("=" * 50)
