#put this in command line and import all the .py 

import os
import sys
import jade_api
from jade_api import *

if __name__ == "__main__":
    user = LocalUser()
    print("User ID:", user.user_id)
    print("System OS:", user.system_os)
    print("Show Name:", user.show_name)
    #print("Show Acronym:", user.show_acronym)
    print("Collab Path:", user.collab_path)
    print("Show Database:", user.show_database)

create_show()
