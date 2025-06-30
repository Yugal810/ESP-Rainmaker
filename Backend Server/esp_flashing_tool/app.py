from fastapi import FastAPI, Request, Form, UploadFile, File, BackgroundTasks
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
import serial.tools.list_ports
import os
import qrcode
from io import BytesIO
import subprocess
import uuid
import requests
import tempfile
import glob
import threading
import time
import traceback
import json

app = FastAPI()
static_dir = os.path.join(os.path.dirname(__file__), "static")
templates = Jinja2Templates(directory=os.path.join(os.path.dirname(__file__), "templates"))

# Mount static directory for JS/CSS if needed
app.mount("/static", StaticFiles(directory=static_dir), name="static")

FIRMWARE_DIR = "firmware"
DEVICE_TYPES = ["Fan", "LED-Light", "Switch", "Temperature Sensor"]

QR_TEMP_DIR = os.path.join(os.path.dirname(__file__), "qr_temp")
os.makedirs(QR_TEMP_DIR, exist_ok=True)

# Clean up old QR files every hour
def cleanup_qr_files():
    while True:
        now = time.time()
        for f in glob.glob(os.path.join(QR_TEMP_DIR, "*.png")):
            if os.path.getmtime(f) < now - 3600:  # older than 1 hour
                try:
                    os.remove(f)
                except Exception:
                    pass
        time.sleep(3600)
threading.Thread(target=cleanup_qr_files, daemon=True).start()

OTA_SERVER_URL = os.getenv("OTA_SERVER_URL", "http://127.0.0.1:8081")
OTA_API_KEY = os.getenv("OTA_API_KEY", "f739475b2212417ece020fdb02c84884e443a93052edf41f2822e798d41199a5")

def get_firmware_path(device_type):
    # Map device type to firmware file
    fname = device_type.replace(" ", "_") + ".bin"
    # Try both with and without underscore for compatibility
    for candidate in [device_type + ".bin", fname]:
        path = os.path.join(FIRMWARE_DIR, candidate)
        if os.path.exists(path):
            return path
    return None

@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request, "device_types": DEVICE_TYPES})

@app.get("/com_ports")
def list_com_ports():
    ports = [port.device for port in serial.tools.list_ports.comports()]
    return {"ports": ports}

@app.get("/firmware_list")
def firmware_list():
    try:
        resp = requests.get(f"{OTA_SERVER_URL}/api/firmware/list", headers={"X-API-Key": OTA_API_KEY}, timeout=10)
        if resp.status_code == 200:
            return resp.json()
        return {"firmware": []}
    except Exception as e:
        return {"firmware": [], "error": str(e)}

@app.post("/flash")
def flash_firmware(background_tasks: BackgroundTasks, com_port: str = Form(...), firmware_filename: str = Form(...), chip_type: str = Form(...)):
    try:
        fw_url = f"{OTA_SERVER_URL}/firmware"
        fw_list_resp = requests.get(f"{OTA_SERVER_URL}/api/firmware/list", headers={"X-API-Key": OTA_API_KEY}, timeout=10)
        fw_list = fw_list_resp.json().get("firmware", [])
        fw_file = next((f for f in fw_list if f["filename"] == firmware_filename), None)
        if not fw_file:
            return JSONResponse({"success": False, "error": f"Firmware {firmware_filename} not found on OTA server."})
        fw_download_url = f"{OTA_SERVER_URL}/firmware?filename={firmware_filename}"
        fw_resp = requests.get(fw_download_url, headers={"X-API-Key": OTA_API_KEY}, timeout=30)
        if fw_resp.status_code != 200:
            return JSONResponse({"success": False, "error": f"Failed to download firmware: {fw_resp.text}"})
        # Save firmware to a temp file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.bin') as temp_fw:
            temp_fw.write(fw_resp.content)
            fw_path = temp_fw.name
        # Actually flash using esptool
        cmd = [
            "esptool.py",
            "--chip", chip_type,
            "--port", com_port,
            "--baud", "460800",
            "write_flash", "-z", "0x1000", fw_path
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            # QR code logic as before
            session_id = str(uuid.uuid4())
            base_name = os.path.splitext(firmware_filename)[0]
            parts = base_name.split('_')
            if len(parts) >= 3:
                device_type = parts[0]
                device_id = f"{parts[0]}_{parts[1]}"
                relay = parts[2]
            elif len(parts) == 2:
                device_type = parts[0]
                device_id = base_name
                relay = 'relay1'
            else:
                device_type = 'unknown'
                device_id = base_name
                relay = 'relay1'
            qr_payload = {
                "device_id": device_id,
                "device_type": device_type,
                "relay": relay
            }
            qr_data = "ESP_DEVICE:" + json.dumps(qr_payload)
            try:
                qr_img = qrcode.make(qr_data)
                qr_path = os.path.join(QR_TEMP_DIR, f"{session_id}.png")
                qr_img.save(qr_path, format="PNG")
            except Exception as e:
                return JSONResponse({"success": True, "qr_url": None, "warning": f"Flashed, but failed to save QR code: {str(e)}"})
            qr_url = f"/qr/{session_id}"
            return JSONResponse({"success": True, "qr_url": qr_url})
        else:
            return JSONResponse({"success": False, "error": result.stderr})
    except Exception as e:
        return JSONResponse({"success": False, "error": str(e)})

@app.get("/qr/{session_id}")
def get_qr(session_id: str):
    qr_path = os.path.join(QR_TEMP_DIR, f"{session_id}.png")
    print(f"QR requested for session_id: {session_id}, path: {qr_path}")
    if not os.path.exists(qr_path):
        print("QR code file not found!")
        return JSONResponse({"error": "QR code not found"}, status_code=404)
    print("QR code file found and being served.")
    return FileResponse(qr_path, media_type="image/png")

# Placeholder for flash and QR code routes 