import datetime
import getpass
from pathlib import Path
from typing import Optional


def log_action(base_path: Path, action: str, details: str = ""):
    """
    Logs the action taken by the user to a plain text log file located
    at <base_path>/.log/activity_log.txt.
    """

    # Define the path for the log folder and file
    log_dir = base_path / ".tools"
    log_dir.mkdir(exist_ok=True)
    log_file = log_dir / "activity_log.txt"

    # Get user, time, and format the message
    user = getpass.getuser()
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Use f-string formatting for alignment and readability
    log_entry = f"[{timestamp}] User: {user:<15} | Action: {action:<20} | Details: {details}\n"

    # Write to the file
    try:
        with open(log_file, 'a') as f:
            f.write(log_entry)
    except Exception as e:
        # If the logging fails (e.g., permissions), print an error but don't crash the main app
        print(f"ERROR writing to log file: {e}")