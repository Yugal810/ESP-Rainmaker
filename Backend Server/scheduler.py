from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime
import pytz  # For timezone handling
from database import db
from mqtt_client import publish  # Assumes you have a publish function

def check_and_execute_schedules():
    now = datetime.now(pytz.timezone("Asia/Kolkata"))  # Set your timezone
    current_time = now.strftime("%H:%M")
    current_day = now.strftime("%A")  # e.g., "Monday"

    users = db.users.find({})
    for user in users:
        for room in user.get("rooms", []):
            for device in room.get("devices", []):
                for schedule in device.get("schedules", []):
                    if current_time == schedule["time"] and current_day in schedule["days_of_week"]:
                        # Execute the action (e.g., send MQTT command)
                        topic = f"device/{device['device_id']}/relay/set"
                        publish(topic, schedule["action"])
                        print(f"Executed {schedule['action']} for {device['device_id']} at {current_time} on {current_day}")

def start_scheduler():
    scheduler = BackgroundScheduler()
    scheduler.add_job(check_and_execute_schedules, 'interval', minutes=1)
    scheduler.start() 