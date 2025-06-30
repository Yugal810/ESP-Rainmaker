#include <WiFi.h>
#include <PubSubClient.h>

// Wi-Fi Credentials
const char* ssid = "YOUR_WIFI_SSID";
const char* password = "YOUR_WIFI_PASSWORD";

// MQTT Broker
const char* mqtt_server = "broker.hivemq.com";
const int mqtt_port = 1883;
const char* device_id = "smart_led_001";

// MQTT Topics
const char* subTopic = "device/smart_led_001/led1/set";
const char* pubTopic = "device/smart_led_001/led1/state";

// LED Pin
const int ledPin = 5; // Change this to the GPIO connected to your LED

WiFiClient espClient;
PubSubClient client(espClient);

void setup_wifi() {
delay(100);
Serial.print("Connecting to ");
Serial.println(ssid);
WiFi.begin(ssid, password);
while (WiFi.status() != WL_CONNECTED) {
delay(500);
Serial.print(".");
}
Serial.println("\nWiFi connected. IP address: ");
Serial.println(WiFi.localIP());
}

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
digitalWrite(ledPin, HIGH);
client.publish(pubTopic, "ON");
} else if (msg == "OFF") {
digitalWrite(ledPin, LOW);
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
pinMode(ledPin, OUTPUT);
digitalWrite(ledPin, LOW);

Serial.begin(115200);
setup_wifi();

client.setServer(mqtt_server, mqtt_port);
client.setCallback(callback);
}

void loop() {
if (!client.connected()) {
reconnect();
}
client.loop();
}