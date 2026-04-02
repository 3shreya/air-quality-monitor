<div align="center">

# 🌬️ Air Quality Monitoring & Alert System

**Real-time air quality analytics, forecasting, and smart alerts for cities worldwide**

[![Python](https://img.shields.io/badge/Python-3.9%2B-blue?logo=python&logoColor=white)](https://python.org)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.28-FF4B4B?logo=streamlit&logoColor=white)](https://streamlit.io)
[![Plotly](https://img.shields.io/badge/Plotly-5.17-3F4F75?logo=plotly&logoColor=white)](https://plotly.com)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![OpenAQ](https://img.shields.io/badge/Data-OpenAQ_API-00AAFF)](https://openaq.org)

[Features](#-features) · [Demo](#-demo) · [Installation](#-installation) · [Usage](#-usage) · [Architecture](#-architecture) · [API Setup](#-api-setup)

</div>

---

## 📌 Overview

A full-stack data application that pulls **live air quality data** from the [OpenAQ API](https://openaq.org), runs statistical analytics and ML forecasting, and fires configurable alerts — all inside an interactive Streamlit dashboard.

Built with a modular architecture: data fetching, analytics, visualizations, and alerting are each separate, independently-testable modules.

---

## ✨ Features

| Module | What it does |
|---|---|
| 🏠 **Live Dashboard** | Real-time AQI gauges, pollutant breakdowns, and city comparisons |
| 📊 **Analytics** | Descriptive stats, outlier detection, rolling averages, correlation heatmaps |
| 🔮 **Forecasting** | 1–14 day predictions using Prophet + confidence intervals |
| 🚨 **Alert System** | AQI threshold alerts with cooldown, custom per-pollutant limits |
| 📈 **Trend Analysis** | Long-term patterns, seasonal decomposition, health risk scoring |
| 🗺️ **Map View** | Geographic distribution of monitoring stations (Folium) |

**Pollutants tracked:** PM2.5 · PM10 · NO₂ · SO₂ · O₃ · CO

---

## 🖥️ Demo

> Run locally with demo data — no API key required!

```bash
git clone https://github.com/YOUR_USERNAME/air-quality-monitor.git
cd air-quality-monitor
pip install -r requirements.txt
streamlit run app.py
```

Then open `http://localhost:8501` in your browser and check **"Use Demo Data"** in the sidebar.

---

## ⚙️ Installation

### Prerequisites
- Python 3.9 or higher
- pip

### Steps

```bash
# 1. Clone the repository
git clone https://github.com/YOUR_USERNAME/air-quality-monitor.git
cd air-quality-monitor

# 2. Create a virtual environment (recommended)
python -m venv venv

# Activate it:
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. (Optional) Set up environment variables
cp .env.example .env
# Edit .env with your OpenAQ API key

# 5. Run the app
streamlit run app.py
```

---

## 🚀 Usage

### Running the App

```bash
streamlit run app.py
```

### Running with a Custom Port

```bash
streamlit run app.py --server.port 8502
```

### Testing Your Installation

```bash
python test_installation.py
```

### Using the Dashboard

1. **Select a city** from the sidebar dropdown (10 global cities available)
2. **Toggle Demo Data** if you don't have an API key yet
3. **Navigate tabs** — Dashboard → Analytics → Forecasting → Alerts → Trends
4. **Set custom alert thresholds** in the Alerts tab for any pollutant
5. **Enable auto-refresh** to get live 30-second data updates

---

## 🏗️ Architecture

```
air-quality-monitor/
│
├── app.py                  # Main Streamlit app — routing & layout
├── config.py               # AQI thresholds, pollutants, app settings
├── data_fetcher.py         # OpenAQ API client & demo data generator
├── analytics.py            # Stats, outlier detection, forecasting (Prophet)
├── alert_system.py         # Alert evaluation, cooldown, history
├── visualizations.py       # All Plotly & Folium chart functions
│
├── run_app.py              # Helper script to launch the app
├── test_installation.py    # Dependency & API connectivity checks
│
├── requirements.txt
├── .env.example
└── README.md
```

### Data Flow

```
OpenAQ API ──► data_fetcher.py ──► app.py (session state)
                                        │
                    ┌───────────────────┼───────────────────┐
                    ▼                   ▼                   ▼
              analytics.py      alert_system.py     visualizations.py
              (stats/forecast)  (threshold check)   (Plotly charts)
```

---

## 🔑 API Setup

The app works out-of-the-box with **demo data**. For live data:

1. Register at [OpenAQ](https://explore.openaq.org) (free)
2. Get your API key from the dashboard
3. Add it to your `.env` file:

```env
OPENAQ_API_KEY=your_api_key_here
```

4. Restart the app and uncheck **"Use Demo Data"** in the sidebar

> **Note:** The free tier allows ~60 requests/minute. The app handles rate limiting automatically.

---

## 📦 Dependencies

| Package | Purpose |
|---|---|
| `streamlit` | Web app framework |
| `pandas` / `numpy` | Data manipulation |
| `plotly` | Interactive charts |
| `prophet` | Time-series forecasting |
| `scikit-learn` | ML utilities |
| `statsmodels` | Statistical analysis |
| `folium` | Map visualizations |
| `requests` | API calls |
| `python-dotenv` | Environment variable management |

---

## 🛠️ Troubleshooting

| Error | Fix |
|---|---|
| `ModuleNotFoundError` | Run `pip install -r requirements.txt` |
| `Port already in use` | Use `streamlit run app.py --server.port 8502` |
| `API rate limit exceeded` | Enable "Use Demo Data" or add an API key |
| `Permission denied` (Windows) | Run terminal as Administrator |
| `Prophet install fails` | Install `pystan` first: `pip install pystan` |

---

## 📄 License

This project is licensed under the [MIT License](LICENSE).

---

## 🙌 Acknowledgements

- [OpenAQ](https://openaq.org) for the open air quality data API
- [Streamlit](https://streamlit.io) for the rapid app framework
- [Facebook Prophet](https://facebook.github.io/prophet/) for time-series forecasting

---

<div align="center">
Made with 🐍 Python · 📊 Data Science · 🌱 Environmental Awareness
</div>
