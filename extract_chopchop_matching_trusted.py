#!/bin/python3

import subprocess
import os
import json

def output_throughput(heartbeat_path):
    stdout = subprocess.run(["/home/proman/chop-chop/target/release/heartbeat_statistics", "--shallow-server", heartbeat_path, "--start", "30", "--duration", "60"], stdout = subprocess.PIPE, stderr = subprocess.DEVNULL).stdout
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

def heartbeat_paths(base_path):
    # Careful: include in the filter the batch size of the TOB.
    # We had one run that did not have a correct batch size and should be thrown away.
    # load_broker_throughput_filter = "6-18-16_" + str(load_broker_throughput)

    heartbeat_paths = []

    vaults = os.listdir(base_path)
    vaults = [vault for vault in vaults if "bftsmart" in vault]
    vaults = [vault for vault in vaults if "4600000" in vault]

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

                print(broadcast + " @ " + str(input_throughput) + " -> " + str(output_throughput_value))

    contents = json.dumps(plot)
    with open('throughput_' + destination + '.json', 'a') as f:
        f.write(contents)

    print("\n\n\n")
    print(contents)

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

                print(broadcast + " @ " + str(input_throughput) + " -> " + str(latencies_values))

    contents = json.dumps(plot)
    with open('latency_' + destination + '.json', 'a') as f:
        f.write(contents)

    print("\n\n\n")
    print(contents)

# print(len(heartbeat_paths_bis("/home/voron/expe-osdi24")))

throughputs = []

for path in heartbeat_paths("/home/voron/expe-osdi24"):
    throughput = output_throughput(path)
    print(throughput)
    throughputs.append(throughput)

print(throughputs)
