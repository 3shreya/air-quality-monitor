import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import logging
from config import AQI_THRESHOLDS, POLLUTANTS
import streamlit as st

logger = logging.getLogger(__name__)

class AirQualityAlertSystem:
    """Handles air quality alerts and notifications"""
    
    def __init__(self):
        self.alert_history = []
        self.user_thresholds = {}
        self.alert_cooldown = {}  # Prevent spam alerts
    
    def set_user_thresholds(self, thresholds: Dict[str, float]):
        """
        Set custom alert thresholds for users
        
        Args:
            thresholds: Dictionary mapping pollutant to threshold value
        """
        self.user_thresholds = thresholds
        logger.info(f"User thresholds set: {thresholds}")
    
    def check_air_quality_alerts(self, df: pd.DataFrame, city: str) -> List[Dict]:
        """
        Check current air quality data for alert conditions
        
        Args:
            df: DataFrame with current air quality measurements
            city: City name for context
            
        Returns:
            List of alert dictionaries
        """
        if df.empty:
            return []
        
        alerts = []
        current_time = datetime.utcnow()
        
        # Group by parameter to get latest values
        latest_data = df.groupby('parameter').first().reset_index()
        
        for _, row in latest_data.iterrows():
            parameter = row['parameter']
            value = row['value']
            location = row['location']
            
            # Check if we should skip this parameter
            if parameter not in POLLUTANTS:
                continue
            
            # Check user-defined thresholds first
            if parameter in self.user_thresholds:
                user_threshold = self.user_thresholds[parameter]
                if value > user_threshold:
                    alert = self._create_alert(
                        parameter=parameter,
                        value=value,
                        threshold=user_threshold,
                        alert_type="user_threshold",
                        severity="high",
                        city=city,
                        location=location,
                        timestamp=current_time
                    )
                    alerts.append(alert)
                    continue
            
            # Check standard AQI thresholds
            aqi_value, aqi_category = self._calculate_aqi(parameter, value)
            
            # Determine alert severity based on AQI category
            severity_map = {
                "Good": "info",
                "Moderate": "warning",
                "Unhealthy for Sensitive Groups": "warning",
                "Unhealthy": "error",
                "Very Unhealthy": "critical",
                "Hazardous": "critical"
            }
            
            severity = severity_map.get(aqi_category, "info")
            
            # Only create alerts for moderate and above
            if aqi_category in ["Moderate", "Unhealthy for Sensitive Groups", "Unhealthy", "Very Unhealthy", "Hazardous"]:
                alert = self._create_alert(
                    parameter=parameter,
                    value=value,
                    threshold=value,  # Current value is the threshold
                    alert_type="aqi_threshold",
                    severity=severity,
                    city=city,
                    location=location,
                    timestamp=current_time,
                    aqi_value=aqi_value,
                    aqi_category=aqi_category
                )
                alerts.append(alert)
        
        # Check for trend-based alerts
        trend_alerts = self._check_trend_alerts(df, city)
        alerts.extend(trend_alerts)
        
        # Check for peak period alerts
        peak_alerts = self._check_peak_alerts(df, city)
        alerts.extend(peak_alerts)
        
        return alerts
    
    def _create_alert(self, parameter: str, value: float, threshold: float, 
                      alert_type: str, severity: str, city: str, location: str, 
                      timestamp: datetime, **kwargs) -> Dict:
        """
        Create an alert dictionary
        
        Args:
            parameter: Pollutant parameter
            value: Current measured value
            threshold: Threshold that was exceeded
            alert_type: Type of alert
            severity: Alert severity level
            city: City name
            location: Location name
            timestamp: When the alert occurred
            **kwargs: Additional alert data
            
        Returns:
            Alert dictionary
        """
        alert = {
            'id': f"{parameter}_{timestamp.strftime('%Y%m%d_%H%M%S')}",
            'parameter': parameter,
            'parameter_name': POLLUTANTS.get(parameter, {}).get('name', parameter),
            'value': round(value, 2),
            'threshold': round(threshold, 2),
            'alert_type': alert_type,
            'severity': severity,
            'city': city,
            'location': location,
            'timestamp': timestamp,
            'message': self._generate_alert_message(parameter, value, threshold, alert_type, **kwargs),
            'acknowledged': False,
            'acknowledged_at': None
        }
        
        # Add any additional kwargs
        alert.update(kwargs)
        
        return alert
    
    def _generate_alert_message(self, parameter: str, value: float, threshold: float, 
                               alert_type: str, **kwargs) -> str:
        """
        Generate human-readable alert message
        
        Args:
            parameter: Pollutant parameter
            threshold: Threshold that was exceeded
            alert_type: Type of alert
            **kwargs: Additional context
            
        Returns:
            Formatted alert message
        """
        param_name = POLLUTANTS.get(parameter, {}).get('name', parameter)
        unit = POLLUTANTS.get(parameter, {}).get('unit', '')
        
        if alert_type == "user_threshold":
            return f"⚠️ {param_name} levels ({value} {unit}) exceeded your custom threshold ({threshold} {unit})"
        
        elif alert_type == "aqi_threshold":
            aqi_category = kwargs.get('aqi_category', 'Unknown')
            return f"🚨 {param_name} levels are {aqi_category.lower()} ({value} {unit})"
        
        elif alert_type == "trend":
            trend_direction = kwargs.get('trend_direction', 'increasing')
            return f"📈 {param_name} levels are {trend_direction} rapidly"
        
        elif alert_type == "peak":
            return f"🔝 {param_name} levels are at peak levels ({value} {unit})"
        
        else:
            return f"Alert: {param_name} levels at {value} {unit}"
    
    def _calculate_aqi(self, pollutant: str, value: float) -> Tuple[int, str]:
        """
        Calculate AQI value and category for a pollutant
        
        Args:
            pollutant: Pollutant type
            value: Measured value
            
        Returns:
            Tuple of (AQI value, AQI category)
        """
        # Simplified AQI calculation (same as in data_fetcher.py)
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
    
    def _check_trend_alerts(self, df: pd.DataFrame, city: str) -> List[Dict]:
        """
        Check for trend-based alerts (rapid increases)
        
        Args:
            df: DataFrame with air quality data
            city: City name
            
        Returns:
            List of trend alerts
        """
        alerts = []
        current_time = datetime.utcnow()
        
        for param in df['parameter'].unique():
            param_data = df[df['parameter'] == param].copy()
            
            if len(param_data) < 6:  # Need at least 6 data points
                continue
            
            # Sort by timestamp and get recent data
            param_data = param_data.sort_values('timestamp')
            recent_data = param_data.tail(6)  # Last 6 measurements
            
            if len(recent_data) < 6:
                continue
            
            # Calculate trend
            x = np.arange(len(recent_data))
            y = recent_data['value'].values
            
            if len(y) > 1:
                slope, _ = np.polyfit(x, y, 1)
                
                # Alert if rapid increase (slope > 20% of mean value)
                mean_value = np.mean(y)
                threshold_slope = mean_value * 0.2
                
                if slope > threshold_slope:
                    # Check cooldown to prevent spam
                    cooldown_key = f"{param}_trend_{city}"
                    if self._check_cooldown(cooldown_key, minutes=30):
                        alert = self._create_alert(
                            parameter=param,
                            value=y[-1],
                            threshold=threshold_slope,
                            alert_type="trend",
                            severity="warning",
                            city=city,
                            location=recent_data.iloc[-1]['location'],
                            timestamp=current_time,
                            trend_direction="increasing",
                            slope=round(slope, 4)
                        )
                        alerts.append(alert)
                        
                        # Set cooldown
                        self.alert_cooldown[cooldown_key] = current_time
        
        return alerts
    
    def _check_peak_alerts(self, df: pd.DataFrame, city: str) -> List[Dict]:
        """
        Check for peak period alerts
        
        Args:
            df: DataFrame with air quality data
            city: City name
            
        Returns:
            List of peak alerts
        """
        alerts = []
        current_time = datetime.utcnow()
        
        for param in df['parameter'].unique():
            param_data = df[df['parameter'] == param]['value']
            
            if len(param_data) < 10:  # Need sufficient data
                continue
            
            # Check if current value is in top 10% of historical values
            threshold = param_data.quantile(0.9)
            current_value = param_data.iloc[0]  # Most recent
            
            if current_value >= threshold:
                # Check cooldown
                cooldown_key = f"{param}_peak_{city}"
                if self._check_cooldown(cooldown_key, minutes=60):
                    alert = self._create_alert(
                        parameter=param,
                        value=current_value,
                        threshold=threshold,
                        alert_type="peak",
                        severity="warning",
                        city=city,
                        location=df[df['parameter'] == param].iloc[0]['location'],
                        timestamp=current_time
                    )
                    alerts.append(alert)
                    
                    # Set cooldown
                    self.alert_cooldown[cooldown_key] = current_time
        
        return alerts
    
    def _check_cooldown(self, key: str, minutes: int = 30) -> bool:
        """
        Check if enough time has passed since last alert
        
        Args:
            key: Unique key for the alert type
            minutes: Minutes to wait between alerts
            
        Returns:
            True if cooldown period has passed
        """
        if key not in self.alert_cooldown:
            return True
        
        last_alert = self.alert_cooldown[key]
        time_diff = datetime.utcnow() - last_alert
        
        return time_diff.total_seconds() > (minutes * 60)
    
    def acknowledge_alert(self, alert_id: str):
        """
        Mark an alert as acknowledged
        
        Args:
            alert_id: ID of the alert to acknowledge
        """
        for alert in self.alert_history:
            if alert['id'] == alert_id:
                alert['acknowledged'] = True
                alert['acknowledged_at'] = datetime.utcnow()
                break
    
    def get_active_alerts(self) -> List[Dict]:
        """
        Get all active (unacknowledged) alerts
        
        Returns:
            List of active alerts
        """
        return [alert for alert in self.alert_history if not alert['acknowledged']]
    
    def get_alert_summary(self) -> Dict:
        """
        Get summary of all alerts
        
        Returns:
            Dictionary with alert summary statistics
        """
        if not self.alert_history:
            return {
                'total_alerts': 0,
                'active_alerts': 0,
                'severity_counts': {},
                'parameter_counts': {}
            }
        
        total_alerts = len(self.alert_history)
        active_alerts = len(self.get_active_alerts())
        
        # Count by severity
        severity_counts = {}
        for alert in self.alert_history:
            severity = alert['severity']
            severity_counts[severity] = severity_counts.get(severity, 0) + 1
        
        # Count by parameter
        parameter_counts = {}
        for alert in self.alert_history:
            parameter = alert['parameter']
            parameter_counts[parameter] = parameter_counts.get(parameter, 0) + 1
        
        return {
            'total_alerts': total_alerts,
            'active_alerts': active_alerts,
            'severity_counts': severity_counts,
            'parameter_counts': parameter_counts
        }
    
    def clear_old_alerts(self, days: int = 7):
        """
        Remove alerts older than specified days
        
        Args:
            days: Number of days to keep alerts
        """
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        self.alert_history = [
            alert for alert in self.alert_history 
            if alert['timestamp'] > cutoff_date
        ]
    
    def display_alerts_ui(self):
        """
        Display alerts in Streamlit UI
        """
        st.subheader("🚨 Air Quality Alerts")
        
        active_alerts = self.get_active_alerts()
        
        if not active_alerts:
            st.success("✅ No active alerts - air quality is good!")
            return
        
        # Display active alerts
        for alert in active_alerts:
            # Create alert container
            severity_colors = {
                "info": "blue",
                "warning": "orange", 
                "error": "red",
                "critical": "darkred"
            }
            
            color = severity_colors.get(alert['severity'], "blue")
            
            with st.container():
                col1, col2, col3 = st.columns([3, 1, 1])
                
                with col1:
                    st.markdown(f"**{alert['parameter_name']}** - {alert['city']}")
                    st.markdown(alert['message'])
                    st.caption(f"Location: {alert['location']} | Time: {alert['timestamp'].strftime('%Y-%m-%d %H:%M UTC')}")
                
                with col2:
                    st.metric(
                        "Value", 
                        f"{alert['value']} {POLLUTANTS.get(alert['parameter'], {}).get('unit', '')}",
                        delta=f"Threshold: {alert['threshold']}"
                    )
                
                with col3:
                    if st.button(f"Acknowledge", key=f"ack_{alert['id']}"):
                        self.acknowledge_alert(alert['id'])
                        st.rerun()
        
        # Display alert summary
        summary = self.get_alert_summary()
        
        with st.expander("📊 Alert Summary"):
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Total Alerts", summary['total_alerts'])
            
            with col2:
                st.metric("Active Alerts", summary['active_alerts'])
            
            with col3:
                st.metric("Acknowledged", summary['total_alerts'] - summary['active_alerts'])
            
            with col4:
                if summary['severity_counts']:
                    most_severe = max(summary['severity_counts'].items(), key=lambda x: x[1])
                    st.metric("Most Common", f"{most_severe[0].title()}")
