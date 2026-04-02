import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
from typing import Dict, List, Optional, Tuple
import streamlit as st
from config import AQI_THRESHOLDS, POLLUTANTS
from datetime import datetime, timedelta

class AirQualityVisualizations:
    """Handles all chart and graph generation for air quality data"""
    
    def __init__(self):
        self.color_palette = px.colors.qualitative.Set3
        self.aqi_colors = [threshold['color'] for threshold in AQI_THRESHOLDS.values()]
    
    def create_current_status_dashboard(self, df: pd.DataFrame, city: str) -> go.Figure:
        """
        Create a comprehensive current status dashboard
        
        Args:
            df: DataFrame with current air quality data
            city: City name
            
        Returns:
            Plotly figure with current status
        """
        if df.empty:
            return self._create_empty_figure("No data available")
        
        # Get latest values for each parameter
        latest_data = df.groupby('parameter').first().reset_index()
        
        # Create subplots
        fig = make_subplots(
            rows=2, cols=3,
            subplot_titles=[f"{POLLUTANTS.get(param, {}).get('name', param)}" for param in latest_data['parameter']],
            specs=[[{"type": "indicator"}, {"type": "indicator"}, {"type": "indicator"}],
                   [{"type": "indicator"}, {"type": "indicator"}, {"type": "indicator"}]]
        )
        
        # Add gauge charts for each parameter
        for i, (_, row) in enumerate(latest_data.iterrows()):
            param = row['parameter']
            value = row['value']
            unit = POLLUTANTS.get(param, {}).get('unit', '')
            
            # Calculate AQI and category
            aqi_value, aqi_category = self._calculate_aqi(param, value)
            
            # Determine gauge colors based on AQI
            if aqi_category == "Good":
                color = "green"
            elif aqi_category == "Moderate":
                color = "yellow"
            elif aqi_category == "Unhealthy for Sensitive Groups":
                color = "orange"
            elif aqi_category == "Unhealthy":
                color = "red"
            elif aqi_category == "Very Unhealthy":
                color = "purple"
            else:
                color = "darkred"
            
            # Add gauge
            fig.add_trace(
                go.Indicator(
                    mode="gauge+number+delta",
                    value=value,
                    domain={'x': [0, 1], 'y': [0, 1]},
                    title={'text': f"{POLLUTANTS.get(param, {}).get('name', param)} ({unit})"},
                    delta={'reference': value * 0.8},  # Simple reference
                    gauge={
                        'axis': {'range': [None, value * 1.5]},
                        'bar': {'color': color},
                        'steps': [
                            {'range': [0, value * 0.5], 'color': "lightgray"},
                            {'range': [value * 0.5, value], 'color': "gray"}
                        ],
                        'threshold': {
                            'line': {'color': "red", 'width': 4},
                            'thickness': 0.75,
                            'value': value
                        }
                    }
                ),
                row=(i // 3) + 1, col=(i % 3) + 1
            )
        
        # Update layout
        fig.update_layout(
            title=f"Current Air Quality Status - {city}",
            height=600,
            showlegend=False,
            template="plotly_white"
        )
        
        return fig
    
    def create_time_series_chart(self, df: pd.DataFrame, pollutant: str, city: str, 
                                show_moving_average: bool = True) -> go.Figure:
        """
        Create time series chart for a specific pollutant
        
        Args:
            df: DataFrame with air quality data
            pollutant: Pollutant to visualize
            city: City name
            show_moving_average: Whether to show moving average line
            
        Returns:
            Plotly figure with time series
        """
        if df.empty:
            return self._create_empty_figure("No data available")
        
        # Filter for specific pollutant
        pollutant_data = df[df['parameter'] == pollutant].copy()
        
        if pollutant_data.empty:
            return self._create_empty_figure(f"No data for {pollutant}")
        
        # Sort by timestamp
        pollutant_data = pollutant_data.sort_values('timestamp')
        
        # Create figure
        fig = go.Figure()
        
        # Add main line
        fig.add_trace(
            go.Scatter(
                x=pollutant_data['timestamp'],
                y=pollutant_data['value'],
                mode='lines+markers',
                name=f"{POLLUTANTS.get(pollutant, {}).get('name', pollutant)}",
                line=dict(color='blue', width=2),
                marker=dict(size=4)
            )
        )
        
        # Add moving average if requested
        if show_moving_average and len(pollutant_data) > 24:
            # Calculate 24-hour moving average
            pollutant_data['ma_24h'] = pollutant_data['value'].rolling(window=24, min_periods=1).mean()
            
            fig.add_trace(
                go.Scatter(
                    x=pollutant_data['timestamp'],
                    y=pollutant_data['ma_24h'],
                    mode='lines',
                    name='24h Moving Average',
                    line=dict(color='red', width=2, dash='dash')
                )
            )
        
        # Add AQI threshold lines
        self._add_aqi_thresholds(fig, pollutant, pollutant_data['value'].max())
        
        # Update layout
        fig.update_layout(
            title=f"{POLLUTANTS.get(pollutant, {}).get('name', pollutant)} Levels Over Time - {city}",
            xaxis_title="Time",
            yaxis_title=f"Concentration ({POLLUTANTS.get(pollutant, {}).get('unit', '')})",
            height=500,
            template="plotly_white",
            hovermode='x unified'
        )
        
        return fig
    
    def create_comparison_chart(self, df: pd.DataFrame, city: str) -> go.Figure:
        """
        Create comparison chart for all pollutants
        
        Args:
            df: DataFrame with air quality data
            city: City name
            
        Returns:
            Plotly figure with comparison
        """
        if df.empty:
            return self._create_empty_figure("No data available")
        
        # Get latest values for each parameter
        latest_data = df.groupby('parameter').first().reset_index()
        
        # Create bar chart
        fig = go.Figure()
        
        # Add bars for each pollutant
        for _, row in latest_data.iterrows():
            param = row['parameter']
            value = row['value']
            unit = POLLUTANTS.get(param, {}).get('unit', '')
            
            # Calculate AQI for color
            aqi_value, aqi_category = self._calculate_aqi(param, value)
            
            # Get color based on AQI category
            color = self._get_aqi_color(aqi_category)
            
            fig.add_trace(
                go.Bar(
                    x=[POLLUTANTS.get(param, {}).get('name', param)],
                    y=[value],
                    name=param,
                    marker_color=color,
                    text=f"{value} {unit}",
                    textposition='auto'
                )
            )
        
        # Update layout
        fig.update_layout(
            title=f"Current Pollutant Levels Comparison - {city}",
            xaxis_title="Pollutants",
            yaxis_title="Concentration",
            height=500,
            template="plotly_white",
            showlegend=False,
            barmode='group'
        )
        
        return fig
    
    def create_heatmap(self, df: pd.DataFrame, pollutant: str, city: str) -> go.Figure:
        """
        Create heatmap showing pollutant levels by hour and day of week
        
        Args:
            df: DataFrame with air quality data
            pollutant: Pollutant to visualize
            city: City name
            
        Returns:
            Plotly figure with heatmap
        """
        if df.empty:
            return self._create_empty_figure("No data available")
        
        # Filter for specific pollutant
        pollutant_data = df[df['parameter'] == pollutant].copy()
        
        if pollutant_data.empty:
            return self._create_empty_figure(f"No data for {pollutant}")
        
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
        
        # Create heatmap
        fig = go.Figure(data=go.Heatmap(
            z=heatmap_matrix.values,
            x=[f"{h:02d}:00" for h in range(24)],
            y=['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'],
            colorscale='Viridis',
            text=heatmap_matrix.values.round(2),
            texttemplate="%{text}",
            textfont={"size": 10},
            hoverongaps=False
        ))
        
        # Update layout
        fig.update_layout(
            title=f"{POLLUTANTS.get(pollutant, {}).get('name', pollutant)} Levels by Time - {city}",
            xaxis_title="Hour of Day",
            yaxis_title="Day of Week",
            height=500,
            template="plotly_white"
        )
        
        return fig
    
    def create_forecast_chart(self, historical_df: pd.DataFrame, forecast_data: pd.DataFrame, 
                             pollutant: str, city: str) -> go.Figure:
        """
        Create forecast chart showing historical data and predictions
        
        Args:
            historical_df: DataFrame with historical air quality data
            forecast_data: DataFrame with forecast data
            pollutant: Pollutant being forecasted
            city: City name
            
        Returns:
            Plotly figure with forecast
        """
        if historical_df.empty and forecast_data.empty:
            return self._create_empty_figure("No data available")
        
        fig = go.Figure()
        
        # Add historical data
        if not historical_df.empty:
            pollutant_historical = historical_df[historical_df['parameter'] == pollutant].copy()
            if not pollutant_historical.empty:
                pollutant_historical = pollutant_historical.sort_values('timestamp')
                
                fig.add_trace(
                    go.Scatter(
                        x=pollutant_historical['timestamp'],
                        y=pollutant_historical['value'],
                        mode='lines+markers',
                        name='Historical Data',
                        line=dict(color='blue', width=2),
                        marker=dict(size=4)
                    )
                )
        
        # Add forecast data
        if not forecast_data.empty:
            fig.add_trace(
                go.Scatter(
                    x=forecast_data['timestamp'],
                    y=forecast_data['predicted_value'],
                    mode='lines+markers',
                    name='Forecast',
                    line=dict(color='red', width=3, dash='dash'),
                    marker=dict(size=6)
                )
            )
            
            # Add confidence intervals if available
            if 'confidence_lower' in forecast_data.columns and 'confidence_upper' in forecast_data.columns:
                fig.add_trace(
                    go.Scatter(
                        x=forecast_data['timestamp'],
                        y=forecast_data['confidence_upper'],
                        mode='lines',
                        line=dict(width=0),
                        showlegend=False,
                        fillcolor='rgba(255,0,0,0.2)',
                        fill='tonexty'
                    )
                )
                
                fig.add_trace(
                    go.Scatter(
                        x=forecast_data['timestamp'],
                        y=forecast_data['confidence_lower'],
                        mode='lines',
                        line=dict(width=0),
                        showlegend=False,
                        fillcolor='rgba(255,0,0,0.2)',
                        fill='tonexty'
                    )
                )
        
        # Update layout
        fig.update_layout(
            title=f"{POLLUTANTS.get(pollutant, {}).get('name', pollutant)} Forecast - {city}",
            xaxis_title="Time",
            yaxis_title=f"Concentration ({POLLUTANTS.get(pollutant, {}).get('unit', '')})",
            height=500,
            template="plotly_white",
            hovermode='x unified'
        )
        
        return fig
    
    def create_statistics_chart(self, stats: Dict) -> go.Figure:
        """
        Create statistics visualization
        
        Args:
            stats: Dictionary with statistics for each pollutant
            
        Returns:
            Plotly figure with statistics
        """
        if not stats:
            return self._create_empty_figure("No statistics available")
        
        # Prepare data for visualization
        pollutants = list(stats.keys())
        means = [stats[p]['mean'] for p in pollutants]
        medians = [stats[p]['median'] for p in pollutants]
        stds = [stats[p]['std'] for p in pollutants]
        
        # Create subplots
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=['Mean Values', 'Median Values', 'Standard Deviation', 'Range (Min-Max)'],
            specs=[[{"type": "bar"}, {"type": "bar"}],
                   [{"type": "bar"}, {"type": "bar"}]]
        )
        
        # Mean values
        fig.add_trace(
            go.Bar(x=pollutants, y=means, name='Mean', marker_color='blue'),
            row=1, col=1
        )
        
        # Median values
        fig.add_trace(
            go.Bar(x=pollutants, y=medians, name='Median', marker_color='green'),
            row=1, col=2
        )
        
        # Standard deviation
        fig.add_trace(
            go.Bar(x=pollutants, y=stds, name='Std Dev', marker_color='orange'),
            row=2, col=1
        )
        
        # Range
        ranges = [stats[p]['max'] - stats[p]['min'] for p in pollutants]
        fig.add_trace(
            go.Bar(x=pollutants, y=ranges, name='Range', marker_color='red'),
            row=2, col=2
        )
        
        # Update layout
        fig.update_layout(
            title="Air Quality Statistics Summary",
            height=600,
            template="plotly_white",
            showlegend=False
        )
        
        return fig
    
    def create_aqi_gauge(self, pollutant: str, value: float) -> go.Figure:
        """
        Create AQI gauge chart for a specific pollutant and value
        
        Args:
            pollutant: Pollutant type
            value: Measured value
            
        Returns:
            Plotly figure with AQI gauge
        """
        # Calculate AQI
        aqi_value, aqi_category = self._calculate_aqi(pollutant, value)
        
        # Get color
        color = self._get_aqi_color(aqi_category)
        
        # Create gauge
        fig = go.Figure(go.Indicator(
            mode="gauge+number+delta",
            value=aqi_value,
            domain={'x': [0, 1], 'y': [0, 1]},
            title={'text': f"AQI - {POLLUTANTS.get(pollutant, {}).get('name', pollutant)}"},
            delta={'reference': 50},
            gauge={
                'axis': {'range': [None, 500]},
                'bar': {'color': color},
                'steps': [
                    {'range': [0, 50], 'color': "lightgreen"},
                    {'range': [51, 100], 'color': "lightyellow"},
                    {'range': [101, 150], 'color': "lightorange"},
                    {'range': [151, 200], 'color': "lightcoral"},
                    {'range': [201, 300], 'color': "plum"},
                    {'range': [301, 500], 'color': "maroon"}
                ],
                'threshold': {
                    'line': {'color': "red", 'width': 4},
                    'thickness': 0.75,
                    'value': aqi_value
                }
            }
        ))
        
        # Update layout
        fig.update_layout(
            title=f"Air Quality Index - {aqi_category}",
            height=400,
            template="plotly_white"
        )
        
        return fig
    
    def _calculate_aqi(self, pollutant: str, value: float) -> Tuple[int, str]:
        """Calculate AQI value and category (same logic as other modules)"""
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
    
    def _get_aqi_color(self, category: str) -> str:
        """Get color for AQI category"""
        color_map = {
            "Good": "#00E400",
            "Moderate": "#FFFF00",
            "Unhealthy for Sensitive Groups": "#FF7E00",
            "Unhealthy": "#FF0000",
            "Very Unhealthy": "#8F3F97",
            "Hazardous": "#7E0023"
        }
        return color_map.get(category, "#808080")
    
    def _add_aqi_thresholds(self, fig: go.Figure, pollutant: str, max_value: float):
        """Add AQI threshold lines to a chart"""
        # Add threshold lines based on pollutant type
        if pollutant == "pm25":
            thresholds = [12.0, 35.4, 55.4, 150.4]
            labels = ["Good", "Moderate", "Unhealthy", "Very Unhealthy"]
        elif pollutant == "pm10":
            thresholds = [54, 154, 254, 354]
            labels = ["Good", "Moderate", "Unhealthy", "Very Unhealthy"]
        else:
            return
        
        colors = ["green", "yellow", "orange", "red"]
        
        for threshold, label, color in zip(thresholds, labels, colors):
            if threshold <= max_value * 1.2:  # Only show if threshold is reasonable
                fig.add_hline(
                    y=threshold,
                    line_dash="dash",
                    line_color=color,
                    annotation_text=f"{label} ({threshold})",
                    annotation_position="top right"
                )
    
    def _create_empty_figure(self, message: str) -> go.Figure:
        """Create an empty figure with a message"""
        fig = go.Figure()
        fig.add_annotation(
            text=message,
            xref="paper", yref="paper",
            x=0.5, y=0.5,
            showarrow=False,
            font=dict(size=16, color="gray")
        )
        fig.update_layout(
            xaxis=dict(visible=False),
            yaxis=dict(visible=False),
            height=400
        )
        return fig
