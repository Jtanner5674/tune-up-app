import tkinter as tk
from tkinter import messagebox
import threading
import logging
from pystray import Icon, MenuItem, Menu
from PIL import Image
from maintenance_script import run_maintenance
import os

# Lock to ensure only one maintenance task is running at a time
maintenance_lock = threading.Lock()

# Function to load the nti.ico file for system tray icon
def create_image():
    # Make sure the nti.ico file is in the same directory as your script
    ico_path = os.path.join(os.path.dirname(__file__), "nti.ico")
    image = Image.open(ico_path)  # Load the icon image
    return image

# Function to run maintenance tasks in a separate thread
def start_maintenance():
    # If maintenance is already running, do nothing
    if maintenance_lock.locked():
        return  # Do nothing if already running

    # Acquire the lock to ensure only one maintenance task is running
    maintenance_lock.acquire()

    def maintenance_thread():
        try:
            logging.info("Starting maintenance...")
            run_maintenance()  # Call your maintenance function here
            messagebox.showinfo("Success", "Maintenance completed successfully!")
        except Exception as e:
            logging.error(f"Error during maintenance: {e}")
            messagebox.showerror("Error", "An error occurred during maintenance.")
        finally:
            maintenance_lock.release()  # Release the lock

    # Start the thread for maintenance
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
    create_tray_icon()
