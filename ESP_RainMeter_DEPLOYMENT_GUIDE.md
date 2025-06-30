# ESP RainMeter Deployment Guide

## Table of Contents
1. [Project Overview](#project-overview)
2. [Prerequisites](#prerequisites)
3. [Backend (FastAPI/MQTT) Deployment](#backend-fastapimqtt-deployment)
4. [OTA Server Deployment](#ota-server-deployment)
5. [Android App Deployment](#android-app-deployment)
6. [ESP Firmware Deployment](#esp-firmware-deployment)
7. [Troubleshooting & Best Practices](#troubleshooting--best-practices)

---

## Project Overview
ESP RainMeter is an IoT platform for smart device management, featuring:
- Native Android app (Jetpack Compose)
- FastAPI backend with MQTT and MongoDB
- OTA (Over-the-Air) firmware update server
- ESP32 firmware for smart devices

---

## Prerequisites
- **OS:** Ubuntu 20.04+/macOS/Windows 10+
- **Python:** 3.11.x (not 3.13+)
- **Node.js:** 16+ (for MQTT/MongoDB controller, if used)
- **Java/Kotlin:** JDK 17+ (for Android app)
- **Android Studio:** Latest stable
- **MongoDB:** Local or cloud instance
- **ESP32 Toolchain:** [ESP-IDF](https://docs.espressif.com/projects/esp-idf/en/latest/esp32/get-started/)
- **Git:** Latest

---

## Backend (FastAPI/MQTT) Deployment

### 1. Clone the Repository
```sh
git clone <repo-url>
cd 'fastapi_mqtt_backend 2'
```

### 2. Create and Activate Python 3.11 Virtual Environment
```sh
python3.11 -m venv venv311
source venv311/bin/activate
```

### 3. Install Dependencies
```sh
pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Configure Environment Variables
- Copy `.env.example` to `.env` and set MongoDB URI, MQTT broker, etc.

### 5. Run the Server
```sh
uvicorn main:app --reload
```
- Access API docs at: `http://localhost:8000/docs`

---

## OTA Server Deployment

### 1. Navigate to OTA Server Directory
```sh
cd ESPR/OTA/ota_server
```

### 2. Create and Activate Virtual Environment
```sh
python3.11 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies
```sh
pip install -r requirements.txt
```

### 4. Run the OTA Server
```sh
python3 app.py
```
- Access OTA dashboard at: `http://localhost:5000`

---

## Android App Deployment

### 1. Open in Android Studio
- Open `ESP_RAINMETER_APP` directory.

### 2. Configure Backend URL
- Update `ServerConfig.kt` or `UrlHolder.kt` with your backend/OTA server URLs.

### 3. Build & Run
- Connect Android device or use emulator.
- Click **Run** in Android Studio.

### 4. Release APK
- Build > Generate Signed Bundle/APK > APK
- Follow prompts to sign and export APK.

---

## ESP Firmware Deployment

### 1. Install ESP32 Toolchain
- Follow [ESP-IDF setup guide](https://docs.espressif.com/projects/esp-idf/en/latest/esp32/get-started/).

### 2. Flash Firmware
```sh
cd ESPR/firmware
esptool.py --chip esp32 --port <PORT> write_flash -z 0x1000 <firmware.bin>
```
- Replace `<PORT>` and `<firmware.bin>` as needed.

### 3. OTA Updates
- Use the OTA server dashboard to upload new firmware and trigger updates.

---

## Troubleshooting & Best Practices
- **Python Version:** Use 3.11.x, not 3.13+ (Pydantic incompatibility).
- **MongoDB:** Ensure MongoDB is running and accessible.
- **CORS:** Configure CORS in FastAPI for mobile app access.
- **Ports:** Ensure ports 8000 (API), 5000 (OTA), and MQTT broker are open.
- **Logs:** Check `backend.log`, `ota_server.log` for errors.
- **Android Build:** Clean/rebuild if Compose or Gradle errors occur.
- **Firmware:** Use correct board and port for ESP32 flashing.

---

## Contact & Support
For issues, open an issue on GitHub or contact the project maintainers. 