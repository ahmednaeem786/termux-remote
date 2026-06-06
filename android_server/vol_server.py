from flask import Flask
import os
import requests
import socket
import threading
from dotenv import load_dotenv

# Initialize the Flask web framework
app = Flask(__name__)

# Load environment variables from the .env file
load_dotenv()

# Retrieve the unique dweet channel ID securely from the environment
DWEET_ID = os.getenv("DWEET_ID")

# Ensure the program doesn't run without the DWEET ID
if not DWEET_ID:
    print("Error: DWEET ID not found in the .env file :(")
    exit()

def get_my_ip():
    """
    Determines the phone's actual local network IP address dynamically.
    Instead of hardcoding, it uses a UDP socket routing trick to force the OS 
    to reveal the IP assigned to it by the current Wi-Fi network.
    """
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # Doesn't actually send data; just forces interface resolution
        s.connect(('10.255.255.255', 1))
        IP = s.getsockname()[0]
    except Exception:
        # Fallback to localhost if no active network connection is found
        IP = '127.0.0.1'
    finally:
        s.close()
    return IP

def publish_ip():
    """
    Acts as an IoT handshake. Grabs the current local IP and publishes it 
    to the dweet.cc cloud broker so the laptop client can discover it automatically.
    """
    ip = get_my_ip()
    try:
        # Pushes the IP payload to the public bulletin board under your unique ID
        requests.get(f"https://dweet.cc/dweet/for/{DWEET_ID}?ip={ip}")
        print(f"\n[+] Successfully registered IP {ip} to dweet.cc!")
    except:
        print("\n[-] Failed to register IP. Check network connection.")

@app.route('/action/<command>')
def execute_action(command):
    """
    A dynamic, universal endpoint. It checks the incoming command against 
    a list of allowed actions and routes it to the correct Android system call.
    """
    # Define all the commands Android's media_session natively supports
    media_dispatch_keys = ["next", "previous", "play", "pause", "play-pause", "stop", "mute"]
    volume_keys = ["raise", "lower", "same"]

    # Route the command to the correct OS execution
    if command in media_dispatch_keys:
        os.system(f"cmd media_session dispatch {command}")
        return f"Dispatched media key: {command}", 200
        
    elif command in volume_keys:
        os.system(f"cmd media_session volume --show --adj {command}")
        return f"Adjusted volume: {command}", 200
        
    # Security/Fallback: Ignore anything that isn't explicitly allowed above
    return "Invalid command", 400

# --- Main Execution Flow ---
if __name__ == '__main__':
    # Run the IP publisher in a separate background thread 
    # so it doesn't block the Flask server from starting immediately
    threading.Thread(target=publish_ip).start()
    
    # Start the Flask API server
    # host='0.0.0.0' tells it to listen on ALL network interfaces (Wi-Fi, etc.)
    # port=5000 is the designated port the laptop will send requests to
    app.run(host='0.0.0.0', port=5000, threaded=True)