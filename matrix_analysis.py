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

# compute limiting distributions and see if all the matrices represent MCs 
# that converge to the limiting distribution. How many different limiting 
# distributions exist? Store them all so they can be smoothened and classified.

import os
import argparse
import itertools
import numpy as np
import matplotlib as mpl
import matplotlib.pyplot as plt

from tqdm import tqdm
from plotfuncs import plot_transmatrix, plot_statdistr_heatmap

# define the constants
WP_MAX = 20.0
WP_MIN = -20.0
WP_STEP = 2
DP_MAX = 10.0
DP_MIN = -10.0
DP_STEP = 2


DELAYS = np.arange(DP_MIN, DP_MAX + DP_STEP, DP_STEP)
print (DELAYS)
WINDOWS = np.arange(WP_MIN, WP_MAX + WP_STEP, WP_STEP)
print (WINDOWS)
STATES = list(itertools.product(DELAYS, WINDOWS))
print(STATES)
NUMSTATES = len(STATES)
print (NUMSTATES)
INDEX_DICT = dict(zip(STATES, range(NUMSTATES)))

def cmax(a, **kwargs):
    """ Complex max """
    a = np.asarray(a)
    a_mag = np.abs(a)
    return a[a_mag==a_mag.max(**kwargs)]


def cmin(a, **kwargs):
    """ Complex min """
    a = np.asarray(a)
    a_mag = np.abs(a)
    return a[a_mag==a_mag.min(**kwargs)]


def compute_kld(p, q):

    # print(p)
    # print(q)
    
    assert np.all(p >= 0)
    assert np.all(q >= 0)
    p_ma = np.ma.masked_equal(p, 0)
    q_ma = np.ma.masked_equal(q, 0)
    crossentropy = np.sum(-p_ma * np.log(q_ma))
    kld = crossentropy - np.sum(-p_ma * np.log(p_ma))
    return crossentropy, kld

def compute_statescounts(dirname, algo, suffix, thres, skip=None, recompute=False):

    print('Computing states counts...')

    savepath = os.path.join('{}-{}-statescounts-{}.txt'.format(algo, suffix, thres))

    # if cached, return it
    if os.path.exists(savepath) and not recompute:
        statescounts = np.loadtxt(savepath, dtype=np.int32)
        return statescounts
    
    # initialize skip if not provided
    if skip is None:
        skip = np.zeros(len(STATES), dtype=np.int32)

    # dirname is the full path to the "processed" directory files
    flist = glob.glob(os.path.join(dirname, algo, 'processed-*.out'))
    flist.sort()
    
    statescounts = np.zeros(len(STATES), dtype=np.int32)
    
    for fpath in tqdm(flist, desc='Reading all processed files'):
        obs = np.loadtxt(fpath)
        j = 1
        while np.isnan(obs[j,:]).any():
            j += 1
        try:
            start = skip[INDEX_DICT[tuple(obs[j,:])]] + 1
        except:
            continue
        # # print(start)
        # print(obs.shape[0])
        for i in range(int(start), obs.shape[0]):
            dp, wp = obs[i,:]
            if DP_MIN <= dp <= DP_MAX and WP_MIN <= wp <= WP_MAX:
                statescounts[INDEX_DICT[(dp, wp)]] += 1

    # cache it
    np.savetxt(savepath, statescounts, fmt='%d')
    
    return statescounts



