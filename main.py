
import datetime
import pygame
import numpy as np
import time
import sys
import os
import binascii
import struct
import read_joystick
import track_movement
import shared
import random
import math


def main():

    global CURSOR_FEEDBACK
    global condition
    global TARGETSET


    # initialize the module containing global variables
    shared.init()

    # get the subject name
    if len(sys.argv)>1:
        subject = sys.argv[1]
    else:
        subject = ""

    while len(subject)==0:
        subject = input('Subject ID: ')

    subject = subject.replace(' ','_') # remove spaces because they mess up our file structure later
    print ("Subject: %s"%subject)


    if len(sys.argv)>2:
        schedulef = sys.argv[2]
        print ("Schedule file: %s"%schedulef)
    else:
        schedulef = ""

    while not os.path.exists(schedulef):
        schedulef = input('Schedule filename: ')
        if not os.path.exists(schedulef):
            print("File does not exist.")
    
    global mySchedule
    mySchedule = shared.readSchedule(schedulef)


    global seq_LastTr

    lastTr      = mySchedule[-1]
    seq_LastTr  = len(mySchedule)/(1+lastTr["block"])-1


    print ("")
    if len(sys.argv)>3:
        calibf = sys.argv[3]
        print ("Calibration file %s"%calibf)
    else:
        calibf = ""

    while not os.path.exists(calibf):
        schedulef = input('Calibration file: ')
        if not os.path.exists(calibf):
            print("File does not exist.")


    print(sys.argv)
    
    condition = "slt"
    if len(sys.argv)>4:
        cond = sys.argv[4]
        if cond=="slt" or cond== "rlt" or cond == "adaptation":
            condition = cond
        else:
            print('\n\n#### CANNOT INTERPRET CONDITION "%s"' %cond)
            sys.exit(-1)
                


    if condition in ("slt", "rlt"):
        tmp =0
        for i in range(len(mySchedule)):
            tmp += mySchedule[i]["rotation"]
        if tmp != 0:
            print("The selected 'schedule' file is for the ADAPTATION condition. Please change the schedule.")
            sys.exit(-1)

    if len(sys.argv)>5:
        if sys.argv[5]== "explicit":
            shared.explicit = True
        elif sys.argv[5]== "implicit":
            shared.explicit = False
        else:
            print('\n\n#### CANNOT INTERPRET LAST INPUT "%s"' %sys.argv[5])
            sys.exit(-1)

            
    now = datetime.datetime.now()

    prefix = (
        subject
        + '_'
        + format(now.year)
        + format(now.month)
        + format(now.day)
        + '_'
        + format(now.hour)
        + format(now.minute)
        + format(now.second)
    )

    # Read the joystick calibration
    shared.readCalib(calibf)


    # initialize the output file
    shared.init_logs(prefix,schedulef)


    global seqlength
    for seqlength in range(len(mySchedule)):
        if mySchedule[seqlength]["seq"] == 1:
            break
    
    global cntseq
    cntseq = 0

    global all_rot
    all_rot = []
    for i in range(len(mySchedule)):
        all_rot.append(mySchedule[i]["direction"])



    print(i)
    print ("")
    print ("             Settings for this run:")
    print ("")
    print ("CONDITION                  = %s "%cond)
    print ("CURSOR_FEEDBACK            = %i "%shared.CURSOR_FEEDBACK)
    print ("USING_MR_TRIGGER           = %i "%shared.USING_TRIGGER)
    print ("MOVE_DURATION              = %i"%shared.MOVEMENT_PHASE_DURATION,"sec")
    print ("CURSOR_ON_TARGET_DURATION  = %i"%shared.TARGET_HOLD_TIME,"sec")
    print ("")
    print ("#############")
    print ("##IMPORTANT##")
    if len(shared.monitor) == 1:
        print("PRIMARY SCREEN INFO IS BEING USED FOR ALL DISTANCE MEASURES:")
        print ("SCREEN_SIZE = %imm by %imm"%(shared.widthmm, shared.heightmm))
    else:
        print("SECONDARY SCREEN INFO IS BEING USED FOR ALL DISTANCE MEASURES:")
        print ("SCREEN_SIZE = %imm by %imm"%(shared.widthmm, shared.heightmm))

    print ("#############")
    print ("")
    input("Verify that these settings are correct and press <ENTER>.")

    # initialize the pygame screen
    shared.init_pygame()

    # run feedback trials
    runTrials(shared.screen, subject)

    # close the joystick file
    # joystick[0].close()

    # close the output files
    shared.close_logs()

    # Close pygame
    shared.close_pygame()

    print("")
    print("")
    print("Experiment ended.")
    print("# of trials           %i"%(shared.TRIAL+1))
    print("# of invalid moves    %i"%(shared.N_INVALID_MOVEMENTS))
    print("# of valid moves      %i"%(shared.N_VALID_MOVEMENTS))


    


