from fastapi import APIRouter, HTTPException, Query, Depends
from models import DeviceControl, DeviceRegister, DeviceSchedule
from mqtt_client import publish
from database import db
from datetime import datetime
from routes.auth import get_current_user
from bson import ObjectId
from uuid import uuid4

router = APIRouter()

@router.post("/device/control")
def control_device(data: DeviceControl, current_user: str = Depends(get_current_user)):
    # Publish to MQTT
    topic = f"device/{data.device_id}/{data.relay}/set"
    publish(topic, data.action)
    
    # Update database
    try:
        # Update or insert device state
        db.device_states.update_one(
            {"device_id": data.device_id, "relay": data.relay},
            {
                "$set": {
                    "state": data.action,
                    "last_updated": datetime.utcnow()
                }
            },
            upsert=True
        )
        
        # Log the command
        db.command_logs.insert_one({
            "device_id": data.device_id,
            "relay": data.relay,
            "action": data.action,
            "timestamp": datetime.utcnow(),
            "source": "app"
        })
        
        return {"msg": "Command sent and database updated"}
    except Exception as e:
        return {"msg": f"Command sent but database update failed: {str(e)}"}

@router.get("/device/status/{device_id}")
def get_device_status(device_id: str):
    device = db.device_states.find_one({"device_id": device_id})
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    return {
        "device_id": device["device_id"],
        "relay": device["relay"],
        "state": device["state"],
        "last_updated": device["last_updated"].isoformat() + "Z",
        "is_online": True  # You may want to implement actual online check
    }

@router.get("/device/status")
def device_status():
    devices = list(db.device_states.find())
    return {
        "devices": [
            {
                "device_id": d["device_id"],
                "relay": d["relay"],
                "state": d["state"],
                "last_updated": d["last_updated"].isoformat() + "Z"
            } for d in devices
        ]
    }

@router.post("/device/add")
def add_device(device: DeviceRegister, current_user: str = Depends(get_current_user)):
    user = db.users.find_one({"email": current_user})
    if not user or "rooms" not in user or not user["rooms"]:
        raise HTTPException(status_code=400, detail="Please create a room first.")

    # Find the room index by name
    room_index = next((i for i, r in enumerate(user["rooms"]) if r["name"] == device.room_name), None)
    if room_index is None:
        raise HTTPException(status_code=404, detail="Room not found.")

    # Add the device to the devices array in the selected room
    update_result = db.users.update_one(
        {"email": current_user, f"rooms.{room_index}.name": device.room_name},
        {"$push": {f"rooms.{room_index}.devices": {
            "device_id": device.device_id,
            "device_name": device.device_name,
            "added_at": datetime.utcnow()
        }}}
    )
    if update_result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Failed to add device to room.")

    return {"msg": "Device added to room successfully"}

@router.get("/devices/all")
def get_all_devices(current_user: str = Depends(get_current_user)):
    user = db.users.find_one({"email": current_user})
    if not user or "rooms" not in user:
        return []
    all_devices = []
    for room in user["rooms"]:
        if "devices" in room:
            for device in room["devices"]:
                device_with_room = device.copy()
                device_with_room["room_name"] = room["name"]
                if "name" not in device_with_room:
                    device_with_room["name"] = device_with_room.get("device_name", "")
                all_devices.append(device_with_room)
    return all_devices

@router.delete("/device/delete/{device_id}")
def delete_device(device_id: str, current_user: str = Depends(get_current_user)):
    result = db.users.update_many(
        {"email": current_user},
        {"$pull": {"rooms.$[].devices": {"device_id": device_id}}}
    )
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Device not found in any room")
    return {"message": "Device deleted from all rooms"}

@router.get("/schedules")
def get_all_schedules(current_user: str = Depends(get_current_user)):
    user = db.users.find_one({"email": current_user})
    if not user or "rooms" not in user:
        return []
    
    all_schedules = []
    for room in user["rooms"]:
        if "devices" in room:
            for device in room["devices"]:
                if "schedules" in device and device["schedules"]:
                    for schedule in device["schedules"]:
                        schedule_with_device_info = {
                            **schedule,
                            "device_id": device["device_id"],
                            "device_name": device.get("device_name", ""),
                            "room_name": room["name"]
                        }
                        all_schedules.append(schedule_with_device_info)
    
    return all_schedules

@router.post("/device/schedule/{device_id}")
def add_schedule(device_id: str, schedule: DeviceSchedule, current_user: str = Depends(get_current_user)):
    # Assign a unique schedule_id if not present
    if not schedule.schedule_id:
        schedule.schedule_id = str(uuid4())
    result = db.users.update_one(
        {"email": current_user, "rooms.devices.device_id": device_id},
        {"$push": {"rooms.$[].devices.$[dev].schedules": schedule.dict()}},
        array_filters=[{"dev.device_id": device_id}]
    )
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Device not found")
    return {"message": "Schedule added", "schedule_id": schedule.schedule_id}

@router.delete("/device/schedule/{device_id}/{schedule_id}")
def remove_schedule(device_id: str, schedule_id: str, current_user: str = Depends(get_current_user)):
    result = db.users.update_one(
        {"email": current_user, "rooms.devices.device_id": device_id},
        {"$pull": {"rooms.$[].devices.$[dev].schedules": {"schedule_id": schedule_id}}},
        array_filters=[{"dev.device_id": device_id}]
    )
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Schedule not found")
    return {"message": "Schedule removed"}