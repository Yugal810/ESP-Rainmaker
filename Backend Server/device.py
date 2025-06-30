from fastapi import APIRouter
from models import DeviceControl
from mqtt_client import publish

router = APIRouter()

@router.post("/device/control")
def control_device(data: DeviceControl):
    topic = f"device/{data.device_id}/{data.relay}/set"
    publish(topic, data.action)
    return {"msg": "Command sent"}