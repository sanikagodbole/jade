#All fuctions dealing with logging and tracking changes to files

import os
import sys
import getpass

class LocalUser:
    #Retrieves info from the computer for use while commiting changes and transferring files
    def __init__(self):
        #Initializes all variables
        self.user_id = getpass.getuser()
        self.system_os = sys.platform
        self.show_name = os.environ.get("JADE_SHOW_NAME")
        self.collab_path = os.environ.get("JADE_COLLAB_BASE_DIR")
        #Set environment variable in .json, otherwise, hardcode path here:
        #self.collab_path = r"I-Drive/Savannah/CollaborativeSpace/stonelions"
        #r"I-Drive/Savannah/CollaborativeSpace/stonelions"
        if self.system_os == "win32":
            self.collab_path = r"I:/Savannah/CollaborativeSpace/stonelions"
        else:
        # Update this to the actual mount point on the Linux machines
            self.collab_path = f"/home/{self.user_id}/mount/CollaborativeSpace/stonelions"

        self.farm_path = os.environ.get("JADE_FARM")
