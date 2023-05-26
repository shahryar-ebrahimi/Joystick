import datetime
import time
import sys
import select
import read_joystick
import numpy as np
import struct
import shared

import numpy as np
import pygame
import os

import subprocess


# The update interval of the GUI
UI_LAST_DISPLAY    = -np.inf # the last time we displayed the interface
UI_UPDATE_INTERVAL = .05    # the interval for updates of the UI.


# the factor with which we multiply joystick readings when we display them on the pygame window
UI_DISPLAY_FACTOR = 1


ADDITIONAL_WAIT_TIME = 2 # how long to wait, continuing to collect data, after the user presses 'q'


# A previous calibration file, which will be read and displayed for reference
prevcalib = None




def format(number):
    if number < 10:
        return '0' + str(number)
    else:
        return str(number)


def drawpos(x,y):
    # This figures out where particular coordinates go on our screen
    return (int( UI_DISPLAY_FACTOR*x),int(UI_DISPLAY_FACTOR*y))





def enough_snapshots(snapshots):
    """ Takes the snapshot object and tells us whether we have enough snapshots, returning True if so and False otherwise. """
    for direct in ["center","left","right","front", "back"]:
        if not len(snapshots[direct])>0:
            #print("Not enough snapshots for %s"%direct)
            return False
    return True





def get_center(positions):
    """ Return the center of a set of positions. """
    xs,ys= [ x for (x,_) in positions ],[ y for (_,y) in positions ]
    return np.mean(xs),np.mean(ys)
    




def get_calib(positions,snapshots):
    """ 
    Compute the joystick calibration based on all the positions recorded and the
    snapshots taken of the cardinal directions.
    Returns a dict with all information defining the calibration (min, max, etc.)
    
    Arguments
    positions : list of all positions recorded as (x,y) pairs
    snapshots : dict of all directions and their corresponding snapshots
    """
    calib = {}

    # First, determine the extreme values along X and Y axes.
    xs = [ x for (x,_) in positions ]
    ys = [ y for (_,y) in positions ]
    calib["xmin"],calib["xmax"]=min(xs),max(xs)
    calib["ymin"],calib["ymax"]=min(ys),max(ys)
    
    # Now determine the center
    calib["xcenter"],calib["ycenter"] = get_center(snapshots["center"])
    calib["xleft"]  ,calib["yleft"]   = get_center(snapshots["left"])
    calib["xfront"] ,calib["yfront"]  = get_center(snapshots["front"])
    calib["xright"] ,calib["yright"]  = get_center(snapshots["right"])
    calib["xback"]  ,calib["yback"]   = get_center(snapshots["back"])

    # Now determine the rotation of the workspace,
    # i.e. a rotation that makes the 180 degree arc fit
    # most closely with the left/right/front points.

    # For each of the cardinal direction snapshots (left,front,right) compute the angle w.r.t. to the vertical from the center.
    calib["left_ang"]  = np.arctan2( calib["xleft"]  -calib["xcenter"], -(calib["yleft"]  -calib["ycenter"]) )
    calib["front_ang"] = np.arctan2( calib["xfront"] -calib["xcenter"], -(calib["yfront"] -calib["ycenter"]) )
    calib["right_ang"] = np.arctan2( calib["xright"] -calib["xcenter"], -(calib["yright"] -calib["ycenter"]) )
    calib["back_ang"]  = np.arctan2( calib["xback"]  -calib["xcenter"], -(calib["yback"]  -calib["ycenter"]) )

    # Now the best rotation of the workspace could be defined as the average deviation of each of the three
    # above angles from the desired angles, which are -pi/2, 0, pi/2 respectively.
    calib["rotation"] = -np.mean([ calib["left_ang"] - (-np.pi/2),
                                  calib["front_ang"] -  0,
                                  calib["right_ang"] - (np.pi/2),
                                  calib["back_ang"]  - (np.pi)])
    print(calib)
    
    
    print ("")
    print ("X range  = (%i,%i)"%(calib["xmin"],calib["xmax"]))
    print ("Y range  = (%i,%i)"%(calib["ymin"],calib["ymax"]))
    print ("Center   = (%.2f,%.2f)"%(calib["xcenter"], calib["ycenter"]))

    return calib








