#!/usr/bin/env python3

import math
import matplotlib.cbook as cbook
import matplotlib.colors as col
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import numpy as np
import pandas as pd
import re
import string

# local import
import utils





#####
##### Global vars are for lazy people
#####

BAR_FORMAT = {
    ### Eval plots
    "CC-BFT-SMaRt": {"hatch": "/", "facecolor": "white", "edgecolor": "tab:blue"},
    "CC-HotStuff": {"hatch": "x", "facecolor": "white", "edgecolor": "tab:red"},
    "NW-Bullshark-sig": {"hatch": "O", "facecolor": "white", "edgecolor": "tab:green"},

    ### Motivation plot
    "motivation-service": {"hatch": "", "facecolor": "white", "edgecolor": "black"},
}

LINE_FORMAT = {
    ### Comma
    "CC-BFT-SMaRt": {"marker": "|", "linestyle": "solid", "color": "tab:blue"},
    "CC-HotStuff": {"marker": "x", "linestyle": "dashed", "color": "tab:red"},
    "NW-Bullshark": {"marker": "^", "linestyle": "dashdot", "color": "tab:orange"}, # tab:purple
    "NW-Bullshark-sig": {"marker": "v", "linestyle": "dotted", "color": "tab:green"},
    "BFT-SMaRt": {"marker": "D", "linestyle": "solid", "color": "darkblue"},
    "HotStuff": {"marker": "s", "linestyle": "dashed", "color": "darkred"},

    ### Linerate
    "Input rate": {"marker": "", "linestyle": "dotted", "color": "black"},
    "Network rate": {"marker": "^", "linestyle": "dashed", "color": "tab:blue"},
    "Output rate": {"marker": "v", "linestyle": "dashdot", "color": "tab:red"},
}





##########
########## Chopchop utils
##########

def barplot(ax, data, dataErr):
    xTicksLabels = list(list(data.values())[0].keys())

    ### Bar locations and width
    xTicks = np.arange(len(xTicksLabels)) # label locations
    nbBars = len(data.keys())
    width = 1.0 / (nbBars + 1) # 2 sets: 0.33 width, 3 sets: 0.25, 4: 0.2, ...
    location = lambda i: xTicks + (i-nbBars/2+0.5)*width

    bars = {}
    for i, approach in enumerate(data.keys()):
        bars[approach] = ax.bar(location(i), data[approach].values(), width,
            yerr=dataErr[approach].values(), label=approach, fill=True, **BAR_FORMAT[approach])

    ### Ticks, limits
    ax.set_xticks(xTicks)
    ax.set_xticklabels(xTicksLabels)

    ### Grid y only
    ax.grid(which='both', axis='x', linestyle='')
    # ax.grid(which='both', axis='y', linestyle='--')
    ax.set_axisbelow(True)

    return ax


def plotCurve(ax, x, y, yerr, label, withShadedArea=True):
    ax.errorbar(x, y,
        label=label,
        # errorevery=markPeriod,
        # markevery=markPeriod,
        # rasterized=True,
        markerfacecolor="none",
        **LINE_FORMAT[label]
        )

    # Shaded areas for deviations
    # https://github.com/mwhittaker/frankenpaxos/blob/master/benchmarks/vldb20_matchmaker/leader_failure/plot.py
    if withShadedArea:
        ax.fill_between(x, y,
            y-yerr,
            # csv["lat 5th"],
            color=LINE_FORMAT[label]["color"], alpha=0.20)
        ax.fill_between(x, y,
            y+yerr,
            # csv["lat 95th"],
            color=LINE_FORMAT[label]["color"], alpha=0.20)


### Populate subplots
def plotCurvesInFiles(fileList, labelList, ax, xColumn, yColumn, yColumnError):
    for i, file in enumerate(fileList):
        csv = pd.read_csv(utils.DIR_STATS + "/" + file, index_col=0)
        # print(csv)
        x = csv[xColumn]
        y = csv[yColumn]
        yerr = csv[yColumnError]

        plotCurve(ax, x, y, yerr, labelList[i])


    ### Add values at the top of bars
    # valueList = []
    # for fault in ["0", "1", "threshold"]:
    #     valueList.append(data[labels[0]][fault])
    #     valueList.append(data[labels[1]][fault])
    # print(valueList)
    # for i in range(len(valueList)):
    #     plt.text(i, valueList[i], valueList[i], ha = 'center')


def decorateBarPlotLog(ax):
    ### Ticks
    ax.set_yscale("log")
    ax.set_ylim(10**5, 1.4*10**8)
    ax.yaxis.set_major_locator(ticker.LogLocator(base=10, numticks=4))
    ax.yaxis.set_minor_locator(ticker.LogLocator(base=10, numticks=10, subs=[x/10 for x in range(1,10)]))
    ax.set_yticks([10**v for v in [5, 6, 7, 8]])
    ax.set_yticklabels(["100k", "1M", "10M", "100M"])



##########
########## Chopchop figs
##########


def plotMotivation(fileCCHotstuff, fileCCBftsmart):
    fig, ax = plt.subplots(1, 1, **utils.FIG_SIZE_ONE_COL_MOTIV)
    utils.commonFigFormat(ax)
    ax.grid(which='both', axis='y', linestyle='') # Only show y grid

    ### One line for chopchop+bftsmart
    data = {}
    csv = pd.read_csv(utils.DIR_STATS + "/" + fileCCBftsmart, index_col=0)
    data["Chop Chop"] = csv["op avg"].max()

    keys = [k for k in data]
    values = [v for v in data.values()]
    ax.barh(keys, values, label='',
        align='center', height=0.8,
        **BAR_FORMAT["CC-BFT-SMaRt"])

    ### One line for chopchop+hotstuff
    # data = {}
    # csv = pd.read_csv(utils.DIR_STATS + "/" + fileCCHotstuff, index_col=0)
    # data["Chop Chop + HotStuff"] = csv["op avg"].max()

    # keys = [k for k in data]
    # values = [v for v in data.values()]
    # ax.barh(keys, values, label='',
    #     align='center', height=0.8,
    #     **BAR_FORMAT["CC-HotStuff"])

    ### Throughput / second
    data = {}
    data["WhatsApp messages"] = 1157000 # 100 billion / day
    data["Google searches"] = 108507
    data["Credit card payments"] = 18423 # 581*10**3 / day
    data["Youtube video watches"] = 11570 # 1 billion / day
    data["Tweets"] = 10311

    keys = [k for k in data]
    values = [v for v in data.values()]
    ax.barh(keys, values, label='',
        align='center', height=0.8,
        **BAR_FORMAT["motivation-service"])

    ax.set_xlabel("Throughput [event/s, log scale]")

    # ax.set_xscale("log")
    ax.set_xscale("symlog")
    ax.set_xlim(1)

    utils.saveFig("motivation-throughput-services")


    ### Value of a bar inside it
    # https://matplotlib.org/3.1.1/gallery/lines_bars_and_markers/horizontal_barchart_distribution.html#sphx-glr-gallery-lines-bars-and-markers-horizontal-barchart-distribution-py
    #     r, g, b, _ = color
    #     text_color = 'white' if r * g * b < 0.5 else 'darkgrey'
    #     for y, (x, c) in enumerate(zip(xcenters, widths)):
    #         ax.text(x, y, str(int(c)), ha='center', va='center',
    #                 color=text_color)
    # ax.legend(ncol=len(category_names), bbox_to_anchor=(0, 1),
    #           loc='lower left', fontsize='small')

    # To invert the x axis and have labels on the right side
    # ax.spines['left'].set_visible(False)
    # ax.spines['right'].set_visible(True)
    # ax.yaxis.set_label_position("right")
    # ax.yaxis.tick_right()
    # ax.set_xlim(135*1000, 0)


