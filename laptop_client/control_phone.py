import requests
import keyboard
import time
import os
from dotenv import load_dotenv

# Loading environment variable
load_dotenv()

# Retrieving the unique DWEET ID from the environment
DWEET_ID = os.getenv("DWEET_ID")

# Safety check to make sure we have retrieved a DWEET ID from the environment variable, if not then exit's the program
if not DWEET_ID:
    print("Error: DWEET ID not found in the .env file :(")
    exit()

# Global variables to track state as well as handle rate-limiting
PHONE_IP = None
last_pressed = 0
COOLDOWN = 0.2 # Minimum delay in seconds between volume changes to prevent spamming

def discover_phone():
    """
    Retrieve latest published IP address of the Android 
    phone from the dweet.cc cloud broker.
    """
    print("Looking for a phone on the network...")
    try:
        # Requesting the latest data payload sent to the unique dweet channel
        r = requests.get(f"https://dweet.cc/get/latest/dweet/for/{DWEET_ID}")
        data = r.json()

        # Parsing the JSON response to extract the IP address nested within
        ip = data['with'][0]['content']['ip']
        print(f"Found phone automatically at: {ip}")
        return ip
    except Exception as e:
        print("!! Could not find phone. Is the Termux server running?")
        return None

def change_vol(direction):
    """
    Sends a HTTP GET request to the Flask server running
    on the phone to adjust the media volume accordingly.
    """
    global last_pressed, PHONE_IP

    if not PHONE_IP or ((time.time() - last_pressed) < COOLDOWN): 
        return
    last_pressed = time.time()
    
    command = "raise" if direction == "up" else "lower"

    try:
        requests.get(f"http://{PHONE_IP}:5000/action/{command}", timeout=1)
    except:
        print("Connection error. Did the IP change?")

def control_media(action):
    """
    Sends a HTTP request to control the media playback i.e. (next/previous track).
    Uses a slighly longer cooldown to prevent double-skipping tracks.
    """
    global last_pressed, PHONE_IP

    if not PHONE_IP or (time.time() - last_pressed) < 0.4:
        return
    last_pressed = time.time()

    command = "previous" if action == "prev" else action
    
    try:
        requests.get(f"http://{PHONE_IP}:5000/action/{command}", timeout=1)
    except:
        print("Connection error. Did the IP change?")

# Attempting to locate the phone on the local network through the DWEET cloud broker
PHONE_IP = discover_phone()

# If phone discovered, then add global hotkeys and start listening
if PHONE_IP:
    # Mapping keyboard hotkeys to adjust the volume accordingly
    keyboard.add_hotkey('alt+up', lambda: change_vol('up'))
    keyboard.add_hotkey('alt+down', lambda: change_vol('down'))

    keyboard.add_hotkey('alt+right', lambda: control_media('next'))
    keyboard.add_hotkey('alt+left', lambda: control_media('prev'))

    keyboard.add_hotkey('alt+space', lambda: control_media('play-pause'))

    print("\n--- Phone Volume Controller Active ---")
    print("Hotkeys: ALT + UP / ALT + DOWN")
    print("Press CTRL+C to quit.")

    # Keeps the script running continuously in the background to waiting for hotkey presses.
    keyboard.wait()