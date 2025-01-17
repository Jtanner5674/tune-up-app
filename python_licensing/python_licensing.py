"""
This module provides the `licensed` decorator for checking license validity 
against a licensing server before executing a function.
"""

import hashlib
import os
import getpass
import uuid
import requests
from pathlib import Path

def generate_unique_hash():
    """
    Generate a unique hash based on the username and machine id.
    """
    username = getpass.getuser()
    machine_id = uuid.getnode()
    unique_string = f"{username}{machine_id}"
    return hashlib.sha256(unique_string.encode()).hexdigest()

def get_activation_key():
    """
    Get the activation key. If the key is not stored locally, ask the user to enter it.
    Store the key locally for future use.
    """
    # Store the .license_key file in the AppData folder under a custom directory (e.g., "NTi")
    key_file = Path(os.getenv("APPDATA")) / "NTi" / ".license_key"
    
    if key_file.exists():
        with open(key_file, 'r', encoding='utf-8') as f:
            return f.read().strip()
    else:
        # If the license key is not found, prompt the user for input
        key = input("Enter your activation key: ")
        # Ensure the directory exists before writing the key
        key_file.parent.mkdir(parents=True, exist_ok=True)
        with open(key_file, 'w', encoding='utf-8') as f:
            f.write(key)
        return key

def licensed(server_url):
    """
    Decorator function to check the license before executing a function.
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            unique_hash = generate_unique_hash()
            activation_key = get_activation_key()
            try:
                response = requests.get(
                    server_url + '/check_license',
                    params={
                        'hash': unique_hash,
                        'key': activation_key
                        },
                    verify=False,
                    timeout=20)
                if response.status_code == 200 and response.json()['valid']:
                    return func(*args, **kwargs)
            except requests.exceptions.Timeout:
                print("The request to the licensing server timed out.")
            except requests.exceptions.RequestException as e:
                print(f"An error occurred: {e}")
            print("Invalid license or unable to reach the licensing server.")
            input("Press any key to exit.")
            return None
        return wrapper
    return decorator
