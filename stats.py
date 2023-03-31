#!/usr/bin/env python3
### Transform data distribution into statistics data

import json
import io
import math
import matplotlib.cbook as cbook
import matplotlib.colors as col
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import numpy as np
import os
# from os import path
import pandas as pd
import re
import string
import sys

### local import
import utils





##########
########## Parsing utils
##########

OPERATIONS_SORTED_LIST = [
    ("avg",  lambda x: sum([v for v in x]) / len(x) if len(x) > 0 else np.nan),
    ("std",  lambda x: np.std(x)                    if len(x) > 0 else np.nan),
    ("min",  lambda x: x[0]                         if len(x) > 0 else np.nan),
    ("1th",  lambda x: quantile(x, 0.01)            if len(x) > 0 else np.nan),
    ("5th",  lambda x: quantile(x, 0.05)            if len(x) > 0 else np.nan),
    ("10th", lambda x: quantile(x, 0.10)            if len(x) > 0 else np.nan),
    ("25th", lambda x: quantile(x, 0.25)            if len(x) > 0 else np.nan),
    ("50th", lambda x: quantile(x, 0.50)            if len(x) > 0 else np.nan),
    ("75th", lambda x: quantile(x, 0.75)            if len(x) > 0 else np.nan),
    ("90th", lambda x: quantile(x, 0.90)            if len(x) > 0 else np.nan),
    ("95th", lambda x: quantile(x, 0.95)            if len(x) > 0 else np.nan),
    ("99th", lambda x: quantile(x, 0.99)            if len(x) > 0 else np.nan),
    ("max",  lambda x: x[len(x) - 1]                if len(x) > 0 else np.nan),
    ]


# quantile function with ordered list (much faster than np.quantile)
# From https://stackoverflow.com/questions/2374640/how-do-i-calculate-percentiles-with-python-numpy
def quantile(N, percent, key=lambda x:x):
    """
    Find the quantile of a list of values.

    @parameter N - is a list of values. Note N MUST BE already sorted.
    @parameter percent - a float value from 0.0 to 1.0.
    @parameter key - optional key function to compute value from each element of N.

    @return - the quantile of the values
    """
    if not N:
        return None
    k = (len(N)-1) * percent
    f = math.floor(k)
    c = math.ceil(k)
    if f == c:
        return key(N[int(k)])
    d0 = key(N[int(f)]) * (c-k)
    d1 = key(N[int(c)]) * (k-f)
    return d0+d1

### Add a column to a dataframe per stat function for a given distribution
def addStatsColumns(df, columnPrefix, distribution):
    sortedDistribution = sorted(distribution)
    for label, function in OPERATIONS_SORTED_LIST:
        column = "{} {}".format(columnPrefix, label)
        df[column] = function(sortedDistribution)





##########
########## Parsing
##########

def parseChopchopGeneric(csvPrefix, throughputFile, latencyFile):
    """
    The two input files should have the same systems and workloads.
    Generates a csv with header ",system,workload,[op stats],[lat stats]".
    One row per workload. One csv file per system.
    """

    ### Read input files
    throughput = None
    latency = None
    with open(throughputFile) as f:
        throughput = json.load(f)
    with open(latencyFile) as f:
        latency = json.load(f)

    ### One dataframe per system/baseline
    for system in throughput:
        dfOut = pd.DataFrame()
        for workloadIndex, workload in enumerate(throughput[system]):
            ### Make a row per workload and fill it with many stats
            dfRow = pd.DataFrame(index=[workloadIndex])
            dfRow["system"] = "cc-{}".format(system)
            dfRow["workload"] = float(workload) * 10**6 # Uniformize units: Mop/s -> op/s

            ### Uniformize units: M op/s -> op/s
            throughputs = [round(v * 10**6) for v in throughput[system][workload]]

            ### Add a column per stat function for each distribution
            addStatsColumns(dfRow, "op", throughputs)
            addStatsColumns(dfRow, "lat", latency[system][workload])

            dfOut = pd.concat([dfOut, dfRow])

        # print(dfOut["lat avg"])
        fileOut = utils.DIR_STATS + "/{}-chopchop-{}.csv".format(csvPrefix, system)
        dfOut.to_csv(fileOut)
        print("Generated {}".format(fileOut))