def _plotCommaSingle(labelList, fileList):
    fig, ax = plt.subplots(1, 1, **utils.FIG_SIZE_ONE_COL)
    utils.commonFigFormat(ax)

    ### Plot data points
    plotCurvesInFiles(fileList, labelList, ax, "op avg", "lat avg", "lat std")

    ### Labels
    ax.set_xlabel("Throughput [op/s]")
    ax.set_ylabel("Latency [s]")

    ### Throughput op/s -> M op/s
    # ax.set_xlim(0, 50)
    ax.xaxis.set_minor_locator(ticker.MultipleLocator(5 * 10**6))
    ax.xaxis.set_major_locator(ticker.MultipleLocator(10 * 10**6))
    ax.set_xticks([0*10**6, 10*10**6, 20*10**6, 30*10**6, 40*10**6, 50*10**6])
    ax.set_xticklabels(["0", "10M", "20M", "30M", "40M", "50M"])

    ### Latency ms -> s
    ax.set_ylim(0)
    ax.yaxis.set_major_locator(ticker.MultipleLocator(2*10**3))
    ax.yaxis.set_minor_locator(ticker.MultipleLocator(1*10**3))
    ax.yaxis.set_major_formatter(ticker.FuncFormatter(lambda x, pos: "%.0f" % (x/10**3)))
    
    ax.legend(**utils.FORMAT_LEGEND, ncol=3, columnspacing=1)

    utils.saveFig("comma-single")

    # ax.fill_between(before.index[::sample_every],
    #                 median_before[::sample_every],
    #                 p95_before[::sample_every],
    #                 color=line.get_color(), alpha=0.25)

    # ax.set_xscale('log')
    # ax.set_yscale('log')

    # # ax.xaxis.set_major_formatter(lambda x, pos: round(x/(1000)))
    # # ax.xaxis.set_major_locator(ticker.MultipleLocator(200*1000))
    # # ax.xaxis.set_major_formatter(ticker.FuncFormatter(lambda x, pos: "%.0fk" % (x/1000)))
    # # ax.xaxis.set_minor_formatter(ticker.FuncFormatter(lambda x, pos: "%.0fk" % (x/1000)))

    # ax.xaxis.set_minor_locator(ticker.LogLocator(base=10, numticks=10)) #, subs=[x/10 for x in range(1,10)]))
    # ax.xaxis.set_major_locator(ticker.LogLocator(base=10, numticks=10))


def plotCommaSplit(labelListA, labelListB, labelListC, labelListD, fileListA, fileListB, fileListC, fileListD):
    fig, ax = plt.subplots(1, 4, **utils.FIG_SIZE_TWO_COL, sharey=True, squeeze=True)
    nbRows, nbCols = len(ax), len(ax)

    utils.commonFigFormat(ax[0])
    utils.commonFigFormat(ax[1])
    utils.commonFigFormat(ax[2])
    utils.commonFigFormat(ax[3])

    ### Remove left border except on leftmost plot
    ax[1].spines['left'].set_visible(False)
    ax[2].spines['left'].set_visible(False)
    ax[3].spines['left'].set_visible(False)

    ### Add break clips on bottom axis
    # Source: http://matplotlib.org/examples/pylab_examples/broken_axis.html
    utils.addBreakClipsX(ax[0], ax[1])
    utils.addBreakClipsX(ax[1], ax[2])
    utils.addBreakClipsX(ax[2], ax[3])

    ### Plot data points
    plotCurvesInFiles(fileListA, labelListA, ax[0], "op avg", "lat avg", "lat std")
    plotCurvesInFiles(fileListB, labelListB, ax[1], "op avg", "lat avg", "lat std")
    plotCurvesInFiles(fileListC, labelListC, ax[2], "op avg", "lat avg", "lat std")
    plotCurvesInFiles(fileListD, labelListD, ax[3], "op avg", "lat avg", "lat std")

    ### Labels
    ax[0].set_xlabel("Throughput [op/s]")
    ax[1].set_xlabel("")
    ax[2].set_xlabel("")
    ax[3].set_xlabel("")
    ax[0].set_ylabel("Latency [s]")

    ### Throughput op/s
    ax[0].set_xlim(0.7*10**3, 1.7*10**3)
    ax[0].xaxis.set_minor_locator(ticker.MultipleLocator(2*10**2))
    ax[0].xaxis.set_major_locator(ticker.MultipleLocator(4*10**2))
    # ax[0].set_xticks([8*10**2, 12*10**2, 16*10**2])
    # ax[0].set_xticklabels(["1k", "2k", "3k", "4k"])

    ax[1].set_xlim(0.7*10**5, 4.2*10**5)
    ax[1].xaxis.set_minor_locator(ticker.MultipleLocator(5*10**4))
    ax[1].xaxis.set_major_locator(ticker.MultipleLocator(10*10**4))
    ax[1].set_xticks([1*10**5, 2*10**5, 3*10**5, 4*10**5])
    ax[1].set_xticklabels(["100k", "200k", "300k", "400k"])

    ax[2].set_xlim(0.8*10**6, 4.2*10**6)
    ax[2].xaxis.set_minor_locator(ticker.MultipleLocator(5*10**5))
    ax[2].xaxis.set_major_locator(ticker.MultipleLocator(10*10**5))
    ax[2].set_xticks([1*10**6, 2*10**6, 3*10**6, 4*10**6])
    ax[2].set_xticklabels(["1M", "2M", "3M", "4M"])

    ### Plot 3 show all points
    # ax[3].set_xlim(-2*10**6,50*10**6)
    # ax[3].xaxis.set_minor_locator(ticker.MultipleLocator(5*10**6))
    # ax[3].xaxis.set_major_locator(ticker.MultipleLocator(10*10**6))
    # ax[3].set_xticks([0*10**6, 10*10**6, 20*10**6, 30*10**6, 40*10**6, 50*10**6])
    # ax[3].set_xticklabels(["0", "10M", "20M", "30M", "40M", "50M"])

    ### Plot 3 show points starting at 10M
    ax[3].set_xlim(8*10**6,52*10**6)
    ax[3].xaxis.set_minor_locator(ticker.MultipleLocator(5*10**6))
    ax[3].xaxis.set_major_locator(ticker.MultipleLocator(10*10**6))
    ax[3].set_xticks([10*10**6, 20*10**6, 30*10**6, 40*10**6, 50*10**6])
    ax[3].set_xticklabels(["10M", "20M", "30M", "40M", "50M"])

    ### Latency ms -> s
    for a in ax:
        a.yaxis.set_major_formatter(ticker.FuncFormatter(lambda x, pos: "%.0f" % (x/10**3)))

    ### Separate yscales per subplot
    # ax[0].set_ylim(0, 13.2*10**3)
    # ax[0].yaxis.set_major_locator(ticker.MultipleLocator(3*10**3))
    # ax[1].set_ylim(0, 88*10**3)
    # ax[1].yaxis.set_major_locator(ticker.MultipleLocator(20*10**3))
    # ax[2].set_ylim(0, 44*10**3)
    # ax[2].yaxis.set_major_locator(ticker.MultipleLocator(10*10**3))
    # ax[3].set_ylim(0, 8.8*10**3)
    # ax[3].yaxis.set_major_locator(ticker.MultipleLocator(2*10**3))

    ### Same yscales across subplots + mirrors ticks
    ax[0].set_ylim(0, 11.1*10**3)
    ax[0].yaxis.set_major_locator(ticker.MultipleLocator(2*10**3))
    ax[1].yaxis.set_ticks_position('none')
    ax[2].yaxis.set_ticks_position('none')
    ax[3].yaxis.set_ticks_position('none')

    fig.legend(**utils.FORMAT_LEGEND, ncol=1, columnspacing=1, loc='center', bbox_to_anchor=(1.02, 0.33))
    utils.saveFig("comma-split")


