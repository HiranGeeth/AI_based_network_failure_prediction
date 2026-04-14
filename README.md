# 🔮 AI-Powered Predictive Network Failure Detection

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![XGBoost](https://img.shields.io/badge/XGBoost-1.7.0-orange.svg)](https://xgboost.ai/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![ML Pipeline](https://img.shields.io/badge/ML-Pipeline-green.svg)](https://github.com/)

## 🎯 Overview

An **end-to-end machine learning system** that predicts network node failures **before they occur** using real-time telemetry data. Achieves **90.3% accuracy** in detecting critical failures with **<1 minute mean absolute error**.

### Key Capabilities
- ⚡ **Real-time inference**        - Predicts failure within 2-10 minute windows
- 🧠 **Gradient boosting**          - XGBoost regression model
- 📊 **Multi-dimensional features** - Latency, packet loss, trends, rolling statistics
- 🚨 **Automated alerting**         - Critical warning system for imminent failures
- 🔄 **Continuous learning**        - Can be retrained with new data

## 🏗️ System Architecture


        DATA INGESTION LAYER 
        Ping Router (192.168.1.1) + DNS (8.8.8.8) every 2 seconds 


        FEATURE ENGINEERING 
        • Rolling windows (5, 10, 20 samples) 
        • Rate of change (1st derivative) 
        • Cross-correlation signals 


        ML MODEL (XGBoost) 
        • 100 decision trees | Max depth: 4 
        • Learning rate: 0.1 | Objective: MSE 


        INFERENCE ENGINE 
        • Real-time prediction every 10 seconds 
        • Confidence scoring | Trend analysis 


## 📊 Model Performance

    | Metric                            | Value         | Industry Benchmark       |
    |-----------------------------------|---------------|--------------------------|
    | **Mean Absolute Error**           | 0.97 minutes  | < 2 minutes       ✅    |
    | **Critical Failure Detection**    | 90.3%         | > 80%             ✅    |
    | **Inference Latency**             | < 100ms       | Real-time         ✅    |
    | **Training Time**                 | 11 seconds    | Fast iteration    ✅    |

### Feature Importance (What the AI Learned)

    DNS Latency (rolling avg)   = 54.2%
    DNS Latency Trend           = 10.0%
    Average Latency             = 9.5%
    DNS Latency (instant)       = 9.1%
    Router Latency(rolling avg) = 6.6%


## 🔬 Technical Deep Dive

### Data Collection Pipeline
- **Sampling frequency**: 0.5 Hz (every 2 seconds)
- **Features extracted**: 11 dimensions
- **Training dataset**: 155 rounds, 310 measurements
- **Failure modes captured**: Gradual degradation, sudden outage, interference

### Feature Engineering Strategy
features = {
    'instant_metrics': [latency, loss, rssi],
    'temporal_features': [rolling_mean_5, rolling_mean_10],
    'derived_features': [latency_trend, loss_trend],
    'cross_domain': [avg_latency, ratio_router_dns]
}


## 🔬 Model Hyperparameters 

XGBRegressor(
    n_estimators=100,      # Ensemble size
    max_depth=4,           # Tree complexity (prevents overfitting)
    learning_rate=0.1,     # Step size shrinkage
    objective='reg:squarederror',  # MSE optimization
    random_state=42        # Reproducibility
)

### 🚧 Limitations

Requires labeled failure data for training
WiFi RSSI not available on all platforms

### 📄 License
MIT - See LICENSE file

### 🤝 Contributing
PRs welcome! Especially for:

Additional feature engineering techniques
Alternative model architectures
Edge deployment optimizations

