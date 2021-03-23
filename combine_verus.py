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
import glob
from tqdm import tqdm

if __name__ == '__main__':
    inputfolders_list = glob.glob('VERUS_training/verus/channel_log_*/')
    
    for folder in tqdm(inputfolders_list):

        if folder.endswith('/'):
            dirname = folder.rsplit('/', 2)[-2]
        else:
            dirname = folder.rsplit('/', 1)[-1]
            
        verusFile = open (os.path.join(folder, 'Verus.out'))
        receiverFile = open (os.path.join(folder, 'Receiver.out'))
        outFile = open (os.path.join(folder, dirname + '-combined.out'), 'w')

        vLine = verusFile.readline()
        vfields = vLine.strip().split(',')
        vfields = list(map(float,vfields))
        
        for line in receiverFile:
            fields = line.strip().split(',')
            fields = list(map(float,fields))

            # print (fields[0], vfields[0])
            while fields[0] > vfields[0]:
                outFile.write(vLine.strip()+','+'-1\n')

                vLine = verusFile.readline()
                if vLine == '':
                    break
                vfields = vLine.strip().split(',')
                vfields = list(map(float,vfields))

            outFile.write(line)

        verusFile.close()
        receiverFile.close()
        outFile.close()
