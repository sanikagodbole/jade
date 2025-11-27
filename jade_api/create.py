#create folder structure

import os
from pathlib import Path
import shutil
from jade_api.info import LocalUser
from typing import Dict

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

CHAR_PUBLISH = {
    "{char_name}": {
        "assembly": {},
        "geo": {},
        "rig": {},
        "tex": {},
    }
}
CHAR_WORKING = {
    "{char_name": {
        "assembly": {
            "export": {}
            },
        "geo": {
            "export": {}
        },
        "rig": {
            "export": {}
        },
        "tex": {
            "export": {}
        },
    }
}


PROP_PUBLISH = {
    "{prop_name}": {
        "assembly": {},
        "geo": {},
        "tex": {},
    }
}
PROP_WORKING = {
    "{prop_name": {
        "assembly": {
            "export": {}
            },
        "geo": {
            "export": {}
        },
        "tex": {
            "export": {}
        },
    }
}

SET_PUBLISH = {
    "{set_name}": {
        "geo": {},
        "tex": {},
    }
}
SET_WORKING = {
    "{set_name}": {
        "geo": {
            "export": {}
        },
        "tex": {
            "export": {}
        },
    }
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
    
    # Get the structure for this asset type
    asset_working_structure = ASSET_WORKING_STRUCTURES[asset_type]
    asset_publish_structure = ASSET_PUBLISH_STRUCTURES[asset_type]
    
    # Create publish and working directories
    for mode in ["working",]:
        asset_path = asset_base_path / mode / asset_type / asset_name
        asset_path.mkdir(parents=True, exist_ok=True)

        create_paths(asset_path, asset_working_structure)

    for mode in ["publish",]:
        asset_path = asset_base_path / mode / asset_type / asset_name
        asset_path.mkdir(parents=True, exist_ok=True)

        create_paths(asset_path, asset_publish_structure)
        
        # Create subdirectories using the asset structure

    





# def create_asset(user):
#     show_root = Path(user.collab_path)
#     prod_root = show_root.joinpath("prod")
#     assets_root = show_root.joinpath("assets")
#     working_root = assets_root.joinpath("working")
#     publish_root = assets_root.joinpath("publish")
