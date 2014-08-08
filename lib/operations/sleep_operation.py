from generic_operation import *
from cryo_delegate import *

class SleepOperation(GenericOperation):
	def __init__(self, sleep_time):
		self.sleep_time = sleep_time

		super(SleepOperation, self).__init__()

	def tick(self, dt):
		# Wait for the sleep time to elapse.
		if time.time() - self.start_time > self.sleep_time:
			self.finished 	= True
			self.success 	= True

	# Sleep operations don't need to write lots of boring updates to the
	# log files.
	def print_log(self, message):
		pass