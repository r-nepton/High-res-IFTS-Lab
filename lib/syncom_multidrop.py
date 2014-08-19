import serial, serial_dummy

# This Syncom MultiDrop adapter is based around the specifications in the 
# Syncom datasheets describing the protocol design. It is also specifically
# adapted to work with a compressr
class SyncomMultiDropAdapter:
	def __init__(self):
		try:
			self.serial_connection = serial.Serial('/dev/ttyUSB1', 9600, timeout=0.1)
		except Exception: 
			print "There was a problem connecting to the serial port constructor of: %s" % type(self)
			self.serial_connection = serial_dummy.SerialDummy()

	def clear_buffer(self):
		self.serial_connection.read(100)
		return True

	def write(self, data = [0x63, 0x0D, 0x8F, 0x00]):
		STX		 	= 0x02 # STX byte

		message = []  
		message.append(0x10) # Address (16) 
		message.append(0x80) # CMD_RSP (dictionary read)
		
		checksum = ( reduce( lambda x,y: (x+y)%256, message ) + reduce( lambda x,y: (x+y)%256, data    ) ) % 256
		#print "checksum = %s" % hex(checksum)
		check1byte = 0x30 + (checksum%0x10)
		check2byte = 0x30 + (checksum - checksum%0x10) / 16

		message.insert(0, STX)
		message.extend(data)

		# Now that the checksums have been all calculated, we need
		# to add the escape characters. The character 0xD0 is illegal, 
		# which is really annoying. It needs to be replaced by 0x07, 0x31 
		# AFTER calculating the checksum.

		for i in range(len(message)):
			# Replace carriage returns.
			if message[i] == 0x0D:
				message[i] = 0x07
				message.insert(i+1, 0x31)

		# Now we should be good to add the checksum bytes and finish up with a <CR>.
		message.extend([ check2byte, check1byte, 0x0D ])

		#print [ hex(x) for x in message ]
		#print [ chr(x) for x in message ]
		result = reduce(lambda x,y: x+y, [ chr(x) for x in message ])

		self.serial_connection.write( result )

	def read(self):
		# Get all of the data together.
		data = self.serial_connection.read(100)
		result = bytearray(data)
		#print [ hex(x) for x in result ]
		
		STX 	= result.pop(0)
		ADDR 	= result.pop(0)
		CMD_RSP = result.pop(0)	

		# Now strip off the second-layer protocol garbage
		READWRITE 	= result.pop(0)
		HASH 		= [ result.pop(0), result.pop(0), result.pop(0) ]
		INDEX		= result.pop(0)

		# Check the result to make sure it is sensible
		if STX != 0x02 or ADDR != 0x10 or READWRITE != 0x63:
			raise Exception("The data from the compressor was invalid -- the serial connection may have been lost.")

		# Take off the checksums.
		[CR, check2byte, check1byte] = [result.pop(), result.pop(), result.pop()]

		value = 0
		index = 0

		# Sometimes we get a weird fifth byte
		# in the syncom multidrop. But it's useless. So get rid of it.
		if len(result) > 4:
			result.pop()

		for b in reversed(result):
			value += b * ( 2**(8*index) )
			index += 1

		if value > 67370:
			print "Problem with syncom multidrop message. Received: "
			print [ hex(x) for x in bytearray(data) ]

		return value