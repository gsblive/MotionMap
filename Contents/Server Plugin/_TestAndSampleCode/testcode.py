import os
import sys
import ntpath
from datetime import datetime
from tkinter.filedialog import askopenfilename
import re
import time

ft = datetime.now()
varString = "Unknown"
varString = varString.partition(' ')[0] + " ( Non-Motion Timeout at " + '{:%-I:%M %p}'.format(ft) + " )"
print(varString)