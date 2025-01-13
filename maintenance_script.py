import os
import subprocess
import sys
import logging
from multiprocessing import Process
import platform
import psutil
from cpuinfo import cpuinfo 

# Setup logging to both console and a file
log_filename = 'maintenance_log.txt'
logging.basicConfig(level=logging.DEBUG, 
                    format='%(asctime)s - %(message)s',
                    handlers=[
                        logging.FileHandler(log_filename),  # Log to file
                        logging.StreamHandler()             # Log to console
                    ])

# Variable to enable/disable SFC for testing purposes
sfc_enabled = False  # Set to False to skip SFC scan for testing

# Function to install packages locally in the project directory using requirements.txt
def install_packages_from_requirements():
    script_dir = os.path.dirname(os.path.realpath(__file__))  # Get the directory where the script is located
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

# Collect Memory (RAM) Information
def get_memory_details():
    memory_info = psutil.virtual_memory()
    memory_details['total_memory'] = memory_info.total

# Collect CPU Information (Only the processor name)
def get_cpu_details():
    cpu_brand = _read_windows_registry_key(r"Hardware\Description\System\CentralProcessor\0", "ProcessorNameString")
    return cpu_brand
    
# Collect OS Version Information
def get_os_version():
    system_info['os_version'] = platform.version()

# Collect Internet Speed (This will require external library like speedtest-cli)
def get_internet_speed():
    try:
        import speedtest
        st = speedtest.Speedtest()
        download_speed = st.download() / 1_000_000  # Convert to Mbps
        upload_speed = st.upload() / 1_000_000  # Convert to Mbps
        system_info['internet_speed'] = f"{download_speed:.2f} Mbps / {upload_speed:.2f} Mbps"
    except Exception as e:
        system_info['internet_speed'] = f"Error fetching speed: {e}"

# Collect Router Speed (this may need manual checking or router-specific software)
def get_router_speed():
    # For the sake of example, using a placeholder. You'd likely need a specific API or method.
    system_info['router_speed'] = "1000 Mbps"

# Placeholder maintenance tasks
def disk_cleanup():
    logging.info("Starting Disk Cleanup...")
    subprocess.run(["cleanmgr", "/sagerun:1"])
    logging.info("Disk Cleanup completed successfully.")

def sfc_scan():
    if sfc_enabled:
        logging.info("Starting SFC...")
        subprocess.run(["sfc", "/scannow"])
        logging.info("SFC completed successfully.")
    else:
        logging.info("SFC is skipped for testing purposes.")

def defragmentation():
    logging.info("Starting Defragmentation...")
    
    # Run defrag command with retrim
    defrag_output = subprocess.run(
        ["defrag", "C:", "/O", "/L"], capture_output=True, text=True
    )

    # Capture the output
    output = defrag_output.stdout
    logging.info(output)  # Print output for debugging

    # Parse the trimmed space from the output (example)
    trimmed_space = None
    for line in output.splitlines():
        if "Total space trimmed" in line:
            # Extract the number after the equals sign
            parts = line.split("=")
            if len(parts) > 1:
                # Get the last part and remove the " GB" to get only the number
                trimmed_space_str = parts[1].strip()
                trimmed_space = trimmed_space_str.replace(' GB', '')  # Remove " GB" from the string
                
                # Now convert to float
                try:
                    trimmed_space = float(trimmed_space)
                except ValueError:
                    logging.error(f"Error converting trimmed space '{trimmed_space_str}' to float.")

    if trimmed_space:
        storage_details['trimmed_space'] = trimmed_space
    logging.info(f"Defragmentation completed successfully. Trimmed space: {trimmed_space} GB")




# Start each maintenance task in a separate process
def run_maintenance():
    # Run tasks in separate processes
    processes = []

    # Start Disk Cleanup
    p1 = Process(target=disk_cleanup)
    p1.start()
    processes.append(p1)

    # Start SFC scan if enabled
    if sfc_enabled:
        p2 = Process(target=sfc_scan)
        p2.start()
        processes.append(p2)

    # Start Defragmentation
    p3 = Process(target=defragmentation)
    p3.start()
    processes.append(p3)

    # Wait for all processes to finish
    for p in processes:
        p.join()

    # Get final storage (drives) and memory (RAM) details after optimization
    get_storage_details()
    get_memory_details()
    get_cpu_details()
    get_os_version()
    get_internet_speed()
    get_router_speed()

    # Log the details after optimization
    logging.info("Post-maintenance Report:")
    logging.info(f"Total RAM: {memory_details['total_memory'] / (1024**3):.2f} GB")
    logging.info(f"Storage - Volume Size: {storage_details['volume_size'] / (1024**3):.2f} GB, "
                 f"Free Space: {storage_details['free_space'] / (1024**3):.2f} GB, "
                 f"Trimmed Space: {storage_details['trimmed_space'] / (1024**3):.2f} GB")
    logging.info(f"CPU: {cpu_details['cpu_name']}")
    logging.info(f"OS Version: {system_info['os_version']}")
    logging.info(f"Internet Speed: {system_info['internet_speed']}")
    logging.info(f"Router Speed: {system_info['router_speed']}")

# Run maintenance
if __name__ == "__main__":
    logging.info("Starting maintenance tasks...")
    run_maintenance()
    logging.info("Maintenance tasks completed.")

    # Wait for user input to keep the window open
    close = input("Press enter to exit...")
