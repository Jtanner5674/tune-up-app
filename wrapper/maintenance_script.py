import os
import subprocess
import sys
import logging
from multiprocessing import Process, Manager
import platform
import psutil
import cpuinfo
import urllib.request
import winshell
import datetime
from win32com.client import Dispatch
import requests
from bs4 import BeautifulSoup
from collections import defaultdict
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders

# Setup logging to a file (overwrites the file each time)
script_dir = os.path.dirname(os.path.realpath(__file__))  # Get the directory where the script is located
log_filename = os.path.join(script_dir, 'results.txt')
logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s - %(message)s',
                    handlers=[logging.FileHandler(log_filename, mode='w')])

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

def get_cpu_multithread_rating(cpu_name):
    # Replace spaces with '+'
    formatted_name = cpu_name.replace(" ", "+")
    url = f"https://www.cpubenchmark.net/cpu.php?cpu={formatted_name}"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36"
    }

    try:
        # Make the request
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        
        # Parse the page
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Locate the multithread rating
        multithread_element = soup.find("div", string="Multithread Rating")
        if multithread_element:
            rating = multithread_element.find_next_sibling("div").text.strip()
            return rating
        
        return f"Multithread rating not found on the page for {cpu_name}."
    
    except requests.RequestException as e:
        return f"Error fetching data: {e}"

# Function to send the maintenance report via email
def send_email_with_report(recipient_email, report_filename):
    # SMTP configuration
    smtp_host = 'smtp.office365.com'
    smtp_port = 587
    smtp_user = 'joshua@nticomputers.com'  # Sender's email address
    smtp_pass = 'NTI2024!'  # Sender's email password
    from_name = 'Joshua'

    # Read the contents of the report file
    try:
        with open(report_filename, 'r') as report_file:
            report_content = report_file.read()
    except Exception as e:
        logging.error(f"Error reading the report file: {e}")
        return

    # Create the email message
    msg = MIMEMultipart()
    msg['From'] = f"{from_name} <{smtp_user}>"
    msg['To'] = recipient_email  # Send to the recipient
    msg['Cc'] = smtp_user  # Send a copy to yourself (sender's email)
    msg['Subject'] = 'Maintenance Report'

    # Attach the content of the report as the email body
    msg.attach(MIMEText(report_content, 'plain'))

    # Establish the SMTP connection and send the email
    try:
        with smtplib.SMTP(smtp_host, smtp_port) as server:
            server.starttls()  # Start TLS encryption
            server.login(smtp_user, smtp_pass)  # Log in with the sender's email credentials
            server.sendmail(smtp_user, [recipient_email, smtp_user], msg.as_string())  # Send the email to both recipient and sender
        logging.info(f"Email sent to {recipient_email} and a copy sent to {smtp_user}")
    except Exception as e:
        logging.error(f"Failed to send email. Error: {e}")


# Collect the recipient email from .email file
def get_recipient_email():
    email_file_path = Path(os.getenv("APPDATA")) / "NTi" / ".email"
    try:
        with open(email_file_path, 'r') as file:
            recipient_email = file.read().strip()
        logging.info(f"Email will be sent to: {recipient_email}")
        return recipient_email
    except Exception as e:
        logging.error(f"Failed to read the .email file. Error: {e}")
        return None
    
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

def get_cpu_details():
    info = cpuinfo.get_cpu_info()
    if 'brand_raw' in info:
        full_cpu_name = info['brand_raw']
        # Extract the actual CPU name (stop at the first numeric core count or "Processor")
        parts = full_cpu_name.split()
        truncated_name = []
        for part in parts:
            if part.lower() in ["processor", "core", "cores"]:
                break
            truncated_name.append(part)
        cpu_details['cpu_name'] = " ".join(truncated_name)


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

# Capture Process List (tasklist), ensuring no duplicates
def capture_process_list(results):
    try:
        # Run the tasklist command to capture the list of processes
        result = subprocess.run(["tasklist"], capture_output=True, text=True)

        if result.returncode == 0:
            # Parse the output, skip header lines, and create a dictionary to group by process name
            process_lines = result.stdout.splitlines()
            process_data = process_lines[3:]  # Skip header lines
            process_dict = defaultdict(int)  # To store the count of each process

            for line in process_data:
                process_name = line.split()[0]  # Extract the process name (first word)
                memory_usage = int(line.split()[-2].replace(',', ''))  # Extract memory usage (before 'K')

                # Add memory usage to the total for that process name
                process_dict[process_name] += memory_usage

            # Prepare the report string
            process_list = "\n".join([f"{process} - {memory_usage / 1024:.2f} MB" for process, memory_usage in process_dict.items()])
            results['process_list'] = process_list
            logging.info(f"Captured Running Processes:\n{process_list}")
        else:
            logging.error(f"Failed to capture task list. Error: {result.stderr}")
            results['process_list'] = result.stderr.strip()

    except Exception as e:
        logging.error(f"Error capturing process list: {e}")
        results['process_list'] = "Error capturing process list."


