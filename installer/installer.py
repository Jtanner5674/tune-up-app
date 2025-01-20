import os
import shutil
import subprocess
import sys
import tkinter as tk
from tkinter import ttk, messagebox
from pathlib import Path
import time
import ctypes

# Constants
APP_NAME = "NTi AutoMaintenance"
INSTALL_DIR = os.path.join(os.environ['PROGRAMFILES'], APP_NAME)
LICENSE_FILE = os.path.expanduser(r'~\AppData\Roaming\NTi\.license_key')

# Adjust paths based on whether we are running as a script or a bundled executable
if getattr(sys, 'frozen', False):
    # Running as a bundled executable
    base_path = sys._MEIPASS
else:
    # Running as a normal script
    base_path = os.path.dirname(__file__)

ICON_PATH = os.path.join(base_path, 'nti.ico')
EXECUTABLE_PATH = os.path.join(base_path, 'NTiMaintenance.exe')
INSTALLER_PATH = sys.argv[0]  # Path to the current installer executable

def is_admin():
    """Check if the script is run with administrator privileges."""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin() != 0
    except Exception:
        return False

def install():
    if not is_admin():
        # Re-run the script as an administrator if not already running with admin privileges
        ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, sys.argv[0], None, 1)
        sys.exit(0)  # Exit the current process once the admin request is triggered

    # Step 1: Check if the directory exists, create it if not
    if not os.path.exists(INSTALL_DIR):
        os.makedirs(INSTALL_DIR)

    # Step 2: Copy executable and icon to the installation directory
    if os.path.exists(EXECUTABLE_PATH):
        shutil.copy(EXECUTABLE_PATH, INSTALL_DIR)
    else:
        print(f"Error: {EXECUTABLE_PATH} not found.")
        return

    if os.path.exists(ICON_PATH):
        shutil.copy(ICON_PATH, INSTALL_DIR)

    # Step 3: Prompt for license key and email
    get_license_key_and_email()

    # Step 4: Create scheduled tasks (weekly maintenance and startup)
    create_scheduled_tasks()

    # Step 5: Delete the installer executable after installation is complete
    delete_installer()

    print(f"{APP_NAME} installed successfully!")

    # Step 6: Launch the application and start maintenance
    launch_application()

    # Show the message to the user about scheduled maintenance
    show_maintenance_message()

def create_scheduled_tasks():
    # Task 1: Create weekly maintenance task at 11 PM every Sunday
    task_command = f'"{INSTALL_DIR}\\NTiMaintenance.exe" run_maintenance'
    subprocess.run(['schtasks', '/Create', '/SC', 'WEEKLY', '/D', 'SUN', '/TN', f'{APP_NAME} Task',
                    '/TR', task_command, '/RL', 'HIGHEST', '/ST', '23:00', '/RU', 'SYSTEM'], check=True)

    # Task 2: Create startup task (runs when user logs in)
    subprocess.run(['schtasks', '/Create', '/SC', 'ONLOGON', '/TN', f'{APP_NAME} Startup',
                    '/TR', f'"{INSTALL_DIR}\\NTiMaintenance.exe"', '/RL', 'HIGHEST'], check=True)

def get_license_key_and_email():
    # Create a tkinter root window
    license_window = tk.Tk()
    license_window.title("Enter License Key and Email")
    license_window.geometry("400x250")
    license_window.resizable(False, False)

    try:
        license_window.iconbitmap(ICON_PATH)
    except Exception as e:
        print(f"Failed to load icon: {e}")

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

    def validate_license():
        entered_key = license_entry.get().strip()

        if entered_key:
            # Save the license key to a file
            license_key_path = Path(os.getenv("APPDATA")) / "NTi" / ".license_key"
            license_key_path.parent.mkdir(parents=True, exist_ok=True)
            with open(license_key_path, "w") as f:
                f.write(entered_key)  # Save license key

            # Now proceed to email collection
            get_email()
        else:
            messagebox.showerror("Error", "Please enter a valid license key.")

    ttk.Button(frame, text="Submit", command=validate_license).pack(pady=20)

    license_window.mainloop()

def get_email():
    # Create a tkinter window for email input
    email_window = tk.Tk()
    email_window.title("Enter Email")
    email_window.geometry("400x250")
    email_window.resizable(False, False)

    try:
        email_window.iconbitmap(ICON_PATH)
    except Exception as e:
        print(f"Failed to load icon: {e}")

    # Apply a style for the modern look
    style = ttk.Style()
    style.theme_use("clam")  # Switch to a modern theme
    style.configure("TLabel", font=("Arial", 12))
    style.configure("TButton", font=("Arial", 10))
    style.configure("TEntry", font=("Arial", 12), padding=5)

    # Layout configuration
    frame = ttk.Frame(email_window, padding=20)
    frame.pack(fill="both", expand=True)

    ttk.Label(frame, text="Please enter your email:").pack(pady=10)
    email_entry = ttk.Entry(frame, width=40)
    email_entry.pack(pady=10)

    ttk.Label(frame, text="Confirm your email:").pack(pady=10)
    confirm_email_entry = ttk.Entry(frame, width=40)
    confirm_email_entry.pack(pady=10)

    def validate_email():
        entered_email = email_entry.get().strip()
        confirmed_email = confirm_email_entry.get().strip()

        if entered_email and confirmed_email:
            if entered_email == confirmed_email:
                # Save the email to a file
                email_path = Path(os.getenv("APPDATA")) / "NTi" / ".email"
                email_path.parent.mkdir(parents=True, exist_ok=True)

                with open(email_path, "w") as f:
                    f.write(entered_email)  # Save email

                messagebox.showinfo("Email", "Email validated successfully!")
                email_window.destroy()
            else:
                messagebox.showerror("Error", "Emails do not match. Please try again.")
        else:
            messagebox.showerror("Error", "Please enter both a valid email and confirm it.")

    ttk.Button(frame, text="Submit", command=validate_email).pack(pady=20)

    email_window.mainloop()

def delete_installer():
    # Delete the installer executable after installation is complete
    try:
        time.sleep(1)  # Wait for a moment to ensure the installer has finished any final tasks
        os.remove(INSTALLER_PATH)
        print("Installer deleted successfully.")
    except Exception as e:
        print(f"Error deleting installer: {e}")

def launch_application():
    try:
        # Launch the application after installation
        subprocess.run([f'"{INSTALL_DIR}\\NTiMaintenance.exe"'], check=True)
    except Exception as e:
        print(f"Error launching application: {e}")

def show_maintenance_message():
    # Show a message box to inform the user about the maintenance schedule
    message = (
        "This is what it will look like when a tune-up is being performed.\n"
        "It will happen once weekly at 9 PM on Sundays.\n"
        "Please leave your computer on during this time."
    )
    messagebox.showinfo("Scheduled Maintenance", message)

def main():
    # Automatically call install() when the EXE is run
    install()

if __name__ == '__main__':
    main()
