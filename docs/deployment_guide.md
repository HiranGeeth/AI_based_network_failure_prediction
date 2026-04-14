# Deployment Guide: Network Failure Prediction System

## For PC (Windows/Linux/Mac) - Quick Start

### Prerequisites
- Python 3.8 or higher
- Git (optional)
- Administrative access (for ping permissions)

---

## One-Click Setup

### 1. Clone or Download

download ZIP from GitHub and extract.

### 2. Create Virtual Environment

**Windows:**
```bash
python -m venv venv
venv\Scripts\activate
```

**Linux/Mac:**
```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Router IP

Edit `config.yaml` (create if doesn't exist):

```yaml
network:
  router_ip: "192.168.1.1"  # Change to YOUR router IP
  dns_ip: "8.8.8.8"
  check_interval: 10  # seconds between predictions
```

Find your router IP:
- **Windows**: `ipconfig` → Default Gateway
- **Linux/Mac**: `ip route | grep default`

---

## Run the System

### Option A: Full Pipeline (Train + Predict)

```bash
# Step 1: Collect training data (20 minutes)
python src/data_collection.py

# Step 2: Label the data
python src/label_data.py

# Step 3: Train AI model
python src/train_model.py

# Step 4: Start live monitoring
python src/predict_live.py
```

### Option B: Use Pre-trained Model (Skip Training)

Download pre-trained model from releases, then:

```bash
# Place model in models/ folder
python src/live_inference.py
```

---

## File Structure

```
network-failure-prediction/
├── src/
│   ├── data_collection.py
│   ├── data_labeling.py
│   ├── model_training.py
│   └── live_inference.py
├── models/
│   ├── failure_predictor.pkl
│   └── feature_columns.pkl
├── data/
│   ├── raw/          # Collected data
│   └── processed/    # Labeled data
├── requirements.txt
├── config.yaml
└── README.md
```

---

## Quick Test

After running `live_inference.py`, you should see:

```
[OK] Model loaded successfully
[STARTING] Real-time monitor...
[ROUND 1] HEALTHY | Failure in 10+ minutes
[ROUND 2] HEALTHY | Failure in 10+ minutes
```

**To test predictions:**
1. Walk to farthest room from router
2. Watch prediction drop: 10min → 5min → 2min → CRITICAL
3. Move back → prediction recovers

---

## Common Issues & Fixes

| Issue | Solution |
|-------|----------|
| `Module not found` | Run `pip install -r requirements.txt` |
| `Permission denied` | Run terminal as Administrator (Windows) or `sudo` (Linux) |
| `Router not found` | Check IP in `config.yaml` |
| `Model not found` | Run `python src/model_training.py` first |
| `No ping response` | Disable firewall temporarily |

---

## Running as Background Service

### Windows (Task Scheduler)

```powershell
# Create scheduled task
schtasks /create /tn "NetworkMonitor" /tr "C:\path\to\venv\Scripts\python.exe C:\path\to\live_inference.py" /sc minute /mo 1
```

### Linux (Cron)

```bash
# Add to crontab (runs every minute)
crontab -e
* * * * * /path/to/venv/bin/python /path/to/live_inference.py
```

---

## Stopping the System

Press `Ctrl+C` in the terminal where `live_inference.py` is running.

---

## Updating the Model

```bash
# Collect new data (more failure examples)
python src/data_collection.py --duration 30

# Retrain with new data
python src/model_training.py

# Model automatically updates
```

---

## Performance Expectations

| Metric | Value |
|--------|-------|
| CPU Usage | <5% |
| RAM Usage | ~200MB |
| Network Usage | ~10KB/minute |
| Prediction Latency | <100ms |

---

## Uninstall

```bash
# Delete virtual environment
deactivate  # if activated
rm -rf venv/

# Delete project folder
cd ..
rm -rf network-failure-prediction/
```

---

## Support

- **Issues**: GitHub Issues tab
- **Documentation**: `/docs` folder
- **Model accuracy**: 90% critical failure detection

---

## Next Steps After Deployment

1. **Add email alerts** - Modify `live_inference.py` to send notifications
2. **Create dashboard** - Use Streamlit for web interface
3. **Deploy to Raspberry Pi** - 24/7 monitoring for $35
4. **Collect more data** - Improve accuracy over time

---

**Version**: 1.0.0 | **Last Updated**: April 2026

---

## Quick Reference Card

```bash
# Most common commands
python src/data_collection.py   # Collect data (20 min)
python src/model_training.py    # Train model (11 sec)
python src/live_inference.py    # Start monitoring

# Stop monitoring
Ctrl+C
```

---

**That's it! Your AI-powered network monitor is running.** 🚀