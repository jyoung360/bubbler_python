import paho.mqtt.client as mqtt
import os

MQTT_HOST = os.environ.get('MQTT_HOST', 'localhost')
MQTT_USER = os.environ.get('MQTT_USER', 'user')
MQTT_PWD = os.environ.get('MQTT_PWD', 'password')
# The callback for when the client receives a CONNACK response from the server.
def on_connect(client, userdata, flags, rc):
    print("Connected with result code "+str(rc))

    # Subscribing in on_connect() means that if we lose the connection and
    # reconnect then subscriptions will be renewed.
    client.subscribe("$SYS/#")

# The callback for when a PUBLISH message is received from the server.
def on_message(client, userdata, msg):
    print(msg.topic+" "+str(msg.payload))

client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message

client.username_pw_set(MQTT_USER, password=MQTT_PWD)
client.connect(MQTT_HOST", 1883, 60)

# Blocking call that processes network traffic, dispatches callbacks and
# handles reconnecting.
# Other loop*() functions are available that give a threaded interface and a
# manual interface.
client.publish("bubbles/count", 123)