def _plotMergeMostBars(
        payloadLabels, payloadFilesA, payloadFilesB, payloadFilesC, payloadFilesD,
        systemLabels, systemFilesA, systemFilesB, systemFilesC, systemFilesD,
        distillationLabelsA, distillationFilesNoFaults, distillationFilesFaults, distillationLabelsB, distillationFilesB,
        appLabels, appFilesA, appFilesB, appFilesC
        ):

    fig, ax = plt.subplots(1, 4, **utils.FIG_SIZE_TWO_COL, sharey=True, squeeze=True)
    nbRows, nbCols = len(ax), len(ax)

    utils.commonFigFormat(ax[0])
    utils.commonFigFormat(ax[1])
    utils.commonFigFormat(ax[2])
    utils.commonFigFormat(ax[3])

    ### Remove left border except on leftmost plot
    ax[1].spines['left'].set_visible(False)
    ax[2].spines['left'].set_visible(False)
    ax[3].spines['left'].set_visible(False)

    plotPayloadSizesAx(ax[0], payloadLabels, payloadFilesA, payloadFilesB, payloadFilesC, payloadFilesD)
    plotSystemSizesAx(ax[1], systemLabels, systemFilesA, systemFilesB, systemFilesC, systemFilesD)
    plotDistillationAx(ax[2], distillationLabelsA, distillationFilesNoFaults, distillationFilesFaults, distillationLabelsB, distillationFilesB)
    plotAppsAx(ax[3], appLabels, appFilesA, appFilesB, appFilesC)
    # plotServerFaultsAx(ax[1], labels, filesNoFaults, filesFaults)

    ### Labels
    ax[0].set_ylabel("Throughput\n[op/s, log]") #, loc="top")
    # ax[0].set_xlabel("Payload size")
    # ax[1].set_xlabel("System size")
    # ax[2].set_xlabel("Distillation ratio")
    # ax[3].set_xlabel("Application")

    ### Same yscales across subplots + mirrors ticks
    decorateBarPlotLog(ax[0])
    ax[1].yaxis.set_ticks_position('none')
    ax[2].yaxis.set_ticks_position('none')
    ax[3].yaxis.set_ticks_position('none')

    ### Smaller font size for some ticks
    # ax[0].tick_params(axis='x', which='major', labelsize=utils.FONT_SIZE_S)
    ax[3].tick_params(axis='x', which='major', labelsize=utils.FONT_SIZE_XS)

    ax[0].legend(**utils.FORMAT_LEGEND, ncol=1, columnspacing=1, loc='center', bbox_to_anchor=(5.3, 0.5))
    utils.saveFig("merged-bars")


def plotMergeDistillationAndPayloadSizes(
        distillationLabelsA, distillationFilesNoFaults, distillationFilesFaults, distillationLabelsB, distillationFilesB,
        payloadLabels, payloadFilesA, payloadFilesB, payloadFilesC, payloadFilesD,
        ):
    fig, ax = plt.subplots(1, 2, **utils.FIG_SIZE_ONE_COL_LINERATE, sharey=True, squeeze=True) # FIG_SIZE_ONE_COL_LINERATE
    nbRows, nbCols = len(ax), len(ax)

    utils.commonFigFormat(ax[0])
    utils.commonFigFormat(ax[1])

    ### Remove left border except on leftmost plot
    ax[1].spines['left'].set_visible(False)

    plotDistillationAx(ax[0], distillationLabelsA, distillationFilesNoFaults, distillationFilesFaults, distillationLabelsB, distillationFilesB)
    plotPayloadSizesAx(ax[1], payloadLabels, payloadFilesA, payloadFilesB, payloadFilesC, payloadFilesD)

    ### Labels
    ax[0].set_ylabel("Throughput\n[op/s, log]") #, loc="top")

    ### Same yscales across subplots + mirrors ticks
    decorateBarPlotLog(ax[0])
    ax[1].yaxis.set_ticks_position('none')

    ax[0].legend(**utils.FORMAT_LEGEND, ncol=3, columnspacing=1, loc='center', bbox_to_anchor=(0.87, 1.2))
    utils.saveFig("merged-distillation-payloed-sizes")


def plotMergeSystemSizesAndMatchingResources(
        systemLabels, systemFilesA, systemFilesB, systemFilesC, systemFilesD,
        matchingLabelsAB, matchingFilesA, matchingFilesB, matchingLabelCD, matchingFileC, matchingFileD
        ):
    fig, ax = plt.subplots(1, 2, **utils.FIG_SIZE_ONE_COL_LINERATE, sharey=True, squeeze=True) # FIG_SIZE_ONE_COL_LINERATE
    nbRows, nbCols = len(ax), len(ax)

    utils.commonFigFormat(ax[0])
    utils.commonFigFormat(ax[1])

    ### Remove left border except on leftmost plot
    ax[1].spines['left'].set_visible(False)

    plotSystemSizesAx(ax[0], systemLabels, systemFilesA, systemFilesB, systemFilesC, systemFilesD)
    plotMatchingTrustedResourcesAx(ax[1], matchingLabelsAB, matchingFilesA, matchingFilesB, matchingLabelCD, matchingFileC, matchingFileD)

    ### Labels
    ax[0].set_ylabel("Throughput\n[op/s, log]") #, loc="top")

    ### Same yscales across subplots + mirrors ticks
    decorateBarPlotLog(ax[0])
    ax[1].yaxis.set_ticks_position('none')

    ax[0].legend(**utils.FORMAT_LEGEND, ncol=3, columnspacing=1, loc='center', bbox_to_anchor=(0.87, 1.2))
    utils.saveFig("merged-system-sizes-matching-trusted-resources")


