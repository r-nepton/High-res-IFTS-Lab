# The GenericOperation class defines a generic operation. Each operation is a
# long-timescale sequence of commands. One example of an operation might be mag-up. 

import time, datetime

class GenericOperation(object):
	def __init__(self):
		self.step_index = 0
		self.start_time = int(time.time()) # The start time, in seconds (unix time)

		# The "yield" command finishes the operation. After each step, the operator
		# checks the yield flag to determine if the operation is completed.
		self.finished = False
		# If the command finishes, but doesn't set the "success" parameter,
		# something went wrong with it.
		self.success  = False
		self.last_tick_time = 0

		# If an operation is sleeping, it won't tick.
		self.sleeping = False
		self.sleep_time = 0
		self.sleep_start_time = 0

		# Operation started message
		self.has_started_message = False
		self.started_message = "<%s>" % self.__class__.__name__

	# This function returns the time elapsed since the start of the operation, in seconds.
	def time(self):
		return int(time.time()) - self.start_time

	def print_log(self, message):
		now = datetime.datetime.now()
		print " [%s] <%s> %s " % ( now.strftime("%I:%M%p %d %B %Y"), self.__class__.__name__, message )

	# The step function is called whenever a generic operation is stepped.
	def step(self):
		self.print_log("Attempted operation step.")
		# If the operation is completed, don't run.
		if self.finished == True:
			return
		# If the step index is zero, we are now starting the operation.
		if self.step_index == 0:
			# Calculate the start time.
			self.start_time = int(time.time())
			self.last_tick_time = self.start_time
			self.started()

		# It is possible that the "started()" event caused the operation
		# to finish, e.g. via an error. So check AGAIN that it's not done.
		if self.finished == True:
			return

		# If we're currently sleeping, check to see if we should be done
		# sleeping yet.
		if self.sleeping == True and int(time.time()) > (self.sleep_start_time + self.sleep_time):
			self.sleeping = False
			self.sleep_completed()

		# It's also possible that the sleep_completed event caused us
		# to finish. So check AGAIN AGAIN that it's not done.
		if self.finished == True:
			return

		# Need to check if the system is still sleeping.
		if self.sleeping == True:
			pass
		else:
			# Okay, now perform the next step of the operation.
			self.tick( time.time() - self.last_tick_time )

		# Now record the tick time.
		self.last_tick_time = time.time()
		self.step_index += 1

	def sleep(self, time):
		self.sleeping = True
		self.sleep_start_time = int(time.time())
		self.sleep_time = time

	def sleep_completed(self):
		pass

	# The tick function is called every step, and should be overriden by children of GenericOperation to implement
	# functionality. The parameter "dt" corresponds to the time since the last
	# tick.
	def tick(self, dt):
		raise Exception("You can't actually run a GenericOperation!")

	# The "started" event is called on the first step.
	def started(self):
		pass

	# The "terminated" event is called on the last step.
	def ended(self):
		pass