from flask import Flask, request
import random

from requests.api import delete
from rsa.key import PublicKey
from sbft_util import load_config, create_nodes, create_transaction_id, generate_rsa_key_pairs, create_url, time_now, sort_and_convert_dict, create_hash, dump_config
from transaction import Transaction
from transaction_queue import TransactionQueue

import json
import argparse
import requests
import pickle


app = Flask(__name__)

faulty_nodes = set()
votes = {}
view_change_count = [0]

# Default Host, port
public_key = None
n = 0
f = 0
c = 0

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

def proof(key) :
	# Proof part needs to be implemented
	return True

def add_faulty_node(key, proof) :
	if proof(key) :
		faulty_nodes.add(key)
		
def leader_election(network_info) :
	network_info = load_config("network_info.json")
	
	non_faulty_nodes = set(network_info['nodes'].keys())
	non_faulty_nodes = non_faulty_nodes - faulty_nodes
	
	# Arbitrarily pick a non faulty node
	return random.sample(non_faulty_nodes,  1)[0]
	return random.choice(non_faulty_nodes)
		
'''
initiate_view_change_request/view_change_trigger - send view change request
recieve_view_change_request - recieve view change request; choose new leader
recieve_votes - tally votes recieved and select new leader

view-change - send request to elected leader to be new primary
new-view - acknowledge request
'''

@app.route("/view_change_trigger", methods = ['POST','GET'])
def view_change_trigger(data=None) :
	network_info = load_config("network_info.json")
	nodes_info = network_info['nodes']

	msg = {}
	msg['message'] = 'view-change-trigger'
	msg['view_number'] = network_info['view_number']
	msg['sender'] = public_key
	#msg = ['view-change-trigger', network_info['view_number'], public_key]
	
	print("View-change trigger initiated")
	for node in nodes_info.values() :
		d=requests.post(create_url(node["server_ip"],node["port"],"elect_new_leader"), json = msg)
	
	return 'view-change-trigger'

@app.route("/elect_new_leader", methods = ['POST','GET'])
def elect_new_leader(data=None) :
	network_info = load_config("network_info.json")
	nodes_info = network_info['nodes']
	
	# Check if request is sent from non-faulty replica 
	
	for (key,node) in nodes_info.items() :
		#if key == data['sender'] and key in faulty_nodes :
		#	return
		if node['node_type'] == 'primary' :
			primary_key = key	
	add_faulty_node(primary_key, proof)
	
	leader = leader_election(network_info)
	
	votes[public_key] = leader
	
	msg = {}
	msg['message'] = 'elect-new-leader'
	msg['view_number'] = network_info['view_number']
	msg['sender'] = public_key
	msg['vote'] = leader
	
	#msg[''] = ['elect-new-leader', network_info['view_number'], public_key, leader]
	
	print("Leader elected to be ", leader)
	
	for node in nodes_info.values() :
		d=requests.post(create_url(node["server_ip"],node["port"],"view_change"), json = msg)
		
	return 'elect-new-leader'
	

@app.route("/view_change", methods = ['POST','GET'])
def view_change(data=None) :
	network_info = load_config("network_info.json")
	nodes_info = network_info['nodes']
	
	d = request.get_json()
	sender_key = d['sender']
	sender_vote = d['vote']
	
	
	if len(votes) < 2*f + 2*c + 1 :
		votes[sender_key] = sender_vote
	
	if len(votes) == 2*f + 2*c + 1 :
		tally = {}
		for v in votes :
			if votes[v] not in tally :
				tally[votes[v]] = 1
			else :
				tally[votes[v]] += 1
		tally = list(tally.items())
		tally.sort(key = lambda x : x[1], reverse = True)
		leader = tally[0][0]
		
		msg = {}
		msg['message'] = 'view-change'
		msg['view_number'] = network_info['view_number'] + 1
		msg['sender'] = public_key
		
		print("Requesting for new view")
		#msg = ['view-change', network_info['view_number'] + 1, public_key]

		leader_node = nodes_info[leader]
		print("Leader Node : ", leader_node["server_ip"], leader_node["port"])
		d=requests.post(create_url(leader_node["server_ip"], leader_node["port"],"create_new_view"), json = msg)
	
	print('Number of votes - ', len(votes))
	print('Threshold - ', 2*f + 2*c + 1)
	return 'view-change'

@app.route("/create_new_view", methods = ['POST','GET'])
def create_new_view(data=None) :
	view_change_count[0] += 1
	
	if view_change_count[0] >= 2*f + 2*c + 1 : 
		network_info = load_config("network_info.json")
		
		network_info['view_number'] += 1
		for key in network_info['nodes'] :
			if network_info['nodes'][key]['node_type'] == 'primary' :
				network_info['nodes'][key]['node_type'] = 'replica'
			if key == public_key :
				network_info['nodes'][key]['node_type'] = 'primary'
	
		print("Primary has been updated")
		print("New view created")
		
		dump_config(network_info, "network_info.json")
	
	print('Number of requests - ', view_change_count[0])
	print('Threshold - ', 2*f + 2*c + 1)
	
	return 'new-view'

def get_public_key(host, port) :
	network_info = load_config("network_info.json")
	nodes_info = network_info['nodes']
	
	for key, node in nodes_info.items() :
		if node['port'] == port :
			return key

def get_n_c() :
	network_info = load_config("network_info.json")
	return network_info['n'], network_info['c']

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

@app.route("/get_primary", methods = ['POST','GET'])
def get_primary(data=None):
	network_info = load_config("network_info.json")
	nodes_info = network_info['nodes']
	
	for (key,node) in nodes_info.items() :
		if node['node_type'] == 'primary' :
			return "IP - " + str(node['server_ip']) + ", Port - " + str(node['port']) + "\n"
	

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
    
    public_key = get_public_key(h, p)
    n, c = get_n_c()
    f = (n - 2*c - 1) // 3
    #view_change_count = 0
    
    app.run(debug=True, threaded=True, host = h, port = p)
