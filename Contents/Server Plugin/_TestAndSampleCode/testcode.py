import os
import sys
import ntpath
from datetime import datetime
from tkinter.filedialog import askopenfilename
import re
import time
import platform
import datetime

userPin = "84 8"
newPin = ""

for c in userPin:
	if c in "0123456789":
		newPin = newPin+c
	else:
		newPin = newPin + '0'
print(newPin)
