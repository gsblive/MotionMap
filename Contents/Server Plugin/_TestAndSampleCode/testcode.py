import os
import sys
import ntpath
from datetime import datetime as dt
from datetime import datetime as dt
from tkinter.filedialog import askopenfilename
import re

arrivalTimeISO = dt.isoformat(dt.strptime("08/20/20", "%m/%d/%y"))
departureTimeISO = dt.isoformat(dt.strptime("08/20/20", "%m/%d/%y"))

print("Departure: " + departureTimeISO + " Arrival: " + arrivalTimeISO)

if arrivalTimeISO == departureTimeISO:
	print("stirngs are equal")
elif arrivalTimeISO > departureTimeISO:
	print("arrivalTimeISO greater than departureTimeISO")
else:
	print("arrivalTimeISO less than departureTimeISO")