def plotMergeServerFaultsAndApps(
        faultsLabels, filesNoFaults, filesFaults,
        appLabels, appFilesA, appFilesB, appFilesC
        ):
    fig, ax = plt.subplots(1, 2, **utils.FIG_SIZE_ONE_COL_LINERATE, sharey=True, squeeze=True) # FIG_SIZE_ONE_COL_LINERATE
    nbRows, nbCols = len(ax), len(ax)

    utils.commonFigFormat(ax[0])
    utils.commonFigFormat(ax[1])

    ### Remove left border except on leftmost plot
    ax[1].spines['left'].set_visible(False)

    plotServerFaultsAx(ax[0], faultsLabels, filesNoFaults, filesFaults)
    plotAppsAx(ax[1], appLabels, appFilesA, appFilesB, appFilesC)

    ### Labels
    ax[0].set_ylabel("Throughput\n[op/s, log]") #, loc="top")

    ### Same yscales across subplots + mirrors ticks
    decorateBarPlotLog(ax[0])
    ax[1].yaxis.set_ticks_position('none')

    ### Smaller font size for the application ticks
    ax[1].tick_params(axis='x', which='major', labelsize=utils.FONT_SIZE_XS)

    ax[0].legend(**utils.FORMAT_LEGEND, ncol=3, columnspacing=1, loc='center', bbox_to_anchor=(0.87, 1.2))
    utils.saveFig("merged-servers-faults-applications")


def plotPayloadSizesAx(ax, labels, filesComma, filesPayloadA, filesPayloadB, filesPayloadC):
    ### Kind of manually reconstruct the data
    data = {}
    dataErr = {}
    for i, label in enumerate(labels):
        data[label] = {}
        dataErr[label] = {}

        ### Payload syze = 8 is comma data
        csv = pd.read_csv(utils.DIR_STATS + "/" + filesComma[i], index_col=0)
        p = "8"
        data[label][p] = csv["op avg"].max()
        if label.startswith("CC"):
            ### Can only show statistically significant std for chopchop, not bftsmart or bullshark
            dataErr[label][p] = csv.loc[csv["op avg"] == data[label][p]]["op std"].values[0]
        else:
            dataErr[label][p] = 0

        #### Other payload sizes are in their own files
        for p, files in [("32", filesPayloadA[i]),
                    ("128", filesPayloadB[i]),
                    ("512", filesPayloadC[i])]:
            csv = pd.read_csv(utils.DIR_STATS + "/" + files, index_col=0)
            data[label][p] = csv["op avg"].max()
            if label.startswith("CC"):
                ### Can only show statistically significant std for chopchop, not bftsmart or bullshark
                dataErr[label][p] = csv.loc[csv["op avg"] == data[label][p]]["op std"].values[0]
            else:
                dataErr[label][p] = 0

    # print(data)
    ax = barplot(ax, data, dataErr)


def _plotPayloadSizes(labels, filesComma, filesPayloadA, filesPayloadB, filesPayloadC):
    fig, ax = plt.subplots(1, 1, **utils.FIG_SIZE_ONE_COL_SMALL)
    utils.commonFigFormat(ax)

    plotPayloadSizesAx(ax, labels, filesComma, filesPayloadA, filesPayloadB, filesPayloadC)
    decorateBarPlotLog(ax)

    ax.set_xlabel("Message size [B]")
    ax.set_ylabel("Throughput [op/s]", loc="top")

    ax.legend(**utils.FORMAT_LEGEND, ncol=1, columnspacing=1, loc='center', bbox_to_anchor=(1.53, 0.5))
    utils.saveFig("payload-sizes")


def plotSystemSizesAx(ax, labels, filesSystemA, filesSystemB, filesSystemC, filesComma):
    ### Kind of manually reconstruct the data
    data = {}
    dataErr = {}
    for i, label in enumerate(labels):
        data[label] = {}
        dataErr[label] = {}

        #### Other system sizes are in their own files
        for p, files in [("8", filesSystemA[i]),
                    ("16", filesSystemB[i]),
                    ("32", filesSystemC[i])]:
            csv = pd.read_csv(utils.DIR_STATS + "/" + files, index_col=0)
            data[label][p] = csv["op avg"].max()
            if label.startswith("CC"):
                ### Can only show statistically significant std for chopchop, not bftsmart or bullshark
                dataErr[label][p] = csv.loc[csv["op avg"] == data[label][p]]["op std"].values[0]
            else:
                dataErr[label][p] = 0

        ### System size = 64 is comma data
        csv = pd.read_csv(utils.DIR_STATS + "/" + filesComma[i], index_col=0)
        p = "64"
        data[label][p] = csv["op avg"].max()
        if label.startswith("CC"):
            ## Can only show statistically significant std for chopchop, not bftsmart or bullshark
            dataErr[label][p] = csv.loc[csv["op avg"] == data[label][p]]["op std"].values[0]
        else:
            dataErr[label][p] = 0

    ax = barplot(ax, data, dataErr)


def _plotSystemSizes(labels, filesSystemA, filesSystemB, filesSystemC, filesComma):
    fig, ax = plt.subplots(1, 1, **utils.FIG_SIZE_ONE_COL_SMALL)
    utils.commonFigFormat(ax)

    plotSystemSizesAx(ax, labels, filesSystemA, filesSystemB, filesSystemC, filesComma)
    decorateBarPlotLog(ax)

    ax.set_xlabel("System size")
    ax.set_ylabel("Throughput [op/s]", loc="top")

    ax.legend(**utils.FORMAT_LEGEND, ncol=1, columnspacing=1, loc='center', bbox_to_anchor=(1.53, 0.5))
    utils.saveFig("system-sizes")


def plotDistillationAx(ax, labelsA, filesNoFaults, filesFaults, labelB, fileB):
    ### Kind of manually reconstruct the data
    data = {}
    dataErr = {}
    for i, label in enumerate(labelsA):
        data[label] = {}
        dataErr[label] = {}

        ### 0% distillation
        csv = pd.read_csv(utils.DIR_STATS + "/" + filesFaults[i], index_col=0)
        for p in ["0%"]:
            data[label][p] = csv["op avg"].values[0]
            dataErr[label][p] = csv["op std"].values[0]

        ### 100% distillation is comma data
        csv = pd.read_csv(utils.DIR_STATS + "/" + filesNoFaults[i], index_col=0)
        p = "100%"
        data[label][p] = csv["op avg"].max()
        dataErr[label][p] = csv.loc[csv["op avg"] == data[label][p]]["op std"].values[0]

    ### Bullshark
    label = labelB
    data[label] = {}
    dataErr[label] = {}
    csv = pd.read_csv(utils.DIR_STATS + "/" + fileB, index_col=0)

    for p in ["0%", "100%"]:
        data[label][p] = csv["op avg"].max()
        dataErr[label][p] = 0

    # print(data)
    ax = barplot(ax, data, dataErr)


