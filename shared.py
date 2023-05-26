import time, os, sys
import numpy as np
import struct
import pygame
from screeninfo import get_monitors 


# The device that we read from 
JS_DEVICE = 'joystick-event'



# INSTRUCTIONS
# YOU CAN HAVE UPTO 5 PAGES OF INSTRUCTION PAGES IN THE BEGINNING OF THE EXPERIMENT. USE THE FOLLOWING FORMAT TO DEFINE MORE IF YOU WISH TO DO SO.

INST_MESSAGE = {}

INST_MESSAGE["page1"] = "[PLACE HOLDER FOR INSTRUCTIONS IN THE FIRST PAGE]\n\n"\
                      + "Press key '5' to move on."

INST_MESSAGE["page2"] = "[PLACE HOLDER FOR INSTRUCTIONS IN THE SECOND PAGE]\n\n"\
                      + "You can add upto 5 pages.\n\n"\
                      + "Press '5' to move on"


INST_MESSAGE["page3"] = "THE EXPERIMENT IS ABOUT TO START"




# DURATION DURING WHICH THE SUBJECT IS ALLOWED TO MOVE IN SECONDS
MOVEMENT_PHASE_DURATION    = 5.0 #sec

# DURATION BETWEEN THE TIME SUBJECT HITS THE TARGET AND THE NEXT TARGET SHOWS UP IN SECONDS
TARGET_HOLD_TIME           = 0.5 #sec

# DURATION FOR A MESSAGE SHOWN BETWEEN SEQUENCES IN SECONDS
# IF YOU DO NOT WANT AN INTERRUPTION BETWEEN SEQUENCES, SET IT TO 0
TIME_SEQ_MESSAGE_DISPLAY   = 0.0 #sec

# DURATION FOR A MESSAGE SHOWN BETWEEN BLOCKS IN SECONDS
# IF YOU DO NOT WANT AN INTERRUPTION BETWEEN BLOCKS, SET IT TO 0
TIME_BLOCK_MESSAGE_DISPLAY = 10.0 #sec

# DURATION BETWEEN THE LAS PAGE OF THE BEGINNING INSTRUCTIONS AND START OF THE EXPERIMENT
TIME_EXP_INST_INTERVAL     = 3.0 #sec



# The background color of the screen
global BGCOLOR
BGCOLOR              = (127,127,127) # gray

# Target background Color
global TARGETBCCOLOR
TARGETBCCOLOR        = (160, 160, 160) # whitish gray 


# goal target color on each trial
global TRIALTARGETCOLOR
TRIALTARGETCOLOR     = (0, 255, 0) # green

# Target color when hit
global TARGET_HIT_COLOR
TARGET_HIT_COLOR     = (0, 0, 255) # blue

# Cursor color
global CURSOR_COLOR
CURSOR_COLOR         = (255, 0, 0) # red

# THE TEXT ON SCREEN
global TEXTSCREENCOLOR
TEXTSCREENCOLOR      = (255, 255, 255) # white


# Target radius in mm
global TARGETSIZE
TARGETSIZE           = 5 #mm

# Cursor radius in mm
global CURSORSIZE
CURSORSIZE           = 2.5 #mm


# Distance between the center of the target and cursor to say whether the cursor has hit the target or not in pixels
# in mm
TARGET_REACH_DISTANCE = TARGETSIZE+CURSORSIZE #mm


# Main Font for instructions
global mainfont
mainfont             = None
mainFontSize         = 22


# Sequence Label Font
global labelfont
labelfont             = None
labelfontSize         = 30



# Difne Screen
global screen
screen               = None

# File of the font being used
FONTFILE             = "fonts/Helvetica.ttf"

# pygame screen settings
FULLSCREEN = False

# if full screen is False, define screen size in mm
DISPLAY_SIZE         = [200, 200]  #mm

# Pygame configuration constants
#displayFlags = 0 # for non-fullscreen
displayFlags         = pygame.FULLSCREEN

# magnification factor for online display of the trajectory - Applies to whole worksapce in cluding cursor and targets
# in other words, it is the radius of the circle on which targets are placed in mm
EXCURSION            = 75  # mm

# Extra magnification factor only for cursor allowing for overshoot
CURSOR_EXCURSION_FAC = 1.2


# Whether to present cursor feedback
global CURSOR_FEEDBACK
CURSOR_FEEDBACK = True

# The update time for the GUI if we are running in "continuous display" mode.
# Usually we don't run in continuous display mode.
UI_TIME_REF          = 0
UI_UPDATE_INTERVAL   = 0.01


# Whether to play audi feedback / should be false for now
# AUDIO_FEEDBACK = False


