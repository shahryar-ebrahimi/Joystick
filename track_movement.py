import read_joystick
import shared
import numpy as np
import time
import struct



# This allows us to transform joystick readings: 
# all readings are multiplied by the corresponding TRANSFORM
# prior to further processing.
TRANSFORM = {
    "x":1,
    "y":-1
}
#TRANSFORM = -1
# This allows you to flip the workspace but not rotate.




def centerAndScale(value, axis):
    # Return the centered and scaled version of the given axis value, using the calibration from shared.CALIB
    tmp = value - shared.CALIB["%scenter"%axis]

    # Decide if the reading is towards the one or the other extremity
    ref = "min" if tmp<0 else "max"

    return TRANSFORM[axis]* (tmp/(np.absolute(shared.CALIB["%scenter"%axis] - shared.CALIB["%s%s"%(axis,ref)])))
    #if tmp < 0: # if we are "left" of the center
    #    return TRANSFORM[axis]* (tmp/(np.absolute(shared.CALIB["%scenter"%axis] - shared.CALIB["%smin"%axis])))
    #else: # if we are "right" of the center
    #    return TRANSFORM[axis]* (tmp/(np.absolute(shared.CALIB["%scenter"%axis] - shared.CALIB["%smax"%axis])))




def writeMovement(outfile):
    # We write all movement data to file
    for reading in shared.MOVEMENT:
        bn = struct.pack('ffffiii', *reading)
        outfile.write(bn)




def commit_position():
    # We write the current position to the MOVEMENT record
    # which holds all past positions.
    # Note that we should only do this when we have reached a "logical" 
    # state, that is, not after receiving only one x update
    # when another y update may be waiting in the stack.

    # Add the movement to the stack
    shared.MOVEMENT.append((shared.AXIS_STATES['x'], 
                            shared.AXIS_STATES['y'], 
                            shared.AXIS_RAW["x"],
                            shared.AXIS_RAW["y"],
                            shared.t_since_start(),
                            shared.DEVICE_TIME,
                            shared.SAMPLE, 
                            shared.TRIAL, 
                            shared.PHASE))

    





def trackMovement(trialdata):

    # Get all packets from the joystick that are currently waiting in the pipeline
    readings = read_joystick.readjs()

    # check if any position data was received
    # if yes, process it all
    # right time.time all readings are processed serially
    # need to come up with a method for packaging data
    # maybe only update the position after everything is read?
    # is it possible that multiple readings for the same axis can come at the same time?
    if readings:
        updated= {"x":False,"y":False}

        for reading in readings:

            ( tp, pckt_type, pck_code, axis, value, timestamp, deviceTime ) = reading
            #(tp,axis,value,timestamp,deviceTime) = reading

            # If this is a reading that changed the joystick position, it's called an "axis" reading
            if tp == 'axis':

                position                 = centerAndScale(value, axis)
                shared.AXIS_STATES[axis] = position             # Update the corresponding "current" axis reading (only updates x or y)
                shared.AXIS_RAW[axis]    = value                # Also keep track of the "raw" axis reading (prior to calibration-recentering)
                shared.SAMPLE            = shared.SAMPLE + 1    # This tracks how many axis-updates we have received (only x and y events)
                shared.DEVICE_TIME       = deviceTime           # The latest known device time
                
                updated[axis]=True

                if all([ updated[x] for x in shared.AXIS_STATES.keys() ]):
                    # If all axes (x and y) have been updated, commit this as a "completed" position
                    commit_position()
                    updated= {"x":False,"y":False}  # reset the updated log
                    

            elif tp == 'button' and value == 1: 

                if pck_code==289:

                # A trigger signal is received from the joystick

                # TODO: make a smarter way to decide when we should write movement data for an *inactive* trial.
                #if shared.TRIGGER_COUNT not in shared.SCHEDULE and shared.TRIGGER_COUNT >= 0:

                # If this is the first trigger, mark the corresponding global value
                    shared.new_trigger_received()
                    print ('Trigger (pck_code = %s, axis = %s) received from button')%(str(pck_code),str(axis))
                else:
                    print ('Button (pck_code = %s, axis = %s) ignored.')%(str(pck_code),str(axis))
                        

            elif not (pckt_type == 0 and pck_code == 0): # throw away SYN packet with code 0 and value 0; these only act as separators
                # If we don't know what to do with this packet, drop it (but keep it for future debugging)
                shared.UNINTERPRETED.append(reading)

                

        # We have processed all the packets that have come in.
        # Based on cursory observations we found at most 2 packets in a batch,
        # one x and one y. So this is why we don't fire separate updates for a single packet but
        # only for a complete batch.

        # if it is the MOVE phase, check if the furthest position needs to be updated
        if shared.phase_in(["MOVE"]):
            
            # Distance from the center
            readingDistance = np.linalg.norm([shared.AXIS_STATES['x'], shared.AXIS_STATES['y']])

            #print("FURTHEST = ",trialdata["furthest.position"])
            #print("Dist = ",readingDistance,"for",shared.AXIS_STATES)
            # check if the current reading is further from the start than the furthest previously known excursion
            if readingDistance >= trialdata["furthest.distance"]:
                #print("Updating furthest")
                trialdata["furthest.position"] = (shared.AXIS_STATES["x"],shared.AXIS_STATES["y"])
                trialdata["furthest.distance"] = readingDistance
                trialdata["furthest.sample"]   = shared.SAMPLE
                

        if any([ updated[x] for x in shared.AXIS_STATES.keys() ]):
            # If all axes (x and y) have been updated, commit this as a "completed" position
            commit_position()




        # Check if the subject returned to the center (if they are not already there)
        if (shared.phase_in(["WRITE","WAIT","FEEDBACK"])) and not shared.RETURNED_TO_ORIGIN:
            readingDistance = np.linalg.norm([shared.AXIS_STATES['x'], shared.AXIS_STATES['y']])
            if readingDistance < shared.ORIGIN_THRESHOLD:
                shared.RETURNED_TO_ORIGIN = True
                print ('Subject returned to origin')

    
    return