def parseBaselinesGeneric(csvPrefix, parameterKey, system, dataDir, latencyFactor=10**3, withByteRate=False):
    """
    The input dataDir contains one directory per workload/payload, each of which contains
    one json file per run. Generates a csv with header
    ",system,workload|payload,[op stats],[lat stats]". One row per workload|payload.
    """

    ### Find dirs that have the right prefix
    # dataDirPath = os.path.join(os.path.dirname(sys.argv[0]), dataDir)
    dataDirPath = os.path.abspath(dataDir)
    dirs = []
    with os.scandir(dataDirPath) as it:
        for entry in it:
            if entry.name.startswith(parameterKey) and entry.is_dir():
                dirs.append(entry.path)
    dirs = sorted(dirs)

    ### Parse the dirs to load all jsons
    allData = {}
    for dirPath in dirs:
        dirName = os.path.basename(dirPath)
        parameter = re.sub("{}-".format(parameterKey), "", dirName)
        parameter = int(parameter)

        ### Fill data structure with each run's json
        allData[parameter] = []
        with os.scandir(dirPath) as it:
            # print(dirPath)
            for entry in it:
                if entry.name.endswith('.json') and entry.is_file():
                    # print("{}/{}".format(dirPath,entry.name))
                    with open(entry.path) as f:
                        allData[parameter].append(json.load(f))

    ### Fill dataframe used for csv output
    dfOut = pd.DataFrame()
    for parameterIndex, parameter in enumerate(allData):
        # Make a row per parameter value and fill it with many stats
        dfRow = pd.DataFrame(index=[parameterIndex])
        dfRow["system"] = system
        dfRow[parameterKey] = parameter

        ### Add the average throughput column, the only one available :(
        throughputs = []
        for run in allData[parameter]:
            throughputs.append(run["throughput-avg"])
        dfRow["op avg"] = np.mean(throughputs)

        ### Aggregate all latency values and add a column per stat function
        latencies = []
        for run in allData[parameter]:
            for singleValue in run["latency"]:
                # Uniformize units: seconds -> milliseconds
                latencies.append(singleValue * latencyFactor)
        addStatsColumns(dfRow, "lat", latencies)

        ### Only linerate files contain server byte rates
        if withByteRate:
            outputRateOp = []
            outputRateBytes = []
            goodputRatios = []
            goodputRateOp = []
            goodputRateBytes = []
            for run in allData[parameter]:
                ### Don't use whole distribution in the end since goodputRateOp is only avg
                # byterates.append(run["server-byterate"])

                ### Warning dark magic. Easier to understand in parseLinerateChopchop
                go = run["throughput-avg"]
                ### Ideal payload size = 11.5; actual payload size = 88
                gb = go * 11.5
                ob = run["server-byterate-avg"]
                gr = gb / ob
                oo = go / gr
                # print(ob)

                outputRateOp.append(oo)
                outputRateBytes.append(ob)
                goodputRatios.append(gr)
                goodputRateOp.append(go)
                goodputRateBytes.append(gb)

            dfRow["output rate op avg"]  = np.mean(outputRateOp)
            dfRow["output rate B avg"]   = np.mean(outputRateBytes)
            dfRow["goodput ratio avg"]   = np.mean(goodputRatios)
            dfRow["goodput rate op avg"] = np.mean(goodputRateOp) # = dfRow["op avg"]
            dfRow["goodput rate B avg"]  = np.mean(goodputRateBytes)

        dfOut = pd.concat([dfOut, dfRow])

    fileOut = utils.DIR_STATS + "/{}-{}.csv".format(csvPrefix, system)
    dfOut.to_csv(fileOut)
    print("Generated {}".format(fileOut))


def parseServerFaults(throughputFile, latencyFile):
    ### Read input files
    throughput = None
    latency = None
    with open(throughputFile) as f:
        throughput = json.load(f)
    with open(latencyFile) as f:
        latency = json.load(f)

    ### Prepare to add number of faults in output
    faultLabels = ["threshold", "1"]

    ### One dataframe per system/baseline
    for system in throughput:
        dfOut = pd.DataFrame()
        for workloadIndex, workload in enumerate(throughput[system]):
            # Make a row per workload and fill it with many stats
            dfRow = pd.DataFrame(index=[workloadIndex])
            dfRow["system"] = "cc-{}".format(system)
            dfRow["nb-faults"] = faultLabels[workloadIndex]
            dfRow["workload"] = float(workload) * 10**6 # Uniformize units: MB -> B

            ### Uniformize units: M op/s -> op/s
            throughputs = [round(v * 10**6) for v in throughput[system][workload]]

            ### Add a column per stat function for each distribution
            addStatsColumns(dfRow, "op", throughputs)
            addStatsColumns(dfRow, "lat", latency[system][workload])

            dfOut = pd.concat([dfOut, dfRow])

        # print(dfOut)
        fileOut = utils.DIR_STATS + "/faults-chopchop-{}.csv".format(system)
        dfOut.to_csv(fileOut)
        print("Generated {}".format(fileOut))


