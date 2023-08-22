from psychopy import visual, core, logging
from psychopy.visual import TextStim, Rect

import pandas as pd
import numpy as np
import socket, serial, os, subprocess
import cedrus_util
from blockConditions import informationInputGUI, instructions, nbackStim, collectResponse, saveExperimentData


def experiment(participantInfo, path, level, numBlocks, numStimuli, experimentBlocksLabels, experimentBlocksStim, itemStimSize, preBlockDuration, prestimDuration, stimDuration, postStimDuration):

    # Socket settings.
    HOST = '127.0.0.1'
    PORT = 1033
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    
    # messages to send to thermal camera.
    msgCollect = 'Collect'
    msgEndTrial = bytes('Stop', 'utf-8')
    msgEndExp = bytes('End', 'utf-8')

    try:
    	s.bind((HOST, PORT))
    	s.listen(1) # only one connection
    	print(f"Listening on {HOST}:{PORT}...")
    	
    	
    	# cedrus initialization.
    	portname, keymap = cedrus_util.getname()
    	ser = serial.Serial(portname, 115200) 

   
    	# psychopy initialization.
    	win = visual.Window(size=(1920, 1080), units='pix', fullscr = True)
    	win.recordFrameIntervals = True    
    	win.refreshThreshold = 1/60 + 0.004
    	frameRate = round(win.getActualFrameRate())

    	# cedrus and regular timer.
    	cedrus_util.reset_timer(ser)    # reset responsebox timer
    	timer = core.Clock()
    	experimentStartTime = timer.getTime() * 1000
    	print('fps', frameRate)

    	# load instructions.
    	instructions(win, timer, ser, keymap, -3)
    	instructions(win, timer, ser, keymap, -2)
    	instructions(win, timer, ser, keymap, -1)
    
   	 # DIGITAL: photocell presentation
    	digitalPhotoLeft = visual.ImageStim(win=win, image='./photocell/rect.png', units="pix", pos=(-930,-110))
    	digitalPhotoRight = visual.ImageStim(win=win, image='./photocell/rect.png', units="pix", pos=(930,-110)) 
	
    	# ANALOG: photocell presentation
    	analogPhotoLeft = visual.ImageStim(win=win, image='./photocell/rect.png', units="pix", pos=(-930,-230))
    	analogPhotoRight = visual.ImageStim(win=win, image='./photocell/rect.png', units="pix", pos=(930,-230))


    	# load up the circle grid reference
    	circlePositionGrid = [[125, 0],
                        [88, 88],
                        [0, 125],
                        [-88, 88],
                        [-125, 0],
                        [-88, -88],
                        [0, -125],
                        [88, -88]]
    	circleStimRef = []

    	for i, circlePos in enumerate(circlePositionGrid):
        	circleStimRef.append(Rect(
                win=win,
                units="pix",
                width=50,
                height=50,
                lineColor = "white",
                pos = circlePos))

    	screenshot = visual.BufferImageStim(win, stim=circleStimRef)
    	# screenshot.setAutoDraw(True)

    	# the actual stim!!
    	rectPos = Rect(
    	win=win,
    	units="pix",
    	width=50,
    	height=50,
    	fillColor= "black")

    	# first fixation to start experiment:
    	fixation = TextStim(win, text = '+', pos = (0,0), color = 'white', height = 25)
    	preBlockDurationFrames = round((preBlockDuration / 1000) * frameRate)
    	prestimDurationFrames = round((prestimDuration / 1000) * frameRate)
    	postStimDurationFrames = round((postStimDuration / 1000) * frameRate)
    	stimDurationFrames = round((stimDuration / 1000) * frameRate)

    	correct = None

       # Experiment goes here.  
       
       
    	# it waits until a connection is made here!
    	subprocess.Popen(['python', 'clientNBackV1.py', path])        
    	conn, addr = s.accept()
    	
    	
    
    	for block in range(numBlocks): # there are 10 blocks total for each level.
            blockData = []

            for lvl in range(level): # go through each level: 1-back, 2-back, 4-back
                fixation.color = "white"
                # Prompt telling them that the next level is starting.
                instructions(win, timer, ser, keymap, lvl)

                screenshot.setAutoDraw(True)
                fixation.setAutoDraw(True)

            
                # a little bit of time before the block actually begins!
                for frame in range(preBlockDurationFrames): # 0(n)
                    win.flip()
                
                # okay start thermal imaging here!!!!!
                
                analogPhotoLeft.setAutoDraw(True)
                digitalPhotoLeft.setAutoDraw(True)
                
            	
                msgCollectLabel = bytes(msgCollect + str(block) + str(lvl), 'utf-8')

		# send message to thermal camera for block 
                conn.sendall(msgCollectLabel)
                
                for pos in range(numStimuli): # all the stimuli to pop out in that level-block
                
                    stim = experimentBlocksStim[lvl, block, pos, :]
                    label = experimentBlocksLabels[lvl, block, pos]

                    fixation.color = "white"
                    
                    

                    # prestim duration: 500 ms
                    for frame in range(prestimDurationFrames): # 0(n)
                        win.flip()

                    # stim duration: 250 ms
                    nbackStim(win, digitalPhotoRight, rectPos, stim, stimDurationFrames)

                    # post-stim / collect response: 1000 ms response
                    response = collectResponse(win, ser, keymap, fixation, postStimDurationFrames)
                
                    # feedback color
                    if response == label:
                        fixation.color = "green"
                        correct = 1
                    else:
                        fixation.color = "red"
                        correct = 0

                    # feedback presentation: 250 ms feedback
                    for frame in range(stimDurationFrames): # 0(n)
                        win.flip()

                    blockData.append({'level': lvl, ' block': block, 'pos': pos, 'target': label, 'response': response, 'correct': correct})
            
                    # reset back to white.
                    fixation.color = "white"
            
                conn.sendall(msgEndTrial)
                
                # check that the data has been saved.
                data = conn.recv(1024).decode()
                while data != 'Saved':
                    data = conn.recv(1024).decode()
                    
                
                print('saved block')
                fixation.setAutoDraw(False)
                screenshot.setAutoDraw(False)
                digitalPhotoLeft.setAutoDraw(False)
                analogPhotoLeft.setAutoDraw(False)

            # print(blockData)
            saveExperimentData(participantInfo, blockData, block, path)
            blockData = []

            print()

        #win.close()
        #core.quit()
    except OSError as e:
        print(f"Error: {e}")
        
        
    finally:
        s.close()
        win.close()
        core.quit()
        
    return

if __name__ == '__main__':
    participantInfo = informationInputGUI()

    currentPath = os.getcwd()
    path = os.path.join(currentPath, 'data/' + participantInfo['Participant ID'] + 'Session' + participantInfo['Session'])

    if not os.path.isdir(path):
            os.mkdir(path)

    if participantInfo['Session'] == 'practice':
        print('practice')
        # participant0_labels
        experimentBlocksLabels = np.load('participant' + participantInfo['Participant ID'] + '_labels.npy')
        experimentBlocksStim = np.load('participant' + participantInfo['Participant ID'] + '_stim.npy')

        experiment(participantInfo = participantInfo, path = path, level = 3, numBlocks = 10, numStimuli = 30, experimentBlocksLabels = experimentBlocksLabels,
                    experimentBlocksStim = experimentBlocksStim, itemStimSize =  25, preBlockDuration = 500, prestimDuration = 500, stimDuration = 250, postStimDuration = 1000)

