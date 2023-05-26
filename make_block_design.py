#
# This makes a schedule file for a simple block-design.
#
# ---------------------------------------------------------------------
# SET THE VARIABLES BASED ON YOUR EXPERIMENT DESIGN


fileName    = 'schedule_new.txt'

condition   = 'SLT'  # SLT/RLT



### -------------------------###
######### SLT SETTINGS #########


# Defined Sequence in SLT
seq_slt         = 'FBLRFBLR'

# Number of sequences within a block
nseqs_slt       = 2

# Number of blocks
nblocks_slt     = 1



### -------------------------###
######### RLT SETTINGS #########

# Number of Trials inside each seq
seqLength_rlt  = 8  
nseq_rlt       = 5 
nblocks_rlt    = 5


### -------------------------------###
########## ROTATION SETTINGS #########
### IMPORTANT FOR BOTH SLT AND RLT ###


# maximum applied rotation
rot_max     = 10

# type of applied rotation
rot_type    = 'zero'    # gradual/abrupt/zero

# ONLY USED IN GRADUAL VERSION
# tr: trials based increments. seq: sequence based increments
grad_type   = 'tr'         # tr/seq


# trial/sequence at which rotation starts to increment
# keep in mind that trial/sequence number starts from "1" 
rot_start   = 5          

# ONLY USED IN GRADUAL VERSION
# trial/sequence at which rotation makes the plateau
# keep in mind that trial/sequence number starts from "1"
rot_plateau = 41         



# ---------------------------------------------------------------------
# DO NOT CHANGE THIS PART



import numpy as np
import sys
import matplotlib.pyplot as plt
import random as rd
import time

# Defined dictionary for the directions of the targets and their names
myDict      = { "F": 90,
                "L": 180,
                "B": -90,
                "R": 0,
                "f": 90,
                "l": 180,
                "b": -90,
                "r": 0,
                }



num2let     = { 1: "F",
                2: "R",
                3: "B",
                4: "L",
                }




seq_length  = len(seq_slt)
seq_total   = nseqs_slt*nblocks_slt
ntrials     = seq_length*seq_total


iti     = 0  # time between trial onsets
#offset = (4*2.5)-1.0   # time relative to TR signal
offset  = 0


if condition.lower() == "rlt":

    ntrials = seqLength_rlt*nseq_rlt*nblocks_rlt
    
    TargNow = rd.randint(1, 4)
    allTarg   = []
    allTargLabel = []
    for rep in range(ntrials):
        targetSet = [1, 2, 3, 4]
        targetSet.remove(TargNow)
        TargNow = targetSet[rd.randint(0, 2)]
        allTarg.append(myDict[num2let[TargNow]])
        allTargLabel.append(TargNow)



if rot_type.lower() == "zero":
    
    rot   = np.zeros(ntrials)

elif rot_type.lower() == "gradual":
    
    if grad_type.lower() == "seq":
    
        zer   = np.zeros(seq_length*(rot_start-1))
        slope = np.array(range((rot_plateau-rot_start)))/(rot_plateau-rot_start)
        slope = list(np.repeat(slope, seq_length))
        
        plat  = np.ones(seq_length*(seq_total-rot_plateau+1))
        
        rot   = np.concatenate((zer, slope, plat))
        rot   = rot_max*rot
        
    elif grad_type.lower() == "tr":
        
        zer   = np.zeros(rot_start-1)
        slope = np.array(range(rot_plateau-rot_start))/(rot_plateau-rot_start)
        plat  = np.ones(ntrials-rot_plateau+1)
        
        rot   = np.concatenate((zer, slope, plat))
        rot   = rot_max*rot
        
    else:
        print("Set the gradual rotation type to either: tr/seq")
        sys.exit()


elif rot_type.lower() == "abrupt":
    
    zer   = np.zeros(rot_start-1)
    plat  = np.ones(ntrials-rot_start+1)
    
    rot   = np.concatenate((zer, plat))
    rot   = rot_max*rot
    
else:
    print("Set the rotation type to either: abrupt/gradual/zero")
    sys.exit()




# writing to file

fname = 'schedule/' + fileName
f = open(fname,'w')
f.write('trial seq trialInSeq block type direction rotation TR t t.offset\n')



if condition.lower() == "rlt":
    tr = 0
    for b in range(nblocks_rlt):
        for s in range(nseq_rlt):
            for t in range(seqLength_rlt):
                f.write('%i %i %i %i active %i %f 1 %f 0.0\n'%(tr, s, t, b, allTarg[tr], rot[tr], iti*tr+offset))
                tr += 1
    f.close()

elif condition.lower() == "slt":
    tr = 0
    for b in range(nblocks_slt):
        for s in range(nseqs_slt):
            for t in range(seq_length):
                f.write('%i %i %i %i active %i %f 1 %f 0.0\n'%(tr, s, t, b, myDict[seq_slt[t]], rot[tr], iti*tr+offset))
                tr += 1
    f.close()
else:
    print("set condition to either rlt or slt")
    sys.exit(-1)











# plotting

if condition.lower() == "slt":

    for xc in range(nblocks_slt):
        plt.axvline(x=seq_length*nseqs_slt*xc, color='r', label='Block', linewidth=1)


    a = np.linspace(0,ntrials-1,ntrials)
    b = rot_max*np.ones(ntrials)

    for xc in range(1, ntrials, 2):
        plt.fill_between(a, b, 0,
                         where = (a >= seq_length*xc) & (a < seq_length*(xc+1)),
                         color = 'g', alpha = .3, linewidth=0)
        plt.fill_between(a, b, 0,
                         where = (a >= seq_length*(xc-1)) & (a < seq_length*(xc)),
                         color = 'y', alpha = .3, linewidth=0)

        
    plt.plot(range(0, ntrials), rot, linewidth=3, alpha=.9)


else:

    for xc in range(nblocks_rlt):
        plt.axvline(x=seqLength_rlt*nseq_rlt*xc, color='r', label='Block', linewidth=1)

    if rot_type.lower() == "zero" or  rot_max == 0:
        plt.plot(range(ntrials), allTargLabel, '-o', linewidth= .25 , color='gray', markersize=2, markerfacecolor='k', markeredgecolor='k',markeredgewidth=.5)
    else:
        plt.plot(range(ntrials), .8*rot_max*allTargLabel, '-o', linewidth= .25, color='gray', markersize=2, markerfacecolor='k', markeredgecolor='k',markeredgewidth=.5)


    plt.plot(range(0, ntrials), rot, linewidth=3, alpha=.9)    






plt.ylabel('Rotation')
plt.xlabel('Trial Number')
plt.savefig(fname[0:-4]+'.png', dpi=1000)

print("Written to %s"%fname)

