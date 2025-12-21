#Init module and some logging defaults


import logging
#from .transfer import *
from .info import *
from .create import *

# API wide config
logging.basicConfig(level=logging.DEBUG)