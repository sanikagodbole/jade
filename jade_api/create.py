#create folder structure

import os
from pathlib import Path
from jade_api.info import LocalUser
from typing import Dict
import re
import shutil

# create dictionary of file structure, what folders you want within each folder
DIR_CONFIG = {
    'prod': {
        'asset': {
            'publish': {
                'char': {},
                'prop': {},
                'set': {}
            },
            'working': {
                'char': {},
                'prop': {},
                'set': {}
            }
        },
        'sequences': {}
    },
    'pre': {},
    'post': {},
    '.tools': {},
}


def create_show(user: LocalUser):
    root_dir = Path(user.collab_path) #path of where directory is located is imported from localuser class from info.py
    root_dir.mkdir(parents=True, exist_ok=True)
    create_paths(root_dir, DIR_CONFIG)

# recursively check through file structure in DIR_CONFIG to make new directory if it does not exist
# because it is based on what is in the dictionary, the code itself will work even if the file structure
# is later changed
def create_paths(root_dir, dir_config: Dict): # path of where the directory is located, dictionary of directory
    for dir_this_level, sub_dirs in dir_config.items():
        new_path : Path = root_dir / dir_this_level # connect new directory level to root
        new_path.mkdir(exist_ok=True) # check if directory exists
        create_paths(root_dir=new_path, dir_config=sub_dirs) # run create path function in the next directory level



def create_new_asset(asset_name: str, asset_type: str, asset_base_path: Path):
    """
    Create a new asset directory structure for char, prop, or set.
    
    Args:
        asset_name: Name of the asset (e.g., "lion", "stone", "forest")
        asset_type: Type of asset ("char", "prop", or "set")
        asset_base_path: Path to the assets folder (prod/assets)
    
    Raises:
        ValueError: If asset_type is not "char", "prop", or "set"
    """
    if asset_type not in ["char", "prop", "set"]:
        raise ValueError(f"asset_type must be 'char', 'prop', or 'set', got '{asset_type}'")
    
    # Define folder structure for each asset type
    ASSET_WORKING_STRUCTURES = {
        "char": {
            "assembly": {"export": {}},
            "geo": {"export": {}},
            "rig": {"export": {}},
            "tex": {"export": {}},
        },
        "prop": {
            "assembly": {"export": {}},
            "geo": {"export": {}},
            "tex": {"export": {}},
        },
        "set": {
            "geo": {"export": {}},
            "tex": {"export": {}},
        },
    }

    ASSET_PUBLISH_STRUCTURES = {
        "char": {
            "assembly": {},
            "geo": {},
            "rig": {},
            "tex": {},
        },
        "prop": {
            "assembly": {},
            "geo": {},
            "tex": {},
        },
        "set": {
            "geo": {},
            "tex": {},
        },
    }
    
    # Shot structures are handled separately by create_new_shot()

    # Get the structure for this asset type
    asset_working_structure = ASSET_WORKING_STRUCTURES[asset_type]
    asset_publish_structure = ASSET_PUBLISH_STRUCTURES[asset_type]
    # shot structures not used here
    
    # Create publish and working directories
    for mode in ["working"]:
        asset_path = asset_base_path / mode / asset_type / asset_name
        asset_path.mkdir(parents=True, exist_ok=True)
        create_paths(asset_path, asset_working_structure)

    for mode in ["publish"]:
        asset_path = asset_base_path / mode / asset_type / asset_name
        asset_path.mkdir(parents=True, exist_ok=True)
        create_paths(asset_path, asset_publish_structure)


def create_new_shot(sequence_num: float, shot_num: float, shot_base_path: Path):
    """
    Create a new shot directory structure under working and publish folders.
    
    Args:
        sequence_num: Sequence number (e.g., 1 for seq_010, 4 for seq_040)
        shot_num: Shot number (e.g., 1 for shot_0010, 25 for shot_0250)
        shot_base_path: Path to the sequences folder (prod/sequences)
    """
    # Format sequence and shot numbers with decimal slots (multiply by 10)
    # This reserves the last digit for decimal inserts (e.g., seq 1 -> 010, shot 1 -> 0010)
    seq_formatted = str(int(round(sequence_num * 10))).zfill(3)  # e.g., 1 -> "010", 4 -> "040", 1.5 -> "015"
    shot_formatted = str(int(round(shot_num * 10))).zfill(4)     # e.g., 1 -> "0010", 25 -> "0250", 1.5 -> "0015"
    shot_name = f"seq_{seq_formatted}_shot_{shot_formatted}"
    
    # Define shot folder structures
    SHOT_WORKING_STRUCTURE = {
        "assembly": {"export": {}},
        "light": {"export": {}},
        "anim": {"export": {}},
        "fx": {"export": {}},
        "charfx": {"export": {}},
        "set": {"export": {}},
        "camera": {"export": {}},
    }
    
    SHOT_PUBLISH_STRUCTURE = {
        "assembly": {},
        "light": {},
        "anim": {},
        "fx": {},
        "charfx": {},
        "set": {},
        "camera": {},
    }
    
    # Create working directory structure (prod/sequences/working/seq_xxx_shot_xxx/...)
    for mode in ["working"]:
        shot_path = shot_base_path / shot_name / mode
        shot_path.mkdir(parents=True, exist_ok=True)
        create_paths(shot_path, SHOT_WORKING_STRUCTURE)
    
    # Create publish directory structure (prod/sequences/publish/seq_xxx_shot_xxx/...)
    for mode in ["publish"]:
        shot_path = shot_base_path / shot_name / mode
        shot_path.mkdir(parents=True, exist_ok=True)
        create_paths(shot_path, SHOT_PUBLISH_STRUCTURE)


def find_highest_version_file(export_path: Path, asset_name: str, department: str, file_extension: str):
    """
    Identifies the file with the highest numerical version in the given directory.
    Pattern: <asset_name>_<department>_v<numerical_version>_<user_initials>.<file_extension>

    The file_extension should include the leading dot, e.g., '.usd'.
    """
    if not export_path.is_dir():
        return None

    # Create the expected file prefix, standardizing to lower case
    name_prefix = f"{asset_name.lower()}_{department.lower()}_v"

    # List to store (version_number, file_path) tuples
    versioned_files = []

    # Ensure the extension starts with a dot for accurate filtering
    ext = file_extension if file_extension.startswith('.') else f".{file_extension}"

    for file_path in export_path.iterdir():
        filename = file_path.name

        # Check if the file starts with the prefix and ends with the specified extension
        if filename.startswith(name_prefix) and filename.endswith(ext):
            try:
                # Look for digits between 'v' and the next '_'
                # This regex captures the version number: e.g., 'v' followed by digits, followed by '_'
                # We use re.escape in case the prefix contains regex special characters (safer practice)
                match = re.search(f"{re.escape(name_prefix)}(\\d+)_", filename)
                if match:
                    version = int(match.group(1))
                    versioned_files.append((version, file_path))
            except Exception:
                # Skip files that don't perfectly conform to the version pattern
                continue

    if not versioned_files:
        return None

    # Find the file path associated with the maximum version number
    highest_version_file = max(versioned_files, key=lambda x: x[0])[1]
    return highest_version_file

