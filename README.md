Chop Chop Plots
===============

Repository containing the scripts used to extract, aggregate, analyze and visualize the data generated by the benchmarks of Chop Chop and its baselines. The repository also contains the data and plots used in the Chop Chop paper.

1. Prerequisites
2. Extract and aggregate relevant data from the benchmarks
3. Compute statistics on the aggregated data
4. Plot dem stats
5. Write a dope paper


### 1. Prerequisites

- Install `python3` and its packages: `matplotlib`, `numpy`, `pandas`
- Compile Chop Chop to obtain the `heartbeat_statistics` binary
- Coffee
- Patience


### 2. Extract and aggregate data

The following assumes that each run of each system configuration has been executed.
Different systems require different scripts to parse the logs but they all output `.json` files for uniformity. You will need to create directories to sort the evaluation files generated for the BFT-SMaRt, HotStuff and Bullshark baselines; feel free to use symbolic links to avoid moving or duplicating many large files (`ln -s <origin> <destination>`).

For comparison, the archive `sorted-results-little-boy.tar.xz` (435 MB decompressed) contains the directory tree, the dead symlinks and the aggregated `.json` files of the baselines, as used in the paper. The archive `agg-data.tar.xz` (83 MB decompressed) contains all the aggregated `.json` files needed for the plots (some duplicated from the sorted results).


#### 2.1. Chop Chop (`*.bin` &rarr; `*.json`)

The script `extract_chopchop.py` aggregates the data from Chop Chop logs into `.json`. Please fill the variables at the top of the script to indicate: (1) the directory containing the compiled code of Chop Chop in order to access the `heartbeat_statistics` binary, (2) the directory containing the raw evaluation data, and (3) the name of the ethernet interface of the servers used to determine the total throughput of a run.

**Inputs**: directories containing raw evaluation files (`.bin` heartbeat files) as indicated in the variable `DIR_RESULT` at the top and in the main loop at the bottom of the script.

**Outputs**: one `.json` file per latency and per throughput per system configuration, and one `.json` file for line rate measurements.

```
python3 extract_chopchop.py
```


#### 2.2. BFT-SMaRt and HotStuff (`*.out` + `*.err` &rarr; `*.json`)

The script `extract_bftsmart_hotstuff.py` must be run once per evaluation run. For instance, it must be run 5 times per system configuration to obtain the data used in the paper, while the script `extract_chopchop.py` must only be run once regardless of the number of runs.

**Inputs**:

1. `bftsmart` or `hotstuff` depending on the system configuration to parse;
2. A directory `DIR` that contains 80 `.out` and 80 `.err` files of a single run (16 honest clients + 64 load clients).

**Outputs**: `DIR.json` located in the same directory as `DIR`.

```
python3 extract_bftsmart_hotstuff.py bftsmart <DIR>
python3 extract_bftsmart_hotstuff.py hotstuff <DIR>
```


#### 2.3. Bullshark (`*.out` + `*.err` &rarr; `*.json`)

The script `extract_bullshark.py` must be run once per evaluation run as with `bftsmart_hotstuff.py`. The script is mostly copied from the original Bullshark's `easy_log.py`. The main changes are around lines 375 to generate a `.json` containing the latency distribution and to include the logs of the worker nodes.

**Inputs**: a directory `DIR` that contains the `.out` and `.err` files of a single run, as with `bftsmart_hotstuff.py`.

**Outputs**: `DIR.easier-log.json` located in the same directory as `DIR`.

```
python3 extract_bullshark.py <DIR>
```


### 3. Stats `stats.py` (`agg-data/*.json` &rarr; `stats/*.csv`)

The script `stats.py` computes statistics on all the aggregated `.json` from all the runs of all the system configurations.

**Inputs**: aggregated `.json` files in `agg-data/`, the exact location of each file can be found at the bottom of the script.

**Outputs**: one statistics `.csv` file per system configuration stored in `stats/`. The `stats/` directory is already populated with the files used in the paper.

```
python3 stats.py
```


### 4. Plot (`stats/*.csv` &rarr; `figs/*.pdf`)

The script `plot.py` generates plots from the previously computed statistics.
with helper functions and variables in `utils.py`.

**Inputs**: statistical data in `stats/`, the exact location of each `.csv` file can be found at the bottom of the script.

**Outputs**: plots in `.pdf` format stored in `figs/`, the exact location of each pdf can be found at the end of each function. Functions that start with an underscore (e.g. `_plotCommaSingle`) contain older code that generates figures that are not in the paper. See `utils.py` to generate `.eps` in addition to `.pdf`.

```
python3 plot.py
```

Directory `figs/` is already populated with the figures used in the paper:

* Fig 1: `motivation-throughput-services.pdf`
* Fig 7: `comma-split.pdf`
* Fig 8: `merged-distillation-payloed-sizes.pdf` (let's keep the typo)
* Fig 9: `linerate-throughput-log.pdf`
* Fig 10: `merged-system-sizes-matching-trusted-resources.pdf`
* Fig 11: `merged-servers-faults-applications.pdf`


### 5. Write paper

TODO. Input welcome.
