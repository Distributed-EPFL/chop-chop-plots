#!/bin/python3

import subprocess
import os
import json

### local import
import utils

def output_throughput(heartbeat_path):
    stdout = subprocess.run([utils.DIR_CHOPCHOP + "/target/release/heartbeat_statistics", "--shallow-server", heartbeat_path, "--start", "30", "--duration", "60"], stdout = subprocess.PIPE, stderr = subprocess.DEVNULL).stdout
    stdout = str(stdout)
    stdout = stdout.split("\n")
    
    for line in stdout:
        if "Deliveries:" in line:
            return float(line.split("(")[1].split("Mops")[0])
    
    raise "Malformed heartbeat output!"

def total_messages(heartbeat_path):
    stdout = subprocess.run([utils.DIR_CHOPCHOP + "/target/release/heartbeat_statistics", "--shallow-server", heartbeat_path], stdout = subprocess.PIPE, stderr = subprocess.DEVNULL).stdout
    stdout = str(stdout)
    stdout = stdout.split("\n")
    
    for line in stdout:
        if "Deliveries:" in line:
            return int(line.split(":")[1].split("(")[0])
    
    raise "Malformed heartbeat output!"

def network_transfer(before_path, after_path):
    before_lines = open(before_path).readlines()
    after_lines = open(after_path).readlines()

    befores = [line for line in before_lines if "ens5:rx_bytes:" in line]
    afters = [line for line in after_lines if "ens5:rx_bytes:" in line]

    before = int(befores[0].split(":")[2])
    after = int(afters[0].split(":")[2])

    return after - before

def linerate_paths(broadcast, load_broker_throughput, base_path):
    load_broker_throughput_filter = "64-64-6-18-16_" + str(load_broker_throughput)
    secondary_filter = "8_400_2022"

    linerate_paths = []

    vaults = os.listdir(base_path)
    vaults = [vault for vault in vaults if broadcast in vault]
    vaults = [vault for vault in vaults if load_broker_throughput_filter in vault and secondary_filter in vault]

    for vault in vaults:
        vault_path = base_path + "/" + vault

        processes = os.listdir(vault_path)
        servers = [process for process in processes if "result_server_" in process]
        
        for server in servers:
            server_path = vault_path + "/" + server

            files = os.listdir(server_path)
            
            heartbeats = [file for file in files if ".bin" in file]
            befores = [file for file in files if ".before" in file]
            afters = [file for file in files if ".after" in file]

            if len(heartbeats) > 1:
                print("WHAT THE HELL??")
            elif len(heartbeats) > 0:
                heartbeat = server_path + "/" + heartbeats[0]
                before = server_path + "/" + befores[0]
                after = server_path + "/" + afters[0]

                linerate_paths.append({"heartbeat": heartbeat, "before": before, "after": after})
    
    return linerate_paths

######## Linerate ########
def compute_linerate(base_path, input_rates, destination, payload_size):
    plot = {}

    for broadcast in ["bftsmart", "hotstuff"]:
        plot[broadcast] = {}

        for load_broker_throughput in input_rates:
            input_throughput = load_broker_throughput + 432000  / payload_size * 8.
            input_throughput = float(input_throughput) / 1000000.

            plot[broadcast][input_throughput] = []

            for linerate_path in linerate_paths(broadcast, load_broker_throughput, base_path):
                output_throughput_value = output_throughput(linerate_path["heartbeat"])
                output_total_messages = total_messages(linerate_path["heartbeat"])
                network_transfer_value = network_transfer(linerate_path["before"], linerate_path["after"])

                goodput = float(output_total_messages) * 11.5 / float(network_transfer_value)

                plot[broadcast][input_throughput].append({"output_throughput": output_throughput_value, "goodput": goodput})

                # print(broadcast + " @ " + str(input_throughput) + " -> " + str(output_throughput_value) + "  (" + str(goodput) + ")")

    contents = json.dumps(plot)
    filename = 'linerate_' + destination + '.json'
    with open(filename, 'a') as f:
        f.write(contents)
    print("Created json file: " + filename)
    # print("\n\n\n")
    # print(contents)





#####
##### Main
#####

ARGS = [
    (utils.DIR_RESULT + "/linerate", [10000000, 20000000, 30000000, 40000000, 50000000, 60000000], "chopchop", 8)
    ]

for arg in ARGS:
    compute_linerate(args[0], args[1], args[2], args[3])
