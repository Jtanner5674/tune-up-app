import subprocess

def copy_to_clipboard(text):
    subprocess.run("clip", text=True, input=text, encoding='utf-8')

def system_report():
    print("\n--- SYSTEM CHECKLIST ---\n")

    # Collecting PC Specifications
    model = input("Enter Computer Model: ")
    cpu = input("Enter CPU: ")
    cpu_benchmark = input("Enter CPU Benchmark: ")
    memory = input("Enter Memory size (in GB): ")
    num_drives = int(input("Enter the number of storage drives: "))
    drives = []

    for i in range(num_drives):
        drive_letter = input(f"Enter Drive {i + 1} Letter (e.g., C:): ")
        total_storage = float(input(f"Enter Total Storage for {drive_letter} (in GB): "))
        free_storage = float(input(f"Enter Free Storage for {drive_letter} (in GB): "))
        used_storage = total_storage - free_storage
        drives.append((drive_letter, total_storage, free_storage, used_storage))

    internet_download = input("Enter Internet Download Speed (Mbps): ")
    internet_upload = input("Enter Internet Upload Speed (Mbps): ")
    wifi_speed = input("Enter WiFi Speed: ")
    network_company = input("Enter Network Provider: ")
    windows_version = input("Enter Windows Version: ")
    antivirus = input("Enter Antivirus (subscription & expiration): ")
    backup = input("Enter Backup Method: ")

    # Task confirmations
    malware_scanned = "" if input("Scanned for malware, spyware, and viruses? (Press Enter if yes): ") == "" else "❌"
    unwanted_apps_removed = "" if input("Removed unwanted and malicious apps/extensions? (Press Enter if yes): ") == "" else "❌"
    private_connection_set = "" if input("Internet connection set to Private? (Press Enter if yes): ") == "" else "❌"
    temp_files_cleaned = "" if input("Temporary files & Windows Registry cleaned? (Press Enter if yes): ") == "" else "❌"
    boot_apps_removed = "" if input("Removed unnecessary startup apps? (Press Enter if yes): ") == "" else "❌"
    disk_optimized = "" if input("Verified disk optimization? (Press Enter if yes): ") == "" else "❌"
    log_files_checked = "" if input("Checked log files for critical errors? (Press Enter if yes): ") == "" else "❌"
    updates_obtained = "" if input("Obtained Windows updates? (Press Enter if yes): ") == "" else "❌"
    taskbar_checked = "" if input("Checked Taskbar settings? (Press Enter if yes): ") == "" else "❌"
    sfc_run = "" if input("System File Checker run? (Press Enter if yes): ") == "" else "❌"
    nti_shortcut_added = "" if input("NTI shortcut added and tested? (Press Enter if yes): ") == "" else "❌"
    restore_point_created = "" if input("System restore point created? (Press Enter if yes): ") == "" else "❌"

    # Final Checklist Report
    drives_report = "\n".join(
        [f"    Drive {drive[0]}: {drive[1]} GB (Free: {drive[2]} GB, Used: {drive[3]:.2f} GB)" for drive in drives]
    )

    report = f"""
PC Specifications:
    CPU: {cpu} / *Benchmark: {cpu_benchmark}
    Computer Model: {model}
    Memory: {memory} GB
    Storage:
{drives_report}
    Internet Speed: Download {internet_download} Mbps / Upload {internet_upload} Mbps
    Connection to router (WiFi speed): {wifi_speed} Mbps
    Network Provider: {network_company}
    Windows Version: {windows_version}
    Anti-Virus: {antivirus}

MALWARE / SPYWARE / VIRUSES:
    Scanned for malware, spyware, and viruses {malware_scanned}
    Removed unwanted and malicious apps/extensions {unwanted_apps_removed}
    Internet connection set to Private {private_connection_set}

CLEANING:
    Temporary files & Windows Registry cleaned {temp_files_cleaned}
    Removed unnecessary startup apps {boot_apps_removed}
    Verified disk optimization {disk_optimized}
    Checked log files for critical errors {log_files_checked}
    Obtained Windows updates {updates_obtained}
    Checked Taskbar settings {taskbar_checked}
    System File Checker run {sfc_run}

BACKUP AND SUPPORT
    Backup: {backup}
    NTI shortcut added and tested {nti_shortcut_added}
    System restore active and Restore Point created {restore_point_created}

* Benchmark (0-4000 replace computer, 4000-8000 fair, 
8000-14000 good, 14000-32000+ great)
"""
    print(report)

    # Copy to clipboard
    copy_to_clipboard(report)
    print("The report has been copied to your clipboard!")

# Run the checklist
if __name__ == "__main__":
    system_report()
