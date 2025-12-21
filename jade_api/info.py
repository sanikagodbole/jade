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
        self.farm_path = os.environ.get("JADE_FARM")
        #self.sftp_host = os.environ.get("SFTP_HOST")
        #set environment variable in .json, otherwise, hardcode sftp host here:
        self.sftp_host = "myfile.scad.edu"
        # base folder path: \I - Drive\Savannah\CollaborativeSpace\stonelions

