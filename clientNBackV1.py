import ctypes as ct
import socket
import numpy as np
import serial
from ctypes.util import find_library
import time
import cv2
import errno
import select
import sys


dataPath = sys.argv[1]
print("Data Path:", dataPath)

#Define EvoIRFrameMetadata structure for additional frame infos
class EvoIRFrameMetadata(ct.Structure):
     _fields_ = [("counter", ct.c_uint),
                 ("counterHW", ct.c_uint),
                 ("timestamp", ct.c_longlong),
                 ("timestampMedia", ct.c_longlong),
                 ("flagState", ct.c_int),
                 ("tempChip", ct.c_float),
                 ("tempFlag", ct.c_float),
                 ("tempBox", ct.c_float),
                 ]

    # OPTRIS INITIALIZATION
    # load library on linux
    
frameSize = (382, 288)
libir = ct.cdll.LoadLibrary(ct.util.find_library("irdirectsdk"))
 #path to config xml file
pathXml = ct.c_char_p(b'../config/20072014.xml')

# init vars
pathFormat = ct.c_char_p()
pathLog = ct.c_char_p(b'./logs/logfilename')

palette_width = ct.c_int()
palette_height = ct.c_int()

thermal_width = ct.c_int()
thermal_height = ct.c_int()

serial = ct.c_ulong()

# init EvoIRFrameMetadata structure
metadata = EvoIRFrameMetadata()

# init lib
ret = libir.evo_irimager_usb_init(pathXml, pathFormat, pathLog)
if ret != 0:
    print("error at init")
    exit(ret)

# get thermal image size
libir.evo_irimager_get_thermal_image_size(ct.byref(thermal_width), ct.byref(thermal_height))
print('thermal width: ' + str(thermal_width.value))
print('thermal height: ' + str(thermal_height.value))

# get palette image size
libir.evo_irimager_get_palette_image_size(ct.byref(palette_width), ct.byref(palette_height))
print('palette width: ' + str(palette_width.value))
print('palette height: ' + str(palette_height.value))

# init thermal data container
np_thermal = np.zeros([thermal_width.value * thermal_height.value], dtype=np.uint16)
npThermalPointer = np_thermal.ctypes.data_as(ct.POINTER(ct.c_ushort))

# init image container
np_img = np.zeros([palette_width.value * palette_height.value * 3], dtype=np.uint8)
npImagePointer = np_img.ctypes.data_as(ct.POINTER(ct.c_ubyte))

    # call once outside for init.
ret = libir.evo_irimager_get_thermal_palette_image_metadata(thermal_width, thermal_height, npThermalPointer, palette_width, palette_height, npImagePointer, ct.byref(metadata))

# give it some time to spawn
time.sleep(1) # Wait for 1 second

HOST = 'localhost'
PORT = 1033

captureDuration = 60 # in seconds?
optrisFrameRate = 20 # fps
offset = 1.05 # how much to overshoot memory space 105%


captureFrames = int(round(optrisFrameRate * captureDuration * offset)) 

# Create a socket 
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

trialsHeatMatrix = np.zeros([captureFrames, thermal_width.value * thermal_height.value], dtype=np.float32)
timestampMatrix = np.zeros([captureFrames], dtype=np.float64)

endCount = 0
trial = 0
frame = 0

try:
    s.connect((HOST, PORT))
    print(f"Connected to {HOST}:{PORT}")
    
    msgStartReady = b"Start Ready"
    msgcollected = b"Collected"
    msgSaved = b"Saved"
    
    # set socket as non-blocking
    s.setblocking(False)

    while True:
        # Receive data from server to begin data collection.
        # does it wait until message comes? check it out.
        
        try:
            serverMessage = s.recv(1024).decode()

            if 'Collect' in serverMessage:
                print(serverMessage)
                block = serverMessage[-2]
                level = serverMessage[-1]
                frame = 0

                while serverMessage != "Stop":
                    ret = libir.evo_irimager_get_thermal_palette_image_metadata(thermal_width, thermal_height, npThermalPointer, palette_width, palette_height, npImagePointer, ct.byref(metadata))

                    if ret != 0:
                        print('error on evo_irimager_get_thermal_palette_image ' + str(ret))
                        continue  

                    # print(trial, frame)
                    trialsHeatMatrix[frame, :]  = np_thermal
                    timestampMatrix[frame] = metadata.timestamp

                    frame += 1

                    try:
                        serverMessage = s.recv(1024).decode()

                    except IOError as e:
                        if e.errno != errno.EAGAIN and e.errno != errno.EWOULDBLOCK:
                            print('Reading error: {}'.format(str(e)))
                            sys.exit()

                        # We just did not receive anything
                        continue

                np.save(dataPath + '/imagesBlock' + str(block) + 'level' + str(level), trialsHeatMatrix)
                np.save(dataPath + '/timeStampBlock' + str(block) + 'level' + str(level), timestampMatrix)       
                
                trialsHeatMatrix = np.zeros([captureFrames, thermal_width.value * thermal_height.value], dtype=np.float32)
                timestampMatrix = np.zeros([captureFrames], dtype=np.float64)
                s.sendall(msgSaved)  
                
                trial += 1

            elif serverMessage == 'End':
                print(serverMessage)
                break
               


        except IOError as e:
            # This is normal on non blocking connections - when there are no incoming data error is going to be raised
            # Some operating systems will indicate that using AGAIN, and some using WOULDBLOCK error code
            # We are going to check for both - if one of them - that's expected, means no incoming data, continue as normal
            # If we got different error code - something happened
            if e.errno != errno.EAGAIN and e.errno != errno.EWOULDBLOCK:
                print('Reading error: {}'.format(str(e)))
                sys.exit()

            # We just did not receive anything
            continue
        
	

        
except OSError as e:
    print(f"Error: {e}")
    
finally:
    s.close()
    print('CLOSE CLIENT SCRIPT')

    
    
    
