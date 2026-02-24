
# Navigation App - Laptop Server

This is the laptop server component for the Android Navigation App. It receives real-time GPS data and navigation instructions from your phone and speaks them aloud.

## 📋 Prerequisites

- **Python 3.8 or higher** installed on your laptop
- **Android Phone** with USB Debugging enabled
- **USB Cable** for connecting phone to laptop
- **Android Studio** (for the phone app) or the pre-built APK

## 🚀 Quick Setup Guide

### Step 1: Install Python Requirements

Open **PowerShell** or **Command Prompt** and run:

```bash
# Navigate to your project folder
cd path\to\your\code

# Create virtual environment
python -m venv venv

# Activate virtual environment (Windows)
venv\Scripts\activate

# For Mac/Linux:
# source venv/bin/activate

# Install required packages
pip install websockets pyttsx3 requests
```

### Step 2: Setup Phone for USB Debugging

1. **Enable Developer Options:**
   - Go to `Settings → About Phone`
   - Tap `Build Number` 7 times

2. **Enable USB Debugging:**
   - Go to `Settings → Developer Options`
   - Enable `USB Debugging`

3. **Connect Phone:**
   - Plug in your phone via USB
   - Set USB mode to `File Transfer`
   - Accept the `Allow USB debugging?` prompt
   - Check `Always allow from this computer`

### Step 3: Verify ADB Connection

```bash
# Check if phone is detected
adb devices
```

Expected output:
```
List of devices attached
XXXXXXXXXXXXXX    device
```

### Step 4: Run the Server

```bash
# Make sure you're in the project folder
cd path\to\your\code

# Activate virtual environment (if not already)
venv\Scripts\activate

# Run the server
python server.py
```

### Step 5: Run the Android App

1. Open the Android app on your phone
2. The app should automatically connect
3. You'll see `✅ Connected to laptop` on your phone
4. The server will show `✨ CONNECTION SUCCESS!`

## 📁 Project Files

```
D:\FYp\code\
├── server.py           # Main server script
├── requirements.txt    # Python dependencies
├── README.md          # This file
└── venv/              # Virtual environment (created after setup)
```

## 🔧 Troubleshooting

### "No device found" or "unauthorized"

```bash
# Kill ADB server
adb kill-server

# Restart ADB
adb start-server

# Check devices again
adb devices
```

### Connection keeps dropping

The server has built-in ping/pong (20 second intervals) to maintain connection.

### Nothing is being spoken

Check:
- Your laptop speakers are on
- Volume is up
- No other app is blocking audio

### Port 8765 already in use

```bash
# Find process using port 8765 (Windows)
netstat -ano | findstr :8765

# Kill the process using its PID
taskkill /PID [PID] /F

## 📊 Server Output Example

```
✅ ADB Reverse: Port 8765 forwarded successfully

==================================================
🚀 SERVER RUNNING
📡 Listening on: ws://127.0.0.1:8765
📱 Phone connected and ready
==================================================

✨ CONNECTION SUCCESS! Phone is now talking to Laptop.
📍 32.424693, 74.461702 | Continue straight | 127m | Nav: True
🎯 DESTINATION: Motra, PB, Pakistan
🔊 SPEAKING: Heading to Motra, PB, Pakistan
🗺️ ROUTE: 7.8 kilometers
🔊 SPEAKING: Route loaded. Total distance 7.8 kilometers
🚗 NAVIGATION STARTED
🔊 SPEAKING: Navigation started
🗣️ Continue straight
🔊 SPEAKING: Continue straight
📏 116m
🔊 SPEAKING: In 116 meters
```
