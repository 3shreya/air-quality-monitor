import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
import warnings
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_absolute_error, mean_squared_error
import logging

# Suppress warnings for cleaner output
warnings.filterwarnings('ignore')

logger = logging.getLogger(__name__)

class AirQualityAnalytics:
    """Handles data analysis, statistics, and forecasting for air quality data"""
    
    def __init__(self):
        self.scaler = StandardScaler()
        self.forecast_model = None
    
    def calculate_statistics(self, df: pd.DataFrame) -> Dict:
        """
        Calculate comprehensive statistics for air quality data
        
        Args:
            df: DataFrame with air quality measurements
            
        Returns:
            Dictionary containing statistics for each pollutant
        """
        if df.empty:
            return {}
        
        stats = {}
        
        # Group by parameter and calculate statistics
        for param in df['parameter'].unique():
            param_data = df[df['parameter'] == param]['value']
            
            if len(param_data) > 0:
                stats[param] = {
                    'count': len(param_data),
                    'mean': round(param_data.mean(), 2),
                    'median': round(param_data.median(), 2),
                    'std': round(param_data.std(), 2),
                    'min': round(param_data.min(), 2),
                    'max': round(param_data.max(), 2),
                    'q25': round(param_data.quantile(0.25), 2),
                    'q75': round(param_data.quantile(0.75), 2),
                    'iqr': round(param_data.quantile(0.75) - param_data.quantile(0.25), 2)
                }
        
        return stats
    
    def detect_outliers(self, df: pd.DataFrame, method: str = 'iqr') -> pd.DataFrame:
        """
        Detect outliers in air quality data
        
        Args:
            df: DataFrame with air quality measurements
            method: Method to use ('iqr' or 'zscore')
            
        Returns:
            DataFrame with outlier information
        """
        if df.empty:
            return pd.DataFrame()
        
        outliers = []
        
        for param in df['parameter'].unique():
            param_data = df[df['parameter'] == param]['value']
            
            if len(param_data) < 4:  # Need at least 4 points for outlier detection
                continue
            
            if method == 'iqr':
                Q1 = param_data.quantile(0.25)
                Q3 = param_data.quantile(0.75)
                IQR = Q3 - Q1
                lower_bound = Q1 - 1.5 * IQR
                upper_bound = Q3 + 1.5 * IQR
                
                outlier_mask = (param_data < lower_bound) | (param_data > upper_bound)
                
            elif method == 'zscore':
                z_scores = np.abs((param_data - param_data.mean()) / param_data.std())
                outlier_mask = z_scores > 3
            
            if outlier_mask.any():
                outlier_indices = param_data[outlier_mask].index
                for idx in outlier_indices:
                    outliers.append({
                        'timestamp': df.loc[idx, 'timestamp'],
                        'parameter': param,
                        'value': df.loc[idx, 'value'],
                        'location': df.loc[idx, 'location'],
                        'method': method
                    })
        
        return pd.DataFrame(outliers)
    
    def calculate_moving_averages(self, df: pd.DataFrame, window: int = 24) -> pd.DataFrame:
        """
        Calculate moving averages for trend analysis
        
        Args:
            df: DataFrame with air quality measurements
            window: Window size for moving average (in hours)
            
        Returns:
            DataFrame with moving averages
        """
        if df.empty:
            return pd.DataFrame()
        
        # Create a copy and sort by timestamp
        df_copy = df.copy().sort_values('timestamp')
        
        # Calculate moving averages for each parameter
        moving_avg_data = []
        
        for param in df_copy['parameter'].unique():
            param_df = df_copy[df_copy['parameter'] == param].copy()
            
            if len(param_df) >= window:
                # Select only numeric columns for resampling
                numeric_cols = ['timestamp', 'value']
                param_df_numeric = param_df[numeric_cols].copy()
                
                # Resample to hourly data if needed
                param_df_numeric = param_df_numeric.set_index('timestamp').resample('h').mean().reset_index()
                
                # Calculate moving average
                param_df_numeric[f'{window}h_ma'] = param_df_numeric['value'].rolling(window=window, min_periods=1).mean()
                param_df_numeric[f'{window}h_std'] = param_df_numeric['value'].rolling(window=window, min_periods=1).std()
                
                # Add to results
                for _, row in param_df_numeric.iterrows():
                    if pd.notna(row[f'{window}h_ma']):
                        moving_avg_data.append({
                            'timestamp': row['timestamp'],
                            'parameter': param,
                            'value': row['value'],
                            'moving_average': round(row[f'{window}h_ma'], 2),
                            'moving_std': round(row[f'{window}h_std'], 2) if pd.notna(row[f'{window}h_std']) else None
                        })
        
        return pd.DataFrame(moving_avg_data)
    
    def identify_peak_periods(self, df: pd.DataFrame, threshold_percentile: float = 90) -> pd.DataFrame:
        """
        Identify peak pollution periods
        
        Args:
            df: DataFrame with air quality measurements
            threshold_percentile: Percentile threshold for peak detection
            
        Returns:
            DataFrame with peak period information
        """
        if df.empty:
            return pd.DataFrame()
        
        peaks = []
        
        for param in df['parameter'].unique():
            param_data = df[df['parameter'] == param]['value']
            
            if len(param_data) > 0:
                threshold = param_data.quantile(threshold_percentile / 100)
                peak_mask = param_data >= threshold
                
                if peak_mask.any():
                    peak_indices = param_data[peak_mask].index
                    for idx in peak_indices:
                        peaks.append({
                            'timestamp': df.loc[idx, 'timestamp'],
                            'parameter': param,
                            'value': df.loc[idx, 'value'],
                            'threshold': round(threshold, 2),
                            'percentile': threshold_percentile,
                            'location': df.loc[idx, 'location']
                        })
        
        return pd.DataFrame(peaks)
    
    def forecast_air_quality(self, df: pd.DataFrame, pollutant: str, days: int = 7) -> Dict:
        """
        Simple time series forecasting for air quality
        
        Args:
            df: DataFrame with historical air quality data
            pollutant: Pollutant to forecast
            days: Number of days to forecast
            
        Returns:
            Dictionary with forecast results
        """
        if df.empty:
            return {}
        
        # Filter data for the specific pollutant
        pollutant_data = df[df['parameter'] == pollutant].copy()
        
        if len(pollutant_data) < 24:  # Need at least 24 hours of data
            return {}
        
        try:
            # Prepare data for forecasting - select only numeric columns
            numeric_cols = ['timestamp', 'value']
            pollutant_data = pollutant_data[numeric_cols].copy()
            pollutant_data = pollutant_data.sort_values('timestamp')
            pollutant_data = pollutant_data.set_index('timestamp')
            
            # Resample to hourly data
            pollutant_data = pollutant_data.resample('h').mean().ffill()
            
            # Create time features
            pollutant_data['hour'] = pollutant_data.index.hour
            pollutant_data['day_of_week'] = pollutant_data.index.dayofweek
            pollutant_data['is_weekend'] = pollutant_data['day_of_week'].isin([5, 6]).astype(int)
            
            # Create lag features
            pollutant_data['lag_1h'] = pollutant_data['value'].shift(1)
            pollutant_data['lag_24h'] = pollutant_data['value'].shift(24)
            
            # Remove rows with NaN values
            pollutant_data = pollutant_data.dropna()
            
            if len(pollutant_data) < 48:  # Need sufficient data after lag creation
                return {}
            
            # Prepare features and target
            features = ['hour', 'day_of_week', 'is_weekend', 'lag_1h', 'lag_24h']
            X = pollutant_data[features]
            y = pollutant_data['value']
            
            # Split data (use last 20% for validation)
            split_idx = int(len(X) * 0.8)
            X_train, X_test = X[:split_idx], X[split_idx:]
            y_train, y_test = y[:split_idx], y[split_idx:]
            
            # Scale features
            X_train_scaled = self.scaler.fit_transform(X_train)
            X_test_scaled = self.scaler.transform(X_test)
            
            # Train model
            model = LinearRegression()
            model.fit(X_train_scaled, y_train)
            
            # Make predictions on test set
            y_pred = model.predict(X_test_scaled)
            
            # Calculate metrics
            mae = mean_absolute_error(y_test, y_pred)
            rmse = np.sqrt(mean_squared_error(y_test, y_pred))
            
            # Generate future predictions
            last_timestamp = pollutant_data.index[-1]
            future_timestamps = pd.date_range(
                start=last_timestamp + timedelta(hours=1),
                periods=days * 24,
                freq='h'
            )
            
            future_data = []
            for timestamp in future_timestamps:
                # Create features for future timestamp
                hour = timestamp.hour
                day_of_week = timestamp.dayofweek
                is_weekend = int(day_of_week in [5, 6])
                
                # Use last known values for lags (simplified approach)
                lag_1h = pollutant_data['value'].iloc[-1] if len(pollutant_data) > 0 else 0
                lag_24h = pollutant_data['value'].iloc[-24] if len(pollutant_data) >= 24 else lag_1h
                
                features = [hour, day_of_week, is_weekend, lag_1h, lag_24h]
                features_scaled = self.scaler.transform([features])
                
                prediction = model.predict(features_scaled)[0]
                
                future_data.append({
                    'timestamp': timestamp,
                    'predicted_value': max(0, round(prediction, 2)),
                    'confidence_lower': max(0, round(prediction - mae, 2)),
                    'confidence_upper': round(prediction + mae, 2)
                })
            
            forecast_df = pd.DataFrame(future_data)
            
            return {
                'forecast_data': forecast_df,
                'model_performance': {
                    'mae': round(mae, 2),
                    'rmse': round(rmse, 2),
                    'r2': round(model.score(X_test_scaled, y_test), 3)
                },
                'last_training_date': last_timestamp,
                'forecast_horizon': f"{days} days"
            }
            
        except Exception as e:
            logger.error(f"Error in forecasting {pollutant}: {e}")
            return {}
    
    def generate_trend_analysis(self, df: pd.DataFrame) -> Dict:
        """
        Generate trend analysis for air quality data
        
        Args:
            df: DataFrame with air quality measurements
            
        Returns:
            Dictionary with trend analysis results
        """
        if df.empty:
            return {}
        
        trends = {}
        
        for param in df['parameter'].unique():
            param_data = df[df['parameter'] == param].copy()
            
            if len(param_data) < 2:
                continue
            
            # Sort by timestamp
            param_data = param_data.sort_values('timestamp')
            
            # Calculate simple linear trend
            x = np.arange(len(param_data))
            y = param_data['value'].values
            
            if len(y) > 1:
                slope, intercept = np.polyfit(x, y, 1)
                
                # Calculate trend direction and strength
                trend_direction = "increasing" if slope > 0 else "decreasing" if slope < 0 else "stable"
                trend_strength = abs(slope)
                
                # Calculate percentage change
                if y[0] != 0:
                    pct_change = ((y[-1] - y[0]) / y[0]) * 100
                else:
                    pct_change = 0
                
                trends[param] = {
                    'slope': round(slope, 4),
                    'trend_direction': trend_direction,
                    'trend_strength': round(trend_strength, 4),
                    'percentage_change': round(pct_change, 2),
                    'start_value': round(y[0], 2),
                    'end_value': round(y[-1], 2),
                    'data_points': len(y)
                }
        
        return trends
    
    def create_heatmap_data(self, df: pd.DataFrame, pollutant: str) -> pd.DataFrame:
        """
        Create heatmap data for pollutant levels by hour and day of week
        
        Args:
            df: DataFrame with air quality measurements
            pollutant: Pollutant to analyze
            
        Returns:
            DataFrame formatted for heatmap visualization
        """
        if df.empty:
            return pd.DataFrame()
        
        # Filter for specific pollutant
        pollutant_data = df[df['parameter'] == pollutant].copy()
        
        if len(pollutant_data) == 0:
            return pd.DataFrame()
        
        # Add time features
        pollutant_data['hour'] = pollutant_data['timestamp'].dt.hour
        pollutant_data['day_of_week'] = pollutant_data['timestamp'].dt.dayofweek
        pollutant_data['day_name'] = pollutant_data['timestamp'].dt.day_name()
        
        # Create pivot table for heatmap
        heatmap_data = pollutant_data.groupby(['day_of_week', 'hour'])['value'].mean().reset_index()
        
        # Pivot to create matrix format
        heatmap_matrix = heatmap_data.pivot(index='day_of_week', columns='hour', values='value')
        
        # Fill missing values with 0
        heatmap_matrix = heatmap_matrix.fillna(0)
        
        return heatmap_matrix
    
    def calculate_health_risk_score(self, df: pd.DataFrame) -> Dict:
        """
        Calculate health risk score based on air quality data
        
        Args:
            df: DataFrame with air quality measurements
            
        Returns:
            Dictionary with health risk assessment
        """
        if df.empty:
            return {}
        
        risk_scores = {}
        
        for param in df['parameter'].unique():
            param_data = df[df['parameter'] == param]['value']
            
            if len(param_data) == 0:
                continue
            
            # Calculate risk metrics
            current_value = param_data.iloc[0]  # Most recent value
            max_value = param_data.max()
            avg_value = param_data.mean()
            
            # Define risk thresholds (simplified)
            risk_thresholds = {
                'pm25': {'low': 12, 'moderate': 35.4, 'high': 55.4, 'very_high': 150.4},
                'pm10': {'low': 54, 'moderate': 154, 'high': 254, 'very_high': 354},
                'no2': {'low': 53, 'moderate': 100, 'high': 360, 'very_high': 649},
                'so2': {'low': 35, 'moderate': 75, 'high': 185, 'very_high': 304},
                'o3': {'low': 54, 'moderate': 70, 'high': 85, 'very_high': 105},
                'co': {'low': 4.4, 'moderate': 9.4, 'high': 12.4, 'very_high': 15.4}
            }
            
            thresholds = risk_thresholds.get(param, risk_thresholds['pm25'])
            
            # Calculate risk score (0-100)
            if current_value <= thresholds['low']:
                risk_score = 0
                risk_level = "Low"
            elif current_value <= thresholds['moderate']:
                risk_score = 25
                risk_level = "Moderate"
            elif current_value <= thresholds['high']:
                risk_score = 50
                risk_level = "High"
            elif current_value <= thresholds['very_high']:
                risk_score = 75
                risk_level = "Very High"
            else:
                risk_score = 100
                risk_level = "Critical"
            
            risk_scores[param] = {
                'current_value': round(current_value, 2),
                'risk_score': risk_score,
                'risk_level': risk_level,
                'max_value': round(max_value, 2),
                'avg_value': round(avg_value, 2),
                'trend': "increasing" if current_value > avg_value else "decreasing" if current_value < avg_value else "stable"
            }
        
        return risk_scores
