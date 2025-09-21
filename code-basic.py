# SPDX-FileCopyrightText: 2025 ClumzyaziD for Robotronix Inc
# SPDX-License-Identifier: MIT
"""
Minimal Implementation of Blynk-MQTT with CircuitPython
"""
from os import getenv
import ipaddress
import wifi
import socketpool
from binascii import hexlify

import adafruit_connection_manager
import adafruit_minimqtt.adafruit_minimqtt as MQTT
from adafruit_io.adafruit_io import IO_MQTT
import time

import board
from digitalio import DigitalInOut
from microcontroller import cpu
import traceback, sys
import supervisor

firmware_version = "0.0.1"
BLYNK_LOGO = r"""
      ___  __          __
     / _ )/ /_ _____  / /__
    / _  / / // / _ \/  '_/
   /____/_/\_, /_//_/_/\_\
          /___/ MQTT CircuitPython Device Demo for {} | v{}
""".format(sys.platform, firmware_version)

AIO_LOGO = r"""
       ___       __      ____           _ __     ____ ___ 
      /   | ____/ /___ _/ __/______  __(_) /_   /  _/ __ \
     / /| |/ __  / __ `/ /_/ ___/ / / / / __/   / // / / /
    / ___ / /_/ / /_/ / __/ /  / /_/ / / /_   _/ // /_/ / 
   /_/  |_\__,_/\__,_/_/ /_/   \__,_/_/\__/  /___/\____/ 
                    MQTT CircuitPython Device Demo for {} | v{}
""".format(sys.platform, firmware_version)

use_blynk = True        # set to False for Adafruit IO server
is_free_plan = True     # only applicable for Blynk | True = Free Plan
enable_sync = True      # to minimize Message Usage in Blynk, set to False
push_interval = 3600    # in seconds. Default to 1 hour to minimize Blynk quota usage

# Configure the RP2040 Pico LED Pin as an output
led_pin = DigitalInOut(board.LED)
led_pin.switch_to_output()

# Get WiFi details and Adafruit IO keys, ensure these are setup in settings.toml
# (visit io.adafruit.com if you need to create an account, or if you need your Adafruit IO key.)
ssid = getenv("CIRCUITPY_WIFI_SSID")
password = getenv("CIRCUITPY_WIFI_PASSWORD")
aio_username = getenv("ADAFRUIT_AIO_USERNAME")
aio_key = getenv("ADAFRUIT_AIO_KEY")

if None in [ssid, password]:
    raise RuntimeError(
        "WiFi settings are kept in settings.toml, "
        "please add them there. The settings file must contain "
        "'CIRCUITPY_WIFI_SSID', 'CIRCUITPY_WIFI_PASSWORD', "
        "at a minimum."
    )

print()
if use_blynk:
    print(BLYNK_LOGO)
else:
    print(AIO_LOGO)
print("Connecting to WiFi")

#  connect to your SSID
try:
    wifi.radio.connect(ssid, password)
except TypeError:
    print("Could not find WiFi info. Check your settings.toml file!")
    supervisor.reload()

print("Connected to WiFi")

pool = socketpool.SocketPool(wifi.radio)
ssl_context = adafruit_connection_manager.get_radio_ssl_context(wifi.radio)

try:
    rssi = wifi.radio.ap_info.rssi 
    print(f"\nConnecting to {ssid}...")
    print(f"Signal Strength: {rssi}")
except NotImplementedError:
    print("Caught NotImplementedError")

# print hexlified MAC
mac_addr = wifi.radio.mac_address
print(hex(len(mac_addr)), hexlify(mac_addr, ":"))

#  prints IP address to REPL
print(f"My IP address is {wifi.radio.ipv4_address}")

#  pings Google
ipv4 = ipaddress.ip_address("8.8.4.4")
try:
    print("Ping google.com: %f ms" % (wifi.radio.ping(ipv4)*1000))
except TypeError:
    print("NoneType for ipv4. Possibly network is down!")


# Define callback functions which will be called when certain events happen.
def connected(client):
    # Connected function will be called when the client is connected to Adafruit IO.
    # This is a good place to subscribe to feed changes.  The client parameter
    # passed to this function is the Adafruit IO MQTT client so you can make
    # calls against it easily.
    if use_blynk:
        print("Connected to Blynk.Cloud!")
    else:
        print("Connected to Adafruit IO!")

def subscribe(client, userdata, topic, granted_qos):
    # This method is called when the client subscribes to a new feed.
    print(f"Subscribed to {topic} with QOS level {granted_qos}")


