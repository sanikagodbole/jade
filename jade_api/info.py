#All fuctions dealing with logging and tracking changes to files

import os
import sys

os.environ["JADE_SHOW_NAME"] = "Stone_Lions_Dont_Roar"
os.environ["JADE_COLLAB"] = r"C:/Users/valgo/Desktop/JADE/TEST_STONE_LIONS"

class LocalUser:
    #Retrieves info from the computer for use while commiting changes and transfering files
    def __init__(self):
        #Initializes all variables
        self.user_id = os.environ.get("USER") or os.environ.get("USERNAME")
        self.system_os = sys.platform
        self.show_name = os.environ.get("JADE_SHOW_NAME")
        self.collab_path = os.environ.get("JADE_COLLAB")
        self.show_database = os.environ.get("JADE_SHOW_DATABASE")
        self.show_asset = os.environ.get("JADE_ASSET_DATABASE")
        self.farm_path = os.environ.get("JADE_FARM")
        self.show_contributors = os.environ.get("JADE_SHOW_CONTRIBUTORS")

if __name__ == "__main__":
    user = LocalUser()
    print("User ID:", user.user_id)
    print("System OS:", user.system_os)
    print("Show Name:", user.show_name)
    print("Collab Path:", user.collab_path)
    print("Show Database:", user.show_database)