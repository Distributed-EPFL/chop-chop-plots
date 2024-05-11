#!/usr/bin/env python3

import glob
import json
#import numpy as np
import os
import re
import string
import sys


RUN_LENGTH = 120 # seconds

### subPattern is much slower than searchPattern so we keep them separate for fast search
hotstuffConfig = {}
hotstuffConfig["suffix"] = "err"
hotstuffConfig["searchPattern"] = r'fin decision.* wall: '
hotstuffConfig["subPattern"] = r'^.*fin decision.* wall: ([^,]+),.*$'
# ex: <date> [hotstuff info] got <fin decision=1 cmd_idx=390 cmd_height=31 cmd=88 blk=e11724f422>, wall: 1.408, cpu: 0.010

bftsmartConfig = {}
bftsmartConfig["suffix"] = "out"
bftsmartConfig["searchPattern"] = r'^[0-9]+ -> [0-9]+ = [0-9]+$'
bftsmartConfig["subPattern"] = r'[0-9]+ -> [0-9]+ = ([0-9]+)$'
# ex: 1670590989146 -> 1670590989823 = 677


def extract(config, dirNames):
    ### Find all directory paths
    dirPaths = []
    for dirName in dirNames:
        if not os.path.isdir(dirName):
            print("Not a directory: " + dirName)
            return
        path = os.path.relpath(dirName).rstrip('/') # remove righ-most slashes
        dirPaths.append(path)

    ### Recursively find all client files to parse
    clientFiles = []
    for dirPath in dirPaths:
        files = glob.glob("{}/*_client_*.{}".format(dirPath, config["suffix"]), recursive=True)
        clientFiles = clientFiles + files
    if len(clientFiles) != 80:
        print("Warning: expected 80 files (16 honest clients + 64 load clients) but counted {} files instead.".format(len(clientFiles)))

    ### Parse input client files
    latencies = []
    for counter, clientFile in enumerate(clientFiles):
        # print("Parsing file {:03d}/{:03d}: {}".format(counter+1, len(clientFiles), clientFile))
        with open(clientFile) as f:
            for line in f:
                line = line.strip() # Remove return character

                if re.search(config["searchPattern"] , line):
                    latency = re.sub(config["subPattern"], r'\1', line)
                    latency = float(latency)
                    latencies.append(latency)

    throughputAvg = len(latencies)/RUN_LENGTH
    latencyAvg = sum([v for v in latencies]) / len(latencies) if len(latencies) > 0 else 0
    # print("Count: {}\t lat-avg: {}\t throughput-avg: {}".format(len(latencies), latencyAvg, throughputAvg))

    ### Generate and store json
    data = {}
    data['throughput-avg'] = throughputAvg
    data['latency-avg'] = latencyAvg
    data['latency'] = latencies
    prefix = dirPaths[0].rstrip('/') # remove righ-most slashes
    fileName = '{}.json'.format(prefix)
    with open(fileName, 'w') as f:
        json.dump(data, f)
    print("Created json file: " + fileName)




#####
##### Main
#####

if __name__ == "__main__":
    if len(sys.argv) < 3 or (sys.argv[1] != "bftsmart" and sys.argv[1] != "hotstuff"):
        print("Expected at least two arguments: <bftsmart|hotstuff> <directories containing all .{err,out} files for one run>")
        sys.exit(1)

    cfg = bftsmartConfig
    if sys.argv[1] == "hotstuff":
        cfg = hotstuffConfig

    extract(cfg, sys.argv[2:])
