import os
import subprocess
import sys
import logging
from multiprocessing import Process
import platform
import psutil
import cpuinfo
import datetime
import urllib.request
import winshell
from python_licensing import licensed

# Setup logging to a file (overwrites the file each time)
log_filename = 'results.txt'
logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s - %(message)s',
                    handlers=[logging.FileHandler(log_filename, mode='w')])

# Global data storage for system details
storage_details = {'volume_size': None, 'free_space': None, 'used_space': None}
memory_details = {'total_memory': None}
cpu_details = {'cpu_name': None}
system_info = {'os_version': None, 'internet_speed': None}

# Functions for collecting system information
def get_storage_details():
    """Gather details about storage (disk usage)."""
    disk_usage = psutil.disk_usage('/')
    storage_details.update({
        'volume_size': disk_usage.total,
        'free_space': disk_usage.free,
        'used_space': disk_usage.used
    })

def get_memory_details():
    """Retrieve total memory (RAM)."""
    memory_info = psutil.virtual_memory()
    memory_details['total_memory'] = memory_info.total

def get_cpu_details():
    """Fetch CPU details, specifically the processor name."""
    info = cpuinfo.get_cpu_info()
    cpu_details['cpu_name'] = info.get('brand_raw', 'Unknown CPU')

def get_os_version():
    """Get the OS version."""
    system_info['os_version'] = platform.version()

def get_internet_speed():
    """Measure and record internet speed."""
    try:
        import speedtest
        st = speedtest.Speedtest()
        download_speed = st.download() / 1_000_000  # Mbps
        upload_speed = st.upload() / 1_000_000  # Mbps
        system_info['internet_speed'] = f"{download_speed:.2f} Mbps / {upload_speed:.2f} Mbps"
    except Exception as e:
        system_info['internet_speed'] = f"Error fetching speed: {e}"

def create_restore_point(description="NTi TuneUp"):
    """Create a system restore point."""
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    description = f"{description} ({now})"
    try:
        cmd = [
            "powershell.exe",
            "-Command",
            f"Checkpoint-Computer -Description '{description}' -RestorePointType 'MODIFY_SETTINGS'"
        ]
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

        if result.returncode == 0:
            logging.info(f"Restore point '{description}' created successfully.")
        else:
            logging.error(f"Failed to create restore point. Error: {result.stderr.strip()}")
    except Exception as e:
        logging.error(f"Error creating restore point: {e}")

# Maintenance task functions
def disk_cleanup():
    logging.info("Starting Disk Cleanup...")
    subprocess.run(["cleanmgr", "/sagerun:1"])
    logging.info("Disk Cleanup completed successfully.")

def run_sfc_scan():
    logging.info("Starting SFC Scan...")
    subprocess.run(["sfc", "/scannow"])
    logging.info("SFC Scan completed successfully.")

def run_defragmentation():
    logging.info("Starting Disk Defragmentation...")
    defrag_output = subprocess.run(["defrag", "C:", "/O", "/L"], capture_output=True, text=True)
    logging.info(defrag_output.stdout)

def update_windows():
    logging.info("Starting Windows Update detection...")
    subprocess.run(["wuauclt", "/detectnow"], check=True)
    logging.info("Windows Update detection initiated successfully.")

def run_defender_scan():
    defender_path = r"C:\Program Files\Windows Defender\MpCmdRun.exe"
    command = [defender_path, "-Scan", "-ScanType", "1"]  # Quick Scan
    try:
        logging.info("Starting Windows Defender Quick Scan...")
        subprocess.run(command, check=True)
        logging.info("Windows Defender Quick Scan completed successfully.")
    except subprocess.CalledProcessError as e:
        logging.error(f"Windows Defender Scan failed: {e}")
    except FileNotFoundError:
        logging.error(f"Windows Defender not found at {defender_path}. Please verify the path.")

def create_nti_shortcut():
    desktop = winshell.desktop()
    shortcut_path = os.path.join(desktop, 'NTi Support.lnk')
    if not os.path.exists(shortcut_path):
        script_dir = os.path.dirname(os.path.abspath(__file__))
        ico_path = os.path.join(script_dir, 'nti.ico')  
        if os.path.exists(ico_path):
            from win32com.client import Dispatch
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

# Run maintenance tasks and save report
@licensed('http://localhost:5000')
def run_maintenance():
    tasks = [
        Process(target=disk_cleanup),
        Process(target=run_sfc_scan),
        Process(target=run_defender_scan),
        Process(target=create_nti_shortcut),
        Process(target=update_windows),
        Process(target=run_defragmentation),
    ]

    # Start and join tasks
    for task in tasks:
        task.start()
    for task in tasks:
        task.join()

    # Collect updated system details
    get_storage_details()
    get_memory_details()
    get_cpu_details()
    get_os_version()
    get_internet_speed()
    create_restore_point()

    # Save the final report
    report_path = os.path.join(os.path.dirname(__file__), 'maintenance_report.txt')
    try:
        with open(report_path, 'w') as report_file:
            report_file.write(f"System Report:\n")
            report_file.write(f"  CPU: {cpu_details['cpu_name']}\n")
            report_file.write(f"  RAM: {memory_details['total_memory'] / (1024**3):.2f} GB\n")
            report_file.write(f"  Storage: {storage_details['volume_size'] / (1024**3):.2f} GB total, "
                              f"{storage_details['free_space'] / (1024**3):.2f} GB free\n")
            report_file.write(f"  Internet Speed: {system_info['internet_speed']}\n")
            report_file.write(f"  OS Version: {system_info['os_version']}\n")
        logging.info(f"Maintenance report saved at {report_path}.")
    except Exception as e:
        logging.error(f"Error saving the maintenance report: {e}")

# Execute maintenance tasks
if __name__ == "__main__":
    logging.info("Starting maintenance...")
    run_maintenance()
    logging.info("Maintenance completed.")