def parseLinerateChopchop(file):
    ### Read input file
    data = None
    with open(file) as f:
        data = json.load(f)

    ### One dataframe per system/baseline
    for system in data:
        dfOut = pd.DataFrame()
        for inputThroughputIndex, inputThroughput in enumerate(data[system]):
            ### Make a row per workload and fill it with many stats
            dfRow = pd.DataFrame(index=[inputThroughputIndex])
            dfRow["system"] = "cc-{}".format(system)
            dfRow["input"] = float(inputThroughput) * 10**6 # Uniformize units: Mop/s -> op/s

            ### Collect and sort distributions, recompute other metrics for plots
            outputRateOp = []
            outputRateBytes = []
            goodputRatios = []
            goodputRateOp = []
            goodputRateBytes = []
            for entry in data[system][inputThroughput]:
                ### The column "output_throughput" actually contains the goodput (names can be confusing here)
                go = float(entry["output_throughput"]) * 10**6 # Uniformize units: Mop/s -> op/s
                gb = 11.5 * go         # 11.5 = 8 bytes of payload + 3.5 bytes of id
                gr = entry["goodput"]  # Goodput ratio
                oo = go / gr           # Recompute the goodput in op/s from the ratio
                ob = 11.5 * oo
                outputRateOp.append(oo)
                outputRateBytes.append(ob)
                goodputRatios.append(gr)
                goodputRateOp.append(go)
                goodputRateBytes.append(gb)

            ### Add a column per stat function for each distribution
            addStatsColumns(dfRow, "output rate op", outputRateOp)
            addStatsColumns(dfRow, "output rate B", outputRateBytes)
            addStatsColumns(dfRow, "goodput ratio", goodputRatios)
            addStatsColumns(dfRow, "goodput rate op", goodputRateOp)
            addStatsColumns(dfRow, "goodput rate B", goodputRateBytes)

            dfOut = pd.concat([dfOut, dfRow])
        # print(system)
        # print(dfOut["op avg"])
        print(dfOut["goodput ratio avg"])
        # print(dfOut)
        fileOut = utils.DIR_STATS + "/linerate-chopchop-{}.csv".format(system)
        dfOut.to_csv(fileOut)
        print("Generated {}".format(fileOut))



#####
##### Main
#####

if __name__ == "__main__":
    ### Comma plot
    parseChopchopGeneric("comma", utils.DIR_DATA + "/comma-chopchop-throughput.json", utils.DIR_DATA + "/comma-chopchop-latency.json")
    parseBaselinesGeneric("comma", "workload", "bullshark", utils.DIR_DATA + "/comma-64-bullshark")
    parseBaselinesGeneric("comma", "workload", "bullshark-sig", utils.DIR_DATA + "/comma-64-bullshark-sig")
    parseBaselinesGeneric("comma", "workload", "bftsmart", utils.DIR_DATA + "/comma-64-bftsmart", latencyFactor=1) # bftsmart is already in millisec, no need to multiply
    parseBaselinesGeneric("comma", "workload", "hotstuff", utils.DIR_DATA + "/comma-64-hotstuff")

    ### Server faults plot
    parseServerFaults("raw-data/faults-throughput.json", "raw-data/faults-latency.json")

    ### Applications plot
    for app in ["auction", "payment", "pixelwar"]:
        parseChopchopGeneric("app-{}".format(app), utils.DIR_DATA + "/app-{}-throughput.json".format(app), utils.DIR_DATA + "/app-{}-latency.json".format(app))

    ### Payload sizes plot
    for size in ["032", "128", "512"]:
        parseChopchopGeneric("payload-{}".format(size), utils.DIR_DATA + "/payload-{}-throughput.json".format(size), utils.DIR_DATA + "/payload-{}-latency.json".format(size))
        parseBaselinesGeneric("payload-{}".format(size), "payload", "bullshark-sig", utils.DIR_DATA + "/payload-sizes-bullshark-sig-{}".format(size))

    ### System sizes plot
    for size in ["08", "16", "32"]:
        parseChopchopGeneric("system-{}".format(size), utils.DIR_DATA + "/system-{}-throughput.json".format(size), utils.DIR_DATA + "/system-{}-latency.json".format(size))
        parseBaselinesGeneric("system-{}".format(size), "system", "bullshark-sig", utils.DIR_DATA + "/system-sizes-bullshark-sig-{}".format(size))

    ### Reduction plot when clients crash
    parseChopchopGeneric("reduction-00", utils.DIR_DATA + "/reduction-0-throughput.json", utils.DIR_DATA + "/reduction-0-latency.json")

    ### Linerate plot
    parseLinerateChopchop("raw-data/linerate-chopchop.json")
    parseBaselinesGeneric("linerate", "workload", "bullshark-sig", utils.DIR_DATA + "/linerate-64-bullshark-sig", withByteRate=True)

    ### Matching trusted and untrusted CPU for bullshark
    parseChopchopGeneric("matching-trusted-192", utils.DIR_DATA + "/matching-trusted-throughput.json", utils.DIR_DATA + "/matching-trusted-latency.json")
    parseBaselinesGeneric("matching-trusted-192", "system", "bullshark-sig", utils.DIR_DATA + "/matching-trusted-bullshark-sig")
