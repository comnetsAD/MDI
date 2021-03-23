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

# file with all plotting functions

import itertools
import numpy as np
import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.colors import LogNorm

# cmap = mpl.cm.hot
# invHot = reverse_colourmap(cmap)

# define the constants
WP_MAX = 60.0
WP_MIN = -60.0
WP_STEP = 2
DP_MAX = 4.0
DP_MIN = -4.0
DP_STEP = 2
DELAYS = np.arange(DP_MIN, DP_MAX + DP_STEP, DP_STEP)
WINDOWS = np.arange(WP_MIN, WP_MAX + WP_STEP, WP_STEP)
STATES = list(itertools.product(DELAYS, WINDOWS))
NUMSTATES = len(STATES)
INDEX_DICT = dict(zip(STATES, range(NUMSTATES)))


def reverse_colourmap(cmap, name = 'my_cmap_r'):
    reverse = []
    k = []

    for key in cmap._segmentdata:
        k.append(key)
        channel = cmap._segmentdata[key]
        data = []

        for t in channel:
            data.append((1-t[0],t[2],t[1]))
        reverse.append(sorted(data))

    LinearL = dict(zip(k,reverse))
    my_cmap_r = mpl.colors.LinearSegmentedColormap(name, LinearL)
    return my_cmap_r


def plot_statdistr_heatmap(statdistr, statesdistr, savepath_noext):

    statdistr_mat = statdistr.reshape((len(DELAYS), len(WINDOWS)))
    statesdistr_mat = statesdistr.reshape((len(DELAYS), len(WINDOWS)))
    
    plt.rc('font', size=40)
    plt.rc('ps', useafm=True)
    plt.rc('pdf', use14corefonts=True)

    window_ticks = np.arange(0, len(WINDOWS)+1, 10, dtype=np.int8)
    window_ticklabels = [''] + list(map(str, WINDOWS[window_ticks].astype(np.int8)))
    delay_ticks = np.arange(len(DELAYS), dtype=np.int8)
    delay_ticklabels = [''] + list(map(str, DELAYS[delay_ticks].astype(np.int8)))

    # print(window_ticks)
    # print(window_ticklabels)
    # print(delay_ticks)
    # print(delay_ticklabels)
    
    kw = dict(xlim=(-0.5, len(WINDOWS)-0.5), ylim=(-0.5, len(DELAYS)-0.5),
              xticks=window_ticks, yticks=delay_ticks,
              xticklabels=window_ticklabels, yticklabels=delay_ticklabels)
    
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(40,10), sharex=True, sharey=True, subplot_kw=kw)
    
    # ax = fig.add_subplot(111)
    im = ax1.matshow(statdistr_mat,
                     interpolation='none',
                     cmap=plt.get_cmap('gnuplot2_r'),
                     norm=mpl.colors.LogNorm(vmin=1e-7, vmax=statdistr_mat.max()),
                     aspect='auto')
    ax1.set_title('Theoretical stationary distribution')
    ax1.set_xlabel('WINDOW', labelpad=10)
    ax1.set_ylabel('DELAY', labelpad=10)
    ax1.tick_params(labelbottom=1, labeltop=0, left=0, bottom=0, pad=10)
    
    im = ax2.matshow(statesdistr_mat,
                     interpolation='none',
                     cmap=plt.get_cmap('gnuplot2_r'),
                     norm=mpl.colors.LogNorm(vmin=1e-7, vmax=statesdistr_mat.max()),
                     aspect='auto')
    ax2.set_title('After mixing time')
    ax2.set_xlabel('WINDOW', labelpad=10)
    ax2.tick_params(labelbottom=1, labeltop=0, pad=10)

    # print(plt.xticks())

    # print(ax1.get_xticklabels())
    
    cbar = fig.colorbar(im, ax=[ax1, ax2], orientation='horizontal', shrink=0.6, anchor=(0.5,0.05), aspect=30)
    cbar.solids.set_edgecolor('face')

    fig.subplots_adjust(0.1)
    fig.savefig(savepath_noext + '.png')
    fig.savefig(savepath_noext + '.pdf')
    
    plt.close(fig)
    plt.rcdefaults()

    return


