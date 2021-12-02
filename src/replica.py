from flask import Flask, request
from sbft_util import load_config, create_nodes, create_transaction_id, generate_rsa_key_pairs, create_url

import argparse
import requests

app = Flask(__name__)

@app.route("/start_transaction", methods = ['POST','GET'])
def start_transaction(data=None):
    network_info = load_config("node_info.json")
    for node in network_info.values():
        if node["node_type"] != "primary":
            d=requests.post(create_url(node["server_ip"],node["port"],"pre_prepare"),data=request.json)
        else:
            pre_prepare(data)

    print(request.json)
    return "<p>Hello, World!</p>"

@app.route("/pre_prepare", methods = ['POST','GET'])
def pre_prepare(data=None):
    network_info = load_config("node_info.json")
    print(request.json)
    return "<p>Hello, World!</p>"

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
    
    app.run(debug=True, threaded=False, host = h, port = p)