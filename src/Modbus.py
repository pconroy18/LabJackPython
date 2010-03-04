# File: Modbus.py
# Author: LabJack Corp.
# Created: 05.05.2008
# Last Modified: 12/3/2009

from struct import pack, unpack #, unpack_from  # unpack_from is new in 2.5

AES_CHANNEL               = 64000
IP_PART1_CHANNEL          = 64008
IP_PART2_CHANNEL          = 64009
PORT_CHANNEL              = 64010
HEARTBEAT_CHANNEL         = 64016

DEBUG_CHANNEL             = 64017
DEVICE_TYPE_CHANNEL       = 65000
SERIAL_NUMBER_CHANNEL     = 65001

READ_PACKET               = 3
WRITE_PACKET              = 6

HEADER_LENGTH             = 9
BYTES_PER_REGISTER        = 2

# See the LabJack Modbus Protocol doc.
# 6 byte packet, which includes the 255 following the 6
OUTGOING_HEADER_BYTES = (0, 0, 6, 0xff)
TCP_HEADER = pack('>HHHB', *OUTGOING_HEADER_BYTES)

def readHoldingRegistersRequest(addr, numReg = None, unitId = None):
    if numReg is None:
        numReg = calcNumberOfRegisters(addr)
        
    if unitId is None:
        packet = TCP_HEADER + pack('>BHH', 0x03, addr, numReg)
    else:
        bytes = list(OUTGOING_HEADER_BYTES)
        bytes[3] = unitId
        packet = pack('>HHHB', *bytes) + pack('>BHH', 0x03, addr, numReg)

    return packet

def readHoldingRegistersResponse(packet, payloadFormat=None):
    # Example: Device type is 9
    # [0, 0, 5, 255, 3, 2, 9]
    #  H  H  H    c  c  c  payload
    #  0  1  2    3  4  5  6+
    HEADER_LENGTH = 9
    header = unpack('>HHHBBB', packet[:HEADER_LENGTH])
    #print "header", [ c for c in header ]
    #print "header", header
    
    #print "packet", [ c for c in packet ]

    #Check for exception
    if header[4] == 0x83:
        raise ModbusException(header[5])

    #Check for proper command
    if header[4] != 0x03:
        raise ModbusException("Not a read holding registers packet.")

    #Check for proper length
    payloadLength = header[5]
    if (payloadLength + HEADER_LENGTH) != len(packet):
        #print "packet length is", len(packet)
        #print "payload and header is", payloadLength + HEADER_LENGTH
        raise ModbusException("Packet length not valid.")

    if payloadFormat is None:
        payloadFormat = '>' + 'H' * (payloadLength/2)

    # When we write '>s', we mean a variable-length string.
    # We just didn't know the length when we wrote it.
    if payloadFormat == '>s': 
       payloadFormat = '>' + 's' *  payloadLength

    #print "Info: "
    #print payloadFormat
    #print type(packet)
    #print [ ord(c) for c in packet ]
    
    # Mike C.: unpack_from new in 2.5.  Won't work on Joyent.
    #payload = unpack_from(payloadFormat, packet, offset = HEADER_LENGTH)
    payload = unpack(payloadFormat, packet[HEADER_LENGTH:])
    
    if len(payload) == 1:
        return payload[0]
    else:
        return list(payload)

def readInputRegistersRequest(addr, numReg = None):
    if numReg is None:
        numReg = calcNumberOfRegisters(addr)
    packet = TCP_HEADER + pack('>BHH', 0x04, addr, numReg)
    #print "making readHoldingRegistersRequest packet"
    #print [ ord(c) for c in packet ]
    return packet

