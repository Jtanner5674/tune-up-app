import tkinter as tk
from tkinter import messagebox
from tkinter.simpledialog import askstring
import logging
from pystray import Icon, MenuItem, Menu
from PIL import Image
import os
import time

# Lock to ensure only one maintenance task is running at a time
maintenance_lock = False

# Function to load the nti.ico file for system tray icon
def create_image():
    # Make sure the nti.ico file is in the same directory as your script
    ico_path = os.path.join(os.path.dirname(__file__), "nti.ico")
    image = Image.open(ico_path)  # Load the icon image
    return image

# Function to verify if the license key is valid
def is_license_valid():
    # Simulate the license check (replace with actual license check code)
    # Example: you can check a .license_key file here
    license_key = "4ea5f034-87ee-45ca-8f28-bd918494446e"  # This is just an example
    try:
        with open(".license_key", "r") as f:
            stored_key = f.read().strip()
            if stored_key == license_key:
                return True
    except FileNotFoundError:
        return False

    return False

# Function to handle invalid license and ask for activation code
def handle_invalid_license():
    def show_license_dialog():
        dialog_window = tk.Toplevel(root)
        dialog_window.title("Activate License")
        dialog_window.geometry("300x150")
        
        label = tk.Label(dialog_window, text="Please enter your activation code:", font=("Arial", 10))
        label.pack(pady=10)

        entry = tk.Entry(dialog_window, font=("Arial", 12), show="*")
        entry.pack(pady=10)

        def submit_license():
            activation_code = entry.get()
            if activation_code == "4ea5f034-87ee-45ca-8f28-bd918494446e":  # Example validation
                with open(".license_key", "w") as f:
                    f.write(activation_code)  # Save the valid license key
                messagebox.showinfo("License Validated", "License validated successfully!")
                dialog_window.destroy()
                start_maintenance()  # Restart maintenance task with valid license
            else:
                messagebox.showerror("Invalid License", "The activation code is invalid.")

        submit_button = tk.Button(dialog_window, text="Submit", font=("Arial", 12), command=submit_license)
        submit_button.pack(pady=10)

    show_license_dialog()

# Function to run maintenance tasks
def start_maintenance():
    global maintenance_lock

    # If maintenance is already running, do nothing
    if maintenance_lock:
        return  # Do nothing if already running

    maintenance_lock = True  # Lock to prevent re-entry

    try:
        logging.info("Starting maintenance...")
        if not is_license_valid():
            handle_invalid_license()  # License check before running tasks
        else:
            run_maintenance()  # Call your maintenance function here
            messagebox.showinfo("Success", "Maintenance completed successfully!")
    except Exception as e:
        logging.error(f"Error during maintenance: {e}")
        messagebox.showerror("Error", "An error occurred during maintenance.")
    finally:
        maintenance_lock = False  # Release the lock

# Simulate maintenance function (you can replace this with your actual maintenance logic)
def run_maintenance():
    # Simulate a long-running task
    time.sleep(3)

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
    root = tk.Tk()  # Root window required for dialog boxes
    root.withdraw()  # Hide the root window, we only need the tray icon

    # Show the license dialog if the license is invalid
    if not is_license_valid():
        handle_invalid_license()

    # Start the system tray icon
    create_tray_icon()

    # Now run the main event loop to handle GUI events
    root.mainloop()
