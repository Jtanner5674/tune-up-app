import subprocess
import datetime

def create_restore_point(description="NTi TuneUp"):
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    description = f"{description} ({now})"

    try:
        # Use PowerShell via subprocess to create a restore point
        cmd = [
            "powershell.exe",
            "-Command",
            f"""
            Checkpoint-Computer -Description "{description}" -RestorePointType "MODIFY_SETTINGS"
            """
        ]
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

        # Check for errors
        if result.returncode == 0:
            print(f"Restore point '{description}' created successfully.")
        else:
            print(f"Failed to create restore point. Output: {result.stdout.strip()}")
            print(f"Error: {result.stderr.strip()}")

    except Exception as e:
        print(f"Error creating restore point: {e}")

if __name__ == "__main__":
    create_restore_point()
