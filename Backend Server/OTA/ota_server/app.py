from flask import Flask, request, jsonify, send_file, render_template, session, redirect, url_for
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_cors import CORS
import os
import logging
import yaml
import json
import hashlib
from datetime import datetime
from werkzeug.utils import secure_filename
from logging.handlers import RotatingFileHandler
import shutil
from typing import Dict, Any, Optional
from functools import wraps
import threading
import time
from database import register_device, get_device, update_device_status, get_all_devices, set_force_update, set_force_restart

# Load configuration
def load_config() -> Dict[str, Any]:
    config_path = os.path.join(os.path.dirname(__file__), 'config', 'config.yaml')
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)

config = load_config()

# Configure logging
def setup_logging():
    log_dir = os.path.join(os.path.dirname(__file__), 'logs')
    os.makedirs(log_dir, exist_ok=True)
    
    log_file = os.path.join(log_dir, config['logging']['file'])
    handler = RotatingFileHandler(
        log_file,
        maxBytes=config['logging']['max_size_mb'] * 1024 * 1024,
        backupCount=config['logging']['backup_count']
    )
    
    formatter = logging.Formatter(config['logging']['format'])
    handler.setFormatter(formatter)
    
    logger = logging.getLogger(__name__)
    logger.setLevel(config['logging']['level'])
    logger.addHandler(handler)
    
    return logger

logger = setup_logging()

# Firmware management
class FirmwareManager:
    def __init__(self):
        self.firmware_folder = os.path.join(os.path.dirname(__file__), config['firmware']['folder'])
        self.backup_folder = os.path.join(self.firmware_folder, 'backup')
        self.temp_folder = os.path.join(self.firmware_folder, 'temp')
        os.makedirs(self.firmware_folder, exist_ok=True)
        os.makedirs(self.backup_folder, exist_ok=True)
        os.makedirs(self.temp_folder, exist_ok=True)
    
    def validate_firmware(self, file_path: str) -> tuple[bool, str]:
        """Validate firmware file"""
        try:
            # Check file size
            size = os.path.getsize(file_path)
            if size == 0:
                return False, "Firmware file is empty"
            if size > config['firmware']['max_size_mb'] * 1024 * 1024:
                return False, f"Firmware file too large (max {config['firmware']['max_size_mb']}MB)"
            
            # Check file header (basic validation)
            with open(file_path, 'rb') as f:
                header = f.read(4)
                if not header.startswith(b'\xE9'):  # ESP32 firmware magic number
                    return False, "Invalid firmware file format"
            
            return True, "Valid firmware file"
        except Exception as e:
            return False, f"Error validating firmware: {str(e)}"
    
    def get_latest_firmware(self) -> Optional[str]:
        firmware_files = [f for f in os.listdir(self.firmware_folder) 
                         if f.endswith('.bin') and not f.startswith('.')]
        if not firmware_files:
            return None
        return max(firmware_files, 
                  key=lambda x: os.path.getctime(os.path.join(self.firmware_folder, x)))
    
    def calculate_hash(self, file_path: str) -> str:
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    
    def backup_firmware(self, filename: str):
        if not config['firmware']['backup_enabled']:
            return
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_name = f"{os.path.splitext(filename)[0]}_{timestamp}.bin"
        shutil.copy2(
            os.path.join(self.firmware_folder, filename),
            os.path.join(self.backup_folder, backup_name)
        )
        logger.info(f"Created backup: {backup_name}")

    def cleanup_temp_files(self):
        """Clean up temporary files older than 1 hour"""
        try:
            current_time = time.time()
            for filename in os.listdir(self.temp_folder):
                file_path = os.path.join(self.temp_folder, filename)
                if os.path.getctime(file_path) < (current_time - 3600):  # 1 hour
                    os.remove(file_path)
                    logger.info(f"Cleaned up temp file: {filename}")
        except Exception as e:
            logger.error(f"Error cleaning up temp files: {str(e)}")

# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'your-secret-key-here')  # Change this in production
CORS(app)

# Initialize firmware manager
firmware_manager = FirmwareManager()

# Setup rate limiting
limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"]
)

# User credentials (in production, use a proper database)
USERS = {
    'admin': 'admin123'  # username: password
}

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def api_key_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        api_key = request.headers.get('X-API-Key')
        if not api_key or api_key != os.getenv('API_KEY'):
            return jsonify({'error': 'Invalid API key'}), 401
        return f(*args, **kwargs)
    return decorated_function

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        if username in USERS and USERS[username] == password:
            session['user'] = username
            return redirect(url_for('index'))
        return render_template('login.html', error='Invalid credentials')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('login'))

@app.route('/')
@login_required
def index():
    """Serve the web interface"""
    return render_template('index.html', username=session['user'], api_key=os.getenv('API_KEY'))

# Start cleanup timer
def cleanup_temp_files_periodically():
    while True:
        firmware_manager.cleanup_temp_files()
        time.sleep(3600)  # Run every hour

threading.Thread(target=cleanup_temp_files_periodically, daemon=True).start()

@app.route('/upload', methods=['POST'])
@api_key_required
@limiter.limit("10/minute")
def upload_firmware():
    """Upload a new firmware file"""
    try:
        if 'firmware' not in request.files:
            return jsonify({'error': 'No firmware file provided'}), 400
        
        file = request.files['firmware']
        if file.filename == '':
            return jsonify({'error': 'No selected file'}), 400
        
        if not file.filename.endswith('.bin'):
            return jsonify({'error': 'Invalid file type. Only .bin files are allowed'}), 400
        
        # Save to temporary file first
        temp_filename = secure_filename(f"temp_{int(time.time())}_{file.filename}")
        temp_path = os.path.join(firmware_manager.temp_folder, temp_filename)
        
        try:
            file.save(temp_path)
            
            # Validate firmware
            is_valid, message = firmware_manager.validate_firmware(temp_path)
            if not is_valid:
                os.remove(temp_path)
                return jsonify({'error': message}), 400
            
            # Check file size
            size = os.path.getsize(temp_path)
            if size > config['firmware']['max_size_mb'] * 1024 * 1024:
                os.remove(temp_path)
                return jsonify({'error': f'File too large (max {config["firmware"]["max_size_mb"]}MB)'}), 400
            
            # Calculate hash
            file_hash = firmware_manager.calculate_hash(temp_path)
            
            # Move to final location
            final_filename = secure_filename(file.filename)
            final_path = os.path.join(firmware_manager.firmware_folder, final_filename)
            
            # Backup existing firmware if it exists
            if os.path.exists(final_path):
                firmware_manager.backup_firmware(final_filename)
            
            # Move the file
            shutil.move(temp_path, final_path)
            
            logger.info(f"New firmware uploaded: {final_filename} (Hash: {file_hash})")
            
            return jsonify({
                'message': 'Firmware uploaded successfully',
                'filename': final_filename,
                'hash': file_hash,
                'size': size,
                'upload_date': datetime.now().isoformat()
            })
            
        except Exception as e:
            # Clean up temp file if it exists
            if os.path.exists(temp_path):
                os.remove(temp_path)
            raise e
            
    except Exception as e:
        logger.error(f"Error uploading firmware: {str(e)}")
        return jsonify({'error': f'Failed to upload firmware: {str(e)}'}), 500

@app.route('/firmware/verify/<filename>', methods=['GET'])
@api_key_required
def verify_firmware(filename):
    """Verify firmware file integrity"""
    try:
        file_path = os.path.join(firmware_manager.firmware_folder, filename)
        if not os.path.exists(file_path):
            return jsonify({'error': 'Firmware file not found'}), 404
        
        is_valid, message = firmware_manager.validate_firmware(file_path)
        if not is_valid:
            return jsonify({'error': message}), 400
        
        file_hash = firmware_manager.calculate_hash(file_path)
        size = os.path.getsize(file_path)
        
        return jsonify({
            'status': 'valid',
            'filename': filename,
            'hash': file_hash,
            'size': size,
            'last_modified': datetime.fromtimestamp(os.path.getmtime(file_path)).isoformat()
        })
    except Exception as e:
        logger.error(f"Error verifying firmware: {str(e)}")
        return jsonify({'error': f'Failed to verify firmware: {str(e)}'}), 500