def readInputRegistersResponse(packet, payloadFormat=None):
    # Example: Device type is 9
    # [0, 0, 5, 255, 3, 2, 9]
    #  H  H  H    c  c  c  payload
    #  0  1  2    3  4  5  6+
    HEADER_LENGTH = 9
    header = unpack('>HHHBBB', packet[:HEADER_LENGTH])
    #print "header", [ c for c in header ]
    #print "header", header
    
    #print "packet", [ c for c in packet ]

    #Check for exception
    if header[4] == 0x83:
        raise ModbusException(packet[5])

    #Check for proper command
    if header[4] != 0x04:
        raise ModbusException("Not a read holding registers packet.")

    #Check for proper length
    payloadLength = header[5]
    if (payloadLength + HEADER_LENGTH) != len(packet):
        #print "packet length is", len(packet)
        #print "payload and header is", payloadLength + HEADER_LENGTH
        raise ModbusException("Packet length not valid.")

    if payloadFormat is None:
        payloadFormat = '>' + 'H' * (payloadLength/2)

    # When we write '>s', we mean a variable-length string.
    # We just didn't know the length when we wrote it.
    if payloadFormat == '>s': 
       payloadFormat = '>' + 's' *  payloadLength

    #print payloadFormat
    #print [ ord(c) for c in packet ]
    
    # Mike C.: unpack_from new in 2.5.  Won't work on Joyent.
    #payload = unpack_from(payloadFormat, packet, offset = HEADER_LENGTH)
    payload = unpack(payloadFormat, packet[HEADER_LENGTH:])

    return payload


def writeRegisterRequest(addr, value, unitId = None):
    if not isinstance(value, int):
        raise TypeError("Value written must be an integer.")

    if unitId is None:
        packet = TCP_HEADER + pack('>BHH', 0x06, addr, value)
    else:
        bytes = list(OUTGOING_HEADER_BYTES)
        bytes[3] = unitId
        packet = pack('>HHHB', *bytes) + pack('>BHH', 0x06, addr, value)

    return packet
    
def writeRegistersRequest(startAddr, values, unitId = None):
    numReg = len(values)
    
    for v in values:
        if not isinstance(v, int):
            raise TypeError("Value written must be an integer.")
    
    if unitId is None:
        unitId = 0xff
    
    header = (0, 0, 7+(numReg*2), unitId, 16, startAddr, numReg, numReg*2)
    header = pack('>HHHBBHHB', *header)
    
    format = '>' + 'H' * numReg
    packet = header + pack(format, *values)
    return packet

def writeAesStingRegisterRequest(addr, a, b):
    packet = TCP_HEADER + pack('>BHcc', 0x06, addr, a, b)
    return packet

    
def writeRegisterRequestValue(data):
    """Return the value to be written in a writeRegisterRequest Packet."""
    packet = unpack('>H', data[10:])
    return packet[0]


class ModbusException(Exception):
    
    def __init__(self, exceptCode):
        self.exceptCode = exceptCode

    def __str__(self):
        return repr(self.exceptCode)


def calcNumberOfRegisters(addr):
    return calcNumberOfRegistersAndFormat(addr)[0]

def calcFormat(addr):
    return calcNumberOfRegistersAndFormat(addr)[1]

def calcNumberOfRegistersAndFormat(addr):
    # TODO add special cases for channels above
    if addr < 1000:
        # Analog Inputs
        return (2, '>f')
    elif addr >= 5000 and addr < 6000:
        # DAC Values
        return (2, '>f')
    elif addr >= 7000 and addr < 8000:
        # Timers / Counters
        return (2, '>I')
    elif addr in range(64008,64018) or addr == 65001:
        # Serial Number
        return (2, '>I')
    elif addr in range(10000,10010):
        # VBatt/Temp/RH/Light/Pressure
        return (2, '>f')
    elif addr in range(57002, 57010):
        # TX/RX Bridge stuff
        return (2, '>I')
    elif addr in range(57050, 57056):
        # VUSB/VJack/VST
        return (2, '>f')
    else:
        return (1, '>H')


def getStartingAddress(packet):
    """Get the address of a modbus request"""
    return ((ord(packet[8]) << 8) + ord(packet[9]))

    
def getRequestType(packet):
    """Get the request type of a modbus request."""
    return ord(packet[7])
    
def getTransactionId(packet):
    """Pulls out the transaction id of the packet"""
    if isinstance(packet, list):
        return unpack(">H", pack("BB", *packet[:2]) )
    else:
        return unpack(">H", packet[:2])