def _plotDistillation(labelsA, filesNoFaults, filesFaults, distillationLabelsB, distillationFilesB):
    fig, ax = plt.subplots(1, 1, **utils.FIG_SIZE_ONE_COL_SMALL)
    utils.commonFigFormat(ax)

    plotDistillationAx(ax, labelsA, filesNoFaults, filesFaults, distillationLabelsB, distillationFilesB)
    decorateBarPlotLog(ax)

    ax.set_xlabel("Distillation ratio")
    ax.set_ylabel("Throughput [op/s]", loc="top")

    fig.legend(**utils.FORMAT_LEGEND, ncol=1, columnspacing=1, loc='center', bbox_to_anchor=(1.25, 0.5))
    utils.saveFig("distillation")


def plotAppsAx(ax, labels, filesAuction, filesPayments, filesPixelwar):
    ### Kind of manually reconstruct the data
    data = {}
    dataErr = {}
    for i, label in enumerate(labels):
        data[label] = {}
        dataErr[label] = {}

        for app, files in [("Auction", filesAuction[i]),
                    ("Payment", filesPayments[i]),
                    ("Pixel war", filesPixelwar[i])]:
            csv = pd.read_csv(utils.DIR_STATS + "/" + files, index_col=0)
            data[label][app] = csv["op avg"].max()
            dataErr[label][app] = csv.loc[csv["op avg"] == data[label][app]]["op std"].values[0]

    # print(data)
    ax = barplot(ax, data, dataErr)


def _plotApps(labels, filesAuction, filesPayments, filesPixelwar):
    fig, ax = plt.subplots(1, 1, **utils.FIG_SIZE_ONE_COL_SMALL)
    utils.commonFigFormat(ax)

    plotAppsAx(ax, labels, filesAuction, filesPayments, filesPixelwar)
    decorateBarPlotLog(ax)

    ### Labels
    ax.set_xlabel("Application")
    ax.set_ylabel("Throughput [op/s]", loc="top")

    ax.legend(**utils.FORMAT_LEGEND, ncol=1, columnspacing=1, loc='center', bbox_to_anchor=(1.5, 0.5))
    utils.saveFig("applications")


def plotServerFaultsAx(ax, labels, filesNoFaults, filesFaults):
    ### Kind of manually reconstruct the data
    data = {}
    dataErr = {}
    for i, label in enumerate(labels):
        data[label] = {}
        dataErr[label] = {}

        ### f = 0 is comma data
        csv = pd.read_csv(utils.DIR_STATS + "/" + filesNoFaults[i], index_col=0)
        p = "0"
        data[label][p] = csv["op avg"].max()
        dataErr[label][p] = csv.loc[ csv["op avg"] == data[label][p] ]["op std"].values[0]

        ### f = 1 and f = t
        csv = pd.read_csv(utils.DIR_STATS + "/" + filesFaults[i], index_col=0)
        for p in ["1", "threshold"]:
            data[label][p] = csv.loc[csv["nb-faults"] == p]["op avg"].values[0]
            dataErr[label][p] = csv.loc[csv["nb-faults"] == p]["op std"].values[0]

    # print(data)
    ax = barplot(ax, data, dataErr)


def _plotServerFaults(labels, filesNoFaults, filesFaults):
    fig, ax = plt.subplots(1, 1, **utils.FIG_SIZE_ONE_COL_SMALL)
    utils.commonFigFormat(ax)

    plotServerFaultsAx(ax, labels, filesNoFaults, filesFaults)
    # decorateBarPlot(ax)

    ### Labels
    ax.set_xlabel("Number of faults")
    # ax.set_ylabel("Throughput [Mop/s]", loc="top")
    ax.set_ylabel("Throughput\n[M op/s]", loc="center")

    ### Ticks
    ax.set_ylim(0*10**6, 55*10**6)
    # ax.yaxis.set_minor_locator(ticker.MultipleLocator(5*10**6))
    ax.yaxis.set_major_locator(ticker.MultipleLocator(10*10**6))
    ax.set_yticks([v*10**7 for v in [0, 1, 2, 3, 4, 5]])
    ax.set_yticklabels(range(0, 60, 10))

    ### Ticks log
    # ax.set_yscale("log")
    # ax.set_ylim(10**5, 1.4*10**8)
    # ax.yaxis.set_major_locator(ticker.LogLocator(base=10, numticks=4))
    # ax.yaxis.set_minor_locator(ticker.LogLocator(base=10, numticks=10, subs=[x/10 for x in range(1,10)]))
    # ax.set_yticks([10**v for v in [5, 6, 7, 8]])
    # ax.set_yticklabels(["100k", "1M", "10M", "100M"])

    ax.legend(**utils.FORMAT_LEGEND, ncol=1, columnspacing=1, loc='center', bbox_to_anchor=(1.47, 0.5))
    utils.saveFig("server-faults")


def plotMatchingTrustedResourcesAx(ax, labelsAB, filesA, filesB, labelCD, fileC, fileD):
    ### Kind of manually reconstruct the data
    data = {}
    dataErr = {}

    ### Chopchop
    for i, label in enumerate(labelsAB):
        data[label] = {}
        dataErr[label] = {}

        ### First cluster of bars is chopchop comma data
        p = "1"
        csv = pd.read_csv(utils.DIR_STATS + "/" + filesA[i], index_col=0)
        data[label][p] = csv["op avg"].max()
        dataErr[label][p] = csv.loc[ csv["op avg"] == data[label][p] ]["op std"].values[0]

        ### Second cluster of bars is chopchop with only honest brokers (no load brokers)
        p = "2"
        csv = pd.read_csv(utils.DIR_STATS + "/" + filesB[i], index_col=0)
        data[label][p] = csv["op avg"].max()
        dataErr[label][p] = csv.loc[ csv["op avg"] == data[label][p] ]["op std"].values[0]

        ### Fill third and fourth clusters with empty values for bullshark
        for p in [3, 4]:
            data[label][p] = 0
            dataErr[label][p] = 0

    ### Bullshark
    label = labelCD
    data[label] = {}
    dataErr[label] = {}

    ### Fill first and second clusters with empty values for bullshark
    for p in [1, 2]:
        data[label][p] = 0

    ### No error bars on bullshark
    for p in [1, 2, 3, 4]:
        dataErr[label][p] = 0

    ### Third cluster of bars is bullshark with 2x workers
    csv = pd.read_csv(utils.DIR_STATS + "/" + fileC, index_col=0)
    data[label]["3"] = csv["op avg"].max()

    ### Fourth cluster of bars is bullshark comma data
    csv = pd.read_csv(utils.DIR_STATS + "/" + fileD, index_col=0)
    data[label]["4"] = csv["op avg"].max()

    # print(data)
    ax = barplot(ax, data, dataErr)

    ### Ticks
    ax.set_xticklabels(["64 s\n$\\infty$ m", "64 s\n128 m", "64 s\n128 m", "64 s\n  64 m"])


