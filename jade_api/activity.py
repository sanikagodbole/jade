import datetime
import getpass
from pathlib import Path

def log_action(base_path: Path, action: str, details: str = ""):

    # logs user along with what action they entered and when and what version
    # Define the path for the log folder and file
    log_dir = base_path / ".tools"
    log_dir.mkdir(exist_ok=True)
    log_file = log_dir / "activity_log.txt"

    # time
    user = getpass.getuser()
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # formatting
    log_entry = f"[{timestamp}] User: {user:<15} | Action: {action:<20} | Details: {details}\n"

    # writes in the file
    try:
        with open(log_file, 'a') as f:
            f.write(log_entry)
    except Exception as e:
        print(f"ERROR writing to log file: {e}")