import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# OpenAQ API Configuration
OPENAQ_API_BASE_URL = "https://api.openaq.org/v2"
OPENAQ_API_KEY = os.getenv("OPENAQ_API_KEY", "")  # Optional API key for higher rate limits

# Air Quality Index (AQI) Thresholds
AQI_THRESHOLDS = {
    "Good": {"min": 0, "max": 50, "color": "#00E400"},
    "Moderate": {"min": 51, "max": 100, "color": "#FFFF00"},
    "Unhealthy for Sensitive Groups": {"min": 101, "max": 150, "color": "#FF7E00"},
    "Unhealthy": {"min": 151, "max": 200, "color": "#FF0000"},
    "Very Unhealthy": {"min": 201, "max": 300, "color": "#8F3F97"},
    "Hazardous": {"min": 301, "max": 500, "color": "#7E0023"}
}

# Default cities for demo
DEFAULT_CITIES = [
    "London", "New York", "Beijing", "Delhi", "Los Angeles",
    "Paris", "Tokyo", "Mumbai", "Mexico City", "Cairo"
]

# Pollutant parameters
POLLUTANTS = {
    "pm25": {"name": "PM2.5", "unit": "μg/m³", "description": "Fine particulate matter"},
    "pm10": {"name": "PM10", "unit": "μg/m³", "description": "Coarse particulate matter"},
    "no2": {"name": "NO₂", "unit": "ppb", "description": "Nitrogen dioxide"},
    "so2": {"name": "SO₂", "unit": "ppb", "description": "Sulfur dioxide"},
    "o3": {"name": "O₃", "unit": "ppb", "description": "Ozone"},
    "co": {"name": "CO", "unit": "ppm", "description": "Carbon monoxide"}
}

# App Configuration
APP_TITLE = "Real-Time Air Quality Analytics & Alert System"
APP_ICON = "🌬️"
PAGE_CONFIG = {
    "page_title": APP_TITLE,
    "page_icon": APP_ICON,
    "layout": "wide",
    "initial_sidebar_state": "expanded"
}

# Data refresh intervals (in seconds)
REFRESH_INTERVALS = {
    "live": 30,
    "hourly": 3600,
    "daily": 86400
}

# Forecasting parameters
FORECAST_DAYS = 7
FORECAST_CONFIDENCE = 0.95
