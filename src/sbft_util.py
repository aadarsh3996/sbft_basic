import os
import rsa
import time
import json
import uuid
import hashlib
from rsa import key


def generate_rsa_key_pairs():
    
    key_pairs = {}
    public_key, private_key = rsa.newkeys(2048)
    key_pairs['public_key'] = public_key.save_pkcs1().decode('utf8')
    key_pairs['private_key'] = private_key.save_pkcs1().decode('utf8')
    return key_pairs

def encrypt_data(encryption_key, message):
    
    return rsa.encrypt(message.encode('utf-8'), rsa.PublicKey.load_pkcs1(encryption_key.encode('utf-8')))

def decrypt_data(decryption_key, message):

    return rsa.decrypt(message, rsa.PrivateKey.load_pkcs1(decryption_key.encode('utf-8'))).decode('utf-8')

def create_transaction_id():

    return str(uuid.uuid4())

def time_now():
    return int(time.time())

def create_nodes(number_of_nodes):
    try:
        os.remove("node_info.json")
    except:
        pass
    port_start_number = 5000
    nodes = {}
    node_types= ["primary","c_collector","e_collector","replica"]
    for i in range(number_of_nodes):
        key_pair = generate_rsa_key_pairs()
        server_ip = "127.0.0.1"
        port = port_start_number+i
        node_info = {}
        node_info["server_ip"] = server_ip
        node_info["port"] = port
        node_info["public_key"] = key_pair["public_key"]
        node_info["private_key"] = key_pair["private_key"]
        if i==0:
            node_info['node_type'] = "primary"
        elif i == 1:
            node_info['node_type'] = "c_collector"
        elif i ==2:
            node_info["node_type"] = "e_collector"
        else:
            node_info["node_type"] = "replica"
        
        nodes[node_info["public_key"]] = node_info
    
    network_info = {}
    network_info['nodes'] = nodes
    network_info['trigger'] = False
    network_info['faulty'] = set()
    network_info['view_number'] = 0
    
    with open("network_info.json", "w") as info:
        json.dump(network_info, info)

def load_config(filename):
    config = {}
    with open(filename) as f:
        config = json.load(f)
        return config

def create_url(host, port, route):
    return "http://" + host + ":" + str(port) + "/" + route

def sort_and_convert_dict(d):
    s = ""
    for k in sorted(d.keys()):
        s+= k+" "+d[k] + " "
    return s 

def create_hash(data):
    return hashlib.sha256(data.encode()).hexdigest()