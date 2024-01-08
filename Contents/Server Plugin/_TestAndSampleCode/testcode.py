import os
import sys
import ntpath
from datetime import datetime
from tkinter.filedialog import askopenfilename
import re
import time
import platform
import datetime

print("Starting test")
String1 = "Insteon Motion"
String2 = "Insteon Motions"
print("'"+String1 + "' and '" + String2 + "' are ")
num = String2.find(String1)
if num == 0: print("Equal")
else:
	if(num == 1): print("similar")
	else:
		print("Different")