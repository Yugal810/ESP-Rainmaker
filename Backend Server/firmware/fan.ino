#include <WiFiManager.h> // https://github.com/tzapu/WiFiManager
#include <PubSubClient.h>

// MQTT Broker
const char* mqtt_server = "broker.hivemq.com";
const int mqtt_port = 1883;
const char* device_id = "fan_001";

// MQTT Topics
const char* subTopic = "device/fan_001/fan1/set";
const char* pubTopic = "device/fan_001/fan1/state";

// Fan Relay Pin
const int fanPin = 5; // Change this to the GPIO connected to your relay/transistor

WiFiClient espClient;
PubSubClient client(espClient);

void callback(char* topic, byte* payload, unsigned int length) {
  String msg;
  for (int i = 0; i < length; i++) {
    msg += (char)payload[i];
  }
  Serial.print("Message arrived [");
  Serial.print(topic);
  Serial.print("]: ");
  Serial.println(msg);

  if (String(topic) == subTopic) {
    if (msg == "ON") {
      digitalWrite(fanPin, HIGH);
      client.publish(pubTopic, "ON");
    } else if (msg == "OFF") {
      digitalWrite(fanPin, LOW);
      client.publish(pubTopic, "OFF");
    }
  }
}

void reconnect() {
  while (!client.connected()) {
    Serial.print("Attempting MQTT connection...");
    if (client.connect(device_id)) {
      Serial.println("connected");
      client.subscribe(subTopic);
      client.publish(pubTopic, "BOOTED");
    } else {
      Serial.print("failed, rc=");
      Serial.print(client.state());
      Serial.println(" try again in 5 seconds");
      delay(5000);
    }
  }
}

void setup() {
  pinMode(fanPin, OUTPUT);
  digitalWrite(fanPin, LOW);

  Serial.begin(115200);

  // WiFiManager setup
  WiFiManager wifiManager;
  // Uncomment for testing: wifiManager.resetSettings();
  wifiManager.autoConnect("FanSetup"); // AP name

  // Now connected to WiFi!
  client.setServer(mqtt_server, mqtt_port);
  client.setCallback(callback);
}

void loop() {
  if (!client.connected()) {
    reconnect();
  }
  client.loop();
} 