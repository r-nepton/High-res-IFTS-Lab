# The GenericOperation class defines a generic operation. Each operation is a
# long-timescale sequence of commands. One example of an operation might be mag-up. 

import time

class GenericOperation(object):
	def __init__(self):
		self.step_index = 0
		self.start_time = int(time.time()) # The start time, in seconds (unix time)

		# The "yield" command finishes the operation. After each step, the operator
		# checks the yield flag to determine if the operation is completed.
		self.yield = False
		self.last_tick_time = 0

	# This function returns the time elapsed since the start of the operation, in seconds.
	def time(self):
		return int(time.time()) - self.start_time

	# The step function is called whenever a generic operation is stepped.
	def step(self):
		# If the operation is completed, don't run.
		if self.yield == True:
			return
		# If the step index is zero, we are now starting the operation.
		if self.step_index == 0:
			# Calculate the start time.
			self.start_time = int(time.time())
			self.last_tick_time = self.start_time
			self.started()

		# It is possible that the "started()" event caused the operation
		# to finish, e.g. via an error. So check AGAIN that it's not done.
		if self.yield == True:
			return

		# Okay, now perform the next step of the operation.
		self.tick( time.time() - self.last_tick_time )

		# Now record the tick time.
		self.last_tick_time = time.time()
		step += 1

	# The tick function is called every step, and should be overriden by children of GenericOperation to implement
	# functionality. The parameter "dt" corresponds to the time since the last
	# tick.
	def tick(self, dt):
		raise Exception("You can't actually run a GenericOperation!")

	# The "started" event is called on the first step.
	def started(self):
		raise Exception("You can't actually run a GenericOperation!")

	# The "terminated" event is called on the last step.
	def terminated(self):
		raise Exception("You can't actually run a GenericOperation!")