# plot the transition matrix as a heatmap
def plot_transmatrix(mat, delays, windows, fig):
    
    C =  np.array([[255,255,0], [255,254,0], [255,253,0], [255,251,0], [255,250,0], [255,248,0], [255,247,0], [255,245,0], [255,244,0], [255,242,0], [255,241,0], [255,239,0], [255,238,0], [255,236,0], [255,235,0], [255,233,0], [255,232,0], [255,230,0], [255,228,0], [255,227,0], [255,225,0], [255,224,0], [255,222,0], [255,221,0], [255,219,0], [255,218,0], [255,216,0], [255,215,0], [255,213,0], [255,212,0], [255,210,0], [255,209,0], [255,207,0], [255,206,0], [255,204,0], [255,203,0], [255,201,0], [255,200,0], [255,198,0], [255,197,0], [255,195,0], [255,194,0], [255,192,0], [255,191,0], [255,189,0], [255,188,0], [255,186,0], [255,185,0], [255,183,0], [255,182,0], [255,180,0], [255,179,0], [255,177,0], [255,175,0], [255,174,0], [255,172,0], [255,171,0], [255,169,0], [255,168,0], [255,166,0], [255,165,0], [255,163,0], [255,162,0], [255,160,0], [255,159,0], [255,157,0], [255,154,0], [254,152,0], [254,150,0], [254,148,0], [254,146,0], [254,144,0], [254,142,0], [253,140,0], [253,138,0], [253,136,0], [253,134,0], [253,132,0], [253,129,0], [252,127,0], [252,125,0], [252,123,0], [252,121,0], [252,119,0], [252,117,0], [251,115,0], [251,113,0], [251,111,0], [251,109,0], [251,107,0], [251,104,0], [250,102,0], [250,100,0], [250,98,0], [250,96,0], [250,94,0], [250,92,0], [249,90,0], [249,88,0], [249,86,0], [249,84,0], [249,82,0], [249,79,0], [248,77,0], [248,75,0], [248,73,0], [248,71,0], [248,69,0], [247,67,0], [247,65,0], [247,63,0], [247,61,0], [247,59,0], [247,57,0], [246,54,0], [246,52,0], [246,50,0], [246,48,0], [246,46,0], [246,44,0], [245,42,0], [245,40,0], [245,38,0], [245,36,0], [245,34,0], [245,31,0], [244,29,0], [244,27,0], [243,26,0], [241,26,0], [239,25,0], [238,25,0], [236,24,0], [234,24,0], [232,24,0], [230,23,0], [228,23,0], [226,22,0], [224,22,0], [222,22,0], [221,21,0], [219,21,0], [217,20,0], [215,20,0], [213,19,0], [211,19,0], [209,19,0], [207,18,0], [205,18,0], [204,17,0], [202,17,0], [200,17,0], [198,16,0], [196,16,0], [194,15,0], [192,15,0], [190,15,0], [188,14,0], [187,14,0], [185,13,0], [183,13,0], [181,12,0], [179,12,0], [177,12,0], [175,11,0], [173,11,0], [171,10,0], [169,10,0], [168,10,0], [166,9,0], [164,9,0], [162,8,0], [160,8,0], [158,8,0], [156,7,0], [154,7,0], [152,6,0], [151,6,0], [149,5,0], [147,5,0], [145,5,0], [143,4,0], [141,4,0], [139,3,0], [137,3,0], [135,3,0], [134,2,0], [132,2,0], [130,1,0], [128,1,0], [126,1,0], [124,0,0], [122,0,0], [120,0,0], [118,0,0], [116,0,0], [114,0,0], [112,0,0], [111,0,0], [109,0,0], [107,0,0], [105,0,0], [103,0,0], [101,0,0], [99,0,0], [97,0,0], [95,0,0], [93,0,0], [91,0,0], [89,0,0], [87,0,0], [85,0,0], [83,0,0], [81,0,0], [80,0,0], [78,0,0], [76,0,0], [74,0,0], [72,0,0], [70,0,0], [68,0,0], [66,0,0], [64,0,0], [62,0,0], [60,0,0], [58,0,0], [56,0,0], [54,0,0], [52,0,0], [50,0,0], [48,0,0], [47,0,0], [45,0,0], [43,0,0], [41,0,0], [39,0,0], [37,0,0], [35,0,0], [33,0,0], [31,0,0], [29,0,0], [27,0,0], [25,0,0], [23,0,0], [21,0,0], [19,0,0], [17,0,0], [16,0,0], [14,0,0], [12,0,0], [10,0,0], [8,0,0], [6,0,0], [4,0,0], [2,0,0], [0,0,0]])
    my_cm = mpl.colors.ListedColormap(C/255)
    palette = my_cm
    palette.set_bad ('w',0.0) # Bad values (i.e., masked, set to white!)
    
    dim = mat.shape[0]
    # l=[]
    # l1=[]
    # for j in range(-4,6,2):
    #     for i in range(1,62):
    #         if i == 1:
    #             l.append(' \t-60')
    #             l1.append('-60\t ')
    #         elif i == 15:
    #             l.append('-30')
    #             l1.append('-30')
    #         elif i == 45:
    #             l.append(' \t30')
    #             l1.append('30\t ')
    #         elif i == 30:
    #             l.append(str(j)+'        0')
    #             l1.append('0        '+str(j))
    #         else:
    #             l.append(' \t ')
    #             l1.append(' \t ')
    #print(l)
    #print(l1)
    # fig, ax1 = plt.subplots(figsize=(8,6))
    ax = fig.add_subplot(111)
    ax_im = ax.matshow(mat, interpolation="none", cmap=palette, norm=LogNorm(vmin=0.01, vmax=np.nanmax(mat)), rasterized=True, aspect='auto', extent=[0, dim, dim, 0])

    # the labels "-4", "-2", "0", "2", "4" above the axes can be
    # plotted by using fig.text() function. To get the positions
    # needed, we allow the display of the xticklabels first, and then
    # pull their positions (both (x, y) coordinate and transform
    # parameter). Then we call fig.text to insert texts in between
    # these positions, but positioned a little higher, using the same
    # transform parameter
    windowslen = len(windows)
    
    # plt.xticks(range(0,len(a),len(windows)), [], rotation='vertical',fontsize='xx-small') #, annotation[::len(windows)], rotation='vertical', fontsize='xx-small')

    minorlabels = []
    numintervals = 4
    intervalgap = round(windowslen/numintervals)
    # print('Interval gap:', intervalgap)
    for k in range(0, dim):
        r = (k % windowslen)
        if (r % intervalgap) == 0:
            # print(k, r, -windowslen + 2*r)
            minorlabels.append(str(-windowslen + 2*r + 1))
        else:
            minorlabels.append('')

    # print(minorlabels)
    ax.set_xticks(np.arange(0, dim, windowslen))
    ax.set_xticklabels([])
    ax.set_xticks(range(0, dim), minor=True)
    ax.set_xticklabels(minorlabels, minor=True, rotation='vertical', fontsize=10)

    #Talal
    # ax.set_xticklabels(l1, minor=True, rotation='vertical', fontsize=10)

    # plt.yticks(range(0,len(a),len(windows)), [], fontsize='xx-small') #, annotation[::len(windows)], fontsize='xx-small')
    ax.set_yticks(np.arange(0, dim, windowslen))
    ax.set_yticklabels([])
    ax.set_yticks(range(0, dim), minor=True)
    ax.set_yticklabels(minorlabels, minor=True, fontsize=10)
    # ax.set_yticks(range(0,len(a)), minor=True)
    # ax.set_yticklabels(list(map(str,windows))*len(delays), minor=True, fontsize=5)

    #Talal
    # ax.set_yticklabels(l, minor=True, fontsize=10)

    plt.tick_params(axis='x', direction='out', pad=20)
    plt.tick_params(axis='y', direction='out', pad=20, labelrotation=90)
    plt.tick_params(axis='both', which='minor', top=0, bottom=0, left=0, right=0)
    
    # render the plot so that the axis label objects are updated 
    plt.draw()

    # now create text objects using minorlabel positions and transforms
    # ...
    # ...
    
    plt.xlabel('(% d *log(d), % w *log(w))')
    plt.ylabel('(% d *log(d), % w *log(w))')

    ax.grid(which='minor', alpha=0.2)
    ax.grid(which='major', alpha=0.5)

    cbar = fig.colorbar(ax_im)
    cbar.solids.set_edgecolor("face")
    plt.draw()

    # fig.savefig('../../figures/ledbat_matrix_transition.pdf')
    # fig.savefig('ledbat_matrix_transition.pdf')
    # fig.savefig(savepath_noext + '.pdf')

    # plt.close(fig)
    return fig

