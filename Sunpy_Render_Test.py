import datetime
import numpy
import sunpy
import subprocess
import glob
import os
import matplotlib

from PIL import ImageFont, ImageDraw, Image
from astropy.io import fits
from sunpy.database import Database
from multiprocessing import Pool

import sunpy.map
import cv2

import sunpy.instr.aia as aia
import matplotlib.pyplot as plt
# import matplotlib.pylab as plt

directory = "test_fits_files/0171/"

def AIA_Sort(DIR):
	newdirs = []
	for f in glob.glob(DIR + "*.fits"):
		wavelen = f.split("_")[4].split(".")[0]
		newdir = wavelen
		if os.path.isdir(DIR + newdir) == False:
			subprocess.call("mkdir " + DIR + newdir, shell = True)
			newdirs.append(newdir)
		subprocess.call("cp " + f + " " + directory + wavelen, shell = True)
	print("sorted: " + str(newdirs))
	return(newdirs)



timestart = datetime.datetime.now()
print("Start time: " + str(timestart))

wavelength = 0
date = 0
time = 0

#Load an opentype font (requires PIL)
font = ImageFont.truetype("BebasNeue Regular.otf", 80)
b,g,r,a = 191,191,191,0
framenum = 0 

#create and initialize our sunpy database
database = Database('sqlite:///sunpydata.sqlite')
print("current database size: " + str(len(database)))

#add an entire directory of fits files to our database, ignoring duplicates
database.add_from_dir("test_fits_files/0171_1", ignore_already_added=True)
print("new database size: " + str(len(database)))

for i in range(0, len(database)):
	print str(database[i].path)

for i in range(0,len(database)):      
	entry = database[i] 
	img = sunpy.map.Map(entry.path)
	valbuff = 0

	
	print "working on " + str(entry.path)
	for fits_header_entry in entry.fits_header_entries[:100]:
		#Index through the header of each fits file looking for the DATE tag
		keybuff = '{entry.key}'.format(entry = fits_header_entry)
		if keybuff == "DATE-OBS":
			#If we find it, we store it, to overlay on the frame
			valbuff = '{entry.value}'.format(entry = fits_header_entry)
		if keybuff == "WAVELNTH":
			wavelength = '{entry.value}'.format(entry = fits_header_entry)

	print valbuff
	
	#database.add_from_dir() creates an entry for each header file. Sometimes AIA fits files have two headers,
	#so if we get to an entry that doesn't have the information we need, we skip it.
	if valbuff != 0:
		fontpath = "BebasNeue Regular.otf"     
		font = ImageFont.truetype(fontpath, 56)

		date = valbuff.split("T")[0]
		time = valbuff.split("T")[1]

		#This is how you get pyplot to export a clean image from your fits file at native resolution
		#No one can tell me why it takes these exact steps in this order, but this is how we finally got it to work
		clockin = datetime.datetime.now()
		sizes = numpy.shape(img.data)     
		fig = plt.figure()
		fig.set_size_inches(1. * sizes[0] / sizes[1], 1, forward = False)
		ax = plt.Axes(fig, [0., 0., 1., 1.])
		ax.set_axis_off()
		fig.add_axes(ax)
		ax.imshow(img.data, norm = img.plot_settings['norm'], cmap = img.plot_settings['cmap'], origin='lower')
		plt.savefig("First_Out" + str(framenum + 1) + ".png", dpi = sizes[0]) 
		plt.close()
		print("Initial Frame Print time: " + str(datetime.datetime.now() - clockin))
		
		clockin = datetime.datetime.now()
		#Convert our image from a numpy array to something PIL can deal with
		img_pil = Image.open("First_Out" + str(framenum + 1) + ".png")
		
		# Convert to RGB mode. Do I want to do this? I should maybe try RGBA
		# if img_pil.mode != "RGBA":
		# img_pil = img_pil.convert("RGBA")
		# #Render it to a frame
		draw = ImageDraw.Draw(img_pil)
		# #Put our text on it
		print("applying timestamp... " + str(valbuff))
		draw.text((3468, 710), str(date), font = font, fill = (b, g, r, a))
		draw.text((3468, 770), str(time), font = font, fill = (b, g, r, a))
		# #Turn it back in to a numpy array for OpenCV to deal with
		frameStamp = numpy.array(img_pil)


		print("printing frame: " + str(framenum + 1) + ". final render time: " + str(datetime.datetime.now() - clockin))
		img_pil.save("Frame_Out" + str(framenum + 1) + ".png", "PNG")
		cv2.imwrite("Frame_Out" + str(framenum + 1) + ".png", cv2.cvtColor(frameStamp, cv2.COLOR_RGB2BGR)) #Converting BGR to RGB because OpenCV
		framenum = framenum + 1
	else:
		print "Entry header contains no date. Skipping..."

OUTNAME = str(date) + "_" + str(wavelength) + ".mp4"

subprocess.call('ffmpeg -r 24 -i Frame_Out%01d.png -vcodec libx264 -b:v 4M -pix_fmt yuv420p -y ' + str(OUTNAME), shell=True)

print("TOTAL ELAPSED TIME: " + str(datetime.datetime.now() - timestart))

# Cleanup the directory when we're done
# for f in glob.glob("First_Out*.png"):
# 	    os.remove(f)

# for f in glob.glob("Frame_Out*.png"):
# 	    os.remove(f)
