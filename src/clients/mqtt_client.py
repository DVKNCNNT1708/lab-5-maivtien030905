import paho.mqtt.client as mqtt
import os
import json
from dotenv import load_dotenv

load_dotenv()

class MQTTClient:
    def __init__(self):
        self.client = mqtt.Client()
        self.broker = os.getenv("MQTT_BROKER")
        self.port = int(os.getenv("MQTT_PORT", 1883))
        self.username = os.getenv("MQTT_USERNAME")
        self.password = os.getenv("MQTT_PASSWORD")
        
        self.client.username_pw_set(self.username, self.password)
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message

    def on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            print(f"✅ Đã kết nối MQTT Broker: {self.broker}")
            topics = [
                os.getenv("MQTT_TOPIC_IOT_EVENTS"),
                os.getenv("MQTT_TOPIC_CAMERA_EVENTS"),
                os.getenv("MQTT_TOPIC_NOTIFICATIONS"),
                os.getenv("MQTT_TOPIC_ANALYTICS")
            ]
            for topic in topics:
                if topic:
                    client.subscribe(topic)
                    print(f"📡 Đã subscribe: {topic}")

    def on_message(self, client, userdata, msg):
        payload = msg.payload.decode('utf-8')
        print(f"📩 Dữ liệu mới từ {msg.topic}: {payload}")

    def start(self):
        self.client.connect(self.broker, self.port, 60)
        self.client.loop_start()