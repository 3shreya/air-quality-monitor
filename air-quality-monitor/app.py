import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import time
import plotly.graph_objects as go
from streamlit_option_menu import option_menu
from streamlit_autorefresh import st_autorefresh

# Import our custom modules
from config import *
from data_fetcher import AirQualityDataFetcher
from analytics import AirQualityAnalytics
from alert_system import AirQualityAlertSystem
from visualizations import AirQualityVisualizations

# Configure Streamlit page
st.set_page_config(**PAGE_CONFIG)

# Initialize session state
if 'data_fetcher' not in st.session_state:
    st.session_state.data_fetcher = AirQualityDataFetcher()
if 'analytics' not in st.session_state:
    st.session_state.analytics = AirQualityAnalytics()
if 'alert_system' not in st.session_state:
    st.session_state.alert_system = AirQualityAlertSystem()
if 'visualizations' not in st.session_state:
    st.session_state.visualizations = AirQualityVisualizations()
if 'current_data' not in st.session_state:
    st.session_state.current_data = pd.DataFrame()
if 'historical_data' not in st.session_state:
    st.session_state.historical_data = pd.DataFrame()
if 'selected_city' not in st.session_state:
    st.session_state.selected_city = DEFAULT_CITIES[0]
if 'use_demo_data' not in st.session_state:
    st.session_state.use_demo_data = False

