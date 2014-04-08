import threading, subprocess

def shell_command(command, timeout=3):
		# This is a function which will be run in a seperate thread. It communicates
		# with the 
		self = {}
		self['process'] = None
		self['response'] = None
		def encapsulation():
			self['process'] = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
			self['response'] = ''.join( self['process'].stdout.readlines() )

		thread = threading.Thread(target=encapsulation)
		thread.start()
		# Block until the thread is finished, or until it times out.
		thread.join(timeout)
		if thread.is_alive():
			raise Exception("Killing a thread which is waiting too long.")
			try:
				self['process'].terminate()
			except:
				raise Exception("Unable to terminate process?")
			thread.join()

		return self['response']