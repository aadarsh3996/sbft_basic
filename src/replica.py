from flask import Flask, request
from requests.api import delete
from rsa.key import PublicKey
from sbft_util import load_config, create_nodes, create_transaction_id, generate_rsa_key_pairs, create_url, time_now, sort_and_convert_dict, create_hash
from transaction import Transaction
from transaction_queue import TransactionQueue

import json
import argparse
import requests
import pickle


app = Flask(__name__)

sequence_number = 0
c_collector_queue = {}
e_collector_queue = {}
commit_queue = {}
block_chain_data = []

#transaction_queue = TransactionQueue()
h = "127.0.0.1"
p = 5000
@app.route("/pre_prepare", methods = ['POST','GET'])
def start_transaction(data=None):
    print("Request received from client")
    global sequence_number
    print(request.get_json())
    #return "<p>Hello, World!</p>"
    sequence_number+=1
    data = request.get_json()
    data['sequence_number'] = sequence_number
    data['transaction_id'] = create_transaction_id()
    data['timestamp'] = time_now()
    network_info = load_config("network_info.json")["nodes"]

    for node in network_info.values():
        if node["node_type"] != "primary":
            d=requests.post(create_url(node["server_ip"],node["port"],"prepare"),json=data)
        else:
            prepare(data)

    sequence_number+=1
    #print(request.json)
    print("Sent pre prepare messages to all replica")
    return "<p>Hello, World!</p>"

@app.route("/prepare", methods = ['POST','GET'])
def prepare(data=None):
    print("Request received from primary")
    data = data if data else request.get_json()
    
    network_info = load_config("network_info.json")["nodes"]
    public_key = ""
    for node in network_info.values():
        if node['port'] == p:
            public_key = node['public_key']
            break
    
    print("Sdata")
    serialized_data = sort_and_convert_dict(data)
    
    data['public_key'] = public_key
    print(serialized_data)
    print("After Sdata")
    data["hash"] = create_hash(serialized_data)

    host = ""
    port = 0
    route = "c_collector"

    flag = 0
    for node in network_info.values():
        if node["node_type"] == "c_collector":
            host = node["server_ip"]
            port = node["port"]
        
        if node["port"] == p and node["node_type"] == "c_collector":
            flag = 1
    print(host, port, route)
    if flag:
        c_collector(data)
    else:
        r = requests.post(create_url(host, port, route), json=data)



    #print(request.json)
    print("Request sent to c_collector")
    return "<p>Hello, World!</p>"

@app.route("/c_collector", methods = ['POST','GET'])
def c_collector(data=None):
    print("Recieved request from replica for verification")
    global c_collector_queue
    collective_hash = ""
    data = data if data else request.get_json()
    hash = data['hash']
    del data["hash"]
    public_key = data['public_key']
    del data['public_key']
    s_data = sort_and_convert_dict(data)
    print(s_data)
    c_hash = create_hash(s_data)
    if 0:#hash!=c_hash:
        print("Dropping the message in c_collector due to hash check fail")
        return "<p>Hello, World!</p>"
    data["hash"] = c_hash
    print("Adding messages to c_collector_queue {}".format(data["transaction_id"]))
    if data["transaction_id"] not in c_collector_queue.keys():
        c_collector_queue[data["transaction_id"]] = [data]
    else:
        c_collector_queue[data["transaction_id"]].append(data)
    
    network_info = load_config("network_info.json")["nodes"]
    f = (len(network_info.values())-1)//3
    v=None
    print("Length for transaction id".format(len(c_collector_queue[data["transaction_id"]])),c_collector_queue)
    if len(c_collector_queue[data["transaction_id"]]) >=2*f+1:
        for t in c_collector_queue[data["transaction_id"]]:
            collective_hash+= t["hash"]
            v=t
        v["collective_hash"] = hash

        v["message_type"]="commit_proof"
        for node in network_info.values():
            if node['port']!=p:
                k = requests.post(create_url(node["server_ip"], node["port"],"commit_proof"),json=v)
            else:
                commit_proof(v)
        print("Received 2f+1 messages from replica and sent commit proof for replicas")        
        c_collector_queue["transaction_id"] = []
    return "<p>Hello, World!</p>"

@app.route("/commit_proof", methods = ['POST','GET'])
def commit_proof(data=None):
    global commit_queue
    data = data if data else request.get_json()
    if data["message_type"] == "commit_proof":
        commit_queue[data["transaction_id"]] = data
    else:
        print("No commit proof signature. Hence dropping the data")
        return "<p>Hello, World!</p>"

    network_info = load_config("network_info.json")["nodes"]
    for n in network_info.values():
        if n["node_type"] == "e_collector" and n["port"]!=p:
            te = requests.post(create_url(n["server_ip"], n["port"], "e_collector"), json=data)
            break
        if n["node_type"] == "e_collector" and n["port"]==p:
            e_collector(data)
            break
    print("Commit proof done for replica")
    return "<p>Hello, World!</p>"

@app.route("/e_collector", methods = ['POST','GET'])
def e_collector(data=None):
    global e_collector_queue
    data = data if data else request.get_json()

    if data["transaction_id"] not in e_collector_queue.keys():
        e_collector_queue[data["transaction_id"]] = [data]
    else:
        e_collector_queue[data["transaction_id"]].append(data)
    
    network_info = load_config("network_info.json")["nodes"]
    f = (len(network_info.values())-1)//3
    v=None
    if len(e_collector_queue[data["transaction_id"]]) >=f+1:
        for t in e_collector_queue[data["transaction_id"]]:
            v=t

        v["message_type"]="execute_proof"
        for node in network_info.values():
            if node['port']!=p:
                k = requests.post(create_url(node["server_ip"], node["port"],"execute_proof"),json=v)
            else:
                execute_proof(v)
        e_collector_queue["transaction_id"] = []
        print(" Received f+1 messages from replica and sent execute proof")
    return "<p>Hello, World!</p>"

@app.route("/execute_proof", methods = ['POST','GET'])
def execute_proof(data=None):
    global block_chain_data
    data = data if data else request.get_json()
    flag =1
    if data["message_type"] == "execute_proof":
        for d in block_chain_data:
            if d["transaction_id"] == data["transaction_id"]:
                flag = 0
                break
        if flag:
            block_chain_data.append(data)
        print("Adding data to block chain after commit proof")
    else:
        print("No execute proof, dropping the message")
    return "<p>Hello, World!</p>"

@app.route("/block_chain", methods = ['POST','GET'])
def block_chain(data=None):
    global block_chain_data
    b = {"block_chain":block_chain}
    print(b)
    return json.dumps({"block_chain":block_chain_data})
    #return "<p>Hello, World!</p>"
    

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
    
    app.run(debug=True, threaded=True, host = h, port = p)