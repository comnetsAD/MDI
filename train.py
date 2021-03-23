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

import os, sys
import math
import random
import argparse
import itertools
import numpy as np
import matplotlib as mpl
import matplotlib.pyplot as plt
#from matrix_analysis import analyze_matrix

from tqdm import tqdm
WP_MAX = 20.0
WP_MIN = -20.0
WP_STEP = 2
DP_MAX = 10.0
DP_MIN = -10.0
DP_STEP = 2

DELAYS = np.arange(DP_MIN, DP_MAX + DP_STEP, DP_STEP)
WINDOWS = np.arange(WP_MIN, WP_MAX + WP_STEP, WP_STEP)
NUM_STATES = DELAYS.size * WINDOWS.size        
index_dict = dict(zip(itertools.product(DELAYS, WINDOWS), range(NUM_STATES)))


def train(algo, findex_list_train, outsuffix):

    findex_list = list(range(int(args.numfiles)))
    findex_list_test = np.setdiff1d(findex_list, findex_list_train, assume_unique=True)
    print(findex_list_test)
    
    print('Creating the transition matrix for', algo)
    
    fpath = 'processed/{0}/processed-{{}}-{0}.out'.format(algo)
    
    matrix = np.zeros((NUM_STATES, NUM_STATES), dtype=np.int32)
    
    for findex in tqdm(findex_list_train):
        obs = np.loadtxt(fpath.format(findex))


        for i in range(obs.shape[0]-1):
            try:
                if not np.isnan(obs[i:i+2,:]).any():
                    matrix[index_dict[tuple(obs[i,:])],index_dict[tuple(obs[i+1,:])]] += 1
            except:
                continue
    
    # store the matrix without normalizing it, so that there are no
    # reductions in accuracy due to floating point arithmetic
    savepath = os.path.join('training/', algo, 'transmatrix-{}-{}.csv'.format(algo, outsuffix))
    np.savetxt(savepath, matrix, delimiter=',', fmt='%d')
    
    savepath = os.path.join('training/', algo, 'findex-train-{}-{}.csv'.format(algo, outsuffix))
    np.savetxt(savepath, findex_list_train, fmt='%d')
    
    savepath = os.path.join('training/', algo, 'findex-test-{}-{}.csv'.format(algo, outsuffix))
    np.savetxt(savepath, findex_list_test, fmt='%d')
    
    return


if __name__ == '__main__':
    
    parser = argparse.ArgumentParser()
    parser.add_argument('algo', choices=('tcp', 'verus', 'sprout', 'bbr', 'ledbat','copa'))
    # parser.add_argument('--mode', '-m', required=True, help='Weather to just plot(p) or calculate(c) the matrices')
    # parser.add_argument('--infolder', '-i', help='Input folder')
    # parser.add_argument('--outfolder', '-o', help='Output directory')
    # parser.add_argument('--outfilesuffix', help='Output file name suffix')
    parser.add_argument('--numfiles', type=int, default=940, help='Number of *.out files to use for training')
    parser.add_argument('--randseed', type=int, default=0, help='Random seed for shuffling input files for selecting subset')
    args = parser.parse_args()
    
    findex_list = list(range(int(args.numfiles)))
    findex_list_train = findex_list
    findex_list_test = []
    
   
    outsuffix = 'N{:03d}-{}'.format(args.numfiles, args.randseed)
    outsuffix = 'N{:03d}'.format(len(findex_list))

    train(args.algo, findex_list_train, outsuffix)
