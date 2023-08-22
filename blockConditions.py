from psychopy.visual import TextStim, Rect
from psychopy import visual, data, event, core, gui, sound
from numpy.random import binomial
import numpy as np
import pandas as pd
import serial
import cedrus_util
import os


def instructions(win, timer, ser, keymap, part):
    if part == -3:
        instructions = TextStim(win, text = 'Welcome to the N-back task! In this task, you will be performing three levels ' +
                                            'of N-back (1-back, 2-back, and 4-back), and the levels will be interleaved. ' + 
                                            'Additionally, you will receive feedback on your responses.\n\n' + 
                                            '(Press any button to continue instructions)', pos = (0,0))
    elif part == -2:
        instructions = TextStim(win, text = 'Task Description:\n\n' + 
                                            '1. Throughout the task, keep your eyes fixated on the fixation cross.\n'
                                            '2. You will be presented with multiple empty squares on the screen.\n' + 
                                            '3. One at a time, a random square will be filled briefly.\n' + 
                                            '4. Your objective is to determine if the currently filled square ' + 
                                            'matches the square shown either 1, 2, or 4 presentations ago\n' + 
                                            '5. If the current stimulus matches the one that appeared N-positions ' +
                                            'back (1, 2, or 4), press the "right" button when the fixation cross turns black.\n' + 
                                            '6. If the current stimulus is different from the one shown N-positions ' + 
                                            'back, press "left" button  when the fixation cross turns black.\n\n'

                                            '(Press any button to continue instructions)', pos = (0,0))
    elif part == -1:
        instructions = TextStim(win, text = 'Task Description:\n\n' + 
                                            '7. Remember that N-back level will change throughout the task (1-back, 2-back, or 4-back), ' + 
                                            'so stay attentive to the current level.\n'
                                            '8. Maintain a high level of concentration and mental focus as you ' + 
                                            'compare each stimulus to the one that appeared N-positions ago.\n' + 
                                            '9. Respond as accurately and quickly as possible. The black fixation will ' + 
                                            'dissapear if no response is given.\n'
                                            '10. The fixation cross will turn green for correct responses, and will ' + 
                                            'turn red for incorrect responses. Use the feedback to adjust your performance.\n\n' + 
                                            '(Press any button to begin task)', pos = (0,0))
    
    elif part == 0:
        instructions = TextStim(win, text = '1-BACK', pos = (0,0))
    elif part == 1:
        instructions = TextStim(win, text = '2-BACK', pos = (0,0))
    elif part == 2:
        instructions = TextStim(win, text = '4-BACK', pos = (0,0))

    instructions.setAutoDraw(True)
    keep_going = True
    totalFrames = 0
    startTime = timer.getTime()
    cedrus_util.reset_timer(ser)    # reset responsebox timer
    keylist = []

    while keep_going:
        totalFrames += 1
        win.flip()
        receiveBuffer = ser.in_waiting
        
        if receiveBuffer != 0:
            endTimer = timer.getTime()
            keylist.append(ser.read(ser.in_waiting))
            key, press, time = cedrus_util.readoutput([keylist[-1]], keymap)
            if key and press == [1]:
                break
    
    endTime = endTimer - startTime
    # convert the time of correct button push

    try:
    	endTimeCedrus = cedrus_util.HexToRt(cedrus_util.BytesListToHexList(time))
    except IndexError:
    	print('Index Error Instance Caught')
    	endTimeCedrus = 999
    
    instructions.setAutoDraw(False)
            
    return
    #  {'Stim Type': 'Instructions', 'Start Time (ms)': startTime * 1000,
    #         'Total Time (ms)': endTime * 1000, 'CEDRUS Total Time (ms)': endTimeCedrus, 'Total Frames': totalFrames}

#===========================================================================================================================

def nbackStim(win, digitalPhotoRight, rectPos, stim, stimDurationFrames):
    rectPos.pos = stim
    rectPos.setAutoDraw(True)
    digitalPhotoRight.setAutoDraw(True)
    
    for frame in range(stimDurationFrames): # 0(n)
        win.flip()
        
    rectPos.setAutoDraw(False)
    digitalPhotoRight.setAutoDraw(False)
    return

#===========================================================================================================================

def collectResponse(win, ser, keymap, fixation, postStimDurationFrames):
    cedrus_util.clear_buffer(ser)
    cedrus_util.reset_timer(ser)    # reset responsebox timer
    keylist = []

    key, press, time = None, None, None
    fixation.color = "black"
    for frame in range(postStimDurationFrames): 
        win.flip()
        receiveBuffer = ser.in_waiting
        if receiveBuffer >= 6 and key == None:
            keylist.append(ser.read(ser.in_waiting))
            key, press, time = cedrus_util.readoutput([keylist[-1]], keymap)
            # print(time, key)
        cedrus_util.clear_buffer(ser)

    try:
        # reactionTimeCedrus = cedrus_util.HexToRt(cedrus_util.BytesListToHexList(time))
        # print(reactionTimeCedrus)
        if key == [0]:
            key = 0
        elif key == [-1]:
            key = 1

    except IndexError:
        print('Index Error Instance Caught')
        # reactionTimeCedrus = 999   
    except TypeError:
        print('No response')
        key = -1

    return key

#===========================================================================================================================

def saveExperimentData(participantInfo, experimentData,  block, dataPath):
    participantInfo['Experiment Data'] = experimentData
    df = pd.DataFrame.from_dict(participantInfo)
    csvFileName = participantInfo['Participant ID'] + '_' + participantInfo['date'] +  '_block' + str(block) + '.csv'
    df.to_csv(os.path.join(dataPath, csvFileName))

    return

#===========================================================================================================================



def informationInputGUI():
    exp_name = 'N-Back Task'
    exp_info = {'Participant ID': '',
    		    'Session': ('practice', '1', '2'),
                'age': ''}

    dlg = gui.DlgFromDict(dictionary = exp_info, title = exp_name)
    exp_info['date'] = data.getDateStr()
    exp_info['exp name'] = exp_name
    
    if dlg.OK == False:
        core.quit() # ends process.
    return exp_info
