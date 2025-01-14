import os
import tkinter as tk
from tkinter import messagebox
import threading
import logging
import requests
from pystray import Icon, MenuItem, Menu
from PIL import Image
from maintenance_script import run_maintenance


# Function to load the license key
def get_license_key():
    # Path to the .license_key file in the same folder as the script
    license_key_path = os.path.join(os.path.dirname(__file__), ".license_key")

    # Check if the .license_key file exists
    if os.path.exists(license_key_path):
        with open(license_key_path, "r") as f:
            license_key = f.read().strip()
            return license_key
    return None


# Function to generate a unique hash (using username and machine id)
def generate_unique_hash():
    import hashlib
    import getpass
    import uuid

    username = getpass.getuser()
    machine_id = uuid.getnode()
    unique_string = f"{username}{machine_id}"
    return hashlib.sha256(unique_string.encode()).hexdigest()


# Function to validate the license using the provided server_url
def validate_license_key(activation_key, server_url="http://localhost:5000"):
    unique_hash = generate_unique_hash()
    try:
        response = requests.get(
            server_url + '/check_license',
            params={'hash': unique_hash, 'key': activation_key},
            verify=False,
            timeout=20
        )
        if response.status_code == 200 and response.json().get('valid'):
            return True
        return False
    except requests.exceptions.RequestException as e:
        logging.error(f"Error during license validation: {e}")
        return False


# Function to prompt user for license key if not found
def prompt_for_license():
    license_key = get_license_key()
    valid = validate_license_key(license_key)
    if not valid:
        # Ask user for the license key
        license_window = tk.Tk()
        license_window.title("Enter License Key")

        tk.Label(license_window, text="Please enter your license key:").pack(padx=10, pady=10)
        license_entry = tk.Entry(license_window)
        license_entry.pack(padx=10, pady=10)

        def validate_license_and_proceed():
            entered_key = license_entry.get().strip()
            license_key_path = os.path.join(os.path.dirname(__file__), ".license_key")
            
            if entered_key:
                # Validate the key using the existing wrapper logic
                if validate_license_key(entered_key):
                    with open(license_key_path, "w") as f:
                        f.write(entered_key)  # Save the license key to the .license_key file
                    messagebox.showinfo("License", "License validated successfully!")
                    license_window.destroy()
                else:
                    # If the key is invalid, delete the existing .license_key (if it exists)
                    if os.path.exists(license_key_path):
                        os.remove(license_key_path)  # Delete invalid .license_key
                    messagebox.showerror("License", "Invalid license key. Please try again.")
                    license_window.destroy()
                    prompt_for_license()  # Re-ask for license key
            else:
                messagebox.showerror("Error", "Please enter a valid license key.")

        tk.Button(license_window, text="Submit", command=validate_license_and_proceed).pack(padx=10, pady=10)
        license_window.mainloop()
    else:
        logging.info("License found and valid.")


# Lock to ensure only one maintenance task is running at a time
maintenance_lock = threading.Lock()


# Function to load the nti.ico file for system tray icon
def create_image():
    ico_path = os.path.join(os.path.dirname(__file__), "nti.ico")
    image = Image.open(ico_path)  # Load the icon image
    return image


# Function to run maintenance tasks in a separate thread
def start_maintenance():
    # Check if license is valid before proceeding with maintenance
    license_key = get_license_key()
    if not license_key:
        messagebox.showerror("Error", "License key is missing. Please enter a valid license key.")
        return

    if not validate_license_key(license_key):
        messagebox.showerror("Error", "Invalid license key.")
        # Delete invalid .license_key and re-prompt
        os.remove(os.path.join(os.path.dirname(__file__), ".license_key"))
        prompt_for_license()
        return

    # If license is valid, proceed with maintenance
    logging.info("Starting maintenance...")

    # If maintenance is already running, do nothing
    if maintenance_lock.locked():
        return

    maintenance_lock.acquire()

    def maintenance_thread():
        try:
            run_maintenance()  # Call your maintenance function here
            messagebox.showinfo("Success", "Maintenance completed successfully!")
        except Exception as e:
            logging.error(f"Error during maintenance: {e}")
            messagebox.showerror("Error", "An error occurred during maintenance.")
        finally:
            maintenance_lock.release()  # Release the lock

    threading.Thread(target=maintenance_thread, daemon=True).start()


# Create system tray icon and menu
def create_tray_icon():
    icon = Icon("NTi Maintenance", create_image(), menu=Menu(MenuItem("Start Maintenance", start_maintenance), MenuItem("Exit", exit_program)))
    icon.run()


# Exit function for system tray
def exit_program(icon, item):
    icon.stop()


# Run the system tray application
if __name__ == "__main__":
    logging.info("Starting system tray application...")
    prompt_for_license()  # Ensure license key is handled first
    create_tray_icon()  # Start the system tray icon after license is handled
