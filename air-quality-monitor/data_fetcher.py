import requests
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import time
from typing import Dict, List, Optional, Tuple
import logging
from config import OPENAQ_API_BASE_URL, OPENAQ_API_KEY, POLLUTANTS

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AirQualityDataFetcher:
    """Fetches and processes air quality data from OpenAQ API"""
    
    def __init__(self):
        self.base_url = OPENAQ_API_BASE_URL
        self.api_key = OPENAQ_API_KEY
        self.session = requests.Session()
        
        # Add headers if API key is available
        if self.api_key:
            self.session.headers.update({"X-API-Key": self.api_key})
    
    def get_latest_measurements(self, city: str, limit: int = 100) -> pd.DataFrame:
        """
        Fetch latest air quality measurements for a specific city
        
        Args:
            city: City name to fetch data for
            limit: Maximum number of measurements to fetch
            
        Returns:
            DataFrame with latest measurements
        """
        try:
            # Search for locations in the city
            locations_url = f"{self.base_url}/locations"
            params = {
                "city": city,
                "limit": 100,
                "sort": "desc"
            }
            
            response = self.session.get(locations_url, params=params)
            response.raise_for_status()
            
            locations_data = response.json()
            if not locations_data.get("results"):
                logger.warning(f"No locations found for city: {city}")
                return pd.DataFrame()
            
            # Get measurements from the first few locations
            all_measurements = []
            location_count = min(3, len(locations_data["results"]))
            
            for i in range(location_count):
                location = locations_data["results"][i]
                location_id = location["id"]
                
                # Fetch measurements for this location
                measurements_url = f"{self.base_url}/measurements"
                params = {
                    "location_id": location_id,
                    "limit": limit // location_count,
                    "sort": "desc"
                }
                
                response = self.session.get(measurements_url, params=params)
                response.raise_for_status()
                
                measurements_data = response.json()
                if measurements_data.get("results"):
                    all_measurements.extend(measurements_data["results"])
                
                # Rate limiting
                time.sleep(0.1)
            
            if not all_measurements:
                return pd.DataFrame()
            
            # Process and clean the data
            df = self._process_measurements(all_measurements)
            return df
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching data for {city}: {e}")
            return pd.DataFrame()
        except Exception as e:
            logger.error(f"Unexpected error for {city}: {e}")
            return pd.DataFrame()
    
    def get_historical_data(self, city: str, days: int = 30) -> pd.DataFrame:
        """
        Fetch historical air quality data for trend analysis
        
        Args:
            city: City name
            days: Number of days to look back
            
        Returns:
            DataFrame with historical measurements
        """
        try:
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=days)
            
            # Search for locations in the city
            locations_url = f"{self.base_url}/locations"
            params = {
                "city": city,
                "limit": 100
            }
            
            response = self.session.get(locations_url, params=params)
            response.raise_for_status()
            
            locations_data = response.json()
            if not locations_data.get("results"):
                return pd.DataFrame()
            
            # Get measurements from the first location
            location = locations_data["results"][0]
            location_id = location["id"]
            
            # Fetch historical measurements
            measurements_url = f"{self.base_url}/measurements"
            params = {
                "location_id": location_id,
                "limit": 1000,
                "date_from": start_date.isoformat(),
                "date_to": end_date.isoformat(),
                "sort": "asc"
            }
            
            response = self.session.get(measurements_url, params=params)
            response.raise_for_status()
            
            measurements_data = response.json()
            if not measurements_data.get("results"):
                return pd.DataFrame()
            
            # Process the data
            df = self._process_measurements(measurements_data["results"])
            return df
            
        except Exception as e:
            logger.error(f"Error fetching historical data for {city}: {e}")
            return pd.DataFrame()
    
    def _process_measurements(self, measurements: List[Dict]) -> pd.DataFrame:
        """
        Process raw measurement data into a clean DataFrame
        
        Args:
            measurements: List of measurement dictionaries from API
            
        Returns:
            Cleaned DataFrame
        """
        if not measurements:
            return pd.DataFrame()
        
        processed_data = []
        
        for measurement in measurements:
            try:
                # Extract basic info
                location = measurement.get("location", "")
                city = measurement.get("city", "")
                country = measurement.get("country", "")
                coordinates = measurement.get("coordinates", {})
                
                # Extract measurements
                for param in measurement.get("measurements", []):
                    parameter = param.get("parameter", "")
                    value = param.get("value", None)
                    unit = param.get("unit", "")
                    last_updated = param.get("lastUpdated", "")
                    
                    if value is not None and parameter in POLLUTANTS:
                        processed_data.append({
                            "timestamp": last_updated,
                            "location": location,
                            "city": city,
                            "country": country,
                            "latitude": coordinates.get("latitude"),
                            "longitude": coordinates.get("longitude"),
                            "parameter": parameter,
                            "value": value,
                            "unit": unit
                        })
            
            except Exception as e:
                logger.warning(f"Error processing measurement: {e}")
                continue
        
        if not processed_data:
            return pd.DataFrame()
        
        # Create DataFrame and clean up
        df = pd.DataFrame(processed_data)
        
        # Convert timestamp to datetime
        df["timestamp"] = pd.to_datetime(df["timestamp"])
        
        # Sort by timestamp
        df = df.sort_values("timestamp", ascending=False)
        
        # Remove duplicates
        df = df.drop_duplicates(subset=["timestamp", "location", "parameter"])
        
        return df
    
    def calculate_aqi(self, pollutant: str, value: float) -> Tuple[int, str]:
        """
        Calculate Air Quality Index (AQI) for a given pollutant and value
        
        Args:
            pollutant: Pollutant type (pm25, pm10, no2, so2, o3, co)
            value: Measured value
            
        Returns:
            Tuple of (AQI value, AQI category)
        """
        # Simplified AQI calculation based on EPA standards
        # This is a basic implementation - real AQI calculations are more complex
        
        if pollutant == "pm25":
            if value <= 12.0:
                aqi = int(((value - 0) / 12.0) * 50)
                category = "Good"
            elif value <= 35.4:
                aqi = int(((value - 12.1) / 23.3) * 50 + 51)
                category = "Moderate"
            elif value <= 55.4:
                aqi = int(((value - 35.5) / 19.9) * 50 + 101)
                category = "Unhealthy for Sensitive Groups"
            elif value <= 150.4:
                aqi = int(((value - 55.5) / 94.9) * 50 + 151)
                category = "Unhealthy"
            elif value <= 250.4:
                aqi = int(((value - 150.5) / 99.9) * 50 + 201)
                category = "Very Unhealthy"
            else:
                aqi = int(((value - 250.5) / 249.5) * 50 + 301)
                category = "Hazardous"
        
        elif pollutant == "pm10":
            if value <= 54:
                aqi = int(((value - 0) / 54) * 50)
                category = "Good"
            elif value <= 154:
                aqi = int(((value - 55) / 99) * 50 + 51)
                category = "Moderate"
            elif value <= 254:
                aqi = int(((value - 155) / 99) * 50 + 101)
                category = "Unhealthy for Sensitive Groups"
            elif value <= 354:
                aqi = int(((value - 255) / 99) * 50 + 151)
                category = "Unhealthy"
            elif value <= 424:
                aqi = int(((value - 355) / 69) * 50 + 201)
                category = "Very Unhealthy"
            else:
                aqi = int(((value - 425) / 575) * 50 + 301)
                category = "Hazardous"
        
        else:
            # For other pollutants, use a simplified scale
            if value <= 50:
                aqi = int(value)
                category = "Good"
            elif value <= 100:
                aqi = int(value)
                category = "Moderate"
            elif value <= 150:
                aqi = int(value)
                category = "Unhealthy for Sensitive Groups"
            elif value <= 200:
                aqi = int(value)
                category = "Unhealthy"
            elif value <= 300:
                aqi = int(value)
                category = "Very Unhealthy"
            else:
                aqi = int(value)
                category = "Hazardous"
        
        return min(aqi, 500), category
    
    def get_demo_data(self, city: str) -> pd.DataFrame:
        """
        Generate demo data for testing when API is not available
        
        Args:
            city: City name
            
        Returns:
            DataFrame with simulated air quality data
        """
        # Generate timestamps for the last 24 hours
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(hours=24)
        timestamps = pd.date_range(start=start_time, end=end_time, freq="h")
        
        demo_data = []
        
        for timestamp in timestamps:
            # Simulate realistic air quality values with some variation
            base_values = {
                "pm25": np.random.normal(25, 8),
                "pm10": np.random.normal(45, 15),
                "no2": np.random.normal(30, 10),
                "so2": np.random.normal(8, 3),
                "o3": np.random.normal(45, 15),
                "co": np.random.normal(0.8, 0.3)
            }
            
            # Add some daily pattern (higher during day, lower at night)
            hour = timestamp.hour
            if 6 <= hour <= 18:  # Daytime
                multiplier = 1.2
            else:  # Nighttime
                multiplier = 0.8
            
            for param, value in base_values.items():
                adjusted_value = max(0, value * multiplier + np.random.normal(0, value * 0.1))
                
                demo_data.append({
                    "timestamp": timestamp,
                    "location": f"{city} Central",
                    "city": city,
                    "country": "Demo",
                    "latitude": 40.7128 if city == "New York" else 51.5074,
                    "longitude": -74.0060 if city == "New York" else -0.1278,
                    "parameter": param,
                    "value": round(adjusted_value, 2),
                    "unit": POLLUTANTS[param]["unit"]
                })
        
        df = pd.DataFrame(demo_data)
        return df.sort_values("timestamp", ascending=False)