# Distance between letters shown on top of screen in explicit mode
EXPLICIT_TEXT_LETTER_DIST = 10 #mm


# Distance between the letters shown on top of screen and the center of FRONT target
EXPLICIT_TEXT_LETTER_VERTICAL_DIST = 20 #mm


# The sequence shown on top of screen in the explicit mode
NumberOrLetter = "number"     # either number or letter  

# The target name should be shown inside target or not!
global TargetNamePresent
TargetNamePresent = True


#-----------------------------------------------------------------------------------
# DO NOT CHANGE ANYTHING BELOW
#-----------------------------------------------------------------------------------

monitor = get_monitors()

for mon in monitor:
    width     = mon.width
    height    = mon.height
    widthmm   = mon.width_mm
    heightmm  = mon.height_mm
    mm2pix    = (width/widthmm + height/heightmm)/2



TARGET_REACH_DISTANCE   = TARGET_REACH_DISTANCE*mm2pix
TARGETSIZE              = TARGETSIZE*mm2pix
CURSORSIZE              = CURSORSIZE*mm2pix
DISPLAY_SIZE[0]         = DISPLAY_SIZE[0]*width/widthmm
DISPLAY_SIZE[1]         = DISPLAY_SIZE[1]*height/heightmm
EXCURSION               = EXCURSION*mm2pix
EXPLICIT_TEXT_LETTER_DIST = EXPLICIT_TEXT_LETTER_DIST*mm2pix



if FULLSCREEN:
    DISPLAY_SIZE = [widthmm, heightmm] # for fullscreen


# The minimum distance from the center that subjects need to have moved for us to register the trial as a "movement" trial (and process the angle). This is also the threshold for having returned to the center after the movement is completed.
ORIGIN_THRESHOLD     = 0.35    


global explicit
explicit = False


global myDict
myDict      = { 90: "F",
                180: "L",
                -90: "B",
                0: "R",
                }


if NumberOrLetter == 'number':
    myDict      = { 90: "1",
                    180: "4",
                    -90: "3",
                    0: "2",
                    }



if not os.path.exists(JS_DEVICE):
    print("The joystick device does not seem to exist. Please set '%s' to point to the joystick device node."%JS_DEVICE)
    sys.exit(-1)


SCREEN_CENTER        = (DISPLAY_SIZE[0]/2,DISPLAY_SIZE[1]/2)


global TARGETSET
TARGETSET = {   "B": np.asarray(SCREEN_CENTER)+[0, EXCURSION],
                "F": np.asarray(SCREEN_CENTER)+[0, -EXCURSION],
                "R": np.asarray(SCREEN_CENTER)+[EXCURSION, 0],
                "L": np.asarray(SCREEN_CENTER)+[-EXCURSION, 0]}



if NumberOrLetter == 'number':
    TARGETSET = {   "3": np.asarray(SCREEN_CENTER)+[0, EXCURSION],
                    "1": np.asarray(SCREEN_CENTER)+[0, -EXCURSION],
                    "2": np.asarray(SCREEN_CENTER)+[EXCURSION, 0],
                    "4": np.asarray(SCREEN_CENTER)+[-EXCURSION, 0]}



# Keeps track of how many movements are "invalid", that is, the subject was not moving, for example
global N_INVALID_MOVEMENTS
N_INVALID_MOVEMENTS = 0 

# Keeps track of how many movements are valid in principle but fall outside the half circle edges
global N_VALID_MOVEMENTS
N_VALID_MOVEMENTS = 0 




# This points to the entry in the schedule for which we are currently waiting.
SCHEDULE_POINTER = None

# This holds the contents of the schedule file, which tells us when we should present a trial.
SCHEDULE = []

# The number of trials to run (this will be number of items in the schedule)
N_TRIALS = 0

# The current time (from time.time())
current_t = None


# The time (time.time()) the last trigger signal came in
LAST_TRIGGER_T = None


# We keep a list of previous movement endpoints (when not null)
# for display purposes.
global HISTORY_ENDPOINTS
HISTORY_ENDPOINTS = []


global N_INSTRUCTION_PAGES
N_INSTRUCTION_PAGES   = len(INST_MESSAGE)



# MAPPING OF PHASES TO INTS
PHASE_MAP = {
    'INIT':      0,   # Setting up the trial
    'MOVE':      1,   # Target stopped playing, now the subject can move
    'FEEDBACK':  2,   # Feedback sound started
    'WRITE':     3,   # Write the data from the previous trial
    'PREPARE':   4,   # Set up for the next trial
    'WAIT':      5,   # The next trial is set up; wait for the time to arrive to launch it.
}


