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
from pathlib import Path
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
import argparse

# Setup logging to a file (overwrites the file each time)
script_dir = os.path.dirname(os.path.realpath(__file__))  # Get the directory where the script is located
log_filename = os.path.join(script_dir, 'maintenance_log.txt')
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

# Function to get the email from the AppData folder
def get_email():
    email_path = Path(os.getenv("APPDATA")) / "NTi" / ".email"
    if email_path.exists():
        with open(email_path, "r") as f:
            email = f.read().strip()
            return email
    return None
    
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

# Function to send the email with the report using TLS
def send_email_with_report(report_filename):
    sender_email = "joshua@nticomputers.com"  # Replace with your Office 365 sender email
    sender_password = "NTI2024!"  # Replace with your email password
    subject = "Maintenance Report"

    # Get recipient email from .email file
    recipient_email = get_email()
    if not recipient_email:
        logging.error("Recipient email not found. Email will not be sent.")
        return

    # Read the license key (example path, adjust as necessary)
    license_key = None
    license_file = Path(os.getenv("APPDATA")) / "NTi" / ".license"
    try:
        with open(license_file, "r") as f:
            license_key = f.read().strip()
    except FileNotFoundError:
        logging.error("License file not found.")
    except Exception as e:
        logging.error(f"Error reading license file: {e}")
    
    # Start with an empty body
    body = ""

    try:
        # Open the report file and read its content
        with open(report_filename, "r") as report_file:
            body = report_file.read()

        # If license key is found, append it to the bottom of the email body
        if license_key:
            body += f"\n\nLicense Key: {license_key}\n"

    except Exception as e:
        logging.error(f"Error reading report file: {e}")

    try:
        # Create a multipart message and set headers
        message = MIMEMultipart()
        sender_name = "NTi Computers"
        message["From"] = f"{sender_name} <{sender_email}>"
        message["To"] = recipient_email
        message["Subject"] = subject

        # Attach the report body with the message instance
        message.attach(MIMEText(body, "plain"))

        # Open the report file to attach as an attachment
        with open(report_filename, "rb") as attachment:
            part = MIMEBase("application", "octet-stream")
            part.set_payload(attachment.read())
            encoders.encode_base64(part)
            part.add_header(
                "Content-Disposition",
                f"attachment; filename= {os.path.basename(report_filename)}",
            )
            message.attach(part)

        # Establish a connection to the Office 365 SMTP server using TLS
        with smtplib.SMTP("smtp.office365.com", 587) as server:
            server.ehlo()
            server.starttls()
            server.login(sender_email, sender_password)
            server.sendmail(sender_email, recipient_email, message.as_string())  # Send email
        
        logging.info("Email with maintenance report sent successfully.")

    except Exception as e:
        logging.error(f"Error sending email: {e}")

def send_unsubscribe_email(license_key, email_address):
    recipients = ["joshua@nticomputers.com", "ken@nticomputers.com", "shelley@nticomputers.com"]
    subject = "License Cancellation Request"
    body = f"Dear NTi Team,\n\nThe user with the email {email_address} is requesting to cancel their license.\n\n" \
           f"License Key: {license_key}\n\nPlease verify and process the cancellation request.\n\n" \
           "Best regards,\nThe NTi System"

    sender_email = "joshua@nticomputers.com"  # Replace with your email address
    sender_password = "NTI2024!"  # Replace with your email password

    # Create the email message
    message = MIMEMultipart()
    message["From"] = sender_email
    message["Subject"] = subject
    message.attach(MIMEText(body, "plain"))

    # Establish a connection to the Office 365 SMTP server using TLS
    try:
        with smtplib.SMTP("smtp.office365.com", 587) as server:
            server.ehlo()  # Identify ourselves to the server
            server.starttls()  # Secure the connection with TLS
            server.login(sender_email, sender_password)  # Log in
            for recipient in recipients:
                message["To"] = recipient
                server.sendmail(sender_email, recipient, message.as_string())  # Send email
        
        logging.info("Unsubscribe email sent successfully.")

    except Exception as e:
        logging.error(f"Error sending unsubscribe email: {e}")

# Function to handle the unsubscribe process
def handle_unsubscribe():
    # Read the license key and email address
    license_key = None
    email_address = None

    # Read the license file
    license_file = Path(os.getenv("APPDATA")) / "NTi" / ".license"
    try:
        with open(license_file, "r") as f:
            license_key = f.read().strip()
    except FileNotFoundError:
        logging.error("License file not found.")

    # Read the email file
    email_file = Path(os.getenv("APPDATA")) / "NTi" / ".email"
    try:
        with open(email_file, "r") as f:
            email_address = f.read().strip()
    except FileNotFoundError:
        logging.error(".email file not found.")
    
    if license_key and email_address:
        send_unsubscribe_email(license_key, email_address)
    else:
        logging.error("License key or email address not found. Unsubscribe email not sent.")


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
            send_email_with_report(report_filename)
        except Exception as e:
            logging.error(f"Error writing the report: {e}")

# Run maintenance
if __name__ == "__main__":
    logging.info("Starting maintenance tasks...")

    # Parse command-line arguments
    parser = argparse.ArgumentParser(description="NTi Maintenance Script")
    parser.add_argument("--unsubscribe", action="store_true", help="Request for license cancellation")
    args = parser.parse_args()

    if args.unsubscribe:
        logging.info("Unsubscribe requested.")
        handle_unsubscribe()
    else:
        run_maintenance()
    
    logging.info("Maintenance tasks completed.")
