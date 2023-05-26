import os, struct, array
from fcntl import ioctl
import fcntl
import time
import shared





AXIS_MAP = {
    0x00: 'x',
    0x01: 'y'
}


PACKET_SIZE = struct.calcsize('LLHHi')


def poll():
    # Attempts to read a packet from the joystick input device,
    # and returns it if succesful or None otherwise.
    try:
        buff = os.read(shared.JS_FILE, PACKET_SIZE )
        return buff
    except OSError:
        return None



def readjs():
    # Read input from the joystick.
    # The variable start indicates a reference time point relative to which
    # the current time is coded.
    # We return an array of packets that are received:
    #    ( type,    packet_type,  packet_code,    axis,     value,   t,    usecs )
    #  where type is our script-assigned type identifier (axis or button or unknown)
    #  and packet_type is the type-identifier sent by the joystick (for verification)
    #  also packet_code is the type-identifier sent by the joystick,
    #  axis is "" except if this is an axis event in which case we interpret it as "x" or "y",
    #  value is the value in the packet (e.g. the position readout)
    #  t is the time according to our script (from the shared module)
    #  and usecs is the device_time.
    # Phew, that's a lot of stuff!

    updates = []

    # Get the current time
    t = shared.t_since_start()

    received = []
    buff = poll()
    while buff: # While we keep getting data packets
        received.append(buff)
        buff = poll()

    # Now that silence has returned (no more packets are waiting), let's interpret these events
    for buff in received:
        
        # Interpret the binary packet
        secs, usecs, packedType, packedCode, value = struct.unpack('LLHHi', buff)

        # If this is an axis event (change in position)
        if packedType == 0x03:
            ax = packedCode
            if packedCode in AXIS_MAP.keys(): #0x00 or packedCode == 0x01:
                ax = AXIS_MAP[packedCode]
                updates.append(('axis',    packedType,  packedCode,   ax,  value, t, usecs))
            else: # This is not one of the axes that we're reading from
                updates.append(('unknown', packedType,  packedCode,  "", value, t, usecs))

        elif packedType == 0x01: # If this is a button press event
            updates.append(('button', packedType,  packedCode, "", value, t, usecs))

        else: 
            # If this is an unknown event, simply return it as such.
            updates.append(('unknown', packedType, packedCode, "", value, t, usecs))

    return updates




