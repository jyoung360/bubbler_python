#!/usr/bin/env python
import os
import asyncio
import datetime
import random
import websockets
import paho.mqtt.client as mqtt
import json
import numpy
import redis
from collections import OrderedDict 

REDIS_HOST = os.environ.get('REDIS_HOST', 'localhost')
MQTT_HOST = os.environ.get('MQTT_HOST', 'localhost')
MQTT_USER = os.environ.get('MQTT_USER', 'user')
MQTT_PWD = os.environ.get('MQTT_PWD', 'password')
r = redis.Redis(host=REDIS_HOST, port=6379, db=0, decode_responses=True)

def myconverter(o):
    if isinstance(o, datetime.datetime):
        return o.__str__()

message = []
bubbles = []
count = 0
average = 0

import time, threading

WAIT_SECONDS = 1

def ticker():
    global message, average
    valids = filter(lambda x : x['voltage'] > average + 50 or x['voltage'] < average - 50, message)
    validList = list(valids)

    bins = map(lambda x : round(x['date'].timestamp(), 1), validList)
    binsList = list(bins)

    seconds = map(lambda x : round(x['date'].timestamp()), validList)
    secondsList = list(seconds)

    finalBins = []

    if(len(binsList) > 0):
        index = max(binsList)
        x = min(binsList)
        while x <= index:
            finalBins.append(x)
            x = round(x + .1, 1)

        hist, bin_edges = numpy.histogram(binsList, bins='auto')
        if(len(binsList)/len(hist) > 4):
            now = datetime.datetime.now() # current date and time
            date_time = now.strftime("%m/%d/%YT%H:%M")
            r.hincrby('bubbles', date_time, amount=1)
            bubblesRedis = r.hgetall('bubbles')
            total = 0
            for bubble in bubblesRedis:
                total += int(bubblesRedis[bubble])
            
            minBubs = r.hget('bubbles', date_time)
            print("bubbles found:", total, average, minBubs)
            client.publish("bubbles/count", f'{total} Tot')
            client.publish("bubbles/average", f'{minBubs}/min')
            client.publish("bubbles/signal", 1)

        # response = json.dumps(validList, default = myconverter)
        
    message = []
    threading.Timer(WAIT_SECONDS, ticker).start()

ticker()

# The callback for when the client receives a CONNACK response from the server.
def on_connect(client, userdata, flags, rc):
    print("Connected with result code "+str(rc))

    # Subscribing in on_connect() means that if we lose the connection and
    # reconnect then subscriptions will be renewed.
    client.subscribe("bubbles/voltage")

# The callback for when a PUBLISH message is received from the server.
def on_message(client, userdata, msg):
    global message, average, count, bubbles
    # print(msg.topic+" "+str(msg.payload))
    try:
        voltage = int(msg.payload)
        average = ((average * count) + voltage)/(count+1)
        count += 1
        data = {}
        # print(datetime.datetime.utcnow())
        data['date'] = datetime.datetime.utcnow()
        data['voltage'] = int(msg.payload)
        message.append(data)
        if(voltage > average + 50 or voltage < average - 50):
            bubbles.append(data)

    except Exception as e:
        print(e)

client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message

client.username_pw_set(MQTT_USER, password=MQTT_PWD)
client.connect(MQTT_HOST, 1883, 60)

client.loop_start()

async def consumer_handler(websocket, path):
    async for message in websocket:
        # action = await websocket.recv()
        mydict = {
            'messageType': 'fake',
            'data': []
        }
        bubblesRedis = r.hgetall('bubbles')
        total = 0
        for bubble in bubblesRedis:
            total += int(bubblesRedis[bubble])
            try:
                whatTime = datetime.datetime.strptime(bubble, '%m/%d/%YT%H:%M')
                mydict['data'].append({ 'date': str(whatTime), 'value': bubblesRedis[bubble]});
            except Exception as e:
                print(e)
        response = json.dumps(mydict)
        await websocket.send(response)

async def producer_handler(websocket, path):
    global bubbles
    while True:
        # message = await producer()
        response = json.dumps(bubbles, default = myconverter)
        await websocket.send(response)
        bubbles = []
        await asyncio.sleep(1)

async def handler(websocket, path):
    consumer_task = asyncio.ensure_future(
        consumer_handler(websocket, path))
    producer_task = asyncio.ensure_future(
        producer_handler(websocket, path))
    done, pending = await asyncio.wait(
        [consumer_task, producer_task],
        return_when=asyncio.FIRST_COMPLETED,
    )
    for task in pending:
        task.cancel()

start_server = websockets.serve(handler, "0.0.0.0", 5678)

asyncio.get_event_loop().run_until_complete(start_server)
asyncio.get_event_loop().run_forever()