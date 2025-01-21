import os
import shutil
import subprocess
import sys
import tkinter as tk
from tkinter import ttk, messagebox
from pathlib import Path
import time
import ctypes
#pyinstaller --onefile --noconsole --icon=nti.ico NTiMaintenance.py

APP_NAME = "NTi AutoMaintenance"
INSTALL_DIR = os.path.join(os.environ['PROGRAMFILES'], APP_NAME)
LICENSE_FILE = os.path.expanduser(r'~\AppData\Roaming\NTi\.license_key')

# Adjust paths based on whether we are running as a script or a bundled executable
if getattr(sys, 'frozen', False):
    base_path = sys._MEIPASS  # Bundled executable directory
else:
    base_path = os.path.dirname(__file__)  # Script directory

ICON_PATH = os.path.join(base_path, 'nti.ico')
EXECUTABLE_PATH = os.path.join(base_path, 'NTiMaintenance.exe')
INSTALLER_PATH = sys.argv[0]  # Path to the current installer executable

# Check for administrator privileges
def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin() != 0
    except Exception:
        return False

# Installation process
def install():
    if not is_admin():
        # Re-run the script as an administrator if not already running with admin privileges
        ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, sys.argv[0], None, 1)
        sys.exit(0)  # Exit the current process once admin privileges are requested

    # Create installation window with progress bar
    progress_window = tk.Tk()
    progress_window.title("Installation Progress")
    progress_window.geometry("400x200")
    progress_window.resizable(False, False)

    try:
        progress_window.iconbitmap(ICON_PATH)
    except Exception as e:
        print(f"Failed to load icon: {e}")

    # Apply styles
    style = ttk.Style()
    style.theme_use("clam")
    style.configure("TLabel", font=("Arial", 12))
    style.configure("TButton", font=("Arial", 10))
    style.configure("TProgressbar", thickness=30)

    # Layout for progress bar and label
    frame = ttk.Frame(progress_window, padding=20)
    frame.pack(fill="both", expand=True)

    ttk.Label(frame, text="Installing, please wait...").pack(pady=10)
    progress = ttk.Progressbar(frame, mode="indeterminate", length=300)
    progress.pack(pady=20)
    progress.start()

    def finish_installation():
        progress.stop()
        progress_window.destroy()
        show_maintenance_message()
        messagebox.showinfo("Success", f"{APP_NAME} installed successfully!")
        launch_application()

    # Run installation steps in the background
    def run_installation_steps():
        # Step 1: Check if the installation directory exists, create it if not
        if not os.path.exists(INSTALL_DIR):
            os.makedirs(INSTALL_DIR)

        # Step 2: Copy executable and icon to the installation directory
        if os.path.exists(EXECUTABLE_PATH):
            shutil.copy(EXECUTABLE_PATH, INSTALL_DIR)
        else:
            messagebox.showerror("Error", f"Error: {EXECUTABLE_PATH} not found.")
            progress_window.destroy()
            return

        if os.path.exists(ICON_PATH):
            shutil.copy(ICON_PATH, INSTALL_DIR)
        else:
            messagebox.showerror("Error", f"Error: {ICON_PATH} not found.")
            progress_window.destroy()
            return

        # Step 3: Prompt for license key and email
        get_license_key_and_email()

        # Step 4: Create scheduled tasks for maintenance
        create_scheduled_tasks()

        # Step 5: Delete the installer executable after installation
        delete_installer()

        finish_installation()

    # Run installation steps in a separate thread to avoid freezing GUI
    progress_window.after(100, run_installation_steps)
    progress_window.mainloop()

