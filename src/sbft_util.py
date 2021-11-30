import os
import rsa
import time
import json
import uuid

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
    for i in range(number_of_nodes):
        key_pair = generate_rsa_key_pairs()
        server_ip = "127.0.0.1"
        port = port_start_number+i
        node_info = {}
        node_info["server_ip"] = server_ip
        node_info["port"] = port
        node_info["public_key"] = key_pair["public_key"]
        node_info["private_key"] = key_pair["private_key"]
        nodes[node_info["public_key"]] = node_info
    
    with open("node_info.json", "w") as info:
        json.dump(nodes, info)


