#All fuctions dealing with logging and tracking changes to files

import os
import sys
import getpass

class LocalUser:
    #Retrieves info from the computer for use while commiting changes and transfering files
    def __init__(self):
        #Initializes all variables
        self.user_id = getpass.getuser()
        self.system_os = sys.platform
        self.show_name = os.environ.get("JADE_SHOW_NAME")
        self.collab_path = os.environ.get("JADE_COLLAB_BASE_DIR")
        self.show_database = os.environ.get("JADE_SHOW_DATABASE")
        self.show_asset = os.environ.get("JADE_ASSET_DATABASE")
        self.farm_path = os.environ.get("JADE_FARM")
        self.show_contributors = os.environ.get("JADE_SHOW_CONTRIBUTORS")