def _plotMatchingTrustedResources(labelsAB, filesA, filesB, labelCD, fileC, fileD):
    fig, ax = plt.subplots(1, 1, **utils.FIG_SIZE_ONE_COL_SMALL)
    utils.commonFigFormat(ax)

    plotMatchingTrustedResourcesAx(ax, labelsAB, filesA, filesB, labelCD, fileC, fileD)
    decorateBarPlotLog(ax)

    ### Labels
    # ax.set_xlabel("")
    # ax.set_ylabel("Throughput [Mop/s]", loc="top")
    ax.set_ylabel("Throughput\n[op/s, log]", loc="center")

    ax.legend(**utils.FORMAT_LEGEND, ncol=1, columnspacing=1, loc='center', bbox_to_anchor=(1.55, 0.5))
    utils.saveFig("matching-trusted-resources")


def _plotLinerateRatio(labels, files):
    fig, ax = plt.subplots(1, 1, **utils.FIG_SIZE_ONE_COL)
    utils.commonFigFormat(ax)

    ### Optimal line
    label = "Optimal"
    # x = range(0, 70*10**6, 10**5) # (start, end, steps)
    # ax.errorbar(x, [1.0],
    #     label=label,
    #     markevery=100,
    #     # rasterized=True,
    #     markerfacecolor="none",
    #     **LINE_FORMAT[label]
    #     )
    ax.axhline(y=1.0,
        label=label,
        markevery=10,
        markerfacecolor="none",
        # zorder=-1,
        **LINE_FORMAT[label])


    ### Plot data points
    plotCurvesInFiles(files, labels, ax, "input", "goodput ratio avg", "goodput ratio std")

    ### Labels
    ax.set_xlabel("Input rate [Mop/s]")
    ax.set_ylabel("Goodput ratio", loc="top")

    ### Ticks
    ax.set_xlim(0*10**6, 72*10**6)
    # ax.xaxis.set_minor_locator(ticker.MultipleLocator(5*10**6))
    ax.xaxis.set_major_locator(ticker.MultipleLocator(10*10**6))
    ax.set_xticks([0, 10*10**6, 20*10**6, 30*10**6, 40*10**6, 50*10**6, 60*10**6, 70*10**6])
    ax.set_xticklabels(["0", "10", "20", "30", "40", "50", "60", "70"])

    ax.set_ylim(0, 1.05)
    # ax.yaxis.set_minor_locator(ticker.MultipleLocator(0.1))
    ax.yaxis.set_major_locator(ticker.MultipleLocator(0.2))
    # ax.set_yticks([0, 10*10**6, 20*10**6, 30*10**6, 40*10**6, 50*10**6, 60*10**6, 70*10**6])
    # ax.set_yticklabels(["0", "10", "20", "30", "40", "50", "60", "70"])

    fig.legend(**utils.FORMAT_LEGEND, ncol=1, columnspacing=1, loc='center', bbox_to_anchor=(0.35, 0.43))
    utils.saveFig("linerate-ratio")


def _plotLinerateThroughputV1(labels, files):
    fig, ax = plt.subplots(1, 1, **utils.FIG_SIZE_ONE_COL_SQUARE, squeeze=True)
    utils.commonFigFormat(ax)

    ### Optimal line
    label = "Optimal"
    x = range(0, 70*10**6, 10**5) # (start, end, steps)
    ax.errorbar(x, x,
        label=label,
        markevery=100,
        # rasterized=True,
        markerfacecolor="none",
        **LINE_FORMAT[label]
        )

    ### Plot data points
    plotCurvesInFiles(files, labels, ax, "input", "output avg", "output std")

    ### Labels
    ax.set_xlabel("Input rate [Mop/s]")
    ax.set_ylabel("Output rate [Mop/s]")

    ### Ticks
    ax.set_xlim(0*10**6, 72*10**6)
    # ax.xaxis.set_minor_locator(ticker.MultipleLocator(5*10**6))
    ax.xaxis.set_major_locator(ticker.MultipleLocator(10*10**6))
    ax.set_xticks([0, 10*10**6, 20*10**6, 30*10**6, 40*10**6, 50*10**6, 60*10**6, 70*10**6])
    ax.set_xticklabels(["0", "10", "20", "30", "40", "50", "60", "70"])

    ax.set_ylim(0*10**6, 72*10**6)
    # ax.xaxis.set_minor_locator(ticker.MultipleLocator(5*10**6))
    ax.yaxis.set_major_locator(ticker.MultipleLocator(10*10**6))
    ax.set_yticks([0, 10*10**6, 20*10**6, 30*10**6, 40*10**6, 50*10**6, 60*10**6, 70*10**6])
    ax.set_yticklabels(["0", "10", "20", "30", "40", "50", "60", "70"])

    fig.legend(**utils.FORMAT_LEGEND, ncol=1, columnspacing=1, loc='center', bbox_to_anchor=(0.35, 0.75))
    utils.saveFig("linerate-throughput-v1")


def _plotLinerateThroughputV2(labels, files):
    fig, ax = plt.subplots(1, 1, **utils.FIG_SIZE_ONE_COL_SQUARE)
    utils.commonFigFormat(ax)

    ### Plot data points
    # plotCurve(files, labels, ax, "input", "output avg", "output std")
    plotCurvesInFiles(files, labels, ax, "input", "goodput bandwidth avg", "goodput bandwidth std")

    ### Optimal line
    label = "Optimal"
    minPayloadSize = 11.5 # 8 B of payload + 3.5 B of id
    x = range(0, 60*10**6, 10**5) # (start, end, steps)
    y = range(0, int(minPayloadSize*60*10**6), int(minPayloadSize*10**5)) # (start, end, steps)
    ax.errorbar(x, y,
        label=label,
        markevery=100,
        # rasterized=True,
        markerfacecolor="none",
        **LINE_FORMAT[label]
        )

    # ax.fill_between(x, y,
    #     y+yerr,
    #     color=LINE_FORMAT[labelList[i]]["color"], alpha=0.20)

    ### Labels
    ax.set_xlabel("Input rate [Mop/s]")
    ax.set_ylabel("Output bandwidth [MB/s]")

    ### Ticks
    ax.set_xlim(0*10**6, 62*10**6)
    # ax.xaxis.set_minor_locator(ticker.MultipleLocator(5*10**6))
    ax.xaxis.set_major_locator(ticker.MultipleLocator(10*10**6))
    ax.set_xticks([v*10**7 for v in [0, 1, 2, 3, 4, 5, 6]])
    # ax.set_xticklabels(["0", "10", "20", "30", "40", "50", "60", "70"])
    ax.set_xticklabels(range(0, 61, 10))

    ax.set_ylim(0*10**6, 72*10**7)
    # # ax.xaxis.set_minor_locator(ticker.MultipleLocator(5*10**6))
    # ax.yaxis.set_major_locator(ticker.MultipleLocator(10*10**6))
    ax.set_yticks([v*10**8 for v in [0, 1, 2, 3, 4, 5, 6, 7]])
    ax.set_yticklabels(["0", "100", "200", "300", "400", "500", "600", "700"])

    fig.legend(**utils.FORMAT_LEGEND, ncol=1, columnspacing=1, loc='center', bbox_to_anchor=(0.35, 0.75))
    utils.saveFig("linerate-throughput-v2")


