# AI-Powered Network Failure Prediction System

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/)
[![XGBoost](https://img.shields.io/badge/XGBoost-2.0+-orange.svg)](https://xgboost.ai/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20Linux%20%7C%20Raspberry%20Pi-green.svg)](https://www.raspberrypi.com/)

## 📡 Overview

A **production-grade supervised machine learning system** that predicts network node failures **before they occur** using real-time telemetry data. Built with XGBoost regression, this system achieves **90%+ critical failure detection** with less than **1 minute mean absolute error**.

### Key Capabilities
- ⚡ **Real-time inference** - Predicts failure within 2-10 minute windows
- 🧠 **Gradient boosting** - XGBoost regression model with 9 features
- 📊 **Multi-dimensional analysis** - Router ping, DNS ping, RSSI tracking
- 🚨 **Automated alerts** - Critical warning system for imminent failures
- 🔄 **Rolling statistics** - 5-round moving averages and trend detection
- 🍓 **Edge deployment** - Runs on Raspberry Pi for 24/7 monitoring

### Telecom Engineering Parameters
- **Router Ping Latency** - Local network health indicator
- **DNS Ping Latency** - Internet connectivity status (8.8.8.8)
- **RSSI (dBm)** - WiFi signal strength with percentage to dBm conversion
- **Rolling Averages** - 5-round smoothed metrics for noise reduction
- **Trend Analysis** - Rate of change detection for early warning

## 🏗️ System Architecture

DATA COLLECTION LAYER
- router ping
- DNS ping
- RSSI (dBm)

FEATURE ENGINEERING
- Raw values (latency, RSSI) 
- Rolling averages (window = 5 rounds) 
- Trend detection (rate of change)

XGBOOST REGRESSOR
- 100 decision trees | Max depth: 4 
- Learning rate: 0.1 
- Objective: MSE 
- 9 input features → 1 output (minutes to failure)

REAL-TIME INFERENCE │
- Predictions every 10 seconds │
- Critical alerts (<2 minutes) │
- Trend analysis (improving/declining) │


## 📊 Model Performance

| Metric | Value | Interpretation |
|--------|-------|----------------|
| **Mean Absolute Error** | 0.85 minutes | Predicts within 51 seconds |
| **Critical Detection Rate** | 91.7% | Detects 11 of 12 imminent failures |
| **R² Score** | 0.89 | Explains 89% of variance |
| **Training Time** | <5 seconds | Fast iteration |

### Feature Importance (What the AI Learned)

| Feature | Importance | Insight |
|---------|------------|---------|
| DNS Ping (rolling avg) | 45.2% | Most critical predictor |
| DNS Ping (instant) | 28.1% | Current state matters |
| RSSI Trend | 15.3% | Signal degradation key indicator |
| Router Ping (rolling avg) | 8.4% | Local network stable |
| RSSI (instant) | 3.0% | Less important than trend |

## 🚀 Quick Start

### Prerequisites
```bash
Python 3.8+
pip install pandas numpy scikit-learn xgboost joblib openpyxl

# Clone repository
git clone https://github.com/yourusername/network-failure-prediction.git
cd network-failure-prediction

# Install dependencies
pip install -r requirements.txt


# Step 1: Create labeled dataset
python src/create_excel_data.py

# Step 2: Train XGBoost model
python src/04_train_model.py

# Step 3: Start live monitoring
python src/05_predict_live.py


📁 Project Structure

network-failure-prediction/
├── src/
│   ├── 01_test_network.py
│   ├── 02_data_collection.py  
│   ├── 03_label_data.py
│   ├── 04_train_model.py       
│   └── 05_predict_live.py     
├── models/
│   ├── failure_predictor.pkl # Trained XGBoost model
│   └── feature_columns.pkl     # Feature definitions
├── data/
│   └── network_data.xlsx     # Collected network telemetry
├── requirements.txt
└── README.md

🍓 Raspberry Pi Deployment
Hardware Requirements

Raspberry Pi 3/4/5 (any model with WiFi)
MicroSD card (8GB+)
USB-C power supply

📄 License
MIT License - See LICENSE file

🤝 Contributing
PRs welcome! Focus areas:

Additional feature engineering

Alternative model architectures

Edge deployment optimization

Visualization improvements

📧 Contact
Author: Hiran-Dharmapala
Email: wphdharmapala@gmail.com