def runTrials(screen, subject):
    # Start running the trials

    global UI_TIME_REF
    global N_INVALID_MOVEMENTS
    global N_VALID_MOVEMENTS
    global AXIS_STATES
    global endblock_display
    global cntseq
    global all_rot
    global seqlength

    endblock_display = False
    quit_first = False


    # The target of the previous trial
    prevTrial = None

    # variable to track time reference points within trials
    timeReference = None

    writeCounter = 0
    instCount = 0

    # Trialdata is a dict that holds various pieces of information
    # pertaining to the current trial, such as the target angle,
    # the oscillator frequencies, and so on.
    nosound = {'f1.hz':np.nan,'f2.hz':np.nan}
    trialdata = {
        'target.angle'   :None,
        'movement.angle' :np.nan,
    }

    # We start in the "prepare" phase, so that we will choose a (first) target and set it up to play
    shared.PHASE = shared.PHASE_MAP['PREPARE']


    keep_going = True
    end_screen_shown = False # whether we have already shown the ending screen
    first_screen = True
    

    global seqnow
    global oneseq
    oneseq = all_rot[0:seqlength]
    seqnow = ""
    for i in range(len(oneseq)):
        seqnow += shared.myDict[oneseq[i]]


    while keep_going:

        # Get a time stamp for this iteration of the loop
        shared.take_time()
        
        if shared.phase_is("INIT"):

            

            # track the start of the trial
            trialStart = shared.t_since_start()
            trialdata["timestamp"] = time.time()
            trialdata["target.color"] = shared.TRIALTARGETCOLOR
            trialdata["targetHit"] = "UNKNOWN"

            print ('Target Angle: %.02f'%trialdata["target.angle"])

            shared.next_phase()
            timeReference = shared.t()


        elif shared.phase_is("MOVE"):


            curpos = (int(shared.CURSOR_EXCURSION_FAC*shared.EXCURSION*shared.AXIS_STATES['x']),
                      int(shared.CURSOR_EXCURSION_FAC*-shared.EXCURSION*shared.AXIS_STATES['y']))

            curpos = np.array(shared.rot_pos(curpos, trialdata["rotation"], [0,0])) + np.asarray(shared.SCREEN_CENTER)


            #curpos = [shared.AXIS_STATES["x"], shared.AXIS_STATES["y"]]


            goal = shared.TARGETSET[shared.myDict[trialdata["target.angle"]]]



            dist = distance(curpos, goal)   

            # allow a movement phase for some specified time
            if (shared.t() - timeReference) >= shared.MOVEMENT_PHASE_DURATION: 
                trialdata["targetHit"] = "NO"
                timeReference = shared.t()
                shared.next_phase()
            elif dist < shared.TARGET_REACH_DISTANCE: # move to the next phase when subject reaches to the target with a threshold
                trialdata["targetHit"] = "YES"
                trialdata["target.color"] = shared.TARGET_HIT_COLOR
                timeReference = shared.t()
                shared.next_phase()


        elif shared.phase_is("FEEDBACK"):

            if (shared.t() - timeReference) >= shared.TARGET_HOLD_TIME: 
                timeReferenceHold = shared.t()
                shared.next_phase()

            # display the prompt on the screen
            # textScreen(screen, mainfont, u'Return')

            # Now take the furthest position that the subject has moved to during this trial
            #x,y = trialdata["furthest.position"]
            
                if trialdata["targetHit"] == "YES":

                    print('Subject hit the target')

                elif trialdata["targetHit"] == "NO":
                    # If this was not a valid movement
                    shared.N_INVALID_MOVEMENTS += 1
                    print ( 'Subject missed the target' )




            #if shared.AUDIO_FEEDBACK:
                ## ANY AUDIO FEEDBACK WILL BE PLAYED HERE
                        

            

        elif shared.phase_is("WRITE"):

            writeCounter += 1

            ###### Write data from the previous trial while waiting for the next trial to happen

            #print shared.PHASE_LOG

            # Write the log about this trial.
            shared.write_trial_log(trialdata,subject)

            # Write the movement data
            shared.write_movement_log()

            
            shared.next_phase()

            # empty the list of movements (we can't do this earlier because the inter-trial-display needs the MOVEMENT to display)
            shared.MOVEMENT      = []
            shared.UNINTERPRETED = []


            # save angles to be avoided in the next trial
            



        elif shared.phase_is("PREPARE"):

            if not shared.schedule_done():
                ##
                ## Start setting up the next trial 
                ## (since we're in "wait" mode anyway)
                ## (but not yet running it)
                ##

                # select the target for the next trial
                sch = mySchedule[shared.TRIAL+1]
                trialdata["target.angle"] = sch["direction"]
                trialdata["target.color"] = shared.TARGETBCCOLOR
                trialdata["seq"] = sch["seq"]
                trialdata["block"] = sch["block"]
                trialdata["trialInSeq"] = sch["trialInSeq"]
                trialdata["rotation"] = sch["rotation"]

                # we avoid only the reaching movement on trial n when selecting the target on trial n+1

                # generate the hash code for the trial
                trialdata["hash"] = generateHash()

                # reset the reach angle
                trialdata["movement.angle"] = np.nan
                trialdata["furthest.position"] = (0,0)
                trialdata["furthest.distance"] = 0
                trialdata["furthest.sample"] = shared.SAMPLE

                shared.next_phase()

                timeRefMessageBox = shared.t()

                seqchange = False
                bchange = False
                firstrun = True
            else:

                shared.next_phase()

        # See if there are any movement events from the joystick
        track_movement.trackMovement(trialdata)

        # See if there are any events from the keyboard
        keys = shared.pollKeyboard()


        if pygame.K_q in keys and not quit_first:
            quit_first = True
            tq = shared.t()

        if quit_first and shared.t()-tq < .5:
            if pygame.K_SPACE in keys:
                keep_going = False
                print("")
                print("")
                print("Experiment Terminated by the Experimenter.")
        else:
            quit_first = False


        #print((shared.phase_is("WAIT"))

        # If we are not waiting for any next trial (we have finished the schedule)
        if (shared.schedule_done()) and (shared.phase_is("WAIT")):

            keep_going = pygame.K_q not in keys  # stop the main loop if the user pressed q


        else:

            # We're still in the game, so check if we should advance the trial or not.

            #### Decide if it's time to start the next trial
            # (This assumes that that trial is already set up during a wait phase)
            if shared.USING_TRIGGER:

                ##
                ## TODO -The USING_TRIGGER mode needs work. 
                ## I (Floris) probably broke it today.
                ## We don't immediately use it but we should either remove it or fix it.
                ##

                # Check if there is a new trigger that we 
                if shared.TRIGGER_RECEIVED and \
                   (shared.TRIGGER_COUNT>=shared.tr_waiting_for()) and \
                   (shared.t_since_last_trigger() > shared.DELAY[shared.SCHEDULE.index(shared.TRIGGER_COUNT)]):

                    print ("Delay: " + str(time.time() - shared.TRIGGER))
                    shared.launch_next_trial()
                    pygame.mixer.stop()
                    

            else: # if we're not operating based on triggers but on our own clock...



                    if shared.phase_is("WAIT"):

 
                        if (not first_screen) and shared.TRIAL+1 <= (len(mySchedule)-1):
                            if shared.TRIAL != -1 and mySchedule[shared.TRIAL+1]["block"] - mySchedule[shared.TRIAL]["block"] != 0 and (shared.t()-timeRefMessageBox <= shared.TIME_BLOCK_MESSAGE_DISPLAY):
                                bchange = True
                            else:
                                bchange = False


                        if shared.TIME_SEQ_MESSAGE_DISPLAY > 0 and (not first_screen) and shared.TRIAL != -1 and trialdata["trialInSeq"] == 0 and (shared.t()-timeRefMessageBox <= shared.TIME_SEQ_MESSAGE_DISPLAY):
                            seqchange = True

                            
                        else:
                            seqchange = False


                        if (not first_screen) and shared.TRIAL != -1 and trialdata["trialInSeq"] == 0 and firstrun:
                            firstrun = False
                            cntseq += 1
                            oneseq = all_rot[cntseq*seqlength:(cntseq+1)*seqlength]
                            seqnow = ""
                            for i in range(len(oneseq)):
                                seqnow += shared.myDict[oneseq[i]]


                        if (not first_screen) and (not seqchange) and (not bchange) and (shared.TRIAL == -1 or trialdata["targetHit"] == "YES" or trialdata["targetHit"] == "NO"):
                        #if shared.t_since_first_trigger() >= shared.time_waiting_for(): # If the time point we are waiting for has come
                            pygame.mixer.stop()        # If we might be playing a sound, stop it now.
                            shared.launch_next_trial() # advance to the next trial
                            # Advance the pointer to the next schedule entry
                            shared.SCHEDULE_POINTER += 1

                        if instCount < shared.N_INSTRUCTION_PAGES-1 and pygame.K_5 in keys:

                            instCount += 1
                            timeRefMessageBox = shared.t()

                        
                        if instCount == shared.N_INSTRUCTION_PAGES-1 and (shared.t()-timeRefMessageBox)>shared.TIME_EXP_INST_INTERVAL:
                            first_screen = False



                ## BELOW CONDITION IS USED WHEN UNDER MR SCANNER TO CONTROL FOR TIMIMG OF EACH TRIAL
                #if shared.t_since_first_trigger() >= shared.time_waiting_for(): # If the time point we are waiting for has come
                    # If we have received an initial trigger
                    # If this is not the last trial

                    ## If the current time exceeds the scheduled onset time for the trial (which we have set up to happen next),
                    ## start running that trial.
                    
                    # For debug: output the time that the trial starts
                    #t = time.time() - shared.INITIAL_TRIGGER
                    #print(t)

                    #pygame.mixer.stop()        # If we might be playing a sound, stop it now.

                    #shared.launch_next_trial() # advance to the next trial

                    # Advance the pointer to the next schedule entry
                    #shared.SCHEDULE_POINTER += 1

                    # pygame.mixer.stop()
                    # THIS LINE IS ONLY HERE FOR THE SAKE OF TESTING
                    # TO BE REMOVED
                    # time.sleep(1)


        if first_screen:

            shared.show_inter_trial_display(screen,trialdata,shared.N_INVALID_MOVEMENTS,
                                                                'first',
                                                                    timeRefMessageBox,
                                                                        instCount)


        elif shared.schedule_done() and writeCounter >= len(mySchedule):

            shared.show_inter_trial_display(screen,trialdata,shared.N_INVALID_MOVEMENTS,
                                                                'done',
                                                                    timeRefMessageBox)
        elif bchange:

            shared.show_inter_trial_display(screen,trialdata,shared.N_INVALID_MOVEMENTS,
                                                                    'bchange',
                                                                        timeRefMessageBox)
        elif seqchange:

            shared.show_inter_trial_display(screen,trialdata,shared.N_INVALID_MOVEMENTS,
                                                                    'seqchange',
                                                                        timeRefMessageBox)

        elif shared.t() - shared.UI_TIME_REF > shared.UI_UPDATE_INTERVAL:

            # If we are not in TEXT_DISPLAY mode but in continuous display mode, update the
            # position display if the time exceeds the update interval.
            shared.showPosition(trialdata, shared.CURSOR_FEEDBACK, seqnow)
            shared.UI_TIME_REF = time.time()





def distance(a, b):
    return math.sqrt(math.pow(a[0]-b[0], 2)+math.pow(a[1]-b[1], 2))


def format(number):
    if number < 10:
        return '0' + str(number)
    else:
        return str(number)

def generateHash(length = 8):
    return binascii.b2a_hex(os.urandom(length))





if __name__ == '__main__':
    main()
