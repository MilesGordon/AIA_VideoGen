import subprocess
import glob
import os
import datetime
import sys


directory = "/data/SDO/AIA/level1/2017/06/08/"
wavelength = sys.argv[1]

def Parse_Directory(WLEN):

	fits_list = []

	for folder in sorted(glob.glob(str(directory) + "H*")):
		for file in sorted(glob.glob("*" + str(WLEN).zfill(4) + ".fits")):
			fits_list.append(str(file))

	return(fits_list)

new_index = Parse_Directory(wavelength)

for i in len(new_index):
	print(new_index[i])