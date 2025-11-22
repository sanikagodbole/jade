#create folder structure

import os
from pathlib import Path
import shutil
from jade_api.info import LocalUser

from typing import Dict

# create dictionary of file structure, what folders you want within each folder
DIR_CONFIG ={
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
    root_dir = Path(user.collab_path)
    root_dir.mkdir(parents=True, exist_ok=True)
    create_paths(root_dir, DIR_CONFIG)


def create_paths(root_dir, dir_config: Dict):
    for dir_this_level, sub_dirs in dir_config.items():
        new_path : Path = root_dir / dir_this_level
        new_path.mkdir(exist_ok=True)
        create_paths(root_dir=new_path, dir_config=sub_dirs)

    prod_root = root_dir.joinpath("prod")
    prod_dirs = [result.name for result in prod_root.iterdir()]
    standard_prod_dirs = ["assets", "sequences"]
    for standard_dir in standard_prod_dirs:
        if standard_dir not in prod_dirs:
            constructed_path = prod_root.joinpath(standard_dir)
            constructed_path.mkdir(exist_ok=False)

    # create asset publish and working paths in prod
    assets_root = prod_root.joinpath("assets")
    asset_dirs = [result.name for result in assets_root.iterdir()]
    standard_assets_dirs = ["publish","working"]
    for asset_dir in standard_assets_dirs:
        if asset_dir not in asset_dirs:
            assets_dirs_path = assets_root.joinpath(asset_dir)
            assets_dirs_path.mkdir(exist_ok=False)

    # create working paths
    working_root = assets_root.joinpath("working")
    working_dirs = [result.name for result in working_root.iterdir()]
    standard_working_dirs = ["char","prop","rig","set"]
    for working_dir in standard_working_dirs:
        if working_dir not in working_dirs:
            working_dirs_path = working_root.joinpath(working_dir)
            working_dirs_path.mkdir(exist_ok=False)
    
    # create publish paths
    publish_root = assets_root.joinpath("publish")
    publish_dirs = [result.name for result in publish_root.iterdir()]
    standard_publish_dirs = ["char","prop","rig","set"]
    for publish_dir in standard_publish_dirs:
        if publish_dir not in publish_dirs:
            publish_dirs_path = publish_root.joinpath(publish_dir)
            publish_dirs_path.mkdir(exist_ok=False)
    
def create_asset():
    show_root = Path(user.collab_path)
    prod_root = show_root.joinpath("prod")
    assets_root = show_root.joinpath("assets")
    working_root = assets_root.joinpath("working")
    publish_root = assets_root.joinpath("publish")
