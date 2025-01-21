import os
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
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
import re  # Added for email validation

# pyinstaller NTiMaintence.py --icon=nti.ico --add-data "maintenance_script.py;."

# Function to get the license key from the AppData folder
def get_license_key():
    license_key_path = Path(os.getenv("APPDATA")) / "NTi" / ".license_key"
    if license_key_path.exists():
        with open(license_key_path, "r") as f:
            return f.read().strip()
    return None


# Function to get the email from the AppData folder
def get_email():
    email_path = Path(os.getenv("APPDATA")) / "NTi" / ".email"
    if email_path.exists():
        with open(email_path, "r") as f:
            return f.read().strip()
    return None


# Function to validate email format
def is_valid_email(email):
    pattern = r'^[\w\.-]+@[\w\.-]+\.\w+$'
    return re.match(pattern, email) is not None


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


# Function to prompt user for email if not set or invalid
def prompt_for_email():
    email_path = Path(os.getenv("APPDATA")) / "NTi" / ".email"
    
    # Create email entry window with the same style as the license key entry window
    email_window = tk.Tk()
    email_window.title("Enter Email")
    email_window.geometry("400x200")
    email_window.resizable(False, False)

    try:
        icon_path = os.path.join(os.path.dirname(__file__), "nti.ico")
        email_window.iconbitmap(icon_path)
    except Exception as e:
        logging.error(f"Failed to load icon: {e}")

    # Apply a style for the modern look
    style = ttk.Style()
    style.theme_use("clam")  # Switch to a modern theme
    style.configure("TLabel", font=("Arial", 12))
    style.configure("TButton", font=("Arial", 10))
    style.configure("TEntry", font=("Arial", 12), padding=5)

    # Layout configuration for email window
    frame = ttk.Frame(email_window, padding=20)
    frame.pack(fill="both", expand=True)

    ttk.Label(frame, text="Please enter your email address:").pack(pady=10)
    email_entry = ttk.Entry(frame, width=40)
    email_entry.pack(pady=10)

    def save_email_and_proceed():
        entered_email = email_entry.get().strip()

        if entered_email and is_valid_email(entered_email):
            email_path.parent.mkdir(parents=True, exist_ok=True)
            with open(email_path, "w") as f:
                f.write(entered_email)  # Save email
            messagebox.showinfo("Email", "Email address saved successfully.")
            email_window.destroy()
        else:
            messagebox.showerror("Error", "Invalid email format. Please try again.")

    ttk.Button(frame, text="Submit", command=save_email_and_proceed).pack(pady=20)

    email_window.mainloop()

def create_tray_icon():
    icon_path = os.path.join(os.path.dirname(__file__), "nti.ico")
    
    # Create the system tray icon with resizing to ensure a proper size
    image = Image.open(icon_path)
    
    # Resize the image to a more suitable size for the tray
    image = image.resize((32, 32))  # Resize to 32x32 pixels (you can also try 64x64)

    
    # Create the system tray icon
    image = Image.open(icon_path)
    
    # Right-click menu with "Unsubscribe" option
    menu = Menu(
        MenuItem("Unsubscribe", unsubscribe_action),
        MenuItem("Exit", exit_action),
        MenuItem("Run Maintenance", start_maintenance)
    )
    
    # Create and run the icon    
    icon = Icon("NTi Maintenance", image, menu=menu)
    icon.run()

# Function to handle the exit action
def exit_action(icon, item):
    icon.stop()  # Stop the icon and exit the application

def unsubscribe_action(icon, item):
    # Show confirmation dialog
    result = messagebox.askyesno("Confirm Unsubscribe", "Are you sure you want to unsubscribe and cancel your license?")
    if result:  # If user clicks Yes
        license_key = get_license_key()
        email = get_email()

        if license_key and email:
            try:
                logging.info("Unsubscribing and triggering maintenance with --unsubscribe.")
                subprocess.run([sys.executable, 'maintenance_script.py', '--unsubscribe'], check=True)
                messagebox.showinfo("Success", "Your license cancellation request has been sent.")
            except subprocess.CalledProcessError as e:
                logging.error(f"Error while calling maintenance script: {e}")
                messagebox.showerror("Error", "An error occurred while processing your request.")
        else:
            logging.error("License or email not found, cannot unsubscribe.")
    else:
        logging.info("Unsubscribe canceled.")

# Function to prompt user for license key if not found or invalid
def prompt_for_license():
    license_key_path = Path(os.getenv("APPDATA")) / "NTi" / ".license_key"
    license_key = get_license_key()
    email = get_email()

    # Prompt for email if not set or invalid
    if not email or not is_valid_email(email):
        email = prompt_for_email()

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


# Updated function to check both license and email before starting maintenance
def start_maintenance():
    license_key = get_license_key()
    email = get_email()

    # Ensure email is set and valid
    if not email or not is_valid_email(email):
        email = prompt_for_email()

    # Check license validity
    if not license_key or not validate_license_key(license_key):
        messagebox.showerror("Error", "Invalid license key. Please re-enter your license key.")
        os.remove(Path(os.getenv("APPDATA")) / "NTi" / ".license_key")
        prompt_for_license()
        return

    # If license and email are valid, proceed
    logging.info("Starting maintenance...")

    if maintenance_lock.locked():
        return

    maintenance_lock.acquire()

    def maintenance_thread():
        try:
            run_maintenance()
            messagebox.showinfo("Success", "Maintenance completed successfully!")
        except Exception as e:
            logging.error(f"Error during maintenance: {e}")
            messagebox.showerror("Error", "An error occurred during maintenance.")
        finally:
            maintenance_lock.release()

    threading.Thread(target=maintenance_thread, daemon=True).start()


# Run the system tray application
if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "run_maintenance":
        start_maintenance()
    else:
        logging.info("Starting system tray application...")
        prompt_for_license()  # Ensure license key is handled first
        create_tray_icon()  # Start the system tray icon after license is handled