def plotLinerateThroughput(labelA, labelB, fileA, fileB):
    fig, ax = plt.subplots(1, 2, **utils.FIG_SIZE_ONE_COL_LINERATE) #, squeeze=True)
    nbRows, nbCols = len(ax), len(ax)
    utils.commonFigFormat(ax[0])
    utils.commonFigFormat(ax[1])

    ### Input rate baseline
    label = "Input rate"
    minPayloadSize = 11.5 # 8 B of payload + 3.5 B of id
    x = range(0, 80*10**4, 10**3)
    y = range(0, int(minPayloadSize*80*10**4), int(minPayloadSize*10**3))
    ax[0].errorbar(x, y,
        label=label,
        markevery=100,
        # rasterized=True,
        markerfacecolor="none",
        **LINE_FORMAT[label]
        )
    x = range(0, 60*10**6, 10**5)
    y = range(0, int(minPayloadSize*60*10**6), int(minPayloadSize*10**5))
    ax[1].errorbar(x, y,
        label=label,
        markevery=100,
        # rasterized=True,
        markerfacecolor="none",
        **LINE_FORMAT[label]
        )

    ### Left plot bullshark
    plotConfig = [
        ("Network rate", "workload", "output rate B avg"),
        ("Output rate", "workload", "goodput rate B avg"),
        ]
    csv = pd.read_csv(utils.DIR_STATS + "/" + fileA, index_col=0)
    for label, xColumn, yColumn in plotConfig:
        # print(csv)
        x = csv[xColumn]
        y = csv[yColumn]
        yerr = []

        plotCurve(ax[0], x, y, yerr, label, withShadedArea=False)

        ### Shaded gray area for the linerate lost bandwidth
        x = csv[xColumn]
        y1 = csv["output rate B avg"]
        y2 = csv["goodput rate B avg"]
        ax[0].fill_between(x, y1, y2, color="black", alpha=0.15)

    ### Right plot chopchop
    plotConfig = [
        ("Network rate", "input", "output rate B avg", "output rate B std"),
        ("Output rate", "input", "goodput rate B avg", "goodput rate B std"),
        ]
    csv = pd.read_csv(utils.DIR_STATS + "/" + fileB, index_col=0)
    for label, xColumn, yColumn, yErrColumn in plotConfig:
        x = csv[xColumn]
        y = csv[yColumn]
        yerr = csv[yErrColumn]

        plotCurve(ax[1], x, y, yerr, label, withShadedArea=True)

        ### Shaded gray area for the linerate lost bandwidth
        x = csv[xColumn]
        y1 = csv["output rate B avg"]
        y2 = csv["goodput rate B avg"]
        ax[1].fill_between(x, y1, y2, color="black", alpha=0.15)


    ### Labels
    ax[0].set_title(labelA) #, color=LINE_FORMAT[labelA]["color"])
    ax[1].set_title(labelB) #, color=LINE_FORMAT[labelB]["color"])
    ax[0].set_xlabel("Input rate [op/s]")
    ax[0].set_ylabel("Output rate [MB/s]") #, loc="top")

    ### Ticks left plot
    ax[0].set_xlim(0, 82*10**4)
    ax[0].xaxis.set_major_locator(ticker.MultipleLocator(20*10**4))
    ax[0].xaxis.set_minor_locator(ticker.MultipleLocator(10*10**4))
    ax[0].set_xticks([v*10**4 for v in [0, 20, 40, 60, 80]])
    ax[0].set_xticklabels(["0", "200k", "400k", "600k", "800k"])

    ## Linear yscale
    # ax[0].set_ylim(0, 8.2*10**6)
    # ax[0].yaxis.set_major_locator(ticker.MultipleLocator(20*10**6))
    # ax[0].yaxis.set_minor_locator(ticker.MultipleLocator(10*10**6))
    # ax[0].set_yticks([v*10**6 for v in [0, 20, 40, 60, 80]])
    # ax[0].set_yticklabels(["0", "20", "40", "60", "80"])

    ## Log yscale
    ax[0].set_yscale("log")
    ax[0].set_ylim(10**5, 1.2*10**8)
    ax[0].yaxis.set_major_locator(ticker.LogLocator(base=10, numticks=10))
    ax[0].yaxis.set_minor_locator(ticker.LogLocator(base=10, numticks=10, subs=[x/10 for x in range(1,10)]))
    ax[0].set_yticks([v*10**5 for v in [10**0, 10**1, 10**2, 10**3]])
    ax[0].set_yticklabels(["0.1", "1", "10", "100"])

    ### Ticks left plot
    ax[1].set_xlim(0*10**6, 62*10**6)
    ax[1].xaxis.set_major_locator(ticker.MultipleLocator(20*10**6))
    ax[1].xaxis.set_minor_locator(ticker.MultipleLocator(10*10**6))
    ax[1].set_xticks([v*10**6 for v in [0, 20, 40, 60]])
    ax[1].set_xticklabels(["0", "20M", "40M", "60M"])

    ## Linear scale
    ax[1].set_ylim(0, 820*10**6)
    ax[1].yaxis.set_major_locator(ticker.MultipleLocator(2*10**8))
    ax[1].yaxis.set_minor_locator(ticker.MultipleLocator(1*10**8))
    ax[1].set_yticks([v*10**8 for v in [0, 2, 4, 6, 8]])
    ax[1].set_yticklabels(["0", "200", "400", "600", "800"])

    ## Log scale
    # ax[0].set_yscale("log") # nope

    ax[1].legend(**utils.FORMAT_LEGEND, ncol=3, loc='center', bbox_to_anchor=(-0.2, 1.35),
        columnspacing=1)
        #borderaxespad=0.3, handletextpad=1.5, handletextpad=0.5, columnspacing=1
    utils.saveFig("linerate-throughput-log")

    



#####
##### Main
#####