def main():

    # Check if we are given reference calibration values (e.g. a previous calibration file)
    # so that we can compare.
    global UI_DISPLAY_FACTOR

    global prevcalib


    subject = ""
    #if len(sys.argv)>0:
    #    subject = sys.argv[0]
    
    if len(sys.argv)>1:
        # If we have given a previous calibration file as argument

        filename = sys.argv[1]
        if os.path.exists(filename):
            with open(filename,'r') as f:
                    calib = f.readlines()
                    f.close()

            prevcalib = {}
            for row in calib:
                    fields = [ f.strip() for f in row.split("=") ]
                    prevcalib[fields[0]]=float(fields[1])

    else:
        print("You can give a previous calibration file as command-line argument")
        print("in which case I will display that calibration as a reference.")

    shared.init()

    while len(subject)==0:
        subject = input('Enter participant ID: ')
    now = datetime.datetime.now()

    shared.init_pygame()

    CX,CY = shared.screen.get_width()/2,shared.screen.get_height()/2

    packets          = [] # a list of readings from the joystick axes.
    positions        = [] # a list of positions visited
    snapshots        = {"center":[],"left":[],"front":[],"right":[], "back":[]}  # a list of positions that are supposed to estimate the center

    calib = None
    last_position = {"x":None,"y":None}
    
    keep_reading = True
    while keep_reading:
        
        shared.take_time() # Updates the current time
        readings = read_joystick.readjs()

        if len(readings)>0:
            
            # Process all the events received in this batch
            for reading in readings:
                ( tp, _, _, ax, value, t, usecs ) = reading
                
                if tp == 'axis' and ax!="":
                    # Update the last known position
                    last_position[ax]=value
                    packets.append(reading)
                else:
                    #print ("Unknown packet",reading)
                    pass

            # Update the "last known position"
            if None not in list(last_position.values()):
                positions.append( (last_position["x"],last_position["y"]) )


        # If we should update the UI, do it
        if time.time()-UI_LAST_DISPLAY > UI_UPDATE_INTERVAL:
            # Update the interface - reproduce the message
            msg = "Started calibration.\n\n" \
                  +"Press '[' or ']' to zoom\n" \
                  +"(1) Move joystick in circles\n" \
                  +"Move joystick all the way:\n" \
                  +"(2) to the left\n" \
                  +"(3) to the right\n" \
                  +"(4) to the front\n" \
                  +"(5) to the back\n" \
                  "\nPress LEFT/UP/RIGHT/DOWN/'c' \nto take a snapshot of left/front/right/back/center\n"
            
            if enough_snapshots(snapshots):
                msg = msg+ "\nPress 's' to perform calibration with the current data.\nPress 'q' to quit."

            shared.textScreen(msg,
                              x=30,y=150,linespacing=25,
                              show=False)

            if prevcalib!=None:
                # If there is a previous calibration file that we should display as a reference
                # (we can use this to spot any misalignments or biases because the subject doesn't
                #  really move to the edges).
                rect = pygame.Rect( UI_DISPLAY_FACTOR*prevcalib["xmin"]+3*CX/2,
                                    UI_DISPLAY_FACTOR*prevcalib["ymin"]+CY/2,
                                    UI_DISPLAY_FACTOR*(prevcalib["xmax"]-prevcalib["xmin"]),
                                    UI_DISPLAY_FACTOR*(prevcalib["ymax"]-prevcalib["ymin"]))
                pygame.draw.rect( shared.screen, (50,0,0), rect, 1)

                pygame.draw.circle( shared.screen, (50,0,0), (int(UI_DISPLAY_FACTOR*prevcalib["xcenter"]+3*CX/2),
                                                              int(UI_DISPLAY_FACTOR*prevcalib["ycenter"])+CY/2), 10)

            if calib!=None:
                # If we have computed a calibration based on the data collected in this session,
                # let's show it.
                rect = pygame.Rect( UI_DISPLAY_FACTOR*calib["xmin"]+3*CX/2,
                                    UI_DISPLAY_FACTOR*calib["ymin"]+CY/2,
                                    UI_DISPLAY_FACTOR*(calib["xmax"]-calib["xmin"]),
                                    UI_DISPLAY_FACTOR*(calib["ymax"]-calib["ymin"]))
                pygame.draw.rect( shared.screen, (50,0,0), rect, 1)
                pygame.draw.circle( shared.screen, (50,0,0), (int(UI_DISPLAY_FACTOR*calib["xcenter"]+3*CX/2),
                                                              int(UI_DISPLAY_FACTOR*calib["ycenter"])+CY/2), 10)

                # Now show the rotation
                pygame.draw.arc( shared.screen,
                                 (100,0,0),
                                 rect,
                                 calib["rotation"],
                                 calib["rotation"]+np.pi,
                                 5)

                
            # Add the movements captured so far.
            for (x,y) in positions:
                pygame.draw.circle( shared.screen, (0,0,100), drawpos(x+3*CX/2,y+CY/2), 1)

            for (direct,col) in [ ("center", (255,255,255)),
                                  ("left",   (255,0,0)),
                                  ("front",  (0,0,255)),
                                  ("right",  (0,255,0)),
                                  ("back",   (255, 255, 0))]:
                for (x,y) in snapshots[direct]:
                    pygame.draw.circle( shared.screen, col, drawpos(x+3*CX/2,y+CY/2), 3)

                
            if len(positions)>0:
                (x,y)=positions[-1]
                pygame.draw.circle( shared.screen, (255,0,0), drawpos(x+3*CX/2,y+CY/2), 5)


            pygame.display.flip()



        #
        # Allow user input from the keyboard
        #
            
        keys = shared.pollKeyboard()

        if pygame.K_c in keys:
            snapshots["center"].append( (last_position["x"],last_position["y"]) )

        if pygame.K_LEFT in keys:
            snapshots["left"].append( (last_position["x"],last_position["y"]) )

        if pygame.K_RIGHT in keys:
            snapshots["right"].append( (last_position["x"],last_position["y"]) )

        if pygame.K_UP in keys:
            snapshots["front"].append( (last_position["x"],last_position["y"]) )

        if pygame.K_DOWN in keys:
            snapshots["back"].append((last_position["x"],last_position["y"]) )
            
        if pygame.K_s in keys and enough_snapshots(snapshots):
            calib = get_calib(positions,snapshots)


        if pygame.K_ESCAPE in keys:
            keep_reading = False
            
            

        if pygame.K_q in keys and enough_snapshots(snapshots):
            shared.textScreen("Finishing calibration...",
                              show=True)
            keep_reading = False


        if pygame.K_LEFTBRACKET in keys:
            UI_DISPLAY_FACTOR /= 1.05
        if pygame.K_RIGHTBRACKET in keys:
            UI_DISPLAY_FACTOR *= 1.05




    if len(positions)>0 and enough_snapshots(snapshots):
            
        #
        # Now calculate the calibration data
        #

        calib = get_calib(positions,snapshots)



        #
        # Write the calibration file
        #
        prefix = (
            'calib_'
            + subject
            + '_'
            + format(now.year)
            + format(now.month)
            + format(now.day)
            + '_'
            + format(now.hour)
            + format(now.minute)
            + format(now.second)
        )
        filename = 'data/' + prefix + '.txt'
        calibf = open(filename, 'w')
        kys = sorted(calib)
        for k in kys:
            calibf.write("%s = %f\n"%(k,calib[k]))
        #calibf.write('%f\n%f\n%f\n%f\n%f\n%f'%(xmax, xmin, ymax, ymin, xcenter, ycenter))
        calibf.close()

        centerf = 'data/' + prefix + '_cardinals.dat'
        moves = open(centerf, 'w')
        moves.write('x y\n')
        for direct in ["left","right","front","center", "back"]:
            for pos in snapshots[direct]:
                moves.write('%s %i %i\n'%(direct,pos[0],pos[1]))
        moves.close()

        # Also dump all the movements recorded to a file (so we can later check if need be)
        movefile = 'data/' + prefix + '_movements.dat'
        moves = open(movefile, 'wb')
        for reading in packets:
            #print(reading)
            reading = list(reading)
            reading[0] = bytes(reading[0], encoding='utf-8')
            reading[3] = bytes(reading[3], encoding='utf-8')
            reading = tuple(reading)
            #print(reading)
            bn = struct.pack('4sHHsfff', *reading)  # note that we truncate the "type" identifier to four chars: "axis","butt" (sorry),"unkn"
            #print(bn)
            moves.write(bn)
        moves.close()
        
        print("")
        print("Calibration written to %s"%filename)
        print("")
        
        f = open(".lastcalib.txt",'w')
        f.write(filename)
        f.close()

    else:
        # Remove the link to any previous calibration file, which will be signal for our GUI
        # that the calibration was not succesful.
        subprocess.call(['rm','-f',".lastcalib.txt"])

        
    shared.close_pygame()



if __name__ == '__main__':
    main()