def unsubscribe(client, userdata, topic, pid):
    # This method is called when the client unsubscribes from a feed.
    print(f"Unsubscribed from {topic} with PID {pid}")

def disconnected(client):
    # Disconnected function will be called when the client disconnects.
    if use_blynk:
        print("Disconnected from Blynk.Cloud!")
    else:
        print("Disconnected from Adafruit IO!")


def publish(client, userdata, topic, pid):
    # This method is called when the client publishes data to a feed.
    print(f"Published to {topic} with PID {pid}")
    if userdata is not None:
        print("Published User data: ", end="")
        print(userdata)

def on_message(client, feed_id, payload):
    # Message function will be called when a subscribed feed has a new value.
    # The feed_id parameter identifies the feed, and the payload parameter has
    # the new value.
    print(f"Feed {feed_id} received new value: {payload}")
    if feed_id == "Power":
        if payload == "ON" or payload == "1":
            led_pin.value = True
        else:
            led_pin.value = False

def on_battery_msg(client, topic, message):
    # Method called whenever user/feeds/battery has a new value (Adafruit IO template)
    print(f"Battery level: {message}v")

if use_blynk:
    # Initialize a new MQTT Client object
    mqtt_client = MQTT.MQTT(
    broker=getenv("BLYNK_MQTT_BROKER"),
    port=1883,
    username="device",
    password=getenv("BLYNK_AUTH_TOKEN"),
    socket_pool=pool,
    ssl_context=ssl_context,
    keep_alive = 45
)
else:
    # Initialize a new MQTT Client object
    mqtt_client = MQTT.MQTT(
        broker="io.adafruit.com",
        port=1883,
        username=aio_username,
        password=aio_key,
        socket_pool=pool,
        ssl_context=ssl_context,
        keep_alive = 60
    )

# Initialize an Adafruit IO MQTT Client
io = IO_MQTT(mqtt_client, use_blynk)

# Connect the callback methods defined above to Adafruit IO
io.on_connect = connected
io.on_disconnect = disconnected
io.on_subscribe = subscribe
io.on_unsubscribe = unsubscribe
io.on_message = on_message
io.on_publish = publish

def offline_mode(timeout = 10):
    print("\nEntering OFFLINE MODE for {} seconds".format(timeout))
    i = 0
    while i < timeout:
        i += 1
        print(".", end="")
        time.sleep(1)
    print("\nExiting OFFLINE MODE...Reloading now...")
    supervisor.reload()

def main():
    # Connect to MQTT broker of choice
    if use_blynk:
        print("Connecting to Blynk.Cloud...")
    else:
        print("Connecting to Adafruit IO...")
    try:
        io.connect()
    except:
        offline_mode()

    # # Set up a message handler for the battery feed
    io.add_feed_callback("battery", on_battery_msg)

    if use_blynk:
        io.subscribe("downlink/#")
    else:
        io.subscribe("Power") # feed name on your AIO might be different

    if enable_sync:
        # Get latest values from server and update accordingly
        # this is similar to Blynk.syncVirtual on Arduino
        io.get("Power") 

    prv_refresh_time = 0.0
    # Start a blocking loop to check for new messages
    print("All is set! Running blocking main loop...Push Interval set to {}s".format(push_interval))
    while True:
        try:
            io.loop()
        except (ValueError, RuntimeError) as e:
            print("Failed to get data, retrying\n", e)
            io.reconnect()
            continue

        if (time.monotonic() - prv_refresh_time) > push_interval:
            # take the cpu's temperature
            cpu_temp = cpu.temperature
            # truncate to two decimal points
            cpu_temp = str(cpu_temp)[:5]
            if use_blynk:
                print(f"CPU temperature is %s degrees C" % cpu_temp)
                if not is_free_plan:
                    io.publish("ahtxTemp", cpu_temp) # pub to blynk
                    print("Published to Blynk.Cloud!")
            else:
                print(f"CPU temperature is %s degrees C" % cpu_temp)
                # publish for AIO since no limit
                io.publish("ahtxTemp", cpu_temp) # pub to AIO
                print("Published to Adafruit IO!")

            prv_refresh_time = time.monotonic()
        time.sleep(0.1) # MASTER LOOP DELAY 


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        traceback.print_exception(e)
        print("restarting in ")
        timeout = 5
        for i in range(5):
            print(timeout - i, end=" ")
            time.sleep(1)
        supervisor.reload()