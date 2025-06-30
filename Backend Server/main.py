from fastapi import FastAPI
from routes import auth, device, ota
from routes import room  # Import the new room router
import mqtt_client # ensures MQTT starts
import socket
import qrcode
from qrcode.constants import ERROR_CORRECT_L
import io
from PIL import Image
from scheduler import start_scheduler

app = FastAPI()

def get_local_ip():
    try:
        # Create a socket to get the local IP
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"

app.include_router(auth.router)
app.include_router(device.router)
app.include_router(ota.router)
app.include_router(room.router)  # Register the room router

# Start the background scheduler for device schedules
start_scheduler()