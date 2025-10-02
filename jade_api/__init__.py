#Init module and some logging defaults

import logging

#from .database import *
#from .transfer import *
from .info import *
from .create import *
#from .telemetry import *

# API wide config
logging.basicConfig(level=logging.DEBUG)