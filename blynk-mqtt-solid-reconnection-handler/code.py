# SPDX-FileCopyrightText: 2021 ladyada for Adafruit Industries
# SPDX-FileCopyrightText: 2026 ClumzyaziD for Robotronix Industries
# SPDX-License-Identifier: MIT
"""
The most stable and solid network hiccups handling
"""

import wifi
import adafruit_minimqtt.adafruit_minimqtt as MQTT
import adafruit_requests
import adafruit_connection_manager

from asyncio import create_task, gather, run, sleep as async_sleep

from os import getenv
import supervisor
import socketpool
import time
import board
from digitalio import DigitalInOut
import simpleio
import traceback

BLYNK_MSG_QUOTA_SAVING = True

if BLYNK_MSG_QUOTA_SAVING:
    PUSH_INTERVAL = 3600
else:
    PUSH_INTERVAL = 15

# Configure the RP2040 Pico LED Pin as an output
led_pin = DigitalInOut(board.LED)
led_pin.switch_to_output()
PIEZO_PIN = board.GP22 # change to your own buzzer wiring
elapse = "DD:HH:MM:SS"

# Get WiFi details and Adafruit IO keys, ensure these are setup in settings.toml
# (visit io.adafruit.com if you need to create an account, or if you need your Adafruit IO key.)
ssid = getenv("CIRCUITPY_WIFI_SSID")
password = getenv("CIRCUITPY_WIFI_PASSWORD")

print("Connecting to WiFi")
try:
    wifi.radio.connect(ssid, password)
except:
    supervisor.reload()
print("Connected to WiFi")

### Topic Setup ###
mqtt_topic = "downlink/#"

### Code ###

# Define callback methods which are called when events occur
def connect(mqtt_client, userdata, flags, rc):
    # This function will be called when the mqtt_client is connected
    # successfully to the broker.
    print("Connected to MQTT Broker!")
    print(f"MQTT Client:{mqtt_client.client_id} Flags: {flags} RC: {rc}")

def disconnect(mqtt_client, userdata, rc):
    # This method is called when the mqtt_client disconnects
    # from the broker.
    print("Disconnected from MQTT Broker!")

def subscribe(mqtt_client, userdata, topic, granted_qos):
    # This method is called when the mqtt_client subscribes to a new feed.
    print(f"Subscribed to {topic} with QOS level {granted_qos}")

def unsubscribe(mqtt_client, userdata, topic, pid):
    # This method is called when the mqtt_client unsubscribes from a feed.
    print(f"Unsubscribed from {topic} with PID {pid}")

def publish(mqtt_client, userdata, topic, pid):
    # This method is called when the mqtt_client publishes data to a feed.
    print(f"Published to {topic} with PID {pid}")

def message(client, topic, message):
    print(f"New message on topic {topic}: {message}")

    if topic == "downlink/ds/relayA" or topic == "downlink/ds/relayB": 
        if message == "1":
            led_pin.value = True
            simpleio.tone(PIEZO_PIN, 2000, duration=0.02)
        else:
            led_pin.value = False

    if topic == "downlink/ds/FastUpdate":
        if message == "1":
            mqtt_client.publish("ds/elapseString", elapse)

pool = socketpool.SocketPool(wifi.radio)
ssl_context = adafruit_connection_manager.get_radio_ssl_context(wifi.radio)
requests = adafruit_requests.Session(pool, ssl_context)

# Set up a MiniMQTT Client
mqtt_client = MQTT.MQTT(
    broker=getenv("BLYNK_MQTT_BROKER"),
    port=1883,
    username="device",
    password=getenv("BLYNK_AUTH_TOKEN"),
    socket_pool=pool,
    ssl_context=ssl_context,
    keep_alive = 45,
    socket_timeout = 1, 
    client_id = "0000"
)

# Connect callback handlers to mqtt_client
mqtt_client.on_connect = connect
mqtt_client.on_disconnect = disconnect
mqtt_client.on_subscribe = subscribe
mqtt_client.on_unsubscribe = unsubscribe
mqtt_client.on_publish = publish
mqtt_client.on_message = message

try:
    print(f"Attempting to connect to {mqtt_client.broker}")
    mqtt_client.connect()
except Exception as e:
    traceback.print_exception(e)
    # Expecting this: MMQTTException: ('Repeated connect failures', None)
    supervisor.reload()

print(f"Subscribing to {mqtt_topic}")
mqtt_client.subscribe(mqtt_topic)

async def mqtt_task():
    global elapse
    start_time = time.monotonic()
    start_tick = time.monotonic()
    while True:
        try:
            mqtt_client.loop(timeout = 1) 
            
            uptime = time.monotonic() - start_time 
            min, sec = divmod(uptime, 60)
            hour, min = divmod(min, 60)
            day, hour = divmod(hour, 24)

            elapse = f'%02d:%02d:%02d:%02d' % (day, hour, min, sec)
           
            if (time.monotonic() - start_tick >= PUSH_INTERVAL):
                mqtt_client.publish("ds/elapseString", elapse)
                start_tick = time.monotonic()

        except (OSError, ValueError, RuntimeError) as e:
            traceback.print_exception(e)
            try:
                mqtt_client.disconnect()
            except Exception as e:
                print("MQTT disconnect error:", e)
            
            try:
                mqtt_client.connect()
            except Exception as e:
                print("MQTT CONNECT error:", e)
            print(f"Subscribing to {mqtt_topic}")
            mqtt_client.subscribe(mqtt_topic)
            continue

        except Exception as e:
            traceback.print_exception(e)
            print(f"[MMQTTException] Disconnecting from {mqtt_client.broker}")
            try:
                mqtt_client.disconnect()
            except Exception as e:
                print("MQTT disconnect error:", e)
        
            try:
                mqtt_client.connect()
            except Exception as e:
                print("MQTT CONNECT error:", e)
            print(f"Subscribing to {mqtt_topic}")
            mqtt_client.subscribe(mqtt_topic)
            continue
        await async_sleep(0) # yield to scheduler 

async def main():
    await gather(
        create_task(mqtt_task())
    )

if __name__ == "__main__":
    try:
        run(main())
    except Exception as e:
        traceback.print_exception(e)
        supervisor.reload()