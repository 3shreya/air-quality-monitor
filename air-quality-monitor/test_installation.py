#!/usr/bin/env python3
"""
Test script to verify the Air Quality Analytics application installation
"""

import sys
import traceback

def test_imports():
    """Test if all required modules can be imported"""
    print("🧪 Testing module imports...")
    
    modules_to_test = [
        ('streamlit', 'Streamlit web framework'),
        ('pandas', 'Data manipulation library'),
        ('plotly', 'Interactive plotting library'),
        ('numpy', 'Numerical computing library'),
        ('sklearn', 'Machine learning library'),
        ('requests', 'HTTP library'),
        ('datetime', 'Date and time utilities'),
        ('typing', 'Type hints support')
    ]
    
    all_imports_successful = True
    
    for module_name, description in modules_to_test:
        try:
            __import__(module_name)
            print(f"✅ {module_name} - {description}")
        except ImportError as e:
            print(f"❌ {module_name} - {description} (Error: {e})")
            all_imports_successful = False
    
    return all_imports_successful

def test_custom_modules():
    """Test if our custom modules can be imported"""
    print("\n🧪 Testing custom modules...")
    
    custom_modules = [
        ('config', 'Configuration module'),
        ('data_fetcher', 'Data fetching module'),
        ('analytics', 'Analytics module'),
        ('alert_system', 'Alert system module'),
        ('visualizations', 'Visualization module')
    ]
    
    all_custom_imports_successful = True
    
    for module_name, description in custom_modules:
        try:
            module = __import__(module_name)
            print(f"✅ {module_name} - {description}")
            
            # Test if module has expected classes/functions
            if module_name == 'config':
                if hasattr(module, 'POLLUTANTS') and hasattr(module, 'AQI_THRESHOLDS'):
                    print(f"   ✅ {module_name} has expected configuration")
                else:
                    print(f"   ⚠️  {module_name} missing some expected attributes")
                    
            elif module_name == 'data_fetcher':
                if hasattr(module, 'AirQualityDataFetcher'):
                    print(f"   ✅ {module_name} has AirQualityDataFetcher class")
                else:
                    print(f"   ⚠️  {module_name} missing AirQualityDataFetcher class")
                    
            elif module_name == 'analytics':
                if hasattr(module, 'AirQualityAnalytics'):
                    print(f"   ✅ {module_name} has AirQualityAnalytics class")
                else:
                    print(f"   ⚠️  {module_name} missing AirQualityAnalytics class")
                    
            elif module_name == 'alert_system':
                if hasattr(module, 'AirQualityAlertSystem'):
                    print(f"   ✅ {module_name} has AirQualityAlertSystem class")
                else:
                    print(f"   ⚠️  {module_name} missing AirQualityAlertSystem class")
                    
            elif module_name == 'visualizations':
                if hasattr(module, 'AirQualityVisualizations'):
                    print(f"   ✅ {module_name} has AirQualityVisualizations class")
                else:
                    print(f"   ⚠️  {module_name} missing AirQualityVisualizations class")
                    
        except ImportError as e:
            print(f"❌ {module_name} - {description} (Error: {e})")
            all_custom_imports_successful = False
        except Exception as e:
            print(f"⚠️  {module_name} - {description} (Warning: {e})")
    
    return all_custom_imports_successful

def test_basic_functionality():
    """Test basic functionality of our modules"""
    print("\n🧪 Testing basic functionality...")
    
    try:
        # Test config
        from config import POLLUTANTS, AQI_THRESHOLDS, DEFAULT_CITIES
        print("✅ Configuration loaded successfully")
        print(f"   - {len(POLLUTANTS)} pollutants configured")
        print(f"   - {len(AQI_THRESHOLDS)} AQI thresholds defined")
        print(f"   - {len(DEFAULT_CITIES)} default cities available")
        
        # Test data fetcher
        from data_fetcher import AirQualityDataFetcher
        fetcher = AirQualityDataFetcher()
        print("✅ Data fetcher initialized successfully")
        
        # Test analytics
        from analytics import AirQualityAnalytics
        analytics = AirQualityAnalytics()
        print("✅ Analytics module initialized successfully")
        
        # Test alert system
        from alert_system import AirQualityAlertSystem
        alert_system = AirQualityAlertSystem()
        print("✅ Alert system initialized successfully")
        
        # Test visualizations
        from visualizations import AirQualityVisualizations
        viz = AirQualityVisualizations()
        print("✅ Visualizations module initialized successfully")
        
        return True
        
    except Exception as e:
        print(f"❌ Basic functionality test failed: {e}")
        traceback.print_exc()
        return False

def test_demo_data():
    """Test demo data generation"""
    print("\n🧪 Testing demo data generation...")
    
    try:
        from data_fetcher import AirQualityDataFetcher
        fetcher = AirQualityDataFetcher()
        
        # Generate demo data for a test city
        demo_data = fetcher.get_demo_data("Test City")
        
        if not demo_data.empty:
            print("✅ Demo data generated successfully")
            print(f"   - {len(demo_data)} data points")
            print(f"   - Parameters: {list(demo_data['parameter'].unique())}")
            print(f"   - Time range: {demo_data['timestamp'].min()} to {demo_data['timestamp'].max()}")
            return True
        else:
            print("❌ Demo data generation failed - empty DataFrame")
            return False
            
    except Exception as e:
        print(f"❌ Demo data test failed: {e}")
        traceback.print_exc()
        return False

def main():
    """Main test function"""
    print("🌬️  Air Quality Analytics - Installation Test")
    print("=" * 60)
    
    # Test imports
    imports_ok = test_imports()
    
    # Test custom modules
    custom_modules_ok = test_custom_modules()
    
    # Test basic functionality
    basic_functionality_ok = test_basic_functionality()
    
    # Test demo data
    demo_data_ok = test_demo_data()
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY")
    print("=" * 60)
    
    tests = [
        ("Module Imports", imports_ok),
        ("Custom Modules", custom_modules_ok),
        ("Basic Functionality", basic_functionality_ok),
        ("Demo Data Generation", demo_data_ok)
    ]
    
    all_tests_passed = True
    for test_name, test_result in tests:
        status = "✅ PASS" if test_result else "❌ FAIL"
        print(f"{test_name}: {status}")
        if not test_result:
            all_tests_passed = False
    
    print("\n" + "=" * 60)
    
    if all_tests_passed:
        print("🎉 ALL TESTS PASSED!")
        print("✅ Your Air Quality Analytics application is ready to use!")
        print("\n🚀 To start the application, run:")
        print("   python run_app.py")
        print("   or")
        print("   streamlit run app.py")
    else:
        print("❌ SOME TESTS FAILED!")
        print("💡 Please check the error messages above and fix any issues")
        print("\n🔧 Common solutions:")
        print("   1. Install missing packages: pip install -r requirements.txt")
        print("   2. Check Python version (3.8+ required)")
        print("   3. Verify all files are in the same directory")
    
    return all_tests_passed

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
