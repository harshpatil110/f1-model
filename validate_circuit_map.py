"""
Validation script for Circuit Map Comparison Feature

This script validates the implementation without requiring dependencies.
It checks code structure, function signatures, and documentation.
"""

import ast
import os


def validate_file_exists(filepath):
    """Check if file exists"""
    if os.path.exists(filepath):
        print(f"✅ {filepath} exists")
        return True
    else:
        print(f"❌ {filepath} not found")
        return False


def validate_function_exists(filepath, function_name):
    """Check if function exists in file"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            tree = ast.parse(f.read())
        
        functions = [node.name for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)]
        
        if function_name in functions:
            print(f"✅ Function '{function_name}' found in {filepath}")
            return True
        else:
            print(f"❌ Function '{function_name}' not found in {filepath}")
            return False
    except Exception as e:
        print(f"❌ Error parsing {filepath}: {e}")
        return False


def validate_function_signature(filepath, function_name, expected_params):
    """Validate function has expected parameters"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            tree = ast.parse(f.read())
        
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name == function_name:
                actual_params = [arg.arg for arg in node.args.args]
                
                # Check if all expected params are present
                missing = set(expected_params) - set(actual_params)
                if missing:
                    print(f"⚠️  Function '{function_name}' missing parameters: {missing}")
                    return False
                else:
                    print(f"✅ Function '{function_name}' has correct parameters")
                    return True
        
        print(f"❌ Function '{function_name}' not found")
        return False
    except Exception as e:
        print(f"❌ Error validating {function_name}: {e}")
        return False


def validate_imports(filepath, required_imports):
    """Check if file has required imports"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        missing_imports = []
        for imp in required_imports:
            if imp not in content:
                missing_imports.append(imp)
        
        if missing_imports:
            print(f"⚠️  {filepath} missing imports: {missing_imports}")
            return False
        else:
            print(f"✅ {filepath} has all required imports")
            return True
    except Exception as e:
        print(f"❌ Error checking imports in {filepath}: {e}")
        return False


def validate_docstring(filepath, function_name):
    """Check if function has docstring"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            tree = ast.parse(f.read())
        
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name == function_name:
                docstring = ast.get_docstring(node)
                if docstring:
                    print(f"✅ Function '{function_name}' has docstring")
                    return True
                else:
                    print(f"⚠️  Function '{function_name}' missing docstring")
                    return False
        
        return False
    except Exception as e:
        print(f"❌ Error checking docstring: {e}")
        return False