def analyze_matrix(fpath, outfolder, nocache=False):
    # output log    
    if not os.path.exists(outfolder):
        print('Output folder {} does not exist. Creating it...'.format(outfolder))
        os.makedirs(outfolder)
    
    saveprefix = os.path.splitext(os.path.basename(fpath))[0].split('-',1)[1]
    
    # outname = fpath1 + '_analysis'
    fout = open(os.path.join(outfolder, '{}-output.txt'.format(saveprefix)), 'w')
    
    mat = np.loadtxt(fpath, delimiter=',', dtype=np.int32)

    row_indices, = np.where(mat.sum(axis=1) == 0)
    # (1) states that are zero
    states_zero = [STATES[i] for i in row_indices]
    print('Num zero states: ', len(states_zero))
    print('Zero states: ', states_zero)
    print('Num zero states: ', len(states_zero), file=fout)
    print('Zero states: ', states_zero, file=fout)
    
    # now fill in these rows with uniform distribution
    mat_filled_norm = np.array(mat, copy=True, dtype=np.float64)
    mat_filled_norm[row_indices,:] = 1
    mat_filled_norm[:,:] = mat_filled_norm / mat_filled_norm.sum(axis=1)[:,None]
    
    # quadrant normalize
    mat_quadnorm = mat.astype(np.float64)
    for i in range(len(DELAYS)):
        for j in range(len(DELAYS)):
            quadrant = mat_quadnorm[i*len(WINDOWS):(i+1)*len(WINDOWS),j*len(WINDOWS):(j+1)*len(WINDOWS)]
            quadrant[:,:] = quadrant / quadrant.sum(axis=1)[:,None]

            quadrant[quadrant < 0.02] = 0
            quadrant[:,:] = quadrant * (1/quadrant.sum(axis=1)[:,None])
    
    # replace nans with zero that were created on 0/0 divisions
    mat_quadnorm[np.isnan(mat_quadnorm)] = 0
    
    # (2) stationary distribution
    ew, evr = np.linalg.eig(mat_filled_norm.T)
    statdistr = evr[:,0]
    if not np.isreal(statdistr).all():
        raise Exception('Stationary distr has complex entries!')
    statdistr = evr[:,0].real
    statdistr = statdistr / statdistr.sum()
    statdistr[statdistr < np.finfo(statdistr.dtype).eps] = 0
    fig1 = plt.figure()
    plt.plot(statdistr)
    plt.title('Stationary distribution')
    plt.xlabel('States')
    plt.ylabel('Probability')
    plt.savefig(os.path.join(outfolder, '{}-statdistr.png'.format(saveprefix)))
    plt.savefig(os.path.join(outfolder, '{}-statdistr.pdf'.format(saveprefix)))
    plt.close()
    np.savetxt(os.path.join(outfolder, '{}-statdistr.txt'.format(saveprefix)), statdistr, fmt='%f')
    print('Stat distr: min {}, max {}'.format(statdistr.min(), statdistr.max()))
    print('Stat distr: min {}, max {}'.format(statdistr.min(), statdistr.max()), file=fout)

    topstates_stat_ind = np.argsort(statdistr)[::-1]

    print(STATES[topstates_stat_ind[0]], STATES[topstates_stat_ind[1]])
    topstates_statdistr = statdistr[topstates_stat_ind]

    np.savetxt(os.path.join(outfolder, '{}-topstates.txt'.format(saveprefix)),
               [(STATES[i][0], STATES[i][1], statdistr[i]) for i in topstates_stat_ind],
               fmt=['%.0f', '%.0f', '%f'])
    
    topstates_statdistr_cumsum = topstates_statdistr.cumsum()

    plt.figure()
    plt.plot(topstates_statdistr_cumsum)
    plt.title('Cumulative probability from most probable state to least probable state')
    plt.xlabel('States')
    plt.ylabel('Cumulative probability')
    plt.savefig(os.path.join(outfolder, '{}-stat-topstates-cumdistr.png'.format(saveprefix)))
    plt.savefig(os.path.join(outfolder, '{}-stat-topstates-cumdistr.pdf'.format(saveprefix)))
    plt.close()
    
    topstates_n = len(np.where(topstates_statdistr_cumsum <= 0.99)[0])
    print('Stat distr top states (p >= 0.99):', topstates_n)
    # plt.show()
    
    # (3) limiting distribution
    # epsilon "machine epsilon"
    threshold = np.finfo(np.float32).eps

    # list of thresholds
    threshold_list = ['1e-3', '1e-5', '1e-7']

    for thres_str in threshold_list:

        print('\n**** Threshold = {} ****'.format(thres_str))
        print('\n**** Threshold = {} ****'.format(thres_str), file=fout)
        
        threshold = eval(thres_str)
        
        limitdistr = np.zeros(mat_filled_norm.shape, dtype=np.float64)
        
        numiters = np.zeros(NUMSTATES, dtype=np.int32)
        for i in tqdm(range(NUMSTATES)):
            vec = np.zeros(NUMSTATES, dtype=np.float64)
            vec[i] = 1
            while True:
                vec_next = np.matmul(vec, mat_filled_norm)
                if np.abs(vec_next - vec).max() < threshold:
                    limitdistr[i,:] = vec
                    break
                vec = vec_next
                numiters[i] += 1
        # limitdistr[limitdistr < threshold] = 0
        diffs_limitdistr = limitdistr - limitdistr[0,:]
        diffs_limitstatdistr = limitdistr - statdistr
        print('Limiting distr unique? Max diff in probs = {}'.format(diffs_limitdistr.max()))
        print('Limiting distr close to statdistr? Max diff in probs = {}'.format(diffs_limitstatdistr.max()))
        print('Limiting distr unique? Max diff in probs = {}'.format(diffs_limitdistr.max()), file=fout)
        print('Limiting distrs close to statdistr? Max diff in probs = {}'.format(diffs_limitstatdistr.max()), file=fout)
        
        # (4) mixing times
        print('Min mixing time: {} iterations / RTTs'.format(numiters.min()))
        print('Max mixing time: {} iterations / RTTs'.format(numiters.max()))
        print('Min mixing time: {} iterations / RTTs'.format(numiters.min()), file=fout)
        print('Max mixing time: {} iterations / RTTs'.format(numiters.max()), file=fout)
        
        np.savetxt(os.path.join(outfolder, '{}-mixingtimes-{}.txt'.format(saveprefix, thres_str)), numiters, fmt='%d')
            
    # expected values of delays and windows after convergence
    statdistr_mat = statdistr.reshape((len(DELAYS), len(WINDOWS)))
    delaydistr = statdistr_mat.sum(axis=1)
    windowdistr = statdistr_mat.sum(axis=0)
    expecteddelayhat = np.dot(delaydistr, DELAYS)
    expectedwindowhat = np.dot(windowdistr, WINDOWS)
    
    plt.rc('font', size=20)
    
    fig, (ax1, ax2) = plt.subplots(2, 1, sharey=True, subplot_kw=dict(ylabel='Probability', ylim=(0,1)), figsize=(12,12))
    fig.suptitle('Stationary distributions of delay and window')
    
    ax1.plot(delaydistr)
    ax1.set_xlabel(r'$\hat{d}$')
    ax1.set_xlim(-1, len(DELAYS))
    ax1.set_xticks(np.arange(len(DELAYS)))
    xticks = ax1.get_xticks()
    ax1.set_xticklabels(map(str, DELAYS[xticks.astype(np.int8)]))
    ax1.tick_params(length=10, pad=10)
    
    ax2.plot(windowdistr)
    ax2.set_xlabel(r'$\hat{w}$')
    ax2.set_xlim(-1, len(WINDOWS))
    ax2.set_xticks(np.arange(0, len(WINDOWS), 15))
    xticks = ax1.get_xticks()
    #ax2.set_xticklabels(map(str, WINDOWS[xticks.astype(np.int8)]))
    ax2.tick_params(length=10, pad=10)

    fig.savefig(os.path.join(outfolder, '{}-statdistr-delaywindow.png'.format(saveprefix)))
    fig.savefig(os.path.join(outfolder, '{}-statdistr-delaywindow.pdf'.format(saveprefix)))
    plt.close(fig)
    plt.rcdefaults()
    

    # (7) spy plots
    fig4 = plt.figure()
    # plt.spy(mat_filled_norm)
    fig4 = plot_transmatrix(mat_filled_norm, DELAYS, WINDOWS, fig4)
    # plt.title('Sparsity pattern of transition matrix')
    #plt.grid(b=None)
    #plt.axis('off')
    plt.savefig(os.path.join(outfolder, '{}-spy.png'.format(saveprefix)))
    plt.savefig(os.path.join(outfolder, '{}-spy.pdf'.format(saveprefix)), dpi=2000)
    # plt.show()

    fig5 = plt.figure()
    fig5 = plot_transmatrix(mat_quadnorm, DELAYS, WINDOWS, fig5)
    #plt.grid(b=None)
    #plt.axis('off')
    plt.savefig(os.path.join(outfolder, '{}-oldmatrix.png'.format(saveprefix)))
    plt.savefig(os.path.join(outfolder, '{}-oldmatrix.pdf'.format(saveprefix)), dpi=2000)

    outFile = open(os.path.join(outfolder, '{}-transMatrix.csv'.format(saveprefix)),'w')
    outFile.write("{0},{1},{2},{3},{4},{5},{6},{7}\n".format(int((WP_MAX-WP_MIN)/WP_STEP+1),int(WP_MIN),int(WP_MAX),int(WP_STEP),int((DP_MAX-DP_MIN)/DP_STEP+1),int(DP_MIN),int(DP_MAX),int(DP_STEP)))
    np.savetxt(outFile, mat_quadnorm, delimiter=',', fmt='%.10f')
    outFile.close()

    plt.close('all')
    
    fout.close()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('matrixfpath', help='Path to matrix file')
    parser.add_argument('--outfolder', default='figures', help='Folder to save outputs of analyses and figures')
    parser.add_argument('--clean', action='store_true', help='Recompute everything; no cached files')
    args = parser.parse_args()

    with np.errstate(divide='ignore', invalid='ignore'):
        analyze_matrix(args.matrixfpath, args.outfolder, args.clean)

