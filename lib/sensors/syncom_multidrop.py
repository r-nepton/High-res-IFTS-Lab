import serial
import serial_dummy
from functools import reduce


class SyncomMultiDropAdapter:
    def __init__(self):
        try:
            self.serial_connection = serial.Serial('/dev/HE_COMPRESSOR', 9600, timeout=0.1)
        except Exception:
            print("There was a problem connecting to the serial port constructor of: %s" % self.__class__.__name__)
            self.serial_connection = serial_dummy.SerialDummy()

    def write(self, data=[0x63, 0x0D, 0x8F, 0x00]):
        STX = 0x02  # STX byte

        message = []
        message.append(0x10)  # Address (16)
        message.append(0x80)  # CMD_RSP (dictionary read)

        checksum = (reduce(lambda x, y: (x + y) % 256, message) +
                    reduce(lambda x, y: (x + y) % 256, data)) % 256
        check1byte = 0x30 + (checksum % 0x10)
        check2byte = 0x30 + (checksum - checksum % 0x10) // 16  # // for integer division

        message.insert(0, STX)
        message.extend(data)

        # The character 0xD0 is illegal — replace 0x0D with 0x07, 0x31
        # AFTER calculating the checksum.
        for i in range(len(message)):
            if message[i] == 0x0D:
                message[i] = 0x07
                message.insert(i + 1, 0x31)

        # Add checksum bytes and finish with <CR>
        message.extend([check2byte, check1byte, 0x0D])

        # Python 3: serial.write() requires bytes, not a str
        self.serial_connection.write(bytes(message))

    def read(self):
        data = self.serial_connection.read(100)
        result = bytearray(data)
        print([hex(x) for x in result])

        STX     = result.pop(0)
        ADDR    = result.pop(0)
        CMD_RSP = result.pop(0)

        # Strip second-layer protocol fields
        READWRITE = result.pop(0)
        HASH      = [result.pop(0), result.pop(0), result.pop(0)]
        INDEX     = result.pop(0)

        if STX != 0x02 or ADDR != 0x10 or READWRITE != 0x63:
            raise Exception("The data from the compressor was invalid -- the serial connection may have been lost.")

        # Remove checksums
        [CR, check2byte, check1byte] = [result.pop(), result.pop(), result.pop()]

        value = 0
        index = 0

        print([hex(x) for x in result])

        for b in reversed(result):
            value += b * (2 ** (8 * index))
            index += 1

        return value