### Transform clean data into plots
if __name__ == "__main__":
    utils.init()
 
    ### Motivation plot showing the throughput of internet services (manual data) + chopchop
    plotMotivation("comma-chopchop-bftsmart.csv", "comma-chopchop-hotstuff.csv")

    ### Comma plot single subplot
    # commaLabels = ["CC-BFT-SMaRt", "CC-HotStuff"]
    # commaFiles = ["comma-chopchop-bftsmart.csv", "comma-chopchop-hotstuff.csv"]
    # commaLabels = ["CC-BFT-SMaRt", "CC-HotStuff", "NW-Bullshark", "NW-Bullshark-sig"]
    # commaFiles = ["comma-chopchop-bftsmart.csv", "comma-chopchop-hotstuff.csv", "comma-bullshark.csv", "comma-bullshark-sig.csv"]
    # _plotCommaSingle(commaLabels, commaFiles)

    ### Comma plot split in several subplots
    commaLabelsA = ["HotStuff", "BFT-SMaRt"]
    commaLabelsB = ["NW-Bullshark-sig"]
    commaLabelsC = ["NW-Bullshark"]
    commaLabelsD = ["CC-HotStuff", "CC-BFT-SMaRt"]
    commaFilesA = ["comma-hotstuff.csv", "comma-bftsmart.csv"]
    commaFilesB = ["comma-bullshark-sig.csv"]
    commaFilesC = ["comma-bullshark.csv"]
    commaFilesD = ["comma-chopchop-hotstuff.csv", "comma-chopchop-bftsmart.csv"]
    plotCommaSplit(commaLabelsA, commaLabelsB, commaLabelsC, commaLabelsD, commaFilesA, commaFilesB, commaFilesC, commaFilesD)

    ### Payload sizes
    payloadLabels = ["CC-HotStuff", "CC-BFT-SMaRt", "NW-Bullshark-sig"]
    payloadFilesA = ["comma-chopchop-hotstuff.csv", "comma-chopchop-bftsmart.csv", "comma-bullshark-sig.csv"] # payload size = 8
    payloadFilesB = ["payload-032-{}.csv".format(s) for s in ["chopchop-hotstuff", "chopchop-bftsmart", "bullshark-sig"]]
    payloadFilesC = ["payload-128-{}.csv".format(s) for s in ["chopchop-hotstuff", "chopchop-bftsmart", "bullshark-sig"]]
    payloadFilesD = ["payload-512-{}.csv".format(s) for s in ["chopchop-hotstuff", "chopchop-bftsmart", "bullshark-sig"]]
    # _plotPayloadSizes(payloadLabels, payloadFilesA, payloadFilesB, payloadFilesC, payloadFilesD)

    ### System sizes
    systemLabels = ["CC-HotStuff", "CC-BFT-SMaRt", "NW-Bullshark-sig"]
    systemFilesA = ["system-08-{}.csv".format(s) for s in ["chopchop-hotstuff", "chopchop-bftsmart", "bullshark-sig"]]
    systemFilesB = ["system-16-{}.csv".format(s) for s in ["chopchop-hotstuff", "chopchop-bftsmart", "bullshark-sig"]]
    systemFilesC = ["system-32-{}.csv".format(s) for s in ["chopchop-hotstuff", "chopchop-bftsmart", "bullshark-sig"]]
    systemFilesD = ["comma-chopchop-hotstuff.csv", "comma-chopchop-bftsmart.csv", "comma-bullshark-sig.csv"] # system size = 64
    # _plotSystemSizes(systemLabels, systemFilesA, systemFilesB, systemFilesC, systemFilesD)

    ### Distillation = when client crash
    distillationLabelsA = ["CC-HotStuff", "CC-BFT-SMaRt"]
    distillationFilesNoFaults = ["comma-chopchop-hotstuff.csv", "comma-chopchop-bftsmart.csv"] # 100% reduction
    distillationFilesFaults = ["reduction-00-chopchop-hotstuff.csv", "reduction-00-chopchop-bftsmart.csv"]
    distillationLabelsB = "NW-Bullshark-sig" # bullshark for comparison
    distillationFilesB = "comma-bullshark-sig.csv"
    # _plotDistillation(distillationLabels, distillationFilesNoFaults, distillationFilesFaults)

    ### Applications
    appLabels = ["CC-HotStuff", "CC-BFT-SMaRt"]
    appFilesA = ["app-auction-chopchop-hotstuff.csv", "app-auction-chopchop-bftsmart.csv"]
    appFilesB = ["app-payment-chopchop-hotstuff.csv", "app-payment-chopchop-bftsmart.csv"]
    appFilesC = ["app-pixelwar-chopchop-hotstuff.csv", "app-pixelwar-chopchop-bftsmart.csv"]
    # _plotApps(appLabels, appFilesA, appFilesB, appFilesC)

    ### OSDI submission: merge most bar plots into one long line like the comma plot
    # _plotMergeMostBars(
    #     payloadLabels, payloadFilesA, payloadFilesB, payloadFilesC, payloadFilesD,
    #     systemLabels, systemFilesA, systemFilesB, systemFilesC, systemFilesD,
    #     distillationLabelsA, distillationFilesNoFaults, distillationFilesFaults, distillationLabelsB, distillationFilesB,
    #     appLabels, appFilesA, appFilesB, appFilesC
    #     )

    ### Server crashes with f = {0, 1, t}
    faultsLabels = ["CC-HotStuff", "CC-BFT-SMaRt"]
    filesNoFaults = ["comma-chopchop-hotstuff.csv", "comma-chopchop-bftsmart.csv"] # f=0
    filesFaults = ["faults-chopchop-hotstuff.csv", "faults-chopchop-bftsmart.csv"]
    # _plotServerFaults(faultsLabels, filesNoFaults, filesFaults)

    ### Matching trusted resources
    matchingLabelsAB = ["CC-HotStuff", "CC-BFT-SMaRt"]
    matchingFilesA = ["comma-chopchop-hotstuff.csv", "comma-chopchop-bftsmart.csv"]
    matchingFilesB = ["matching-trusted-192-chopchop-hotstuff.csv", "matching-trusted-192-chopchop-bftsmart.csv"]
    matchingLabelCD = "NW-Bullshark-sig"
    matchingFileC = "matching-trusted-192-bullshark-sig.csv"
    matchingFileD = "comma-bullshark-sig.csv"
    # _plotMatchingTrustedResources(matchingLabelsAB, matchingFilesA, matchingFilesB, matchingLabelCD, matchingFileC, matchingFileD)

    ### Linerate
    linerateLabelA = "NW-Bullshark-sig"
    linerateLabelB = "CC-BFT-SMaRt"
    linerateFileA = "linerate-bullshark-sig.csv"
    linerateFileB = "linerate-chopchop-bftsmart.csv"
    # fileB = ["linerate-chopchop-hotstuff.csv"]
    # _plotLinerateRatio(linerateLabels, linerateFiles)
    # _plotLinerateThroughputV1(linerateLabels, linerateFiles)
    # _plotLinerateThroughputV2(linerateLabels, linerateFiles)
    plotLinerateThroughput(linerateLabelA, linerateLabelB, linerateFileA, linerateFileB)

    ### OSDI revision: pair distillation ratio + payload size
    plotMergeDistillationAndPayloadSizes(
        distillationLabelsA, distillationFilesNoFaults, distillationFilesFaults, distillationLabelsB, distillationFilesB,
        payloadLabels, payloadFilesA, payloadFilesB, payloadFilesC, payloadFilesD
        )

    ### OSDI revision: pair system sizes + matching resources
    plotMergeSystemSizesAndMatchingResources(
        systemLabels, systemFilesA, systemFilesB, systemFilesC, systemFilesD,
        matchingLabelsAB, matchingFilesA, matchingFilesB, matchingLabelCD, matchingFileC, matchingFileD,
        )

    ### OSDI revision: pair server faults + applications
    plotMergeServerFaultsAndApps(
        faultsLabels, filesNoFaults, filesFaults,
        appLabels, appFilesA, appFilesB, appFilesC
        )
