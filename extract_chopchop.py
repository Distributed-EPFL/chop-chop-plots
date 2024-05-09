#!/bin/python3

import subprocess
import os
import json


#####
##### Change at will
#####

HW_INTERFACE = "ens5"
DIR_CHOPCHOP = "/home/ubuntu/chop-chop"
DIR_RESULT = "/home/ubuntu/result"


def output_throughput(heartbeat_path):
    """ Find throughput value in a file """
    stdout = subprocess.run([DIR_CHOPCHOP + "/target/release/heartbeat_statistics", "--shallow-server", heartbeat_path, "--start", "30", "--duration", "60"], stdout = subprocess.PIPE, stderr = subprocess.DEVNULL).stdout
    stdout = str(stdout)
    stdout = stdout.split("\n")
    
    for line in stdout:
        if "Deliveries:" in line:
            return float(line.split("(")[1].split("Mops")[0])
    
    raise "Malformed heartbeat output!"


def total_messages(heartbeat_path):
    """ Find number of messages delivered in a file """
    stdout = subprocess.run([DIR_CHOPCHOP + "/target/release/heartbeat_statistics", "--shallow-server", heartbeat_path], stdout = subprocess.PIPE, stderr = subprocess.DEVNULL).stdout
    stdout = str(stdout)
    stdout = stdout.split("\n")

    for line in stdout:
        if "Deliveries:" in line:
            return int(line.split(":")[1].split("(")[0])

    raise "Malformed heartbeat output!"


def latencies(log_path):
    """ Find all latencies in a file """
    lines = open(log_path).readlines()
    deliveries = [line for line in lines if "Message delivered!" in line]
    latencies = [int(line.split("Took")[1].split("ms")[0]) for line in deliveries]
    
    return latencies


def network_transfer(before_path, after_path):
    before_lines = open(before_path).readlines()
    after_lines = open(after_path).readlines()

    befores = [line for line in before_lines if HW_INTERFACE + ":rx_bytes:" in line]
    afters = [line for line in after_lines if HW_INTERFACE + ":rx_bytes:" in line]

    before = int(befores[0].split(":")[2])
    after = int(afters[0].split(":")[2])

    return after - before


def heartbeat_paths(broadcast, load_broker_throughput, base_path, matching_trusted):
    # Careful: include in the filter the batch size of the TOB.
    # We had one run that did not have a correct batch size and should be thrown away.
    load_broker_throughput_filter = "6-18-16_" + str(load_broker_throughput)
    if matching_trusted:
        load_broker_throughput_filter = str(load_broker_throughput)

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


def dump_to_json(plot, filename):
    contents = json.dumps(plot)
    with open(filename, 'a') as f:
        f.write(contents)
    print("Created json file: " + filename)
    # print("\n\n\n")
    # print(contents)


######## Throughputs ########
def compute_throughput(base_path, input_rates, destination, payload_size, matching_trusted):
    plot = {}

    for broadcast in ["bftsmart", "hotstuff"]:
        plot[broadcast] = {}
        
        for load_broker_throughput in input_rates:
            input_throughput = load_broker_throughput + 432000. / payload_size * 8
            input_throughput = float(input_throughput) / 1000000.

            plot[broadcast][input_throughput] = []

            for heartbeat_path in heartbeat_paths(broadcast, load_broker_throughput, base_path, matching_trusted):
                output_throughput_value = output_throughput(heartbeat_path) / payload_size * 8
                plot[broadcast][input_throughput].append(output_throughput_value)

                # print(broadcast + " @ " + str(input_throughput) + " -> " + str(output_throughput_value))

    dump_to_json(plot, 'throughput_' + destination + '.json')


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

    dump_to_json(plot, 'latency_' + destination + '.json')


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

    dump_to_json(plot, 'linerate_' + destination + '.json')





#####
##### Throughput latency
#####

ARGS = [
    (DIR_RESULT + "/faults", [20000000, 44000000], 'faults', 8, False),
    (DIR_RESULT + "/auction", [2000000], 'auction', 8, False),
    (DIR_RESULT + "/payments", [32000000], 'payments', 8, False),
    (DIR_RESULT + "/pixel_war", [35000000], 'pixel_war', 8, False),
    (DIR_RESULT + "/payload-512", [900000], 'payload-512', 512, False),
    (DIR_RESULT + "/payload-128", [4000000], 'payload-128', 128, False),
    (DIR_RESULT + "/payload-32", [18000000], 'payload-32', 32, False),
    (DIR_RESULT + "/reduction-0", [1000000], 'reduction-0', 8, False), # no distillation
    (DIR_RESULT + "/system-32", [48000000], 'system-32', 8, False),
    (DIR_RESULT + "/system-16", [45000000], 'system-16', 8, False),
    (DIR_RESULT + "/system-8", [40000000], 'system-8', 8, False),
    (DIR_RESULT + "/matching_trusted", [4600000], 'matching-trusted', 8, True),
]

for arg in ARGS:
    compute_latency(arg[0], arg[1], arg[2], arg[3])
    compute_throughput(arg[0], arg[1], arg[2], arg[3], arg[4])

#####
##### Linerate
#####

ARGS = [(DIR_RESULT + "/linerate", [10000000, 20000000, 30000000, 40000000, 50000000, 60000000], "chopchop", 8)]
for arg in ARGS:
    compute_linerate(args[0], args[1], args[2], args[3])