# This is a log where we write timestamps for the various phases
# of a trial. When we advance to a next phase, we log the time in this array.
PHASE_LOG = []




DATA_FOLDER        = './data/' # Directory to which we will output the log files


global TRIAL_OUTFILE
global TRIGGER_OUTFILE
global MOVEMENT_OUTFILE
TRIAL_OUTFILE    = None   # the file handle for the log where we write trial information (one row per trial)
TRIGGER_OUTFILE  = None   # the file handle for the log where we write the trigger signal onsets
MOVEMENT_OUTFILE = None   # the file handle for the log where we write the trigger signal onsets



# If USING_TRIGGER is True, trigger signals (normally coming from the scanner) 
# are used to decide when we start the next trial. 
# If False, the script decides on its own when to present the next trial.
USING_TRIGGER      = False


global TEXT_DISPLAY
TEXT_DISPLAY         = True   # Whether we display a summary at the end of each trial (using Pygame)





global MOVEMENT
MOVEMENT = []
# MOVEMENT holds all the movement data that was recorded since last time
# we saved movements to file. That is, it is a kind of movement data buffer.
# It is a list of tuples
#           (x,y,raw_x,raw_y,timestamp,deviceTime,sample,trial,phase)
# recording the last known position at a particular time.
# - x,y is the position after processing this packet (and applying calibration)
# - raw_x,raw_y is the raw x,y reading prior to applying calibration
# - timestamp is the timestamp of the last packet in the batch.
# - sample denotes the sample number, which actually counts axis packets. So between two subsequent MOVEMENT entries
#   there may be multiple samples.
# - deviceTime is the device time of the last packet in the batch (it seemed to be the same for all entries in a batch at least for our lab joystick).
# - trial
# - phase (coded numerically)



def readCalib(filename):
    """ 
    Read a calibration file as output by the calibrate.py script.
    You need the run calibration first, so that this file exists.
    """

    global CALIB

    recent = None

    calib = None

    dateIndex = float('-inf')
    timeIndex = float('-inf')

    if not os.path.exists(filename):
        print("Calibration file %s does not exist."%filename)
        sys.exit(-1)


    # Search for a calibration file for this subject
    try:
        CALIBFILE = filename
        with open(CALIBFILE,'r') as f:
            calib = f.readlines()
            f.close()

        CALIB = {}
        for row in calib:
            fields = [ f.strip() for f in row.split("=") ]
            CALIB[fields[0]]=float(fields[1])
    except:
        print('Error reading calibration file.')
        sys.exit(-1)
        
    CALIB["rotate.circumf"] = CALIB["rotation"]/(2*np.pi) # express the rotation as a fraction of the circumference
        
    # remove whitespace and convert to float
    expected_keys = ["xmin","xmax","xcenter","ymin","ymax","ycenter","rotation"]
    for k in expected_keys:
        if k not in CALIB.keys():
            print("Error reading calibration file. Key %s not found."%k)
            sys.exit(-1)
        else:
            print("\t%s = %f"%(k,CALIB[k]))




def init():
	global PHASE
	global SESSION_START
	global AXIS_STATES
	global AXIS_RAW
	#global FURTHEST_POSITION
	#global FURTHEST_DISTANCE
        #global FURTHEST_SAMPLE
	global DEVICE_TIME
	global SAMPLE
	global TRIGGER_RECEIVED
	global TRIAL
	global START_TRIGGER
	global JS_FILE
	global PLAY_FEEDBACK
	global RETURNED_TO_ORIGIN
	global MOVEMENT
	global UNINTERPRETED
	global DELAY  # DEPRECATED
	global TRIGGER_COUNT
	global CALIBFILE
	global TRIAL_ONSET_TIMES # DEPRECATED
	global INITIAL_TRIGGER
	global N_TRIALS
	global history

        # This counts how many triggers were previously received
	TRIGGER_COUNT = -1

	PHASE = None

	SESSION_START = time.time()

        # This tells us the most recently known position of the joystick (X,Y)
	AXIS_STATES = {
		'x': 0.00,
		'y': 0.00
	}
	AXIS_RAW = {
		'x': 0.00,
		'y': 0.00
	}


	FURTHEST_DISTANCE = 0.0
	FURTHEST_SAMPLE = 0
	SAMPLE = 0
	DEVICE_TIME = 0
	START_TRIGGER = None  # TODO: Eric removes
	TRIGGER_RECEIVED = False   # Keeps track of whether a trigger has been used to initiate a new trial.
	TRIAL = -1            # Has to start at -1 so that the "next" trial is 0.
	history = []
        

	INITIAL_TRIGGER = None
        # This marks the system time (time.time()) at the moment the first trigger was received.

        # Reading the joystick through the event-joystick interface
	JS_FILE            = os.open(JS_DEVICE, os.O_RDWR | os.O_NONBLOCK)
	PLAY_FEEDBACK      = False
	RETURNED_TO_ORIGIN = False


	MOVEMENT = []
	UNINTERPRETED = []


        

