from psychopy import visual, core, logging
from psychopy.visual import TextStim, Rect

import pandas as pd
import numpy as np
import serial
import os
import cedrus_util
from blockConditions import informationInputGUI, instructions, nbackStim, collectResponse, saveExperimentData


def experiment(participantInfo, path, level, numBlocks, numStimuli, experimentBlocksLabels, experimentBlocksStim, itemStimSize, preBlockDuration, prestimDuration, stimDuration, postStimDuration):
    # cedrus initialization
    portname, keymap = cedrus_util.getname()
    ser = serial.Serial(portname, 115200) 

   
    # psychopy initialization
    win = visual.Window(size=(1920, 1080), units='pix', fullscr = False)
    win.recordFrameIntervals = True    
    win.refreshThreshold = 1/60 + 0.004
    frameRate = round(win.getActualFrameRate())

    # cedurs and regular timer
    cedrus_util.reset_timer(ser)    # reset responsebox timer
    timer = core.Clock()
    experimentStartTime = timer.getTime() * 1000
    print('fps', frameRate)

    # load instructions
    instructions(win, timer, ser, keymap, -3)
    instructions(win, timer, ser, keymap, -2)
    instructions(win, timer, ser, keymap, -1)

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
    for block in range(numBlocks):
        blockData = []

        for lvl in range(level):
            fixation.color = "white"
            # Prompt telling them that the next level is starting.
            instructions(win, timer, ser, keymap, lvl)

            screenshot.setAutoDraw(True)
            fixation.setAutoDraw(True)

            # a little bit of time before the block actually begins!
            for frame in range(preBlockDurationFrames): # 0(n)
                win.flip()

            for pos in range(numStimuli):
                
                stim = experimentBlocksStim[lvl, block, pos, :]
                label = experimentBlocksLabels[lvl, block, pos]

                fixation.color = "white"

                # prestim duration
                for frame in range(preBlockDurationFrames): # 0(n)
                    win.flip()

                # stim duration
                nbackStim(win, rectPos, stim, stimDurationFrames)

                # post-stim / collect response
                response = collectResponse(win, ser, keymap, fixation, postStimDurationFrames)
                
                # feedback color
                if response == label:
                    fixation.color = "green"
                    correct = 1
                else:
                    fixation.color = "red"
                    correct = 0

                # feedback presentation
                for frame in range(stimDurationFrames): # 0(n)
                    win.flip()

                blockData.append({'level': lvl, ' block': block, 'pos': pos, 'target': label, 'response': response, 'correct': correct})
            
                # reset back to white.
                fixation.color = "white"
            
            

            fixation.setAutoDraw(False)
            screenshot.setAutoDraw(False)

        print(blockData)
        saveExperimentData(participantInfo, blockData, block, path)
        blockData = []


        print()





    win.close()
    core.quit()

    return

if __name__ == '__main__':
    participantInfo = informationInputGUI()

    currentPath = os.getcwd()
    path = os.path.join(currentPath, 'data\\' + participantInfo['Participant ID'] + 'Session' + participantInfo['Session'])

    if not os.path.isdir(path):
            os.mkdir(path)

    if participantInfo['Session'] == 'practice':
        print('practice')
        # participant0_labels
        experimentBlocksLabels = np.load('participant' + participantInfo['Participant ID'] + '_labels.npy')
        experimentBlocksStim = np.load('participant' + participantInfo['Participant ID'] + '_stim.npy')

        experiment(participantInfo = participantInfo, path = path, level = 3, numBlocks = 10, numStimuli = 30, experimentBlocksLabels = experimentBlocksLabels,
                    experimentBlocksStim = experimentBlocksStim, itemStimSize =  25, preBlockDuration = 500, prestimDuration = 500, stimDuration = 250, postStimDuration = 1000)

