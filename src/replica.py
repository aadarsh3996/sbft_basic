from flask import Flask, request
from sbft_util import load_config, create_nodes, create_transaction_id, generate_rsa_key_pairs, create_url
import random

import argparse
import requests

app = Flask(__name__)

faulty_nodes = set()
votes = {}
view_change_count = 0

# Default Host, port
h = "127.0.0.1"
p = 5000
public_key = None
n = 0
f = 0
c = 0

@app.route("/start_transaction", methods = ['POST','GET'])
def start_transaction(data=None):
    network_info = load_config("node_info.json")
    nodes_info = network_info['nodes']
    
    #msg = ['pre-prepare', request.json]
    
    for node in nodes_info.values():
        if node["node_type"] != "primary":
            d=requests.post(create_url(node["server_ip"],node["port"],"pre_prepare"),data=request.json)
        else:
            pre_prepare(data)

    print(request.json)
    return "<p>Hello, World!</p>"

@app.route("/pre_prepare", methods = ['POST','GET'])
def pre_prepare(data=None):
    network_info = load_config("node_info.json")
    nodes_info = network_info['nodes']
    
    print(request.json)
    return "<p>Hello, World!</p>"

def add_faulty_node(key, proof) :
	if proof(network_info, key) :
		faulty_nodes.add(key)
		
def leader_election(network_info) :
	network_info = load_config("node_info.json")
	
	non_faulty_nodes = set(network_info['nodes'].keys())
	non_faulty_nodes = non_faulty_nodes - faulty_nodes
	
	# Arbitrarily pick a non faulty node
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
	network_info = load_config("node_info.json")
	nodes_info = network_info['nodes']

	msg = ['view-change-trigger', network_info['view_number'], public_key]

	for node in nodes_info.values() :
		d=requests.post(create_url(node["server_ip"],node["port"],"elect_new_leader"), data=msg)

@app.route("/elect_new_leader", methods = ['POST','GET'])
def elect_new_leader(data=None) :
	network_info = load_config("node_info.json")
	nodes_info = network_info['nodes']
	
	# Check if request is sent from non-faulty replica 
	#port = request.portID
	#for (key,node) in nodes_info.items() :
	#	if node['port'] == port and key in faulty_nodes :
	#		return
	#	if node['node_type'] == 'primary' :
	#		primary_key = key	
	#add_faulty_node(primary_key, proof)
	
	leader = leader_election(network_info)
	
	votes[public_key] = leader
	
	msg = ['elect-new-leader', network_info['view_number'], public_key, leader]
	
	for node in nodes_info.values() :
		d=requests.post(create_url(node["server_ip"],node["port"],"view_change"), data=msg)
	

@app.route("/view_change", methods = ['POST','GET'])
def view_change(data=None) :
	network_info = load_config("node_info.json")
	nodes_info = network_info['nodes']
	
	sender_key = data[2]
	sender_vote = data[3]
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
		
		msg = ['view-change', network_info['view_number'] + 1, public_key]

		leader_node = nodes_info[leader]
		d=requests.post(create_url(leader_node["server_ip"], leader_node["port"],"create_new_view"), data=msg)
		

@app.route("/create_new_view", methods = ['POST','GET'])
def create_new_view(data=None) :
	view_count += 1
	
	if view_count == 2*f + 2*c + 1 : 
		network_info = load_config("node_info.json")
		
		for key in network_info['nodes'] :
			if network_info['nodes'][key]['node_type'] == 'primary' :
				network_info['nodes'][key]['node_type'] = 'replica'
			if key == public_key :
				network_info['nodes'][key]['node_type'] = 'primary'
		
	dump_config(network_info, "network_info.json")

def get_public_key(host, port) :
	network_info = load_config("node_info.json")
	nodes_info = network_info['nodes']
	
	for key, node in nodes_info.items() :
		if node['port'] == port :
			return key

def get_n_f() :
	network_info = load_config("node_info.json")
	return network_info['n'], network_info['c']

if __name__ == "__main__":
    
    # Default Host and port
    h = "127.0.0.1"
    p = 5000

    parser = argparse.ArgumentParser()
    parser.add_argument("-i", "--ip", help = "Host ip")
    parser.add_argument("-p", "--port", help = "Port")
    args = parser.parse_args()
    
    if args.ip:
        h = args.ip
    if args.port:
        p = int(args.port)
    
    public_key = get_public_key(host, port)
    n, c = get_n_c()
    f = (n - 2*c - 1) // 3
    
    app.run(debug=True, threaded=False, host = h, port = p)
