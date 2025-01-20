import os
import tkinter as tk
from tkinter import ttk, messagebox
import threading
import logging
import requests
from pystray import Icon, MenuItem, Menu
from PIL import Image
from maintenance_script import run_maintenance
import sys
from pathlib import Path
import uuid
import hashlib

# Function to get the license key from the AppData folder
def get_license_key():
    # Path to the .license_key file in the AppData folder
    license_key_path = Path(os.getenv("APPDATA")) / "NTi" / ".license_key"

    if license_key_path.exists():
        with open(license_key_path, "r") as f:
            license_key = f.read().strip()
            return license_key
    return None


# Function to get the email from the AppData folder
def get_email():
    email_path = Path(os.getenv("APPDATA")) / "NTi" / ".email"
    if email_path.exists():
        with open(email_path, "r") as f:
            email = f.read().strip()
            return email
    return None

def generate_unique_hash():
    mac = hex(uuid.getnode())  # Get the MAC address of the machine
    return hashlib.sha256(mac.encode()).hexdigest()

        
def validate_license_key(activation_key, server_url="http://107.128.239.126:5000"):
    unique_hash = generate_unique_hash()
    try:
        logging.info(f"Validating license for key: {activation_key} with hash: {unique_hash}")
        response = requests.get(
            f"{server_url}/check_license",
            params={'hash': unique_hash, 'key': activation_key},
            verify=True,  # Keep secure communication
            timeout=20
        )
        if response.status_code == 200:
            response_data = response.json()
            return response_data.get('valid', False)
        elif response.status_code == 404:
            logging.warning("License not found on the server.")
            return False
        else:
            logging.error(f"Unexpected status code {response.status_code} from server.")
            return False
    except requests.exceptions.Timeout:
        logging.error("Request to the license server timed out.")
        return False
    except requests.exceptions.RequestException as e:
        logging.error(f"Error during license validation: {e}")
        return False




# Function to prompt user for license key if not found or invalid
def prompt_for_license():
    license_key_path = Path(os.getenv("APPDATA")) / "NTi" / ".license_key"
    license_key = get_license_key()

    # Check if the key is valid
    if not license_key or not validate_license_key(license_key):
        # Create license entry window
        license_window = tk.Tk()
        license_window.title("Enter License Key")
        license_window.geometry("400x200")
        license_window.resizable(False, False)

        try:
            icon_path = os.path.join(os.path.dirname(__file__), "nti.ico")
            license_window.iconbitmap(icon_path)
        except Exception as e:
            logging.error(f"Failed to load icon: {e}")
            
        # Apply a style for the modern look
        style = ttk.Style()
        style.theme_use("clam")  # Switch to a modern theme
        style.configure("TLabel", font=("Arial", 12))
        style.configure("TButton", font=("Arial", 10))
        style.configure("TEntry", font=("Arial", 12), padding=5)

        # Layout configuration
        frame = ttk.Frame(license_window, padding=20)
        frame.pack(fill="both", expand=True)

        ttk.Label(frame, text="Please enter your license key:").pack(pady=10)
        license_entry = ttk.Entry(frame, width=40)
        license_entry.pack(pady=10)

        def validate_license_and_proceed():
            entered_key = license_entry.get().strip()

            if entered_key:
                if validate_license_key(entered_key):
                    license_key_path.parent.mkdir(parents=True, exist_ok=True)
                    with open(license_key_path, "w") as f:
                        f.write(entered_key)  # Save license key
                    messagebox.showinfo("License", "License validated successfully!")
                    license_window.destroy()
                else:
                    if license_key_path.exists():
                        os.remove(license_key_path)
                    messagebox.showerror("License", "Invalid license key. Please try again.")
                    license_window.destroy()
                    prompt_for_license()
            else:
                messagebox.showerror("Error", "Please enter a valid license key.")

        ttk.Button(frame, text="Submit", command=validate_license_and_proceed).pack(pady=20)

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
        messagebox.showerror("Error", "License key is missing. Unable to proceed with scheduled maintenance, please enter a valid license key or contact NTi for support.")
        return

    if not validate_license_key(license_key):
        messagebox.showerror("Error", "Invalid license key. Unable to proceed with scheduled maintenance, please contact NTi for support.")
        # Delete invalid .license_key and re-prompt
        os.remove(Path(os.getenv("APPDATA")) / "NTi" / ".license_key")
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


# Function to prompt the user for a new license key
def change_license():
    license_key = get_license_key()
    if license_key:
        os.remove(Path(os.getenv("APPDATA")) / "NTi" / ".license_key")
    prompt_for_license()


# Function to prompt the user for a new email
def change_email():
    email_path = Path(os.getenv("APPDATA")) / "NTi" / ".email"
    new_email = simpledialog.askstring("Change Email", "Please enter your new email:")
    if new_email:
        email_path.parent.mkdir(parents=True, exist_ok=True)
        with open(email_path, "w") as f:
            f.write(new_email)
        messagebox.showinfo("Success", f"Email updated to {new_email}")
    else:
        messagebox.showerror("Error", "Email change failed. Please try again.")


# Create system tray icon and menu
def create_tray_icon():
    icon = Icon("NTi Maintenance", create_image(), menu=Menu(
        MenuItem("Start Maintenance", start_maintenance),
        MenuItem("Change License", change_license),
        MenuItem("Change Email", change_email),
        MenuItem("Exit", exit_program)
    ))
    icon.run()


# Exit function for system tray
def exit_program(icon, item):
    icon.stop()


# Run the system tray application
if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "run_maintenance":
        start_maintenance()
    else:
        logging.info("Starting system tray application...")
        prompt_for_license()  # Ensure license key is handled first
        create_tray_icon()  # Start the system tray icon after license is handled
