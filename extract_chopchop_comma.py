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

def latencies(log_path):
    lines = open(log_path).readlines()
    deliveries = [line for line in lines if "Message delivered!" in line]
    latencies = [int(line.split("Took")[1].split("ms")[0]) for line in deliveries]
    
    return latencies

def heartbeat_paths(broadcast, load_broker_throughput, base_path):
    # Careful: include in the filter the batch size of the TOB.
    # We had one run that did not have a correct batch size and should be thrown away.
    load_broker_throughput_filter = "6-18-16_" + str(load_broker_throughput)

    heartbeat_paths = []

    vaults = os.listdir(base_path)
    vaults = [vault for vault in vaults if broadcast in vault]
    vaults = [vault for vault in vaults if load_broker_throughput_filter in vault]

    for vault in vaults:
        vault_path = base_path + "/" + vault

        processes = os.listdir(vault_path)
        servers = [process for process in processes if "result_server_" in process]
        
        for server in servers:
            server_path = vault_path + "/" + server

            heartbeats = os.listdir(server_path)
            heartbeats = [heartbeat for heartbeat in heartbeats if ".bin" in heartbeat]

            for heartbeat in heartbeats:
                heartbeat_path = server_path + "/" + heartbeat
                heartbeat_paths.append(heartbeat_path)
    
    return heartbeat_paths

def client_log_paths(broadcast, load_broker_throughput, base_path):
    load_broker_throughput_filter = "6-18-16_" + str(load_broker_throughput)

    heartbeat_paths = []

    vaults = os.listdir(base_path)
    vaults = [vault for vault in vaults if broadcast in vault]
    vaults = [vault for vault in vaults if load_broker_throughput_filter in vault]

    for vault in vaults:
        vault_path = base_path + "/" + vault

        processes = os.listdir(vault_path)
        clients = [process for process in processes if "result_honest-client_" in process]
        
        for client in clients:
            client_path = vault_path + "/" + client

            heartbeats = os.listdir(client_path)
            heartbeats = [heartbeat for heartbeat in heartbeats if ".err" in heartbeat]

            for heartbeat in heartbeats:
                heartbeat_path = client_path + "/" + heartbeat
                heartbeat_paths.append(heartbeat_path)
    
    return heartbeat_paths

######## Throughputs ########
def compute_throughput(base_path, input_rates, destination, payload_size):
    plot = {}

    for broadcast in ["bftsmart", "hotstuff"]:
        plot[broadcast] = {}
        
        for load_broker_throughput in input_rates:
            input_throughput = load_broker_throughput + 432000. / payload_size * 8
            input_throughput = float(input_throughput) / 1000000.

            plot[broadcast][input_throughput] = []

            for heartbeat_path in heartbeat_paths(broadcast, load_broker_throughput, base_path):
                output_throughput_value = output_throughput(heartbeat_path) / payload_size * 8
                plot[broadcast][input_throughput].append(output_throughput_value)

                # print(broadcast + " @ " + str(input_throughput) + " -> " + str(output_throughput_value))

    contents = json.dumps(plot)
    filename = 'throughput_' + destination + '.json'
    with open(filename, 'a') as f:
        f.write(contents)
    print("Created json file: " + filename)
    # print("\n\n\n")
    # print(contents)

####### Latencies ########
def compute_latency(base_path, input_rates, destination, payload_size):
    plot = {}

    for broadcast in ["bftsmart", "hotstuff"]:
        plot[broadcast] = {}
        
        for load_broker_throughput in input_rates:
            input_throughput = load_broker_throughput + 432000 / payload_size * 8.
            input_throughput = float(input_throughput) / 1000000.

            plot[broadcast][input_throughput] = []

            for client_log_path in client_log_paths(broadcast, load_broker_throughput, base_path):
                latencies_values = latencies(client_log_path)

                for latency in latencies_values:
                    plot[broadcast][input_throughput].append(latency)

                # print(broadcast + " @ " + str(input_throughput) + " -> " + str(latencies_values))

    contents = json.dumps(plot)
    filename = 'latency_' + destination + '.json'
    with open(filename, 'a') as f:
        f.write(contents)
    print("Created json file: " + filename)
    # print("\n\n\n")
    # print(contents)





ARGS = [
    (utils.RESULT_DIR + "/faults", [20000000, 44000000], 'faults', 8),
    (utils.RESULT_DIR + "/auction", [2000000], 'auction', 8),
    (utils.RESULT_DIR + "/payments", [32000000], 'payments', 8),
    (utils.RESULT_DIR + "/pixel_war", [35000000], 'pixel_war', 8),
    (utils.RESULT_DIR + "/payload-512", [900000], 'payload-512', 512),
    (utils.RESULT_DIR + "/payload-128", [4000000], 'payload-128', 128),
    (utils.RESULT_DIR + "/payload-32", [18000000], 'payload-32', 32),
    (utils.RESULT_DIR + "/reduction-0", [1000000], 'reduction-0', 8),
    (utils.RESULT_DIR + "/system-32", [48000000], 'system-32', 8),
    (utils.RESULT_DIR + "/system-16", [45000000], 'system-16', 8),
    (utils.RESULT_DIR + "/system-8", [40000000], 'system-8', 8),
]

for arg in ARGS:
    compute_latency(arg[0], arg[1], arg[2], arg[3])
    compute_throughput(arg[0], arg[1], arg[2], arg[3])