def main():
    """Main application function"""
    
    # Header
    st.title(f"{APP_ICON} {APP_TITLE}")
    st.markdown("Real-time air quality monitoring, analysis, and forecasting for cities worldwide")
    
    # Sidebar
    with st.sidebar:
        st.header("🌍 City Selection")
        
        # City selection
        selected_city = st.selectbox(
            "Select City",
            options=DEFAULT_CITIES,
            index=DEFAULT_CITIES.index(st.session_state.selected_city)
        )
        
        if selected_city != st.session_state.selected_city:
            st.session_state.selected_city = selected_city
            st.session_state.current_data = pd.DataFrame()
            st.session_state.historical_data = pd.DataFrame()
            st.rerun()
        
        # Data source selection
        st.subheader("📡 Data Source")
        use_demo_data = st.checkbox(
            "Use Demo Data (for testing)",
            value=st.session_state.use_demo_data,
            help="Use simulated data when API is not available"
        )
        
        if use_demo_data != st.session_state.use_demo_data:
            st.session_state.use_demo_data = use_demo_data
            st.session_state.current_data = pd.DataFrame()
            st.rerun()
        
        # Refresh controls
        st.subheader("🔄 Refresh Controls")
        auto_refresh = st.checkbox("Auto-refresh every 30 seconds", value=True)
        
        if st.button("🔄 Refresh Data Now"):
            fetch_data()
            st.rerun()
        
        # Alert settings
        st.subheader("🚨 Alert Settings")
        with st.expander("Custom Thresholds"):
            st.markdown("Set custom alert thresholds for pollutants:")
            
            custom_thresholds = {}
            for param, info in POLLUTANTS.items():
                threshold = st.number_input(
                    f"{info['name']} ({info['unit']})",
                    min_value=0.0,
                    value=100.0,
                    step=1.0,
                    key=f"threshold_{param}"
                )
                custom_thresholds[param] = threshold
            
            if st.button("Set Thresholds"):
                st.session_state.alert_system.set_user_thresholds(custom_thresholds)
                st.success("Custom thresholds set!")
        
        # Data info
        st.subheader("ℹ️ Data Information")
        if not st.session_state.current_data.empty:
            st.info(f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            st.info(f"Data points: {len(st.session_state.current_data)}")
        else:
            st.warning("No data loaded")
    
    # Main content area
    if st.session_state.current_data.empty:
        fetch_data()
    
    # Navigation menu
    selected_page = option_menu(
        menu_title=None,
        options=["🏠 Dashboard", "📊 Analytics", "🔮 Forecasting", "🚨 Alerts", "📈 Trends", "⚙️ Settings"],
        icons=["house", "graph-up", "crystal-ball", "exclamation-triangle", "trending-up", "gear"],
        menu_icon="cast",
        default_index=0,
        orientation="horizontal",
    )
    
    # Page routing
    if selected_page == "🏠 Dashboard":
        show_dashboard()
    elif selected_page == "📊 Analytics":
        show_analytics()
    elif selected_page == "🔮 Forecasting":
        show_forecasting()
    elif selected_page == "🚨 Alerts":
        show_alerts()
    elif selected_page == "📈 Trends":
        show_trends()
    elif selected_page == "⚙️ Settings":
        show_settings()
    
    # Auto-refresh
    if auto_refresh:
        st_autorefresh(interval=30000, key="auto_refresh")

def fetch_data():
    """Fetch air quality data for the selected city"""
    try:
        with st.spinner(f"Fetching air quality data for {st.session_state.selected_city}..."):
            if st.session_state.use_demo_data:
                # Use demo data
                st.session_state.current_data = st.session_state.data_fetcher.get_demo_data(st.session_state.selected_city)
                st.session_state.historical_data = st.session_state.current_data.copy()
            else:
                # Try to fetch real data
                current_data = st.session_state.data_fetcher.get_latest_measurements(st.session_state.selected_city)
                
                if current_data.empty:
                    st.warning("Could not fetch real-time data. Using demo data instead.")
                    st.session_state.current_data = st.session_state.data_fetcher.get_demo_data(st.session_state.selected_city)
                    st.session_state.historical_data = st.session_state.current_data.copy()
                else:
                    st.session_state.current_data = current_data
                    # Fetch historical data for analysis
                    historical_data = st.session_state.data_fetcher.get_historical_data(st.session_state.selected_city, days=30)
                    if not historical_data.empty:
                        st.session_state.historical_data = historical_data
                    else:
                        st.session_state.historical_data = current_data.copy()
        
        # Check for alerts
        if not st.session_state.current_data.empty:
            alerts = st.session_state.alert_system.check_air_quality_alerts(
                st.session_state.current_data, 
                st.session_state.selected_city
            )
            # Add alerts to history
            st.session_state.alert_system.alert_history.extend(alerts)
            
    except Exception as e:
        st.error(f"Error fetching data: {e}")
        # Fallback to demo data
        st.session_state.current_data = st.session_state.data_fetcher.get_demo_data(st.session_state.selected_city)
        st.session_state.historical_data = st.session_state.current_data.copy()

def show_dashboard():
    """Display the main dashboard"""
    st.header("🏠 Air Quality Dashboard")
    
    if st.session_state.current_data.empty:
        st.warning("No data available. Please refresh the data.")
        return
    
    # Current status overview
    st.subheader("📊 Current Air Quality Status")
    
    # Create current status dashboard
    status_fig = st.session_state.visualizations.create_current_status_dashboard(
        st.session_state.current_data, 
        st.session_state.selected_city
    )
    st.plotly_chart(status_fig, use_container_width=True)
    
    # Quick metrics
    st.subheader("📈 Quick Metrics")
    
    if not st.session_state.current_data.empty:
        latest_data = st.session_state.current_data.groupby('parameter').first().reset_index()
        
        # Display metrics in columns
        cols = st.columns(len(latest_data))
        for i, (_, row) in enumerate(latest_data.iterrows()):
            with cols[i]:
                param = row['parameter']
                value = row['value']
                unit = POLLUTANTS.get(param, {}).get('unit', '')
                
                # Calculate AQI
                aqi_value, aqi_category = st.session_state.data_fetcher.calculate_aqi(param, value)
                
                # Color based on AQI
                if aqi_category == "Good":
                    color = "🟢"
                elif aqi_category == "Moderate":
                    color = "🟡"
                elif aqi_category == "Unhealthy for Sensitive Groups":
                    color = "🟠"
                elif aqi_category == "Unhealthy":
                    color = "🔴"
                elif aqi_category == "Very Unhealthy":
                    color = "🟣"
                else:
                    color = "⚫"
                
                st.metric(
                    label=f"{color} {POLLUTANTS.get(param, {}).get('name', param)}",
                    value=f"{value} {unit}",
                    delta=f"AQI: {aqi_value} ({aqi_category})"
                )
    
    # Comparison chart
    st.subheader("📊 Pollutant Comparison")
    comparison_fig = st.session_state.visualizations.create_comparison_chart(
        st.session_state.current_data, 
        st.session_state.selected_city
    )
    st.plotly_chart(comparison_fig, use_container_width=True)
    
    # Recent measurements table
    st.subheader("📋 Recent Measurements")
    if not st.session_state.current_data.empty:
        display_data = st.session_state.current_data.copy()
        display_data['timestamp'] = display_data['timestamp'].dt.strftime('%Y-%m-%d %H:%M:%S')
        display_data['parameter'] = display_data['parameter'].map(
            lambda x: POLLUTANTS.get(x, {}).get('name', x)
        )
        
        st.dataframe(
            display_data[['timestamp', 'parameter', 'value', 'unit', 'location']].head(20),
            use_container_width=True
        )

def show_analytics():
    """Display analytics and statistics"""
    st.header("📊 Air Quality Analytics")
    
    if st.session_state.current_data.empty:
        st.warning("No data available for analysis.")
        return
    
    # Statistics
    st.subheader("📈 Statistical Summary")
    
    stats = st.session_state.analytics.calculate_statistics(st.session_state.current_data)
    
    if stats:
        # Display statistics in a nice format
        cols = st.columns(len(stats))
        for i, (param, stat_data) in enumerate(stats.items()):
            with cols[i]:
                st.markdown(f"**{POLLUTANTS.get(param, {}).get('name', param)}**")
                st.metric("Mean", f"{stat_data['mean']}")
                st.metric("Median", f"{stat_data['median']}")
                st.metric("Std Dev", f"{stat_data['std']}")
                st.metric("Range", f"{stat_data['max'] - stat_data['min']}")
        
        # Statistics chart
        stats_fig = st.session_state.visualizations.create_statistics_chart(stats)
        st.plotly_chart(stats_fig, use_container_width=True)
    
    # Outlier detection
    st.subheader("🔍 Outlier Detection")
    
    outliers = st.session_state.analytics.detect_outliers(st.session_state.current_data)
    
    if not outliers.empty:
        st.warning(f"Found {len(outliers)} outliers in the data")
        st.dataframe(outliers, use_container_width=True)
    else:
        st.success("No outliers detected in the current data")
    
    # Moving averages
    st.subheader("📊 Moving Averages")
    
    moving_avg_data = st.session_state.analytics.calculate_moving_averages(
        st.session_state.current_data, 
        window=24
    )
    
    if not moving_avg_data.empty:
        # Show moving average for a selected pollutant
        pollutant_options = list(st.session_state.current_data['parameter'].unique())
        selected_pollutant = st.selectbox(
            "Select pollutant for moving average analysis",
            options=pollutant_options,
            index=0
        )
        
        pollutant_ma = moving_avg_data[moving_avg_data['parameter'] == selected_pollutant]
        
        if not pollutant_ma.empty:
            fig = go.Figure()
            
            fig.add_trace(go.Scatter(
                x=pollutant_ma['timestamp'],
                y=pollutant_ma['value'],
                mode='lines+markers',
                name='Actual Values',
                line=dict(color='blue')
            ))
            
            fig.add_trace(go.Scatter(
                x=pollutant_ma['timestamp'],
                y=pollutant_ma['moving_average'],
                mode='lines',
                name='24h Moving Average',
                line=dict(color='red', dash='dash')
            ))
            
            fig.update_layout(
                title=f"{POLLUTANTS.get(selected_pollutant, {}).get('name', selected_pollutant)} Moving Average",
                xaxis_title="Time",
                yaxis_title="Concentration",
                height=400
            )
            
            st.plotly_chart(fig, use_container_width=True)
    
    # Peak periods
    st.subheader("🔝 Peak Periods")
    
    peaks = st.session_state.analytics.identify_peak_periods(st.session_state.current_data)
    
    if not peaks.empty:
        st.info(f"Identified {len(peaks)} peak pollution periods")
        st.dataframe(peaks, use_container_width=True)
    else:
        st.info("No significant peak periods detected")

def show_forecasting():
    """Display forecasting capabilities"""
    st.header("🔮 Air Quality Forecasting")
    
    if st.session_state.historical_data.empty:
        st.warning("Insufficient historical data for forecasting. Need at least 24 hours of data.")
        return
    
    st.markdown("""
    This section provides air quality forecasts using time series analysis. 
    The forecasting model uses historical patterns, seasonal trends, and recent measurements 
    to predict future air quality levels.
    """)
    
    # Forecasting parameters
    st.subheader("⚙️ Forecasting Parameters")
    
    col1, col2 = st.columns(2)
    
    with col1:
        pollutant_options = list(st.session_state.historical_data['parameter'].unique())
        selected_pollutant = st.selectbox(
            "Select pollutant to forecast",
            options=pollutant_options,
            index=0
        )
    
    with col2:
        forecast_days = st.slider(
            "Forecast horizon (days)",
            min_value=1,
            max_value=14,
            value=7
        )
    
    # Generate forecast
    if st.button("🔮 Generate Forecast"):
        with st.spinner("Generating forecast..."):
            forecast_result = st.session_state.analytics.forecast_air_quality(
                st.session_state.historical_data,
                selected_pollutant,
                forecast_days
            )
            
            if forecast_result:
                st.success("Forecast generated successfully!")
                
                # Display forecast chart
                st.subheader("📊 Forecast Visualization")
                
                forecast_fig = st.session_state.visualizations.create_forecast_chart(
                    st.session_state.historical_data,
                    forecast_result['forecast_data'],
                    selected_pollutant,
                    st.session_state.selected_city
                )
                
                st.plotly_chart(forecast_fig, use_container_width=True)
                
                # Display forecast data
                st.subheader("📋 Forecast Data")
                st.dataframe(
                    forecast_result['forecast_data'],
                    use_container_width=True
                )
                
                # Model performance
                st.subheader("📈 Model Performance")
                
                performance = forecast_result['model_performance']
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric("Mean Absolute Error", f"{performance['mae']}")
                
                with col2:
                    st.metric("Root Mean Square Error", f"{performance['rmse']}")
                
                with col3:
                    st.metric("R² Score", f"{performance['r2']}")
                
                # Forecast summary
                st.subheader("📊 Forecast Summary")
                
                forecast_df = forecast_result['forecast_data']
                
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric(
                        "Average Predicted Value",
                        f"{forecast_df['predicted_value'].mean():.2f}"
                    )
                
                with col2:
                    st.metric(
                        "Predicted Trend",
                        "↗️ Increasing" if forecast_df['predicted_value'].iloc[-1] > forecast_df['predicted_value'].iloc[0] else "↘️ Decreasing"
                    )
                
                with col3:
                    st.metric(
                        "Forecast Horizon",
                        forecast_result['forecast_horizon']
                    )
                
            else:
                st.error("Failed to generate forecast. Insufficient data or model error.")

def show_alerts():
    """Display alerts and notifications"""
    st.header("🚨 Air Quality Alerts")
    
    # Display current alerts
    st.session_state.alert_system.display_alerts_ui()
    
    # Alert history
    st.subheader("📚 Alert History")
    
    if st.session_state.alert_system.alert_history:
        # Filter options
        col1, col2 = st.columns(2)
        
        with col1:
            severity_filter = st.selectbox(
                "Filter by severity",
                options=["All"] + list(set([alert['severity'] for alert in st.session_state.alert_system.alert_history])),
                index=0
            )
        
        with col2:
            parameter_filter = st.selectbox(
                "Filter by parameter",
                options=["All"] + list(set([alert['parameter'] for alert in st.session_state.alert_system.alert_history])),
                index=0
            )
        
        # Filter alerts
        filtered_alerts = st.session_state.alert_system.alert_history.copy()
        
        if severity_filter != "All":
            filtered_alerts = [alert for alert in filtered_alerts if alert['severity'] == severity_filter]
        
        if parameter_filter != "All":
            filtered_alerts = [alert for alert in filtered_alerts if alert['parameter'] == parameter_filter]
        
        # Display filtered alerts
        if filtered_alerts:
            for alert in filtered_alerts[-10:]:  # Show last 10 alerts
                with st.container():
                    col1, col2, col3 = st.columns([3, 1, 1])
                    
                    with col1:
                        status = "✅ Acknowledged" if alert['acknowledged'] else "🚨 Active"
                        st.markdown(f"**{status}** - {alert['parameter_name']} - {alert['city']}")
                        st.markdown(alert['message'])
                        st.caption(f"Location: {alert['location']} | Time: {alert['timestamp'].strftime('%Y-%m-%d %H:%M UTC')}")
                    
                    with col2:
                        st.metric(
                            "Value", 
                            f"{alert['value']} {POLLUTANTS.get(alert['parameter'], {}).get('unit', '')}"
                        )
                    
                    with col3:
                        if not alert['acknowledged']:
                            if st.button(f"Acknowledge", key=f"hist_ack_{alert['id']}"):
                                st.session_state.alert_system.acknowledge_alert(alert['id'])
                                st.rerun()
                        else:
                            st.caption(f"Acknowledged: {alert['acknowledged_at'].strftime('%Y-%m-%d %H:%M UTC')}")
        else:
            st.info("No alerts match the selected filters")
    else:
        st.info("No alert history available")
    
    # Clear old alerts
    if st.button("🗑️ Clear Old Alerts (older than 7 days)"):
        st.session_state.alert_system.clear_old_alerts(days=7)
        st.success("Old alerts cleared!")
        st.rerun()

def show_trends():
    """Display trend analysis"""
    st.header("📈 Trend Analysis")
    
    if st.session_state.historical_data.empty:
        st.warning("Insufficient historical data for trend analysis.")
        return
    
    st.markdown("""
    Analyze air quality trends over time to understand patterns, seasonal variations, 
    and long-term changes in pollution levels.
    """)
    
    # Trend analysis
    st.subheader("📊 Overall Trends")
    
    trends = st.session_state.analytics.generate_trend_analysis(st.session_state.historical_data)
    
    if trends:
        # Display trends in a table
        trend_data = []
        for param, trend_info in trends.items():
            trend_data.append({
                'Pollutant': POLLUTANTS.get(param, {}).get('name', param),
                'Trend Direction': trend_info['trend_direction'].title(),
                'Trend Strength': trend_info['trend_strength'],
                'Percentage Change': f"{trend_info['percentage_change']:.1f}%",
                'Start Value': trend_info['start_value'],
                'End Value': trend_info['end_value']
            })
        
        trend_df = pd.DataFrame(trend_data)
        st.dataframe(trend_df, use_container_width=True)
        
        # Visualize trends
        st.subheader("📈 Trend Visualization")
        
        pollutant_options = list(trends.keys())
        selected_pollutant = st.selectbox(
            "Select pollutant for detailed trend analysis",
            options=pollutant_options,
            index=0
        )
        
        # Create trend chart
        pollutant_data = st.session_state.historical_data[
            st.session_state.historical_data['parameter'] == selected_pollutant
        ].copy()
        
        if not pollutant_data.empty:
            pollutant_data = pollutant_data.sort_values('timestamp')
            
            fig = go.Figure()
            
            # Add actual data
            fig.add_trace(go.Scatter(
                x=pollutant_data['timestamp'],
                y=pollutant_data['value'],
                mode='lines+markers',
                name='Actual Values',
                line=dict(color='blue', width=2)
            ))
            
            # Add trend line
            x = np.arange(len(pollutant_data))
            y = pollutant_data['value'].values
            
            if len(y) > 1:
                z = np.polyfit(x, y, 1)
                p = np.poly1d(z)
                
                fig.add_trace(go.Scatter(
                    x=pollutant_data['timestamp'],
                    y=p(x),
                    mode='lines',
                    name='Trend Line',
                    line=dict(color='red', width=3, dash='dash')
                ))
            
            fig.update_layout(
                title=f"{POLLUTANTS.get(selected_pollutant, {}).get('name', selected_pollutant)} Trend Analysis",
                xaxis_title="Time",
                yaxis_title="Concentration",
                height=500,
                template="plotly_white"
            )
            
            st.plotly_chart(fig, use_container_width=True)
    
    # Time-based patterns
    st.subheader("🕐 Time-Based Patterns")
    
    pollutant_options = list(st.session_state.historical_data['parameter'].unique())
    selected_pollutant = st.selectbox(
        "Select pollutant for time pattern analysis",
        options=pollutant_options,
        index=0,
        key="trend_pollutant"
    )
    
    # Create heatmap
    heatmap_fig = st.session_state.visualizations.create_heatmap(
        st.session_state.historical_data,
        selected_pollutant,
        st.session_state.selected_city
    )
    
    st.plotly_chart(heatmap_fig, use_container_width=True)
    
    # Health risk assessment
    st.subheader("🏥 Health Risk Assessment")
    
    risk_scores = st.session_state.analytics.calculate_health_risk_score(st.session_state.current_data)
    
    if risk_scores:
        # Display risk scores
        risk_data = []
        for param, risk_info in risk_scores.items():
            risk_data.append({
                'Pollutant': POLLUTANTS.get(param, {}).get('name', param),
                'Current Value': risk_info['current_value'],
                'Risk Level': risk_info['risk_level'],
                'Risk Score': f"{risk_info['risk_score']}/100",
                'Trend': risk_info['trend'].title()
            })
        
        risk_df = pd.DataFrame(risk_data)
        st.dataframe(risk_df, use_container_width=True)
        
        # Create risk visualization
        fig = go.Figure()
        
        params = list(risk_scores.keys())
        risk_values = [risk_scores[p]['risk_score'] for p in params]
        colors = ['green' if r <= 25 else 'yellow' if r <= 50 else 'orange' if r <= 75 else 'red' for r in risk_values]
        
        fig.add_trace(go.Bar(
            x=[POLLUTANTS.get(p, {}).get('name', p) for p in params],
            y=risk_values,
            marker_color=colors,
            text=risk_values,
            textposition='auto'
        ))
        
        fig.update_layout(
            title="Health Risk Assessment by Pollutant",
            xaxis_title="Pollutants",
            yaxis_title="Risk Score (0-100)",
            height=400,
            template="plotly_white"
        )
        
        st.plotly_chart(fig, use_container_width=True)

def show_settings():
    """Display application settings"""
    st.header("⚙️ Application Settings")
    
    st.markdown("""
    Configure application settings, data sources, and user preferences.
    """)
    
    # Data source settings
    st.subheader("📡 Data Source Configuration")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**OpenAQ API Settings**")
        st.info(f"Base URL: {OPENAQ_API_BASE_URL}")
        
        if OPENAQ_API_KEY:
            st.success("✅ API Key configured")
        else:
            st.warning("⚠️ No API key configured (using public endpoints)")
    
    with col2:
        st.markdown("**Data Refresh Settings**")
        st.info(f"Live refresh: {REFRESH_INTERVALS['live']} seconds")
        st.info(f"Hourly refresh: {REFRESH_INTERVALS['hourly']} seconds")
    
    # Application information
    st.subheader("ℹ️ Application Information")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**Version Information**")
        st.info("Version: 1.0.0")
        st.info("Last Updated: 2024")
        st.info("Python: 3.8+")
    
    with col2:
        st.markdown("**Features**")
        st.info("✅ Real-time data fetching")
        st.info("✅ Advanced analytics")
        st.info("✅ Forecasting capabilities")
        st.info("✅ Alert system")
        st.info("✅ Interactive visualizations")
    
    # Data management
    st.subheader("🗄️ Data Management")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🗑️ Clear All Data"):
            st.session_state.current_data = pd.DataFrame()
            st.session_state.historical_data = pd.DataFrame()
            st.success("All data cleared!")
    
    with col2:
        if st.button("📊 Export Current Data"):
            if not st.session_state.current_data.empty:
                csv = st.session_state.current_data.to_csv(index=False)
                st.download_button(
                    label="📥 Download CSV",
                    data=csv,
                    file_name=f"air_quality_{st.session_state.selected_city}_{datetime.now().strftime('%Y%m%d')}.csv",
                    mime="text/csv"
                )
            else:
                st.warning("No data to export")
    
    # About section
    st.subheader("ℹ️ About")
    
    st.markdown("""
    **Real-Time Air Quality Analytics & Alert System**
    
    This application provides comprehensive air quality monitoring and analysis capabilities:
    
    - **Real-time Data**: Fetches live air quality data from OpenAQ API
    - **Advanced Analytics**: Statistical analysis, outlier detection, and trend analysis
    - **Forecasting**: Time series forecasting for air quality prediction
    - **Alert System**: Intelligent alerts for unhealthy air quality conditions
    - **Interactive Visualizations**: Rich charts and graphs for data exploration
    
    **Data Sources**: OpenAQ API, with fallback to simulated data for testing
    
    **Technologies**: Python, Streamlit, Pandas, Plotly, Scikit-learn
    
    **Purpose**: Environmental health monitoring and public safety awareness
    """)

if __name__ == "__main__":
    main()