# need to make another method reinit to reset global variables after each trial
def launch_next_trial():
        # Causes the next trial to launch and makes sure all variables are set correctly.

	global PHASE
	global SESSION_START
	global AXIS_STATES
	global AXIS_RAW
	global TRIAL
	global START_TRIGGER
	global PLAY_FEEDBACK
	global RETURNED_TO_ORIGIN
	global TRIGGER_RECEIVED
	global current_t

	global PHASE_LOG

	PHASE = PHASE_MAP['INIT']
	PHASE_LOG = [ (PHASE,t_since_start()) ]

	#START_TRIGGER = TRIGGER
	TRIGGER_RECEIVED      = False    # Mark that during this trial, we haven't received the next trigger yet.
	TRIAL                 = upcoming_trial()  # This assumes that the schedule pointer is pointing to the trial we are just starting (it has not yet been advanced)
	PLAY_FEEDBACK         = False
	RETURNED_TO_ORIGIN    = False
        

	print ("")
	print ('Trial: %i / %i'%(TRIAL+1,N_TRIALS))





def new_trigger_received():
        # Run this when you receive a new trigger

        global INITIAL_TRIGGER
        global TRIGGER_RECEIVED
        global TRIGGER_COUNT
        global SCHEDULE
        global SESSION_START
        global current_t
        global LAST_TRIGGER_T
        global TRIGGER_OUTFILE

        # If we haven't received an initial trigger yet, mark this time as the initial trigger time
        if not INITIAL_TRIGGER:
            INITIAL_TRIGGER = current_t

            # Tell the world that we received the first trigger!
            pygame.display.flip()

        global LAST_TRIGGER_T
        LAST_TRIGGER_T = current_t


        TRIGGER_RECEIVED = True
        TRIGGER_COUNT = TRIGGER_COUNT + 1   # the number of triggers received since the beginning of this run
        #if TRIGGER_COUNT in SCHEDULE:
        #    TRIGGER = current_t;

        # log the occurrence of this trigger
        TRIGGER_OUTFILE.write('%i %f\n'%(TRIGGER_COUNT, t_since_start()))
        TRIGGER_OUTFILE.flush()





def phase_is(phasename):
        # Returns true if the current phase equals phasename.
        global PHASE
        return (PHASE == PHASE_MAP[phasename])

def phase_in(phases):
        # Returns true if the current phase is among the given phases
        global PHASE
        return (PHASE in [ PHASE_MAP[ph] for ph in phases ])




def next_phase():
        # Goes to the next phase, and log that we entered that phase
        global PHASE
        PHASE += 1
        global PHASE_LOG
        global current_t
        PHASE_LOG.append( (PHASE,t_since_start()) )
        #print("Entering phase %i"%PHASE)




def take_time():
        # Take a snap of the current time so that we can subsequently report the time accurately
        global current_t
        current_t = time.time()

def t_since_start():
        # Returns the time since the beginning of the session
        global SESSION_START
        global current_t
        return current_t - SESSION_START


def t_since_last_trigger():
        # Returns the time passed since the most recent trigger signal came in.
        global LAST_TRIGGER_T
        global current_t
        return current_t-LAST_TRIGGER_T


def t_since_first_trigger():
        # Returns the time since the first trigger signal was received
        global INITIAL_TRIGGER
        if INITIAL_TRIGGER==None: # If we have not yet received the first trigger...
                return float('-inf')
        global current_t
        return current_t-INITIAL_TRIGGER




def t():
        # Returns the current time stamp (absolute time, as in the latest output from time.time())
        global current_t
        return current_t
        


