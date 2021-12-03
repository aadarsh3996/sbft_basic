import requests
import sbft_util

def create_transaction(data):
    network_info = sbft_util.load_config("node_info.json")
    nodes_info = network_info['nodes']
    
    for node in nodes_info.values():
        if node["node_type"] == "primary":
            host = node["server_ip"]
            port = node["port"]
            route = "start_transaction"
            temp = requests.post(sbft_util.create_url(host,port,route),data = data)
            print("&&&&&&Sent request&&&&&")
            break

data = {"hi":"hello"}
create_transaction(data)
