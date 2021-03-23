'''
  MIT License
  Copyright (c) 2021 Muhammad Khan, Yasir Zaki, Shiva Iyer, Talal Ahmad, 
  Thomas Poetsch, Jay Chen, Anirudh Sivaraman, and Lakshmi Subramanian
  Permission is hereby granted, free of charge, to any person obtaining a copy
  of this software and associated documentation files (the "Software"), to deal
  in the Software without restriction, including without limitation the rights
  to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
  copies of the Software, and to permit persons to whom the Software is
  furnished to do so, subject to the following conditions:
  The above copyright notice and this permission notice shall be included in all
  copies or substantial portions of the Software.
  THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
  IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
  FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
  AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
  LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
  OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
  SOFTWARE.
'''

import os
import numpy as np
from tqdm import tqdm
import sys


def rounding(a,b):
    return round(a/b)*b

findex_list = list(range(int(sys.argv[1])))

print('Number of input files to process:', len(findex_list))

for channel in tqdm(findex_list, desc='Verus'):
    combinedFile = open(os.path.join("VERUS_training/verus", 'channel_log_{0}/channel_log_{0}-combined.out'.format(channel)))
    
    lastD = 1
    lastW = -1
    lastACKtime = 0
    
    delays = []
    observations = []

    for line in combinedFile:
        fields = line.strip().split(',')

        if len (fields) == 5:
            # this line is from Receiver log, we add the delay value
            # this way we can get the dMax of the epoch
            delays.append(float(fields[2]))
            lastACKtime = float(fields[0])

        elif len (fields) >= 7:
            
            w = float(fields[4])
            w = w if w != 0 else 1
          
            
            if len(delays) > 0:
                d = max(delays)
                delays.clear()
            else:
                d = max(lastD, (float(fields[0])-lastACKtime)*1000)

            if lastW < 0:
                lastW = w
                lastD = d
                continue

            wp = rounding ((round(w/lastW, 4)*100 - 100) * np.log10(lastW), WP_STEP)
            dp = rounding ((round(d/lastD, 4)*100 - 100) * np.log10(lastD), DP_STEP)


            observations.append((dp, wp))

            lastD = d
            lastW = w

    # store window and delay values so the train script does not
    # have to be run again
    np.savetxt(os.path.join("processed/verus", 'processed-{}-verus.out'.format(channel)), observations, fmt='%.0f')

