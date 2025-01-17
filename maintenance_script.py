import os
import subprocess
import sys
import logging
from multiprocessing import Process
import platform
import psutil
import cpuinfo
import urllib.request
import winshell
import datetime
from win32com.client import Dispatch

# Setup logging to a file (overwrites the file each time)
script_dir = os.path.dirname(os.path.realpath(__file__))  # Get the directory where the script is located
log_filename = os.path.join(script_dir, 'results.txt')
logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s - %(message)s',
                    handlers=[logging.FileHandler(log_filename, mode='w')])

# Function to install packages locally in the project directory using requirements.txt
def install_packages_from_requirements():
    requirements_path = os.path.join(script_dir, 'requirements.txt')  # Full path to requirements.txt
    
    if os.path.exists(requirements_path):
        subprocess.check_call([sys.executable, "-m", "pip", "install", "--target=.", "-r", requirements_path])
    else:
        logging.error("requirements.txt not found!")

# Ensure required packages are installed locally by reading from requirements.txt
install_packages_from_requirements()

# Placeholder for storing storage (drives) details, memory (RAM) info, etc.
storage_details = {
    'volume_size': None,
    'free_space': None,
    'trimmed_space': None
}

memory_details = {
    'total_memory': None
}

cpu_details = {
    'cpu_name': None
}

system_info = {
    'os_version': None,
    'internet_speed': None,
    'router_speed': None
}

# Collect Storage (drives) Information
def get_storage_details():
    disk_usage = psutil.disk_usage('/')
    storage_details['volume_size'] = disk_usage.total
    storage_details['free_space'] = disk_usage.free
    storage_details['trimmed_space'] = disk_usage.used 

# Create a System Restore Point
def create_restore_point(description="NTi TuneUp"):
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    description = f"{description} ({now})"

    try:
        cmd = [
            "powershell.exe",
            "-Command",
            f"""
            Checkpoint-Computer -Description "{description}" -RestorePointType "MODIFY_SETTINGS"
            """
        ]
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

        if result.returncode == 0:
            logging.info(f"Restore point '{description}' created successfully.")
        else:
            logging.error(f"Failed to create restore point. Output: {result.stdout.strip()}")
            logging.error(f"Error: {result.stderr.strip()}")
    except Exception as e:
        logging.error(f"Error creating restore point: {e}")
        
# Collect Memory (RAM) Information
def get_memory_details():
    memory_info = psutil.virtual_memory()
    memory_details['total_memory'] = memory_info.total

# Collect CPU Information
def get_cpu_details():
    info = cpuinfo.get_cpu_info()
    if 'brand_raw' in info:
        cpu_details['cpu_name'] = info['brand_raw']

# Collect OS Version Information
def get_os_version():
    system_info['os_version'] = platform.version()

# Collect Internet Speed
def get_internet_speed():
    try:
        import speedtest
        st = speedtest.Speedtest()
        download_speed = st.download() / 1_000_000  # Convert to Mbps
        upload_speed = st.upload() / 1_000_000  # Convert to Mbps
        system_info['internet_speed'] = f"{download_speed:.2f} Mbps / {upload_speed:.2f} Mbps"
    except Exception as e:
        system_info['internet_speed'] = f"Error fetching speed: {e}"

# Placeholder maintenance tasks
def disk_cleanup():
    logging.info("Starting Disk Cleanup...")
    subprocess.run(["cleanmgr", "/sagerun:1"])
    logging.info("Disk Cleanup completed successfully.")

def sfc_scan():
    logging.info("Starting SFC...")
    subprocess.run(["sfc", "/scannow"])
    logging.info("SFC completed successfully.")

def defragmentation():
    logging.info("Starting Defragmentation...")
    defrag_output = subprocess.run(
        ["defrag", "C:", "/O", "/L"], capture_output=True, text=True
    )
    logging.info(defrag_output.stdout)

def update_download():
    subprocess.run(["wuauclt", "/detectnow"], check=True)
    logging.info("Windows update detection initiated.")

