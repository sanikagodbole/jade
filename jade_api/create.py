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

GEO_RIG_TEX_CONFIG = {
    'geo': {},  # artists working folder
    'rig': {},  # artists working folder
    'tex': {},  # artists working folder
}

CHAR_CONFIG = {
    'export': {},  # inside export, we create a folder for each new version
    'geo': {},  # artists working folder
    'rig': {},  # artists working folder
    'tex': {},  # artists working folder 
}


def create_show(user: LocalUser):
    root_dir = Path(user.collab_path)
    root_dir.mkdir(parents=True, exist_ok=True)
    create_paths(root_dir, DIR_CONFIG)

def create_paths(root_dir, dir_config: Dict):
    for dir_this_level, sub_dirs in dir_config.items():
        new_path : Path = root_dir / dir_this_level
        new_path.mkdir(exist_ok=True)
        create_paths(root_dir=new_path, dir_config=sub_dirs)
    
def create_asset(user):
    show_root = Path(user.collab_path)
    prod_root = show_root.joinpath("prod")
    assets_root = show_root.joinpath("assets")
    working_root = assets_root.joinpath("working")
    publish_root = assets_root.joinpath("publish")