def main():
    """Run all validations"""
    print("=" * 60)
    print("Circuit Map Comparison Feature - Validation")
    print("=" * 60)
    print()
    
    all_passed = True
    
    # 1. Check files exist
    print("1. Checking file structure...")
    print("-" * 60)
    files_to_check = [
        'backend/telemetry.py',
        'app.py',
        'CIRCUIT_MAP_FEATURE.md',
        'tests/test_circuit_map.py'
    ]
    
    for filepath in files_to_check:
        if not validate_file_exists(filepath):
            all_passed = False
    print()
    
    # 2. Check backend functions
    print("2. Checking backend functions...")
    print("-" * 60)
    
    functions_to_check = [
        'load_aligned_telemetry',
        'build_circuit_comparison_map',
        '_get_driver_colors',
        '_lighten_color',
        'get_telemetry_comparison',
        'get_speed_trace',
        'get_brake_trace',
        'get_throttle_trace',
        'calculate_corner_speeds',
        'calculate_straight_speeds',
        'get_gear_usage',
        'get_drs_zones'
    ]
    
    for func in functions_to_check:
        if not validate_function_exists('backend/telemetry.py', func):
            all_passed = False
    print()
    
    # 3. Check function signatures
    print("3. Validating function signatures...")
    print("-" * 60)
    
    signatures = {
        'load_aligned_telemetry': ['_session', 'driver1', 'driver2', 'lap_type'],
        'build_circuit_comparison_map': ['_session', 'driver1', 'driver2', 'lap_type', 'delta_threshold'],
        '_get_driver_colors': ['_session', 'driver1', 'driver2'],
        '_lighten_color': ['hex_color', 'factor']
    }
    
    for func, params in signatures.items():
        if not validate_function_signature('backend/telemetry.py', func, params):
            all_passed = False
    print()
    
    # 4. Check imports
    print("4. Checking required imports...")
    print("-" * 60)
    
    telemetry_imports = [
        'import pandas',
        'import numpy',
        'import fastf1',
        'import streamlit',
        'from typing import'
    ]
    
    if not validate_imports('backend/telemetry.py', telemetry_imports):
        all_passed = False
    
    app_imports = [
        'import streamlit',
        'import pandas',
        'import fastf1',
        'from backend.telemetry import'
    ]
    
    if not validate_imports('app.py', app_imports):
        all_passed = False
    print()
    
    # 5. Check docstrings
    print("5. Checking documentation...")
    print("-" * 60)
    
    key_functions = [
        'load_aligned_telemetry',
        'build_circuit_comparison_map',
        'get_telemetry_comparison'
    ]
    
    for func in key_functions:
        if not validate_docstring('backend/telemetry.py', func):
            all_passed = False
    print()
    
    # 6. Check Streamlit integration
    print("6. Checking Streamlit integration...")
    print("-" * 60)
    
    try:
        with open('app.py', 'r', encoding='utf-8') as f:
            app_content = f.read()
        
        checks = [
            ('build_circuit_comparison_map', 'Circuit map function imported'),
            ('st.plotly_chart', 'Plotly chart rendering'),
            ('Telemetry', 'Telemetry tab exists'),
            ('Circuit Map', 'Circuit map section exists')
        ]
        
        for check_str, description in checks:
            if check_str in app_content:
                print(f"✅ {description}")
            else:
                print(f"⚠️  {description} not found")
                all_passed = False
    except Exception as e:
        print(f"❌ Error checking app.py: {e}")
        all_passed = False
    print()
    
    # 7. Check caching decorators
    print("7. Checking performance optimizations...")
    print("-" * 60)
    
    try:
        with open('backend/telemetry.py', 'r', encoding='utf-8') as f:
            telemetry_content = f.read()
        
        # Count cache decorators
        cache_count = telemetry_content.count('@st.cache_data')
        print(f"✅ Found {cache_count} cached functions")
        
        if cache_count < 3:
            print(f"⚠️  Expected at least 3 cached functions, found {cache_count}")
            all_passed = False
    except Exception as e:
        print(f"❌ Error checking caching: {e}")
        all_passed = False
    print()
    
    # 8. Check color coding logic
    print("8. Checking color coding implementation...")
    print("-" * 60)
    
    try:
        with open('backend/telemetry.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        color_checks = [
            ('speed_delta', 'Speed delta calculation'),
            ('delta_threshold', 'Delta threshold parameter'),
            ('faster_driver', 'Faster driver detection'),
            ('segment', 'Segment-based rendering')
        ]
        
        for check_str, description in color_checks:
            if check_str in content:
                print(f"✅ {description} implemented")
            else:
                print(f"⚠️  {description} not found")
    except Exception as e:
        print(f"❌ Error checking color logic: {e}")
    print()
    
    # 9. Check hover data implementation
    print("9. Checking hover data implementation...")
    print("-" * 60)
    
    try:
        with open('backend/telemetry.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        hover_elements = [
            'Distance',
            'Speed',
            'Δ Speed',
            'Gear',
            'Throttle',
            'Brake',
            'DRS'
        ]
        
        missing_elements = []
        for element in hover_elements:
            if element not in content:
                missing_elements.append(element)
        
        if missing_elements:
            print(f"⚠️  Missing hover elements: {missing_elements}")
        else:
            print(f"✅ All hover data elements present")
    except Exception as e:
        print(f"❌ Error checking hover data: {e}")
    print()
    
    # Final summary
    print("=" * 60)
    if all_passed:
        print("✅ ALL VALIDATIONS PASSED!")
        print("=" * 60)
        print()
        print("Next steps:")
        print("1. Install dependencies: pip install -r requirements.txt")
        print("2. Run the app: streamlit run app.py")
        print("3. Navigate to 'Telemetry & Circuit Map' tab")
        print("4. Select two drivers and view the circuit comparison")
        print()
        return 0
    else:
        print("⚠️  SOME VALIDATIONS FAILED")
        print("=" * 60)
        print()
        print("Please review the warnings above and fix any issues.")
        print()
        return 1


if __name__ == "__main__":
    exit(main())
