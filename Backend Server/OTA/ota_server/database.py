from pymongo import MongoClient
import os
from dotenv import load_dotenv
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

load_dotenv()
mongo_url = os.getenv("MONGO_URL")
logger.debug(f"Connecting to MongoDB at: {mongo_url}")

try:
    client = MongoClient(mongo_url)
    # Test the connection
    client.admin.command('ping')
    logger.debug("Successfully connected to MongoDB")
except Exception as e:
    logger.error(f"Failed to connect to MongoDB: {str(e)}")
    raise

db = client["smart_home"]

def register_device(device_id, ip_address, firmware_version, device_info):
    """Register or update a device in the database"""
    try:
        device_data = {
            'device_id': device_id,
            'ip_address': ip_address,
            'firmware_version': firmware_version,
            'status': 'online',
            'device_info': device_info,
            'last_seen': datetime.now(),
            'last_update_attempt': None,
            'last_update_status': None,
            'force_update': False,
            'force_restart': False
        }
        
        logger.debug(f"Registering device: {device_id}")
        # Update or insert the device
        result = db.devices.update_one(
            {'device_id': device_id},
            {'$set': device_data},
            upsert=True
        )
        logger.debug(f"Database operation result: {result.raw_result}")
        return device_data
    except Exception as e:
        logger.error(f"Error registering device: {str(e)}")
        raise

def get_device(device_id):
    """Get device information from the database"""
    try:
        logger.debug(f"Getting device: {device_id}")
        device = db.devices.find_one({'device_id': device_id})
        logger.debug(f"Found device: {device}")
        return device
    except Exception as e:
        logger.error(f"Error getting device: {str(e)}")
        raise

def update_device_status(device_id, status):
    """Update device status"""
    try:
        logger.debug(f"Updating device status: {device_id} -> {status}")
        result = db.devices.update_one(
            {'device_id': device_id},
            {'$set': {'status': status, 'last_seen': datetime.now()}}
        )
        logger.debug(f"Update result: {result.raw_result}")
    except Exception as e:
        logger.error(f"Error updating device status: {str(e)}")
        raise

def get_all_devices():
    """Get all registered devices"""
    try:
        logger.debug("Getting all devices")
        devices = list(db.devices.find({}, {'_id': 0}))
        logger.debug(f"Found {len(devices)} devices")
        return devices
    except Exception as e:
        logger.error(f"Error getting all devices: {str(e)}")
        raise

def set_force_update(device_id, force_update=True):
    """Set force update flag for a device"""
    try:
        logger.debug(f"Setting force update for device: {device_id}")
        result = db.devices.update_one(
            {'device_id': device_id},
            {'$set': {'force_update': force_update}}
        )
        logger.debug(f"Update result: {result.raw_result}")
    except Exception as e:
        logger.error(f"Error setting force update: {str(e)}")
        raise

def set_force_restart(device_id, force_restart=True):
    """Set force restart flag for a device"""
    try:
        logger.debug(f"Setting force restart for device: {device_id}")
        result = db.devices.update_one(
            {'device_id': device_id},
            {'$set': {'force_restart': force_restart}}
        )
        logger.debug(f"Update result: {result.raw_result}")
    except Exception as e:
        logger.error(f"Error setting force restart: {str(e)}")
        raise 