# Create scheduled tasks
def create_scheduled_tasks():
    task_command = f'"{INSTALL_DIR}\\NTiMaintenance.exe" run_maintenance'
    try:
        subprocess.run(['schtasks', '/Create', '/SC', 'WEEKLY', '/D', 'SUN', '/TN', f'{APP_NAME} Weekly Maintenance',
                        '/TR', task_command, '/RL', 'HIGHEST', '/ST', '23:00', '/RU', 'SYSTEM'], check=True)
    except subprocess.SubprocessError as e:
        print(f"Error creating weekly maintenance task: {e}")

    try:
        subprocess.run(['schtasks', '/Create', '/SC', 'ONLOGON', '/TN', f'{APP_NAME} Startup',
                        '/TR', f'"{INSTALL_DIR}\\NTiMaintenance.exe"', '/RL', 'HIGHEST'], check=True)
    except subprocess.SubprocessError as e:
        print(f"Error creating startup task: {e}")

# Prompt user for license key and email
def get_license_key_and_email():
    license_window = tk.Tk()
    license_window.title("Enter License Key and Email")
    license_window.geometry("400x250")
    license_window.resizable(False, False)

    try:
        license_window.iconbitmap(ICON_PATH)
    except Exception as e:
        print(f"Failed to load icon: {e}")

    # Apply styles
    style = ttk.Style()
    style.theme_use("clam")
    style.configure("TLabel", font=("Arial", 12))
    style.configure("TButton", font=("Arial", 10))
    style.configure("TEntry", font=("Arial", 12), padding=5)

    frame = ttk.Frame(license_window, padding=20)
    frame.pack(fill="both", expand=True)

    ttk.Label(frame, text="Please enter your license key:").pack(pady=10)
    license_entry = ttk.Entry(frame, width=40)
    license_entry.pack(pady=10)

    def validate_license():
        entered_key = license_entry.get().strip()
        if entered_key:
            license_key_path = Path(os.getenv("APPDATA")) / "NTi" / ".license_key"
            license_key_path.parent.mkdir(parents=True, exist_ok=True)
            with open(license_key_path, "w") as f:
                f.write(entered_key)
            license_window.destroy()
            get_email()
        else:
            messagebox.showerror("Error", "Please enter a valid license key.")

    ttk.Button(frame, text="Submit", command=validate_license).pack(pady=20)

    license_window.mainloop()

# Prompt user for email
def get_email():
    email_window = tk.Tk()
    email_window.title("Enter Email")
    email_window.geometry("400x300")
    email_window.resizable(False, False)

    try:
        email_window.iconbitmap(ICON_PATH)
    except Exception as e:
        print(f"Failed to load icon: {e}")

    style = ttk.Style()
    style.theme_use("clam")
    style.configure("TLabel", font=("Arial", 12))
    style.configure("TButton", font=("Arial", 10))
    style.configure("TEntry", font=("Arial", 12), padding=5)

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
        if entered_email and entered_email == confirmed_email:
            email_path = Path(os.getenv("APPDATA")) / "NTi" / ".email"
            email_path.parent.mkdir(parents=True, exist_ok=True)
            with open(email_path, "w") as f:
                f.write(entered_email)
            messagebox.showinfo("Success", "Email validated successfully!")
            email_window.destroy()
        else:
            messagebox.showerror("Error", "Emails do not match or are invalid. Please try again.")

    ttk.Button(frame, text="Submit", command=validate_email).pack(pady=20)

    email_window.mainloop()

# Delete installer
def delete_installer():
    try:
        time.sleep(1)
        os.remove(INSTALLER_PATH)
        print("Installer deleted successfully.")
    except Exception as e:
        print(f"Error deleting installer: {e}")

# Launch the application
def launch_application():
    try:
        subprocess.run([os.path.join(INSTALL_DIR, "NTiMaintenance.exe")], check=True)
    except Exception as e:
        print(f"Error launching application: {e}")

# Inform user about scheduled maintenance
def show_maintenance_message():
    message = (
        "Maintenance will be performed weekly at 11 PM on Sundays.\n"
        "Please ensure your computer is turned on during this time."
    )
    messagebox.showinfo("Scheduled Maintenance", message)

# Main function
def main():
    install()

if __name__ == '__main__':
    main()
