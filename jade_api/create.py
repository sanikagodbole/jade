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





def create_asset(user):
    show_root = Path(user.collab_path)
    prod_root = show_root.joinpath("prod")
    assets_root = show_root.joinpath("assets")
    working_root = assets_root.joinpath("working")
    publish_root = assets_root.joinpath("publish")