@app.route('/version', methods=['GET'])
@api_key_required
@limiter.limit("60/minute")
def get_version():
    """Return the current firmware version and metadata"""
    try:
        latest_firmware = firmware_manager.get_latest_firmware()
        if not latest_firmware:
            return jsonify({'error': 'No firmware available'}), 404
        
        firmware_path = os.path.join(firmware_manager.firmware_folder, latest_firmware)
        file_hash = firmware_manager.calculate_hash(firmware_path)
        file_size = os.path.getsize(firmware_path)
        last_modified = datetime.fromtimestamp(os.path.getmtime(firmware_path))
        
        return jsonify({
            'version': latest_firmware,
            'url': '/firmware',
            'hash': file_hash,
            'size': file_size,
            'last_modified': last_modified.isoformat(),
            'build_date': datetime.now().isoformat()
        })
    except Exception as e:
        logger.error(f"Error getting version: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/firmware', methods=['GET'])
@api_key_required
@limiter.limit("30/minute")
def get_firmware():
    """Serve the latest firmware file"""
    try:
        latest_firmware = firmware_manager.get_latest_firmware()
        if not latest_firmware:
            return jsonify({'error': 'No firmware available'}), 404
        
        firmware_path = os.path.join(firmware_manager.firmware_folder, latest_firmware)
        logger.info(f"Firmware download requested: {latest_firmware}")
        
        return send_file(
            firmware_path,
            mimetype='application/octet-stream',
            as_attachment=True,
            download_name=latest_firmware
        )
    except Exception as e:
        logger.error(f"Error serving firmware: {str(e)}")
        return jsonify({'error': 'Failed to serve firmware'}), 500

@app.route('/health', methods=['GET'])
@api_key_required
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'version': '1.0.0'
    })

@app.route('/firmware/history')
@login_required
def firmware_history():
    """Get firmware version history"""
    try:
        firmware_files = []
        # Main firmware folder
        for file in os.listdir(firmware_manager.firmware_folder):
            if file.endswith('.bin'):
                file_path = os.path.join(firmware_manager.firmware_folder, file)
                firmware_files.append({
                    'filename': file,
                    'size': os.path.getsize(file_path),
                    'last_modified': datetime.fromtimestamp(os.path.getmtime(file_path)).isoformat(),
                    'hash': firmware_manager.calculate_hash(file_path)
                })
        # Backup folder
        backup_folder = os.path.join(firmware_manager.firmware_folder, 'backup')
        if os.path.exists(backup_folder):
            for file in os.listdir(backup_folder):
                if file.endswith('.bin'):
                    file_path = os.path.join(backup_folder, file)
                    firmware_files.append({
                        'filename': file,
                        'size': os.path.getsize(file_path),
                        'last_modified': datetime.fromtimestamp(os.path.getmtime(file_path)).isoformat(),
                        'hash': firmware_manager.calculate_hash(file_path)
                    })
        return jsonify(firmware_files)
    except Exception as e:
        logger.error(f"Error getting firmware history: {str(e)}")
        return jsonify({'error': 'Failed to get firmware history'}), 500