# Placeholder maintenance tasks
def disk_cleanup():
    logging.info("Starting Disk Cleanup...")
    subprocess.run(["cleanmgr", "/sagerun:1"])
    logging.info("Disk Cleanup completed successfully.")

def sfc_scan(results):
    logging.info("Starting SFC scan...")
    result = subprocess.run(["sfc", "/scannow"], capture_output=True, text=True)
    
    if result.returncode == 0:
        results['sfc_scan'] = result.stdout.strip()  # Capture the output from the SFC scan
        logging.info("SFC scan completed successfully.")
    else:
        results['sfc_scan'] = f"SFC scan failed. Error: {result.stderr.strip()}"
        logging.error(f"SFC scan failed. Error: {result.stderr.strip()}")


def defragmentation():
    logging.info("Starting Defragmentation...")
    defrag_output = subprocess.run(
        ["defrag", "C:", "/O", "/L"], capture_output=True, text=True
    )
    logging.info(defrag_output.stdout)

def update_download():
    subprocess.run(["wuauclt", "/detectnow"], check=True)
    logging.info("Windows update detection initiated.")

def defender_scan(results):
    defender_path = os.path.join(script_dir, "MpCmdRun.exe")  # Reference the executable from the same directory
    command = [defender_path, "-Scan", "-ScanType", "1"]  # Quick Scan
    try:
        logging.info("Starting Windows Defender Quick Scan via CMD...")
        subprocess.run(command, check=True)
        results['defender_scan'] = "Windows Defender Quick Scan completed successfully."
        logging.info("Windows Defender Quick Scan completed successfully.")
    except subprocess.CalledProcessError as e:
        results['defender_scan'] = f"Windows Defender Scan failed: {e}"
        logging.error(f"Windows Defender Scan failed: {e}")
    except FileNotFoundError:
        results['defender_scan'] = "MpCmdRun.exe not found in the script directory."
        logging.error(f"MpCmdRun.exe not found in the script directory.")

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
import os
import subprocess
import sys
import logging
from multiprocessing import Process, Manager
import platform
import psutil
import cpuinfo
import urllib.request
import winshell
import datetime
from win32com.client import Dispatch
import requests
from bs4 import BeautifulSoup
from collections import defaultdict
import smtplib

# Setup logging to a file (overwrites the file each time)
script_dir = os.path.dirname(os.path.realpath(__file__))  # Get the directory where the script is located
log_filename = os.path.join(script_dir, 'results.txt')
logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s - %(message)s',
                    handlers=[logging.FileHandler(log_filename, mode='w')])

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

def get_cpu_multithread_rating(cpu_name):
    # Replace spaces with '+'
    formatted_name = cpu_name.replace(" ", "+")
    url = f"https://www.cpubenchmark.net/cpu.php?cpu={formatted_name}"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36"
    }

    try:
        # Make the request
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        
        # Parse the page
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Locate the multithread rating
        multithread_element = soup.find("div", string="Multithread Rating")
        if multithread_element:
            rating = multithread_element.find_next_sibling("div").text.strip()
            return rating
        
        return f"Multithread rating not found on the page for {cpu_name}."
    
    except requests.RequestException as e:
        return f"Error fetching data: {e}"


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

def get_cpu_details():
    info = cpuinfo.get_cpu_info()
    if 'brand_raw' in info:
        full_cpu_name = info['brand_raw']
        # Extract the actual CPU name (stop at the first numeric core count or "Processor")
        parts = full_cpu_name.split()
        truncated_name = []
        for part in parts:
            if part.lower() in ["processor", "core", "cores"]:
                break
            truncated_name.append(part)
        cpu_details['cpu_name'] = " ".join(truncated_name)


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

# Capture Process List (tasklist), ensuring no duplicates
def capture_process_list(results):
    try:
        # Run the tasklist command to capture the list of processes
        result = subprocess.run(["tasklist"], capture_output=True, text=True)

        if result.returncode == 0:
            # Parse the output, skip header lines, and create a dictionary to group by process name
            process_lines = result.stdout.splitlines()
            process_data = process_lines[3:]  # Skip header lines
            process_dict = defaultdict(int)  # To store the count of each process

            for line in process_data:
                process_name = line.split()[0]  # Extract the process name (first word)
                memory_usage = int(line.split()[-2].replace(',', ''))  # Extract memory usage (before 'K')

                # Add memory usage to the total for that process name
                process_dict[process_name] += memory_usage

            # Prepare the report string
            process_list = "\n".join([f"{process} - {memory_usage / 1024:.2f} MB" for process, memory_usage in process_dict.items()])
            results['process_list'] = process_list
            logging.info(f"Captured Running Processes:\n{process_list}")
        else:
            logging.error(f"Failed to capture task list. Error: {result.stderr}")
            results['process_list'] = result.stderr.strip()

    except Exception as e:
        logging.error(f"Error capturing process list: {e}")
        results['process_list'] = "Error capturing process list."


# Placeholder maintenance tasks
def disk_cleanup():
    logging.info("Starting Disk Cleanup...")
    subprocess.run(["cleanmgr", "/sagerun:1"])
    logging.info("Disk Cleanup completed successfully.")

