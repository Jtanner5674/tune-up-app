import tkinter as tk
from tkinter import messagebox
import os
import sys
from maintenance_script import run_maintenance

# Function to load the license key
def get_license_key():
    # Path to the .license_key file
    license_key_path = os.path.join(os.path.dirname(__file__), ".license_key")

    # Check if the license key file exists
    if os.path.exists(license_key_path):
        with open(license_key_path, "r") as f:
            license_key = f.read().strip()
            return license_key
    return None

# Function to prompt user for license key if not found
def prompt_for_license():
    license_key = get_license_key()

    if not license_key:
        # Ask user for the license key
        license_window = tk.Tk()
        license_window.title("Enter License Key")

        tk.Label(license_window, text="Please enter your license key:").pack(padx=10, pady=10)
        license_entry = tk.Entry(license_window)
        license_entry.pack(padx=10, pady=10)

        def validate_license():
            entered_key = license_entry.get().strip()
            if entered_key:
                # Here you would validate the key, but for now, just assume it's correct
                with open(license_key_path, "w") as f:
                    f.write(entered_key)  # Save the license key to the .license_key file
                messagebox.showinfo("License", "License validated successfully!")
                license_window.destroy()
            else:
                messagebox.showerror("Error", "Please enter a valid license key.")

        tk.Button(license_window, text="Submit", command=validate_license).pack(padx=10, pady=10)
        license_window.mainloop()

# Main GUI function
def main_gui():
    root = tk.Tk()
    root.title("NTi Automated Tune Ups")
    root.geometry("400x300")

    tk.Label(root, text="Welcome to the application!").pack(padx=10, pady=10)
    tk.Button(root, text="Start Maintenance", command=run_maintenance).pack(padx=10, pady=10)

    root.mainloop()

# The actual program start
if __name__ == "__main__":
    prompt_for_license()  # Ensure license key is handled first
    main_gui()  # Start the main GUI if the license is handled