@app.route('/firmware/restore/<filename>')
@login_required
def restore_firmware(filename):
    """Restore a firmware version from backup"""
    try:
        backup_path = os.path.join(firmware_manager.firmware_folder, 'backup', filename)
        if not os.path.exists(backup_path):
            return jsonify({'error': 'Backup file not found'}), 404
        
        # Create a new backup of current firmware
        current_firmware = firmware_manager.get_latest_firmware()
        if current_firmware:
            firmware_manager.backup_firmware(current_firmware)
        
        # Restore the backup
        shutil.copy2(backup_path, os.path.join(firmware_manager.firmware_folder, filename))
        return jsonify({'message': 'Firmware restored successfully'})
    except Exception as e:
        logger.error(f"Error restoring firmware: {str(e)}")
        return jsonify({'error': 'Failed to restore firmware'}), 500

@app.route('/firmware/delete/<filename>')
@login_required
def delete_firmware(filename):
    """Delete a firmware version from both main and backup folders"""
    try:
        deleted = False
        # Main firmware folder
        file_path = os.path.join(firmware_manager.firmware_folder, filename)
        if os.path.exists(file_path):
            os.remove(file_path)
            deleted = True
        # Backup folder
        backup_folder = os.path.join(firmware_manager.firmware_folder, 'backup')
        backup_path = os.path.join(backup_folder, filename)
        if os.path.exists(backup_path):
            os.remove(backup_path)
            deleted = True
        if deleted:
            return jsonify({'message': 'Firmware deleted successfully'})
        else:
            return jsonify({'error': 'File not found'}), 404
    except Exception as e:
        logger.error(f"Error deleting firmware: {str(e)}")
        return jsonify({'error': 'Failed to delete firmware'}), 500

@app.route('/stats')
@login_required
def get_stats():
    """Get server statistics"""
    try:
        firmware_folder = firmware_manager.firmware_folder
        backup_folder = os.path.join(firmware_folder, 'backup')
        
        total_size = sum(os.path.getsize(os.path.join(firmware_folder, f)) 
                        for f in os.listdir(firmware_folder) if f.endswith('.bin'))
        backup_size = sum(os.path.getsize(os.path.join(backup_folder, f)) 
                         for f in os.listdir(backup_folder) if f.endswith('.bin'))
        
        return jsonify({
            'total_firmware_size': total_size,
            'backup_size': backup_size,
            'firmware_count': len([f for f in os.listdir(firmware_folder) if f.endswith('.bin')]),
            'backup_count': len([f for f in os.listdir(backup_folder) if f.endswith('.bin')]),
            'last_update': datetime.now().isoformat()
        })
    except Exception as e:
        logger.error(f"Error getting stats: {str(e)}")
        return jsonify({'error': 'Failed to get stats'}), 500

# Device tracking
DEVICE_TIMEOUT = 60  # Consider device offline after 60 seconds of no activity

def check_device_timeouts():
    while True:
        current_time = datetime.now()
        devices = get_all_devices()
        for device in devices:
            if (current_time - device['last_seen']).total_seconds() > DEVICE_TIMEOUT:
                update_device_status(device['device_id'], 'offline')
        time.sleep(10)  # Check every 10 seconds

@app.route('/device/register', methods=['POST'])
@api_key_required
def register_device_endpoint():
    data = request.get_json()
    print("\n=== Device Registration Request ===")
    print("Raw request data:", data)
    print("Headers:", dict(request.headers))
    
    device_id = data.get('device_id')
    ip_address = request.remote_addr
    firmware_version = data.get('firmware_version', 'unknown')
    device_info = data.get('device_info', {})
    
    print(f"\nDevice registration details:")
    print(f"Device ID: {device_id}")
    print(f"IP Address: {ip_address}")
    print(f"Firmware Version: {firmware_version}")
    print(f"Device Info: {json.dumps(device_info, indent=2)}")
    
    if not device_id:
        return jsonify({'error': 'Device ID is required'}), 400
    
    device_data = register_device(device_id, ip_address, firmware_version, device_info)
    return jsonify({'status': 'success', 'device': device_data})