def readSchedule(fname):
        # Here we read a schedule file prepared for this subject.
        # The schedule file tells us at what times to present trials.
        # For backwards compatibility, we only keep schedule lines
        # that correspond to "active" trials.

        # Empty the current schedule
        global SCHEDULE
        SCHEDULE = []

        scheduleFile = open(fname,'r')
        
        # read the header line
        header = scheduleFile.readline()
        cols = [ h.strip() for h in header.split() ]
        
        try:
                schedule = scheduleFile.readlines()
                for row in schedule:
                        row = row.rstrip('\n')

                        # Read one entry and save it as a dict using the header values
                        entry = dict(zip(cols,row.split()))
                        entry["block"]         =int(entry["block"])
                        entry["seq"]           =int(entry["seq"])
                        entry["trialInSeq"]    =int(entry["trialInSeq"])

                        entry["trial"]    =int(entry["trial"])
                        entry["direction"]=int(entry["direction"])
                        entry["TR"]       =int(entry["TR"])
                        entry["t"]        =float(entry["t"])
                        entry["t.offset"] =float(entry["t.offset"])
                        entry["rotation"] =float(entry["rotation"])


                        if entry["type"]=="active":
                                SCHEDULE.append(entry)

                        #globals.
                        #slot, type, trial, TR, t, delay = row.split(' ')
                        #slot = int(slot)
                        #TR = int(TR)
                        #t = float(t)
                        #delay = float(delay)
                        #if type == 'active': 
                        #        globals.N_TRIALS += 1
                        #        globals.SCHEDULE.append(TR)
                        #        globals.DELAY.append(delay)
                        #        globals.TRIAL_ONSET_TIMES.append(t)
        except:
                print ("Error reading schedule file %s"%fname)
                print (sys.exc_info()[0])
                sys.exit(-1)


        estimated_TR = None
        if len(SCHEDULE)>0:
                # Deduce the TR from the schedule file
                lastsched = SCHEDULE[-1]
                if lastsched["t"]!=0:
                        estimated_TR = lastsched["t"]/lastsched["TR"]


        global N_TRIALS
        N_TRIALS = len(SCHEDULE)

        global SCHEDULE_POINTER
        SCHEDULE_POINTER = 0  # meaning we are pointing to the next entry on the schedule

        print ("")
        print ("Read %i trials from the schedule file."%N_TRIALS)
        if len(SCHEDULE)>0:
                print ("Time of last event onset            = %.01f min"%(SCHEDULE[-1]["t"]/60.))
                print ("TR   of last event onset            = %i"%(SCHEDULE[-1]["TR"]))
        if estimated_TR:
                print ("Estimated TR from the schedule file = %.03f seconds"%estimated_TR)

        scheduleFile.close()

        return SCHEDULE




def current_schedule():
        # Returns the next entry in the schedule
        global SCHEDULE_POINTER
        global SCHEDULE
        if SCHEDULE_POINTER and 0<SCHEDULE_POINTER<len(SCHEDULE):
                return SCHEDULE[ SCHEDULE_POINTER ]
        else:
                return None


def schedule_done():
        # Tells us whether we have completed the schedule.
        global SCHEDULE_POINTER
        global SCHEDULE
        return SCHEDULE_POINTER>=len(SCHEDULE)
                





def tr_waiting_for():
        # Returns the TR number we are currently waiting for
        if SCHEDULE_POINTER == None:
                return None
        else:
                return SCHEDULE[ SCHEDULE_POINTER ]["TR"]




def time_waiting_for():
        # Returns the time point we are currently waiting for
        # This time point is returned in seconds and relative
        # to whatever times in the schedule files are coded relative to.
        if SCHEDULE_POINTER == None or SCHEDULE_POINTER>=len(SCHEDULE):
                return float('inf') # wait until eternity
        else:
                return SCHEDULE[ SCHEDULE_POINTER ]["t"]



def upcoming_trial():

        # Returns the trial number of the upcoming trial
        if SCHEDULE_POINTER == None or SCHEDULE_POINTER>=len(SCHEDULE):
                return np.nan
        else:
                return SCHEDULE[ SCHEDULE_POINTER ]["trial"]







#
#
# Pygame-specifics
#
#






def textScreen(text, surf = None, font = None, bgColor = BGCOLOR, fontcolor = (255,255,255), linespacing = 40, x=None,y=None, show=False):
        """ Display the given text on the screen surface.
        if x==None then we display the text centered, otherwise we use the x given as x-coordinate (left-align)
        """
        if surf==None:
                global screen
                surf = screen
        if font==None:
                global mainfont
                font = mainfont

        surf.fill( bgColor )

        # First convert each line into a separate surface
        lines = text.split("\n")
        textboxes = []
        for line in lines:
                textboxes.append( font.render(line,True,fontcolor) )

        # Then blit the surfaces onto the screen
        if y==None:
                starty = (surf.get_height()-(len(lines)*linespacing))/2
        else:
                starty=y
        i = 0
        if x!=None: display_x = x

        for i in range(len(textboxes)):
                # Put the image of the text on the screen at 250 x250
                if x==None:
                        display_x = ((surf.get_width()-textboxes[i].get_size()[0])/2)
        
                surf.blit(textboxes[i], (display_x, starty+(i*linespacing) - 100))


        if show:
                pygame.display.flip()

        return starty+(len(lines)*linespacing)











