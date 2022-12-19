#!/usr/bin/env python3

import matplotlib.pyplot as plt
import os
import sys


#####
##### Global vars
#####

DIR_FIG = "figs"
DIR_DATA = "data"
DIR_RAW = "raw-data"

FORMAT_LEGEND = dict(framealpha=1, handletextpad=0.5, edgecolor="black")

### NSDI 22
# FIG_SIZE_ONE_COL_SMALL = dict(figsize=(4.8,0.7))
### FC 23
# FIG_SIZE_ONE_COL_FC    = dict(figsize=(4,1.5))
### OSDI 23
FIG_SIZE_ONE_COL        = dict(figsize=(5,1.5))
FIG_SIZE_ONE_COL_LINERATE = dict(figsize=(6,1.65))
FIG_SIZE_ONE_COL_MOTIV  = dict(figsize=(4,1.7))
FIG_SIZE_ONE_COL_SMALL  = dict(figsize=(3,1.5))
# FIG_SIZE_ONE_COL_BIG    = dict(figsize=(6,3)) # toy
# FIG_SIZE_ONE_COL_SQUARE = dict(figsize=(5,5)) # toy
FIG_SIZE_TWO_COL        = dict(figsize=(11,1.5))

# FIG_SIZE_ONE_COL_SMALL = dict(figsize=(4,0.7))
# FIG_SIZE_NO_YLABEL = dict(figsize=(2.0,2))


FONT_SIZE_XS = 10
FONT_SIZE_S  = 12
FONT_SIZE_M  = 13
FONT_SIZE_L  = 14


#####
##### Utils
#####

def init():
    ### Change default font sizes
    ### https://stackoverflow.com/questions/3899980/how-to-change-the-font-size-on-a-matplotlib-plot/39566040#39566040
    plt.rc('font',        size=FONT_SIZE_S) # default text
    plt.rc('axes',   titlesize=FONT_SIZE_M) # figure title
    plt.rc('axes',   labelsize=FONT_SIZE_M) # x and y labels
    plt.rc('xtick',  labelsize=FONT_SIZE_S) # xticks
    plt.rc('ytick',  labelsize=FONT_SIZE_S) # yticks
    plt.rc('legend',  fontsize=FONT_SIZE_M) # legend
    plt.rc('figure', titlesize=FONT_SIZE_L) # overarching figure title


def commonFigFormat(ax):
    ### Grid behind the lines/bars
    ax.grid(which='both', axis='both', linestyle='--')
    ax.set_axisbelow(True)

    ### Remove borders
    ax.spines['top'].set_visible(False)
    # ax.spines['bottom'].set_visible(False)
    # ax.spines['left'].set_visible(False)
    ax.spines['right'].set_visible(False)


def addBreakClipsX(ax1, ax2):
    """
    Code to add diagonal slashes to truncated x-axes.
    Source: http://matplotlib.org/examples/pylab_examples/broken_axis.html
    """
    d = 0.015 # how big to make the diagonal lines in axes coordinates
    # arguments to pass plot, just so we don't keep repeating them
    kwargs = dict(transform=ax1.transAxes, color='black', clip_on=False)
    # ax1.plot((-d,+d),(-d,+d), **kwargs)      # top-left diagonal
    ax1.plot((1-d,1+d),(-d,+d), **kwargs)    # bottom-right diagonal

    kwargs.update(transform=ax2.transAxes)  # switch to the bottom axes
    # ax2.plot((-d,+d),(1-d,1+d), **kwargs)   # bottom-left diagonal
    # ax2.plot((1-d,1+d),(1-d,1+d), **kwargs) # bottom-right diagonal
    ax2.plot((-d,+d),(-d,+d), **kwargs)     # bottom-left diagonal


def addBreakClipsY(ax1, ax2):
    """
    Code to add diagonal slashes to truncated y-axes.
    Source: http://matplotlib.org/examples/pylab_examples/broken_axis.html
    """
    d = 0.015 # how big to make the diagonal lines in axes coordinates
    # arguments to pass plot, just so we don't keep repeating them
    kwargs = dict(transform=ax1.transAxes, color='black', clip_on=False)
    ax1.plot((-d,+d),(-d,+d), **kwargs)      # top-left diagonal
    ax1.plot((1-d,1+d),(-d,+d), **kwargs)    # top-right diagonal

    kwargs.update(transform=ax2.transAxes)  # switch to the bottom axes
    ax2.plot((-d,+d),(1-d,1+d), **kwargs)   # bottom-left diagonal
    ax2.plot((1-d,1+d),(1-d,1+d), **kwargs) # bottom-right diagonal


def autolabel(rects):
    """Attach a text label above each bar in *rects*, displaying its height."""
    for rect in rects:
        height = rect.get_height()
        ax.annotate('{}'.format(height),
            xy=(rect.get_x() + rect.get_width() / 2, height),
            xytext=(0, 3),  # 3 points vertical offset
            textcoords="offset points",
            ha='center', va='bottom')


def saveFig(filename):
    ### Create fig dir if needed
    if not os.path.exists(DIR_FIG):
        os.makedirs(DIR_FIG)
        print("Created " + DIR_FIG)

    # filePathEps = "{}/{}.eps".format(DIR_FIG, filename)
    filePathPdf = "{}/{}.pdf".format(DIR_FIG, filename)
    # plt.savefig(filePathEps, format="eps", bbox_inches='tight', pad_inches=0.01) # to insert
    plt.savefig(filePathPdf, format="pdf", bbox_inches='tight', pad_inches=0.01) # to preview
    plt.close()
    # print("Created {}/{}.{{pdf,eps}}".format(DIR_FIG, filename))
    print("Created {}/{}.pdf".format(DIR_FIG, filename))