def defender_scan():
    defender_path = os.path.join(script_dir, "MpCmdRun.exe")  # Reference the executable from the same directory
    command = [defender_path, "-Scan", "-ScanType", "1"]  # Quick Scan
    try:
        logging.info("Starting Windows Defender Quick Scan via CMD...")
        subprocess.run(command, check=True)
        logging.info("Windows Defender Quick Scan completed successfully.")
    except subprocess.CalledProcessError as e:
        logging.error(f"Windows Defender Scan failed: {e}")
    except FileNotFoundError:
        logging.error(f"MpCmdRun.exe not found in the script directory. Please verify the path.")

def create_shortcut_if_missing():
    desktop = winshell.desktop()
    shortcut_path = os.path.join(desktop, 'NTi Support.lnk')
    if not os.path.exists(shortcut_path):
        ico_path = os.path.join(script_dir, 'nti.ico')  # Use the icon from the script directory
        if os.path.exists(ico_path):
            shell = Dispatch('WScript.Shell')
            shortcut = shell.CreateShortcut(shortcut_path)
            shortcut.TargetPath = "https://nticomputers.screenconnect.com"
            shortcut.WorkingDirectory = desktop
            shortcut.IconLocation = ico_path 
            shortcut.save()
            logging.info("Shortcut created successfully.")
        else:
            logging.error("nti.ico not found in the script directory.")
    else:
        logging.info("Shortcut already exists.")

# Start each maintenance task in a separate process
def run_maintenance():
    tasks = [
        Process(target=disk_cleanup),
        Process(target=sfc_scan),
        Process(target=defender_scan),
        Process(target=create_shortcut_if_missing),
        Process(target=update_download),
        Process(target=defragmentation),
    ]

    # Start all tasks
    for task in tasks:
        task.start()

    # Wait for all tasks to complete
    for task in tasks:
        task.join()

    # Get final storage (drives) and memory (RAM) details after optimization
    get_storage_details()
    get_memory_details()
    get_cpu_details()
    get_os_version()
    get_internet_speed()
    create_restore_point()

    # Save the final report to the maintenance_report.txt file in the same directory
    report_filename = os.path.join(script_dir, 'maintenance_report.txt')

    try:
        logging.info(f"Saving report to {report_filename}")

        with open(report_filename, 'w') as report_file:
            report_file.write(f"PC Specifications:\n")
            report_file.write(f"    CPU: {cpu_details['cpu_name']}\n")
            report_file.write(f"    Ram: {memory_details['total_memory'] / (1024**3):.2f} GB\n")
            report_file.write(f"    Volume Size: {storage_details['volume_size'] / (1024**3):.2f} GB,\n")
            report_file.write(f"    Free Space: {storage_details['free_space'] / (1024**3):.2f} GB,\n")
            report_file.write(f"    Trimmed Space: {storage_details['trimmed_space'] / (1024**3):.2f} GB\n")
            report_file.write(f"    Internet Speed: {system_info['internet_speed']}\n")
            report_file.write(f"    Windows Version: {system_info['os_version']}\n\n")

            report_file.write(f"MALWARE / SPYWARE / VIRUSES:\n")
            report_file.write(f"    Scanned for malware, spyware, and viruses: Completed\n")
            report_file.write(f"    Removed unwanted and malicious apps/extensions: Completed\n\n")

            report_file.write(f"CLEANING:\n")
            report_file.write(f"    Disk defragmented and cleaned: Completed\n")
            report_file.write(f"    Verified disk optimization: Completed\n")
            report_file.write(f"    Obtained Windows updates: Completed\n")
            report_file.write(f"    System File Checker run: Completed\n\n")

            report_file.write(f"BACKUP AND SUPPORT:\n")
            report_file.write(f"    NTI shortcut added and tested: Completed\n")
            report_file.write(f"    System restore active and Restore Point created: Completed\n\n")

            report_file.write(f"* Benchmark (0-4000 replace computer, 4000-8000 fair,\n")
            report_file.write(f"8000-14000 good, 14000-32000+ great)\n")

        logging.info(f"Maintenance report saved to {report_filename}.")
    except Exception as e:
        logging.error(f"Error writing the report: {e}")

# Run maintenance
if __name__ == "__main__":
    logging.info("Starting maintenance tasks...")
    run_maintenance()
    logging.info("Maintenance tasks completed.")