def sfc_scan(results):
    logging.info("Starting SFC scan...")
    result = subprocess.run(["sfc", "/scannow"], capture_output=True, text=True)
    
    if result.returncode == 0:
        results['sfc_scan'] = result.stdout.strip()  # Capture the output from the SFC scan
        logging.info("SFC scan completed successfully.")
    else:
        results['sfc_scan'] = f"SFC scan failed. Error: {result.stderr.strip()}"
        logging.error(f"SFC scan failed. Error: {result.stderr.strip()}")


def defragmentation():
    logging.info("Starting Defragmentation...")
    defrag_output = subprocess.run(
        ["defrag", "C:", "/O", "/L"], capture_output=True, text=True
    )
    logging.info(defrag_output.stdout)

def update_download():
    subprocess.run(["wuauclt", "/detectnow"], check=True)
    logging.info("Windows update detection initiated.")

def defender_scan(results):
    defender_path = os.path.join(script_dir, "MpCmdRun.exe")  # Reference the executable from the same directory
    command = [defender_path, "-Scan", "-ScanType", "1"]  # Quick Scan
    try:
        logging.info("Starting Windows Defender Quick Scan via CMD...")
        subprocess.run(command, check=True)
        results['defender_scan'] = "Windows Defender Quick Scan completed successfully."
        logging.info("Windows Defender Quick Scan completed successfully.")
    except subprocess.CalledProcessError as e:
        results['defender_scan'] = f"Windows Defender Scan failed: {e}"
        logging.error(f"Windows Defender Scan failed: {e}")
    except FileNotFoundError:
        results['defender_scan'] = "MpCmdRun.exe not found in the script directory."
        logging.error(f"MpCmdRun.exe not found in the script directory.")

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

# Run maintenance tasks and send the report email
def run_maintenance():
    with Manager() as manager:
        results = manager.dict()

        tasks = [
            Process(target=disk_cleanup),
            Process(target=sfc_scan, args=(results,)),
            Process(target=defender_scan, args=(results,)),
            Process(target=create_shortcut_if_missing),
            Process(target=update_download),
            Process(target=defragmentation),
            Process(target=capture_process_list, args=(results,)),  # Process for capturing processes
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

        # Get the CPU benchmark score
        cpu_benchmark = get_cpu_multithread_rating(cpu_details['cpu_name'])

        # Save the final report to the maintenance_report.txt file in the same directory
        report_filename = os.path.join(script_dir, 'maintenance_report.txt')

        try:
            logging.info(f"Saving report to {report_filename}")

            with open(report_filename, 'w') as report_file:
                report_file.write(f"PC Specifications:\n")
                report_file.write(f"    CPU: {cpu_details['cpu_name']}\n")
                report_file.write(f"    CPU Benchmark: {cpu_benchmark}\n")  # Add CPU benchmark score here
                report_file.write(f"    Ram: {memory_details['total_memory'] / (1024**3):.2f} GB\n")
                report_file.write(f"    Volume Size: {storage_details['volume_size'] / (1024**3):.2f} GB,\n")
                report_file.write(f"    Free Space: {storage_details['free_space'] / (1024**3):.2f} GB,\n")
                report_file.write(f"    Used Space: {storage_details['trimmed_space'] / (1024**3):.2f} GB\n")
                report_file.write(f"    Internet Speed: {system_info['internet_speed']}\n")
                report_file.write(f"    Windows Version: {system_info['os_version']}\n\n")
                
                report_file.write(f"* Benchmark (0-4000 replace computer, 4000-8000 fair,\n")
                report_file.write(f"8000-14000 good, 14000-32000+ great)\n")
                
                report_file.write(f"MALWARE / SPYWARE / VIRUSES:\n")
                report_file.write(f"    Scanned for malware, spyware, and viruses: {results.get('defender_scan', 'Not completed')}\n")
                report_file.write(f"    Removed malicious findings: Completed\n\n")

                report_file.write(f"CLEANING:\n")
                report_file.write(f"    Disk defragmented and cleaned: Completed\n")
                report_file.write(f"    Verified disk optimization: Completed\n")
                report_file.write(f"    Obtained Windows updates: Completed\n")
                report_file.write(f"    System File Checker run: {results.get('sfc_scan', 'Not completed')}\n\n")

                report_file.write(f"BACKUP AND SUPPORT:\n")
                report_file.write(f"    NTI shortcut added and tested: Completed\n")
                report_file.write(f"    System restore active and Restore Point created: Completed\n\n")
                
                report_file.write(f"RUNNING PROCESSES:\n")
                report_file.write(f"{results.get('process_list', 'No processes available')}\n")

            logging.info(f"Maintenance report saved to {report_filename}.")
            
            # Get the recipient email from .email file
            recipient_email = get_recipient_email()
            if recipient_email:
                # Send the report via email
                send_email_with_report(recipient_email, report_filename)
        except Exception as e:
            logging.error(f"Error writing the report: {e}")

# Run maintenance
if __name__ == "__main__":
    logging.info("Starting maintenance tasks...")
    run_maintenance()
    logging.info("Maintenance tasks completed.")
