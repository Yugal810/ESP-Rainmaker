import paho.mqtt.client as mqtt
import os
from dotenv import load_dotenv
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

mqtt_client = mqtt.Client()

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        logger.info("Connected to MQTT Broker successfully")
    else:
        logger.error(f"Failed to connect to MQTT Broker, return code: {rc}")

def on_disconnect(client, userdata, rc):
    logger.warning(f"Disconnected from MQTT Broker with code: {rc}")

mqtt_client.on_connect = on_connect
mqtt_client.on_disconnect = on_disconnect

try:
    broker = os.getenv("MQTT_BROKER")
    port = int(os.getenv("MQTT_PORT"))
    logger.info(f"Attempting to connect to MQTT Broker at {broker}:{port}")
    mqtt_client.connect(broker, port)
    mqtt_client.loop_start()
except Exception as e:
    logger.error(f"Error connecting to MQTT Broker: {str(e)}")

def publish(topic, msg):
    try:
        result = mqtt_client.publish(topic, msg)
        if result.rc != 0:
            logger.error(f"Failed to publish message to {topic}")
    except Exception as e:
        logger.error(f"Error publishing message: {str(e)}")