# Thickness of the line for the movement display
MOVEMENT_PLOT_THICKNESS = 2

# X/Y-coordinates of the text on the report screen
REPORT_X,REPORT_Y = 100,350


CENTERX,CENTERY = SCREEN_CENTER[0],(SCREEN_CENTER[1]+160)


# In the inter-trial-display these are the colours we plot the various phases in
PHASE_PLOT_COLOR = {
        0:(0,0,0),          # INIT
        1:(0,0,0),          # TARGET
        2:(0,0,0),          # LISTEN
        3:(0,0,0),          # MOVE
        4:(150,150,150),    # FEEDBACK
        5:(150,150,150),
        6:(150,150,150),
        7:(150,150,150),
        8:(150,150,150),
}



def show_inter_trial_display(screen,trialdata,N_INVALID_MOVEMENTS,message,timeRefMessageBox, pagenumber=None):
        # Updates the little window that shows us some essential
        # information about the most recent trial.


        global TRIAL
        global AXIS_STATES
        global TRIGGER_COUNT
        global MOVEMENT
        global SCHEDULE
        
        if current_schedule() != None:
                sch = current_schedule()

        if message == 'bchange':
                messagee = "End of Block %i\n\nPlease Return to the center of the screen.\n\nRemaining time to the start of the next block: %is\n\n\nPlease return to the origin" %(trialdata["block"], np.round(TIME_BLOCK_MESSAGE_DISPLAY-t()+timeRefMessageBox))
        elif message == 'seqchange':
                messagee = "End of Sequence %i\n\nPlease Return to the center of the screen.\n\nRemaining time to the start of the next sequence: %is\n\n\nPlease return to the origin" %(trialdata["seq"], np.round(TIME_SEQ_MESSAGE_DISPLAY-t()+timeRefMessageBox))
        elif message == 'done':

                nvalid = TRIAL+1 - N_INVALID_MOVEMENTS 

                messagee = "Experiment Completed. \n\n Press 'q' to save and exit.\n\n\n\n\nNumber of valid moves: %i\n\nNumber of invalid moves: %i"%(nvalid, N_INVALID_MOVEMENTS)
        elif message == 'first':

                if pagenumber == 0:
                        messagee = INST_MESSAGE["page1"]
                elif pagenumber == 1:
                        messagee = INST_MESSAGE["page2"]
                elif pagenumber == 2:
                        messagee = INST_MESSAGE["page3"]
                elif pagenumber == 3:
                        messagee = INST_MESSAGE["page4"]
                elif pagenumber == 4:
                        messagee = INST_MESSAGE["page5"]


                if pagenumber == N_INSTRUCTION_PAGES-1:
                        messagee += "\n\n\n%i\nsec"%np.round(TIME_EXP_INST_INTERVAL-t()+timeRefMessageBox)

        textScreen(messagee,linespacing=20)
        textScreen(messagee,linespacing=20)
        

        pygame.display.flip()
                