@app.route('/device/heartbeat', methods=['POST'])
@api_key_required
def device_heartbeat():
    data = request.get_json()
    print("\n=== Device Heartbeat Request ===")
    print("Raw request data:", data)
    print("Headers:", dict(request.headers))
    
    device_id = data.get('device_id')
    firmware_version = data.get('firmware_version', 'unknown')
    device_info = data.get('device_info', {})
    
    print(f"\nDevice heartbeat details:")
    print(f"Device ID: {device_id}")
    print(f"Firmware Version: {firmware_version}")
    print(f"Device Info: {json.dumps(device_info, indent=2)}")
    
    if not device_id:
        return jsonify({'error': 'Device ID is required'}), 400
    
    # Ensure device_info is a dictionary
    if not isinstance(device_info, dict):
        device_info = {}
    
    # Add default values for missing fields
    device_info.setdefault('temperature', 0.0)
    device_info.setdefault('humidity', 0.0)
    device_info.setdefault('free_heap', 0)
    device_info.setdefault('uptime', 0)
    device_info.setdefault('mac_address', 'Unknown')
    
    # Get current device status
    device = get_device(device_id)
    if not device:
        return jsonify({'error': 'Device not registered'}), 404
    
    # Update device status
    update_device_status(device_id, 'online')
    
    response = {'status': 'success'}
    
    # Check if force update is requested
    if device.get('force_update'):
        set_force_update(device_id, False)
        response['force_update'] = True
        response['update_url'] = '/firmware'
    
    # Check if restart is requested
    if device.get('force_restart'):
        set_force_restart(device_id, False)
        response['force_restart'] = True
    
    print(f"Sending response: {json.dumps(response, indent=2)}")
    return jsonify(response)

@app.route('/device/force-update/<device_id>', methods=['POST'])
@login_required
def force_device_update(device_id):
    if device_id not in devices:
        return jsonify({'error': 'Device not found'}), 404
    
    devices[device_id]['force_update'] = True
    return jsonify({'status': 'success', 'message': 'Force update requested'})

@app.route('/device/restart/<device_id>', methods=['POST'])
@login_required
def restart_device(device_id):
    print(f"\n=== Restart Device Request ===")
    print(f"Device ID: {device_id}")
    
    if device_id not in devices:
        print(f"Device {device_id} not found")
        return jsonify({'error': 'Device not found'}), 404
    
    print(f"Setting force_restart flag for device {device_id}")
    devices[device_id]['force_restart'] = True
    return jsonify({'status': 'success', 'message': 'Restart requested'})

@app.route('/devices', methods=['GET'])
@api_key_required
def get_devices_endpoint():
    print("\n=== Get Devices Request ===")
    devices = get_all_devices()
    print("Current devices in database:")
    for device in devices:
        print(f"\nDevice {device['device_id']}:")
        print(f"  Status: {device['status']}")
        print(f"  IP: {device['ip_address']}")
        print(f"  Version: {device['firmware_version']}")
        print(f"  Last Seen: {device['last_seen']}")
        print(f"  Device Info: {json.dumps(device.get('device_info', {}), indent=2)}")
    
    return jsonify({'devices': devices})

@app.route('/api/firmware/list', methods=['GET'])
@api_key_required
def api_firmware_list():
    """Return a list of all available firmware files (.bin) with metadata."""
    try:
        firmware_files = []
        for file in os.listdir(firmware_manager.firmware_folder):
            if file.endswith('.bin'):
                file_path = os.path.join(firmware_manager.firmware_folder, file)
                firmware_files.append({
                    'filename': file,
                    'size': os.path.getsize(file_path),
                    'last_modified': datetime.fromtimestamp(os.path.getmtime(file_path)).isoformat()
                })
        return jsonify({'firmware': firmware_files})
    except Exception as e:
        logger.error(f"Error listing firmware: {str(e)}")
        return jsonify({'error': 'Failed to list firmware'}), 500

if __name__ == '__main__':
    logger.info("Starting OTA server...")
    app.run(
        host=config['server']['host'],
        port=config['server']['port'],
        debug=config['server']['debug']
    ) 