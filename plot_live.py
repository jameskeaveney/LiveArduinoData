"""
Use SixChannelReader.py to acquire some data from the Arduino
and make a live plot using matplotlib

Author: James Keaveney
19/05/2015
"""
import LiveArduinoPlotter as LAP
import matplotlib.pyplot as plt
import numpy as np
import time

plt.ion()

def main():
	""" Get data logger data and plot it. Convert raw 12-bit ADC data to voltage """
	st2 = time.clock()
	
	LivePlotter = LAP.SerialDataPlotter(0.4,verbose=True)
	
	t = [0,1]
	C1 = [0,0]
	
	#setup plot
	fig = plt.figure("Test live plotter",figsize=(8,6))
	plt.clf()
	
	ax1 = fig.add_subplot(211)
	ax2 = fig.add_subplot(212)
	
	t, C1 = LivePlotter.get_data()
	line, = ax1.plot(t,C1*3.3/4095)
	fftS = np.fft.fft(C1)
	fftF = np.fft.fftfreq(len(t),d=(t[1]-t[0])/1e3)
	fftI = fftS * fftS.conjugate()
	fftline, = ax2.plot(fftF[fftF>0], fftS[fftF>0])
	ax2.set_xlim(0,8000)
	ax2.set_ylim(0,fftI.max())
	ax2.set_yscale('log')
	#ax1.set_xlim(t[0],t[-1])
	
	#autoscale on/off option here?
	#ax1.set_ylim(0,3.3)
	
	ax1.set_xlabel('Time (ms)')
	ax1.set_ylabel('A0 (V)')
	
	ax1.set_xlim(t[0],t[-1])
	ax1.set_ylim(0,3.3)
					
	fig.tight_layout()
	
	#repeat until Ctrl-C event
	looping = True
	while looping:
		try:
			st = time.clock()
			#get new data
			t, C1 = LivePlotter.get_data()
			C1 *= 3.3/4095
			line.set_data(t,C1)
			fftS = np.fft.fft(C1-C1.mean())
			fftF = np.fft.fftfreq(len(t),d=(t[1]-t[0])/1e3)
			fftI = fftS * fftS.conjugate()
			fftline.set_data(fftF[fftF>0], fftI[fftF>0])
			ax2.set_ylim(0,fftI.max())
			plt.draw()
			et = time.clock() - st
			print 'Time to update (ms):', et*1e3
		
		except KeyboardInterrupt:
			#exit on Ctrl-C event
			looping = False
			dummy = raw_input('Waiting...')
			
	#save data for later
	#filename = 'TestData'
	#SR.save_data(filename)	

	et2 = time.clock()
	print 'Total time elapsed: ', et2-st2


if __name__ == '__main__':
	main()