def showPosition(trialdata=None, CURSOR_FEEDBACK=True, oneseq=None):
        # Shows the current position on the screen

        global screen
        global mainfont
        global labelfont
        global SCREEN_CENTER
        global EXCURSION
        global AXIS_STATES
        
        screen.fill(BGCOLOR)
    
        
        for trg in (0, 90, 180, -90):
            pygame.draw.circle(screen, TARGETBCCOLOR, TARGETSET[myDict[trg]], TARGETSIZE, 0)
            if TargetNamePresent:
                lab = labelfont.render(myDict[trg], 1, BGCOLOR)
                screen.blit(lab, TARGETSET[myDict[trg]]-[labelfontSize/4+1, labelfontSize/2-1])


        if trialdata!=None:

                targetpos = get_pos(trialdata["target.angle"])
                pygame.draw.circle( screen, trialdata["target.color"], targetpos, TARGETSIZE, 0)
                lab = labelfont.render(myDict[trialdata["target.angle"]], 1, BGCOLOR)
                screen.blit(lab, TARGETSET[myDict[trialdata["target.angle"]]]-[labelfontSize/4+1, labelfontSize/2-1])


        #curpos = (int(SCREEN_CENTER[0]+EXCURSION*AXIS_STATES['x']),
        #          int(SCREEN_CENTER[1]-EXCURSION*AXIS_STATES['y']))

        curpos = (int(CURSOR_EXCURSION_FAC*EXCURSION*AXIS_STATES['x']),
                  int(CURSOR_EXCURSION_FAC*-EXCURSION*AXIS_STATES['y']))

        curpos = np.array(rot_pos(curpos, trialdata["rotation"], [0,0])) + np.asarray(SCREEN_CENTER)


        if CURSOR_FEEDBACK:
                pygame.draw.circle(screen, CURSOR_COLOR, curpos, CURSORSIZE, 0)

        
        if explicit:
            #s = "[ %.2f %.2f ]"%(AXIS_STATES['x'], AXIS_STATES['y'])
            
            s = oneseq
            sTarg_pos = trialdata["trialInSeq"]
            sTarg = s[sTarg_pos]

            for i in range(len(s)):
                label1 = labelfont.render(s[i], 1, TEXTSCREENCOLOR)
                screen.blit(label1, np.asarray(SCREEN_CENTER)-[-EXPLICIT_TEXT_LETTER_DIST*(0.3+i-len(s)/2), EXCURSION+EXPLICIT_TEXT_LETTER_VERTICAL_DIST*mm2pix])


            label2 = labelfont.render(sTarg, 1, TRIALTARGETCOLOR)
            screen.blit(label2, np.asarray(SCREEN_CENTER)-[-EXPLICIT_TEXT_LETTER_DIST*(.3+sTarg_pos-len(s)/2), EXCURSION+EXPLICIT_TEXT_LETTER_VERTICAL_DIST*mm2pix])

            #sTarg_pos = (N_SPACE_CHAR+1)*trialdata["trialInSeq"]
            #sTarg = create_space(sTarg_pos+1) + s[sTarg_pos]


            #label1 = labelfont.render(s, 1, TEXTSCREENCOLOR)
            #label2 = labelfont.render(sTarg, 1, TARGET_HIT_COLOR)

            #screen.blit(label1, np.asarray(SCREEN_CENTER)-[0, EXCURSION+15*mm2pix])
            #
            
        pygame.display.flip()
        



def rot_pos(xy, r, xy0):
        r = -r
        xn = xy[0]*np.cos(np.deg2rad(r))-xy[1]*np.sin(np.deg2rad(r))+xy0[0]-np.cos(np.deg2rad(r))*xy0[0]+np.sin(np.deg2rad(r))*xy0[1]
        yn = xy[0]*np.sin(np.deg2rad(r))+xy[1]*np.cos(np.deg2rad(r))+xy0[1]-np.sin(np.deg2rad(r))*xy0[0]-np.cos(np.deg2rad(r))*xy0[1]
        return (xn, yn)



def get_pos(trg):
        
    global TARGETSET
    global myDict

    targetpos = TARGETSET[myDict[trg]]

    return targetpos


def init_pygame():
        # Set up everything that is specfic to Pygame: making a window
        # for display etc.

        pygame.init()
        pygame.mixer.init()
        
        # Initialise the fonts
        global mainfont
        mainfont = pygame.font.Font(FONTFILE, mainFontSize)

        global labelfont
        labelfont = pygame.font.Font(FONTFILE, labelfontSize)


        global screen
        screen = pygame.display.set_mode(DISPLAY_SIZE)
        screen.convert()
        pygame.display.set_caption('Audiomotor experiment')
        pygame.mouse.set_visible(False)
        screen.fill(BGCOLOR)
        


def close_pygame():
        pygame.quit()






def pollKeyboard():
        # Checks which keys are pressed and returns a list of them
        keyspressed = []
        global TEXT_DISPLAY
        events = pygame.event.get()
        for event in events:
                if event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_5:
                                new_trigger_received()
                                print('Trigger received from keyboard')
                        elif event.key == pygame.K_d:
                                #change the display mode
                                print('Changing display mode')
                                TEXT_DISPLAY = not TEXT_DISPLAY
                        keyspressed.append(event.key)
        return keyspressed





def pollForKey(ky):
        # Poll for a particular key
        events = pygame.event.get()
        for event in events:
                if event.type == pygame.KEYDOWN:
                        if event.key == ky:
                                return True
        return False
                    
        
        



# 
# Functions related to logging
#




# The phases for which we want to write time stamps to the log
LOGFILE_PHASES = ["INIT","MOVE","FEEDBACK","WRITE"]




