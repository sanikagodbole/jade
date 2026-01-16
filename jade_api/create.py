#creates folder structures & finds highest version numbers

from pathlib import Path
from jade_api.info import LocalUser
from typing import Dict
import re

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
    'post': {
        'final':{},
        'publish': {},
        'working': {},
    },
    'tools': {},
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
    
    Arguments:
        asset_name: Name of the asset (e.g., "lion", "stone", "forest")
        asset_type: Type of asset ("char", "prop", or "set")
        asset_base_path: Path to the assets folder (prod/assets)
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
        },
    }

    asset_working_structure = ASSET_WORKING_STRUCTURES[asset_type]
    asset_publish_structure = ASSET_PUBLISH_STRUCTURES[asset_type]

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
    # formatting create new shot to naming convention
    seq_formatted = str(int(round(sequence_num * 10))).zfill(3)
    shot_formatted = str(int(round(shot_num * 10))).zfill(4)
    shot_name = f"{seq_formatted}_{shot_formatted}"
    
    # defining shot folder structures
    SHOT_WORKING_STRUCTURE = {
        "anim": {
            "playblast": {"export": {}},
            "emAnim": {"export": {}},
            "chiAnim": {"export": {}},
            },
        "fx": {
            "wispFx": {"export": {}},
            },
        "charfx": {
            "wispFx": {"export": {}},
            "emFx": {"export": {}},
            "chiFx": {"export": {}},
            },
    }
    
    SHOT_PUBLISH_STRUCTURE = {
        "anim": {
            "playblast": {},
            "emAnim": {},
            "chiAnim": {},
        },
        "fx": {
            "wispFx": {},
        },
        "charfx": {
            "wispFx": {},
            "emFx": {},
            "chiFx": {},
        },
    }

    COMP_WORKING_STRUCTURE = {
        "comp": {"export": {}},
        "matte": {"export": {}},
        "renders": {"export": {}},
    }

    COMP_PUBLISH_STRUCTURE = {
        "comp": {},
        "matte": {},
        "renders": {},
    }

    for mode in ["working"]:
        shot_path = shot_base_path / "prod" / "sequences" / shot_name / mode
        shot_path.mkdir(parents=True, exist_ok=True)
        create_paths(shot_path, SHOT_WORKING_STRUCTURE)

        shot_path_comp = shot_base_path / "post" / mode / shot_name
        shot_path_comp.mkdir(parents=True, exist_ok=True)
        create_paths(shot_path_comp, COMP_WORKING_STRUCTURE)

    
    for mode in ["publish"]:
        shot_path = shot_base_path / "prod" / "sequences" / shot_name / mode
        shot_path.mkdir(parents=True, exist_ok=True)
        create_paths(shot_path, SHOT_PUBLISH_STRUCTURE)

        shot_path_comp = shot_base_path / "post" / mode / shot_name
        shot_path_comp.mkdir(parents=True, exist_ok=True)
        create_paths(shot_path_comp, COMP_PUBLISH_STRUCTURE)


def create_new_shot_asset(shot_name: str, shot_asset_name: str, shot_base_path: Path):
    """
    Create a new shot-specific asset structure.

    Args:
        shot_name: The name of the shot (e.g., 'seq_010_shot_0010')
        asset_name: The name of the specific asset to create
        shot_base_path: Path to the sequences folder (prod/sequences)
    """

    SHOT_ASSET_WORKING_STRUCTURE = {
        shot_asset_name: {
                "export": {}
            }
    }

    SHOT_ASSET_PUBLISH_STRUCTURE = {
        shot_asset_name: {}
    }

    working_path = shot_base_path / shot_name / "working"
    working_path.mkdir(parents=True, exist_ok=True)
    create_paths(working_path, SHOT_ASSET_WORKING_STRUCTURE)

    publish_path = shot_base_path / shot_name / "publish"
    publish_path.mkdir(parents=True, exist_ok=True)
    create_paths(publish_path, SHOT_ASSET_PUBLISH_STRUCTURE)



def find_highest_version_file(export_path: Path, asset_name: str, department: str, file_extension: None,
                              is_folder_search: bool = False):
    """
    Identifies the file or folder with the highest numerical version in the given directory.
    Pattern: <asset_name>_<department>_v<numerical_version>_<user_initials>.<file_extension>
    """
    if not export_path.is_dir():
        return None

    # Create file prefix
    name_prefix = f"{asset_name}_{department}_v"

    # List to store version_number, item_path
    versioned_items = []

    # Prepare extension suffix if searching for files
    ext_suffix = file_extension if file_extension and file_extension.startswith(
        '.') else f".{file_extension}" if file_extension else ""

    for item_path in export_path.iterdir():

        if (is_folder_search and item_path.is_dir()) or (not is_folder_search and item_path.is_file()):

            item_name = item_path.name
            # if the file starts with the correct prefix [name of folder]
            if item_name.startswith(name_prefix):

                if not is_folder_search and not item_name.endswith(ext_suffix):
                    continue

                try:
                    #finds verion number based on v__
                    match = re.search(f"{re.escape(name_prefix)}(\\d+)_", item_name)
                    if match:
                        version = int(match.group(1))
                        versioned_items.append((version, item_path))
                except Exception:
                    continue

    if not versioned_items:
        return None

    # find and return highest version number
    highest_version_item = max(versioned_items, key=lambda x: x[0])[1]
    return highest_version_item
