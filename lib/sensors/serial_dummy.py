class SerialDummy:
    def __init__(self):
        print("SerialDummy: no hardware — using dummy serial port")
        
    def write(self, data):
        print(f"SerialDummy.write: {list(data)}")
        
    def read(self, size=1):
        return bytes(size)
    
    def reset_input_buffer(self):
        pass
    
    def reset_output_buffer(self):
        pass
    
    def close(self):
        pass

	# class SerialDummy:
# 	def __init__(self, *args):
# 		pass

# 	def write(self, *args):
# 		pass

# 	def read(self, *args):
# 		return ""