def init_logs(prefix,schedulef=None):
        # Initiate the log file handles and write their headers
        global TRIAL_OUTFILE
        global TRIGGER_OUTFILE
        global MOVEMENT_OUTFILE
        global UNINTERPRETED_OUTFILE

        fileprefix = DATA_FOLDER + prefix

        # Initialises the logs. Takes the subject-specific prefix.
        TRIAL_OUTFILE   = open(fileprefix + '_trial.dat', 'w')
        TRIAL_OUTFILE.write('subject trial trialInSeq seqInBlock block trial.hash target.angle reach.angle furthest.x furthest.y timestamp targetHit rotation t.init t.move t.hit t.write\n')
        
        TRIGGER_OUTFILE = open(fileprefix + '_trigger.dat', 'w')
        TRIGGER_OUTFILE.write('TR t\n')

        MOVEMENT_OUTFILE = open(fileprefix + '_movement.bin', 'wb')

        UNINTERPRETED_OUTFILE = open(fileprefix + '_unint.bin', 'wb')
        # MOVEMENT_OUTFILE.write('pos.x pos.y timestamp device.time sample trial trial.hash phase\n')

        if schedulef!=None:
                # Make a copy of the schedule file for our records
                schedf = open(schedulef,'r')
                schedule = schedf.read()
                schedf.close()

                sched_out = open(fileprefix+"_schedule.dat",'w')
                sched_out.write(schedule)
                sched_out.close()

                
        print ("")
        print ("Logging to %s_*"%fileprefix)





def write_trial_log(
                    trialdata,
                    subject):
        # Write one row to the trial log, corresponding to the data for this trial.
        global TRIAL
        global TRIAL_OUTFILE
        global PHASE_LOG

        far_x,far_y = trialdata["furthest.position"]

        targ,mov = 2*np.pi*trialdata["target.angle"],2*np.pi*trialdata["movement.angle"]

        # generate the string of data representing the trial
        trialdata = map(str, 
                        [subject,
                         TRIAL,
                         trialdata["trialInSeq"],
                         trialdata["seq"],
                         trialdata["block"],
                         trialdata["hash"],
                         trialdata["target.angle"], 
                         trialdata["movement.angle"], 
                         far_x,
                         far_y,
                         trialdata["timestamp"],
                         trialdata["targetHit"],
                         trialdata["rotation"]])



        phaselog = dict(PHASE_LOG)
        for ph in LOGFILE_PHASES:
                trialdata = list(trialdata)
                trialdata.append(str(phaselog.get(PHASE_MAP[ph],np.nan)) )

        trialString = " ".join(trialdata)

        # write the trial data
        TRIAL_OUTFILE.write(trialString + '\n')
        TRIAL_OUTFILE.flush()

        global history
        history.append( (targ,mov) )
                
        
        global HISTORY_ENDPOINTS
        if (far_x,far_y)!=(0,0):
                HISTORY_ENDPOINTS.append( (far_x,far_y) )




def write_movement_log():
        # We write the movement samples to a file, in binary format
        global MOVEMENT
        global MOVEMENT_OUTFILE
        global UNINTERPRETED
        global UNINTERPRETED_OUTFILE

        # Write to file the movement packets
        for reading in MOVEMENT:
                binformat = struct.pack('ffffffiii', *reading)
                MOVEMENT_OUTFILE.write(binformat)
        MOVEMENT_OUTFILE.flush()

        # Write to file uninterpreted packets
        for reading in UNINTERPRETED:
                binformat = struct.pack('4sHHsfff', *reading)
                UNINTERPRETED_OUTFILE.write(binformat)
        UNINTERPRETED_OUTFILE.flush()

        


def close_logs():
        # Close all log files at the end of the day
        global TRIGGER_OUTFILE
        global TRIAL_OUTFILE
        global MOVEMENT_OUTFILE
        global UNINTERPRETED_OUTFILE
        MOVEMENT_OUTFILE.close()
        TRIAL_OUTFILE.close()
        TRIGGER_OUTFILE.close()
        UNINTERPRETED_OUTFILE.close()









def split_contiguous(lst):
        # Takes as input a lst of 2-tuples (a,b) and returns
        # a list where each item is a contiguous chunk of values of b
        # for the same values of a.
        # This is hard to explain, but here is an example:
        # if lst=[ (a,1), (a,2), (b,3), (b,2), (b,1), (a,4), (a,1) ]
        # Then the output will be
        #    [ (a,[1,2]), (b,[3,2,1]), (a,[4,1]) ]
        # Just one warning: a is never allowed to be None
        toreturn = []
        curr = None
        for (a,b) in lst:
                if a==None:
                        return None # violation of assumption
                if a==curr:
                        buff.append(b)
                else:
                        if curr!=None:
                                toreturn.append( (curr,buff) )
                        buff = [b]
                        curr = a
        if len(buff)>0:
                toreturn.append( (curr,buff) )
        return toreturn



def create_space(num):

    BLANK_CHAR = ""
    for i in range(num):
        BLANK_CHAR += " "
        
    return BLANK_CHAR




