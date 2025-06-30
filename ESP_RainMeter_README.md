# ESP RainMeter Android App

## Overview
ESP RainMeter is a smart IoT device management app designed for seamless control and scheduling of ESP-based devices (lights, fans, switches, sensors, etc.) over WiFi. Built for hackathons, it features robust device provisioning, real-time control, and OTA firmware updates, all with a modern, user-friendly interface.

## Features
- **Device Discovery & Registration:** Scan QR codes to quickly add new ESP devices.
- **Real-Time Control:** Toggle devices (lights, fans, switches) instantly from your phone.
- **Scheduling:** Create, edit, and manage schedules for automated device actions.
- **Room & Scene Management:** Organize devices by room and create custom scenes.
- **OTA Updates:** Push firmware updates to devices directly from the app.
- **Secure Authentication:** User login and device access control.
- **Modern UI:** Built with Jetpack Compose and Material 3 for a smooth, responsive experience.

## Architecture
- **Kotlin + Jetpack Compose:** Modern, declarative UI.
- **MVVM Pattern:** Clean separation of UI, business logic, and data.
- **Hilt DI:** Dependency injection for scalable code.
- **Navigation Component:** Type-safe, modular navigation.
- **Retrofit + Coroutines:** Fast, async API communication.
- **Backend:** FastAPI/MQTT server for device management and OTA (see `/ESPR` and `/fastapi_mqtt_backend`).

## Getting Started

### Prerequisites
- Android Studio Hedgehog or newer
- Android SDK 34+
- Kotlin 1.9+
- (Optional) ESP devices flashed with compatible firmware

### Setup
1. **Clone the repository:**
   ```sh
   git clone <your-repo-url>
   ```
2. **Open in Android Studio:**
   - File > Open > Select `ESP_RAINMETER_APP` directory
3. **Sync Gradle:**
   - Let Gradle sync and download dependencies
4. **Configure Backend:**
   - Ensure the FastAPI/MQTT backend is running (see `/ESPR` or `/fastapi_mqtt_backend`)
   - Update `ServerConfig.kt` or `UrlHolder.kt` with your backend URL if needed
5. **Run the App:**
   - Select a device/emulator and click Run

### QR Provisioning
- Use the in-app QR scanner to add new ESP devices. Each device should display a QR code with its unique credentials.

### OTA Updates
- Navigate to the OTA section to push firmware updates to registered devices.

