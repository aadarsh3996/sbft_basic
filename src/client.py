import requests
import sbft_util

def create_transaction(data):
    network_info = sbft_util.load_config("network_info.json")
    
    for node in network_info["nodes"].values():
        if node["node_type"] == "primary":
            host = node["server_ip"]
            port = node["port"]
            route = "pre_prepare"
            print("&&&&&&Sent request&&&&&")
            temp = requests.post(sbft_util.create_url(host,port,route),json=data)
            #temp = requests.post(sbft_util.create_url(host,port,"block_chain"))
            print(temp.text)
            break

data = {"hi":"hello"}
create_transaction(data)
