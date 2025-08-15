
# Hybrid AdafruitIO - Blynk MQTT client for CircuitPython
#### Repo for my work on Raspberry Pi Pico W / 2W 
---
This example was verified to work with `MicroPython v1.25.0 RPI_PICO_W-20250415-v1.25.0.uf2` on:
- `Raspberry Pi Pico W` (RP2040)
- `Raspberry Pi Pico 2W` (RP2350)

> [!NOTE]
> This code cross-compatible for either Adafruit IO and Blynk Cloud MQTT Protocol.
> This code works with bare-minimum Pico W / 2W.
> This code interact with the onboard LED only. No external components required.

These variables will be used to configure either server.

```sh
use_blynk = True        # set to False for Adafruit IO server
is_free_plan = True     # only applicable for Blynk | True = Free Plan
enable_sync = True      # to minimize Message Usage in Blynk, set to False
```

Make sure settings.toml is properly configured.

```sh
CIRCUITPY_WIFI_SSID = "your-ssid-here"
CIRCUITPY_WIFI_PASSWORD = "your-ssid-password-here"

ADAFRUIT_AIO_USERNAME = "your-ADAFRUIT_AIO_USERNAME-here"
ADAFRUIT_AIO_KEY      = "fill_ADAFRUIT_AIO_KEY_up"

BLYNK_AUTH_TOKEN    = "your-BLYNK_AUTH_TOKEN-here" 
BLYNK_MQTT_BROKER   = "blynk.cloud" 
```

## Prepare your Device in Blynk.Cloud

1. Create Blynk template based on the provided blueprint. 
Click the **`Use Blueprint`** button in [`MQTT Air Cooler/Heater Demo`](https://blynk.cloud/dashboard/blueprints/Library/TMPL4zGiS1A7l).
2. In the left panel, select `Devices`
3. Click `New Device` button
4. Select `From Template -> MQTT Demo`, and click **`Create`**

> [!NOTE]
> Please note the device credentials that appear in the upper right corner. You'll need them in the next step.

Run these commands on your development machine (Terminal on macOS):

```sh
# [Step 1] Obtain via git clone 
git clone https://github.com/rtxsc/blynk-mqtt-circuitpython.git

# Navigate to the cloned folder (under home directory)
cd blynk-mqtt-circuitpython/

# [Step 1] Alternative - Obtain via Download zip
# Navigate to the Download folder
cd Downloads/blynk-mqtt-circuitpython/

# [Step 2] Copy the content into CIRCUITPY and that's it!

```

## 4. Run

The device should get connected in a few seconds. Your Serial Monitor should display something like this:

```log
Connecting to WiFi
Connected to WiFi
Caught NotImplementedError
My IP address is 192.168.0.128
Ping google.com: 75.999969 ms
Connecting to Blynk.Cloud...
XXXX.YYYY: INFO - Attempting to connect to MQTT broker (attempt #1)
Connected to Blynk.Cloud!
```

---

## Further reading

