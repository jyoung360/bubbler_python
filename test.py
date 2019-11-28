import matplotlib.pyplot as plt
import numpy as np
import paho.mqtt.client as mqtt
import os
import time

startTime = int(round(time.time() * 1000))

data = []
MQTT_HOST = os.environ.get('MQTT_HOST', 'localhost')
MQTT_USER = os.environ.get('MQTT_USER', 'user')
MQTT_PWD = os.environ.get('MQTT_PWD', 'password')
# The callback for when the client receives a CONNACK response from the server.
def on_connect(client, userdata, flags, rc):
    print("Connected with result code "+str(rc))

    # Subscribing in on_connect() means that if we lose the connection and
    # reconnect then subscriptions will be renewed.
    client.subscribe("bubbles/voltage")

# The callback for when a PUBLISH message is received from the server.
count = 50000

# t = np.arange(256)
# print(np.sin(t))
# sp = np.fft.fft(np.sin(t))
# freq = np.fft.fftfreq(t.shape[-1])
# plt.plot(freq, sp.real, freq, sp.imag)
# plt.show()
def translate(value, leftMin, leftMax, rightMin, rightMax):
    leftSpan = leftMax - leftMin
    rightSpan = rightMax - rightMin
    valueScaled = float(value - leftMin) / float(leftSpan)
    return rightMin + (valueScaled * rightSpan)

def on_message(client, userdata, msg):
    data.append(int(msg.payload))
    if(len(data) == count):
        try:
            print('more than count', np.amax(data), np.amin(data))
            min = np.amin(data)
            max = np.amax(data)

            data2 = map(lambda x : translate(x, min, max, 0, 1), data)
            dataList = list(data2)
            signal = np.array(dataList, dtype=float)
            fourier = np.fft.fft(signal)
            n = signal.size
            freq = np.fft.fftfreq(n)

            print(n)
            print(freq)

            endTime = int(round(time.time() * 1000))
            timeElapsed = endTime - startTime
            dim = timeElapsed/(count*1000)
            # print(dim, timeElapsed)
            # sp = np.fft.fft(signal)
            freq = np.fft.fftfreq(n, d=dim)
            plt.plot(freq, fourier.real, freq, fourier.imag)
            plt.show()
        except Exception as e:
            print(e)

client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message

client.username_pw_set(MQTT_USER, password=MQTT_PWD)
client.connect(MQTT_HOST, 1883, 60)

client.loop_forever()
# Blocking call that processes network traffic, dispatches callbacks and
# handles reconnecting.
# Other loop*() functions are available that give a threaded interface and a
# manual interface.
# client.publish("bubbles/count", 123)

# t = np.arange(256)
# sp = np.fft.fft(np.sin(t))
# freq = np.fft.fftfreq(t.shape[-1])
# plt.plot(freq, sp.real, freq, sp.imag)
# plt.show()