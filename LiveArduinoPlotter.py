""" 
Interface between python and arduino for live data logger 

Author: James Keaveney
19/05/2015
"""

import time
import csv
import serial
import sys
import cPickle as pickle
import numpy as np
import matplotlib.pyplot as plt

nchannels = 2 # number of total channels (time axis + ADC channels)
datalen = 2000 # numbers in each array that serial.print does in arduino

class SerialDataPlotter:
	"""
	class for interfacing with the Arduino Data Logger

	The data logger runs on an Arduino DUE; the sketch is "SixChannelLogger.ino"
	and should also be in this directory

	"""
	def __init__(self,recording_time=1,verbose=True):
		self.recording_time = recording_time
		self.verbose = verbose
		
		self.time_axis = None
	
	def get_data(self):
		""" 
		Initialise serial port and listen for data until timeout. 
		Convert the bytestream into numpy arrays for each channel
		
		Returns:
		
			7 numpy arrays (1D) representing time and ADC channels 0-5 
		
		"""
		
		# setup serial port - it's the native USB port so baudrate is irrelevant, 
		# the data is always transferred at full USB speed
		ser = serial.Serial(
			port='COM4',
			baudrate=115200,
			parity=serial.PARITY_NONE,
			stopbits=serial.STOPBITS_ONE,
			bytesize=serial.EIGHTBITS,
			timeout=self.recording_time # seconds - should be the same amount of time as the arduino will send data for + 1
		)

		#testing - repeat serial read to confirm data arrays are always predictable
		#n_reps = 2
		#for i in range(n_reps):
		st = time.clock()
		
		#sync
		self._handshake(ser)
		
		#get data
		data = ser.readline()	# this number should be larger than the number of 
								# bytes that will actually be sent
		ser.close()				# close serial port
		et = time.clock() - st
		if self.verbose:
			print 'Elapsed time reading data (s): ', et
		
		#make string into list of strings, comma separated
		data_list = data.split(',')
		
		# remove new line characters (are any present?)
		#data_list = filter(lambda a: a != '\n', data_list)
		
		# make list of strings into 1D numpy array of floats (ignore last point as it's an empty string)
		data_array = np.array([float(i) for i in data_list[:-1]])
		if self.verbose:
			print 'Length of array:', len(data_array)

		# reshape array into 3D array
		data_array_3d = data_array.reshape(-1,nchannels,datalen)
		# then separate 1d arrays
		self.time_axis = data_array_3d[0][0]
		for i in range(1,len(data_array_3d)):
			self.time_axis = np.append(self.time_axis, data_array_3d[i][0])
		# convert time axis into ms, and zero the axis
		self.time_axis = (self.time_axis - self.time_axis[0])/1e3
		self.channel1 = data_array_3d[0][1]	
		for i in range(1,len(data_array_3d)):
			self.channel1 = np.append(self.channel1, data_array_3d[i][1])
		
		if self.verbose:
			print 'Data acquisition complete.'
		
		return self.time_axis,self.channel1

	def _handshake(self,serialinst):
		""" Send/receive pair of bytes to synchronize data gathering """
		nbytes = serialinst.write('A') # can write anything here, just a single byte (any ASCII char)		
		if self.verbose:
			print 'Wrote bytes to serial port: ', nbytes
		#wait for byte to be received before returning
		st = time.clock()
		byte_back = serialinst.readline()
		et = time.clock()
		if self.verbose:
			print 'Received handshake data from serial port: ',byte_back
			print 'Time between send and receive: ',et-st
		
	def save_data(self,filename):
		""" Save generated data to pickle file for use later """
		if self.time_axis is not None:
			timestamp = time.strftime("-%Y-%m-%d-%H%M")
			full_filename = filename + timestamp + '.pkl'

			#check if the file already exists - either overwrite or append
			if os.path.isfile(full_filename):
				print '\n\n WARNING - FILE ALREADY EXISTS !!!'
				if raw_input('Overwrite (y/n)?') in ['y','Y']:
					pass
				else:
					full_filename = full_filename[:-4] + '_new.pkl'
			
			with open(full_filename,'wb') as fileobj:
				pickle.dump((self.time_axis,self.channel1,self.channel2,self.channel3, \
					self.channel4,self.channel5,self.channel6), fileobj)
				if self.verbose:
					print 'Output saved'
		else:
			print 'No data to save yet'

	def load_data(self,full_filename):
		""" Load previously generated and pickled data and return it """
		with open(full_filename,'rb') as fileobj:
			self.time_axis,self.channel1,self.channel2,self.channel3, \
				self.channel4,self.channel5,self.channel6 = pickle.load(fileobj)
		return self.time_axis,self.channel1,self.channel2,self.channel3, \
					self.channel4,self.channel5,self.channel6
	
	def cleanup(self):
		# delete serial port instance?
		pass
	
def main():
	""" Grab data once and save it to file, with current timestamp """
	
	SR = SerialDataLogger(recording_time=6)
	
	filename = "TestData"
	t, C1, C2, C3, C4, C5, C6 = SR.get_data()
	SR.save_data(filename)	
	
if __name__ == '__main__':
	main()