#!/usr/bin/env python3
"""
Startup script for the Air Quality Analytics application
"""

import sys
import os
import subprocess
import time

def check_dependencies():
    """Check if required packages are installed"""
    required_packages = [
        'streamlit', 'pandas', 'plotly', 'requests', 'numpy',
        'scikit-learn', 'statsmodels'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print("❌ Missing required packages:")
        for package in missing_packages:
            print(f"   - {package}")
        print("\n💡 Install missing packages with:")
        print("   pip install -r requirements.txt")
        return False
    
    print("✅ All required packages are installed")
    return True

def check_python_version():
    """Check if Python version is compatible"""
    if sys.version_info < (3, 8):
        print("❌ Python 3.8 or higher is required")
        print(f"   Current version: {sys.version}")
        return False
    
    print(f"✅ Python version {sys.version.split()[0]} is compatible")
    return True

def create_env_file():
    """Create .env file if it doesn't exist"""
    env_file = '.env'
    template_file = 'env_template.txt'
    
    if not os.path.exists(env_file) and os.path.exists(template_file):
        print("📝 Creating .env file from template...")
        try:
            with open(template_file, 'r') as f:
                template_content = f.read()
            
            with open(env_file, 'w') as f:
                f.write(template_content)
            
            print("✅ .env file created successfully")
            print("💡 Edit .env file to configure your API keys")
        except Exception as e:
            print(f"⚠️  Warning: Could not create .env file: {e}")
    elif os.path.exists(env_file):
        print("✅ .env file already exists")

def start_application():
    """Start the Streamlit application"""
    print("\n🚀 Starting Air Quality Analytics Application...")
    print("📱 The app will open in your default web browser")
    print("🌐 Local URL: http://localhost:8501")
    print("⏹️  Press Ctrl+C to stop the application")
    print("-" * 50)
    
    try:
        # Start Streamlit
        subprocess.run([
            sys.executable, "-m", "streamlit", "run", "app.py",
            "--server.port", "8501",
            "--server.headless", "false"
        ], check=True)
    except KeyboardInterrupt:
        print("\n\n👋 Application stopped by user")
    except subprocess.CalledProcessError as e:
        print(f"\n❌ Error starting application: {e}")
        return False
    except FileNotFoundError:
        print("\n❌ Streamlit not found. Install with: pip install streamlit")
        return False
    
    return True

def main():
    """Main function"""
    print("🌬️  Air Quality Analytics & Alert System")
    print("=" * 50)
    
    # Check prerequisites
    if not check_python_version():
        sys.exit(1)
    
    if not check_dependencies():
        sys.exit(1)
    
    # Create environment file
    create_env_file()
    
    # Start application
    if not start_application():
        sys.exit(1)

if __name__ == "__main__":
    main()
