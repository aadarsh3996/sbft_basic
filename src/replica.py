from flask import Flask, request
from requests.api import delete
from rsa.key import PublicKey
from aadarsh.sbft_basic.src.client import create_transaction
from sbft_util import load_config, create_nodes, create_transaction_id, generate_rsa_key_pairs, create_url, time_now, sort_and_convert_dict, create_hash
from transaction import Transaction
from transaction_queue import TransactionQueue

import argparse
import requests
import pickle


app = Flask(__name__)

sequence_number = 0
c_collector_queue = {}
e_collector_queue = {}
commit_queue = {}
block_chain = []

#transaction_queue = TransactionQueue()
h = "127.0.0.1"
p = 5000
@app.route("/pre_prepare", methods = ['POST','GET'])
def start_transaction(data=None):
    global sequence_number
    sequence_number+=1
    data = request.json
    data['sequence_number'] = sequence_number
    data['transaction_id'] = create_transaction_id()
    data['timestamp'] = time_now()
    network_info = load_config("node_info.json")

    for node in network_info.values():
        if node["node_type"] != "primary":
            d=requests.post(create_url(node["server_ip"],node["port"],"prepare"),data=data)
        else:
            prepare(data)

    sequence_number+=1
    print(request.json)
    return "<p>Hello, World!</p>"

@app.route("/prepare", methods = ['POST','GET'])
def prepare(data=None):
    data = data if data else request.data
    
    network_info = load_config("node_info.json")
    public_key = ""
    for node in network_info.values():
        if node['port'] == p:
            public_key = node['public_key']
            break
    
    data['public_key'] = public_key
    serialized_data = sort_and_convert_dict(data)
    data["hash"] = create_hash(serialized_data)

    host = ""
    port = 0
    route = "c_collector"

    flag = 0
    for node in network_info:
        if node["node_type"] == "c_collector":
            host = node["server_ip"]
            port = node["port"]
        
        if node["port"] == p and node["node_type"] == "c_collector":
            flag = 1
    
    if flag:
        c_collector(data)
    else:
        r = requests.post(create_url(host, port, route), data = data)



    print(request.json)
    return "<p>Hello, World!</p>"

@app.route("/c_collector", methods = ['POST','GET'])
def c_collector(data=None):
    global c_collector_queue
    collective_hash = ""
    data = data if data else request.data
    hash = data['hash']
    del data["hash"]
    s_data = sort_and_convert_dict(data)
    c_hash = create_hash(s_data)
    if hash!=c_hash:
        print("Dropping the message in c_collector due to hash check fail")
        return "<p>Hello, World!</p>"
    data["hash"] = c_hash
    if data["transaction_id"] not in c_collector_queue.keys():
        c_collector_queue["transaction_id"] = [data]
    else:
        c_collector_queue["transaction_id"].append(data)
    
    network_info = load_config("node_info.json")
    f = (len(network_info.values())-1)//3
    v=None
    if len(c_collector_queue["transaction_id"]) >=2*f+1:
        for t in c_collector_queue["transaction_id"]:
            collective_hash+= t["hash"]
            v=t
        v["collective_hash"] = hash

        v["message_type"]="commit_proof"
        for node in network_info.values():
            if node['port']!=p:
                k = requests.post(create_url(node["server_ip"], node["port"],"commit_proof"),data=v)
            else:
                commit_proof(v)
        c_collector_queue["transaction_id"] = []
    return "<p>Hello, World!</p>"

@app.route("/commit_proof", methods = ['POST','GET'])
def commit_proof(data=None):
    global commit_queue
    data = data if data else request.data
    if data["message_type"] == "commit_proof":
        commit_queue[data["transaction_id"]] = data
    else:
        print("No commit proof signature. Hence dropping the data")
        return "<p>Hello, World!</p>"

    network_info = load_config("node_info.json")
    for n in network_info.values():
        if n["node_type"] == "e_collector" and n["port"]!=p:
            te = requests.post(create_url(n["server_ip"], n["port"], "e_collector"), data = data)
            break
        if n["node_type"] == "e_collector" and n["port"]==p:
            e_collector(data)
            break
    
    return "<p>Hello, World!</p>"

@app.route("/e_collector", methods = ['POST','GET'])
def e_collector(data=None):
    global e_collector_queue
    data = data if data else request.data

    if data["transaction_id"] not in e_collector_queue.keys():
        e_collector_queue["transaction_id"] = [data]
    else:
        e_collector_queue["transaction_id"].append(data)
    
    network_info = load_config("node_info.json")
    f = (len(network_info.values())-1)//3
    v=None
    if len(e_collector_queue["transaction_id"]) >=f+1:
        for t in e_collector_queue["transaction_id"]:
            v=t

        v["message_type"]="execute_proof"
        for node in network_info.values():
            if node['port']!=p:
                k = requests.post(create_url(node["server_ip"], node["port"],"execute_proof"),data=v)
            else:
                execute_proof(v)
        e_collector_queue["transaction_id"] = []
    return "<p>Hello, World!</p>"

@app.route("/execute_proof", methods = ['POST','GET'])
def execute_proof(data=None):
    global block_chain
    data = data if data else request.data
    if data["message_type"] == "execute_proof":
        block_chain.append(data)
    else:
        print("No execute proof, dropping the message")
    return "<p>Hello, World!</p>"

if __name__ == "__main__":
    
    # Default Host and port


    parser = argparse.ArgumentParser()
    parser.add_argument("-i", "--ip", help = "Host ip")
    parser.add_argument("-p", "--port", help = "Port")
    args = parser.parse_args()
    
    if args.ip:
        h = args.ip
    if args.port:
        p = int(args.port)
    
    app.run(debug=True, threaded=False, host = h, port = p)